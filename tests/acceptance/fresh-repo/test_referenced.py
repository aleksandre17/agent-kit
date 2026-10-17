"""Acceptance: a REFERENCED host runs the kit it holds in its own tree, and keeps no copy (ADR-024 d. 18).

A host that holds the kit as a nested repository (a submodule) already pins it by commit; a vendored
copy beside it is a second source for one pin. Held here, on a host whose kit lives in its own tree:

  1. `upgrade --mode referenced` rewrites the lock to reference the kit at its commit, serves every
     setting to run it from there, checks green, and only then removes the copies;
  2. an edit to the referenced kit -- uncommitted -- is refused before any verb runs: `check` red, a
     blocking hook closed; restored, green again;
  3. a kit moved to another commit is named until it is pinned again;
  4. a missing kit (an uninitialised submodule) fails closed with the command that restores it;
  5. a reference that cannot be honest -- a kit outside the host, an uncommitted kit -- is refused.

Every seat, path, code and command is read from the declarations and the module that owns it.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

from harness import KIT, REPO, Fixtures, ship

import hooks
import pin
import provenance
import reference
from manifest import Manifest
from test_adapters import RECORD
from test_hooks import SURFACE
from test_pinned_kit import said

CORE = Manifest(KIT)
TREE, SEAT = pin.seats(CORE)
TAKEN_PLANE = next(i["target"] for c in CORE.capabilities for i in c.installs if i["mode"] == reference.TAKEN)
#: Where the nested kit sits in the host: any path inside it would do.
NESTED = Path("platform") / "kits" / "agent-kit"
PUBLISHED = ("adapters", "bundles", "policies", "starters")
GIT_ENV = {"GIT_AUTHOR_NAME": "suite", "GIT_AUTHOR_EMAIL": "s@invalid",
           "GIT_COMMITTER_NAME": "suite", "GIT_COMMITTER_EMAIL": "s@invalid"}


def git(where, *argv):
    return subprocess.run(["git", "-C", str(where), *argv], capture_output=True, text=True,
                          env={**os.environ, **GIT_ENV})


class Referenced(Fixtures, unittest.TestCase):

    def nested(self):
        host = self.host()
        source = host / NESTED
        ship(source / "kit")
        for name in PUBLISHED:
            shutil.copytree(REPO / name, source / name, ignore=shutil.ignore_patterns("__pycache__"))
        # The kit's own line-ending rule travels with it, as it does in any clone of it.
        shutil.copyfile(REPO / ".gitattributes", source / ".gitattributes")
        git(source, "init", "--quiet")
        git(source, "add", "-A")
        git(source, "commit", "--quiet", "-m", "the kit")
        return host, source

    def kit(self, source, host, verb, *flags, stdin=None):
        ran = subprocess.run([sys.executable, "-I", "-B", str(source / "kit" / "interpreters" / "cli.py"), verb,
                              "--root", str(host), *flags], input=stdin, capture_output=True, text=True)
        print(f"\n$ {verb} {' '.join(flags)}\n[exit {ran.returncode}]\n{ran.stdout}{ran.stderr}")
        return ran

    def referenced(self):
        host, source = self.nested()
        started = self.kit(source, host, "start", "--path", str(source / "starters" / "standard.json"),
                           "--approve", "acceptance-suite")
        self.assertEqual(0, started.returncode, said(started))
        self.assertTrue((host / TREE).is_dir(), "the host was not vendored first")
        moved = self.kit(source, host, "upgrade", "--mode", "referenced", "--approve", "acceptance-suite")
        self.assertEqual(0, moved.returncode, said(moved))
        return host, source

    def test_560_a_referenced_host_runs_its_own_kit_and_keeps_no_copy(self):
        host, source = self.referenced()
        held = json.loads((host / SEAT).read_text(encoding="utf-8"))[reference.FIELD]
        self.assertEqual((NESTED / "kit").as_posix(), held["path"])
        self.assertEqual(git(source, "rev-parse", "HEAD").stdout.strip(), held["commit"])
        self.assertEqual(NESTED.as_posix(), held["repository"])
        self.assertFalse((host / TREE).exists(), "the vendored kit was kept")
        self.assertTrue(held["takes"])
        for take in held["takes"]:
            self.assertFalse((host / TAKEN_PLANE / take["id"]).exists(), f"{take['id']} was kept as a copy")
            self.assertTrue((host / take["path"]).is_dir())
        served = [row["path"] for row in json.loads((host / RECORD).read_text(encoding="utf-8"))["served"]]
        # Every served SETTING that runs the kit (a hook, a pipeline); a context file is prose.
        running = [p for p in served if "interpreters/cli.py" in (host / p).read_text(encoding="utf-8")
                   and not p.endswith(".md")]
        self.assertTrue(running)
        for path in running:
            text = (host / path).read_text(encoding="utf-8")
            self.assertIn(f"{held['path']}/interpreters/cli.py", text, path)
            self.assertNotIn(f"{TREE}interpreters/cli.py", text, path)
        self.assertEqual(0, self.kit(source, host, "check").returncode)

    def test_561_an_edited_kit_is_refused_and_a_moved_one_is_named_until_pinned(self):
        host, source = self.referenced()
        readme = source / "kit" / "README.md"
        readme.write_bytes(readme.read_bytes() + b"an edit nobody pinned\n")
        checked = self.kit(source, host, "check")
        self.assertNotEqual(0, checked.returncode)
        self.assertIn(f"[{reference.ReferenceRefused.code}]", checked.stderr)
        closed = self.kit(source, host, "spawn", "--surface", SURFACE["id"], stdin="{}")
        self.assertEqual(SURFACE["hands"]["refusal"]["exit"], closed.returncode, said(closed))
        git(source, "checkout", "--", ".")
        self.assertEqual(0, self.kit(source, host, "check").returncode)
        # Another commit of the same bytes: named until the host pins it.
        git(source, "commit", "--quiet", "--allow-empty", "-m", "moved")
        moved = self.kit(source, host, "check")
        self.assertNotEqual(0, moved.returncode)
        self.assertIn(reference.RESTORE, moved.stdout + moved.stderr)
        pinned = self.kit(source, host, "upgrade", "--mode", "referenced", "--approve", "acceptance-suite")
        self.assertEqual(0, pinned.returncode, said(pinned))
        self.assertEqual(0, self.kit(source, host, "check").returncode)

    def test_562_a_missing_kit_fails_closed_with_the_command_that_restores_it(self):
        host, source = self.referenced()
        away = source.with_name("elsewhere")
        source.rename(away)
        try:
            ran = self.run_kit(KIT, host, "check")
            self.assertNotEqual(0, ran.returncode)
            self.assertIn(f"{reference.RESTORE} {NESTED.as_posix()}", ran.stderr)
            hook = subprocess.run([sys.executable, "-I", "-B", str(KIT / "interpreters" / "cli.py"), "spawn",
                                   "--root", str(host), "--surface", SURFACE["id"]],
                                  input="{}", capture_output=True, text=True)
            self.assertEqual(hooks.CLOSED, hook.returncode, said(hook))
        finally:
            away.rename(source)

    def test_563_a_reference_that_cannot_be_honest_is_refused(self):
        host, source = self.nested()
        started = self.kit(source, host, "start", "--path", str(source / "starters" / "standard.json"),
                           "--approve", "acceptance-suite")
        self.assertEqual(0, started.returncode, said(started))
        outside = self.run_kit(KIT, host, "upgrade", "--mode", "referenced", "--approve", "acceptance-suite")
        self.assertIn(f"[{reference.ReferenceRefused.code}]", outside.stderr)
        (source / "kit" / "stray.txt").write_text("uncommitted\n", encoding="utf-8")
        dirty = self.kit(source, host, "upgrade", "--mode", "referenced", "--approve", "acceptance-suite")
        self.assertIn(f"[{reference.ReferenceRefused.code}]", dirty.stderr)
        self.assertTrue((host / TREE).is_dir(), "a refused reference removed the vendored kit")


    def assertReferenced(self, host, source):
        held = json.loads((host / SEAT).read_text(encoding="utf-8")).get(reference.FIELD)
        self.assertIsNotNone(held, "the lock lost its reference block")
        self.assertEqual(git(source, "rev-parse", "HEAD").stdout.strip(), held["commit"])
        self.assertFalse((host / TREE).exists(), "the vendored kit was re-created")
        for take in held["takes"]:
            self.assertFalse((host / TAKEN_PLANE / take["id"]).exists(), f"{take['id']} was copied again")
        self.assertEqual(0, self.kit(source, host, "check").returncode)
        return held

    def bump(self, source, capability="stack-kit"):
        """The submodule advances: a taken capability is re-released at a newer version."""
        declaration = source / "adapters" / capability / "capability.json"
        raw = json.loads(declaration.read_text(encoding="utf-8"))
        major, minor, patch = (int(n) for n in raw["version"].split("."))
        raw["version"] = f"{major}.{minor}.{patch + 1}"
        raw["summary"] += " Re-released."
        declaration.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
        git(source, "commit", "--quiet", "-am", f"{capability} {raw['version']}")
        return raw["version"]

    def test_564_a_plain_upgrade_on_a_referenced_host_keeps_it_referenced(self):
        host, source = self.referenced()
        plain = self.kit(source, host, "upgrade", "--approve", "acceptance-suite")
        self.assertEqual(0, plain.returncode, said(plain))
        self.assertReferenced(host, source)

    def test_565_an_advanced_submodule_with_a_newer_take_is_carried_in_one_walk(self):
        host, source = self.referenced()
        version = self.bump(source)
        unapproved = self.kit(source, host, "upgrade", "--mode", "referenced")
        self.assertNotEqual(0, unapproved.returncode)
        self.assertIn(f"stack-kit@{version}", unapproved.stdout + unapproved.stderr)
        carried = self.kit(source, host, "upgrade", "--mode", "referenced", "--approve", "acceptance-suite")
        self.assertEqual(0, carried.returncode, said(carried))
        self.assertReferenced(host, source)
        estate = next(p for p in (host / ".agents").rglob("*.json") if '"taken"' in p.read_text(encoding="utf-8")
                      and '"pinned_by"' in p.read_text(encoding="utf-8"))
        pins = {p["capability"]: p for p in json.loads(estate.read_text(encoding="utf-8"))["taken"]}
        self.assertEqual(version, pins["stack-kit"]["version"])
        self.assertIn("supersedes", pins["stack-kit"])
        self.assertEqual(0, self.kit(source, host, "start", "--path", str(source / "starters" / "standard.json"),
                                     "--approve", "acceptance-suite").returncode)

    def test_568_a_host_truth_the_kit_introduces_is_created_once_by_a_referenced_upgrade(self):
        """A host given its kit before a capability declared a seed has no such file: the referenced
        upgrade that brings the declaration creates it -- once, through its install mode -- and leaves
        every truth the host already holds untouched."""
        host, source = self.referenced()
        seeds = [i["target"] for c in CORE.capabilities for i in c.installs
                 if i.get("mode") == "seed" and i.get("class") == "binding" and (host / i["target"]).is_file()]
        self.assertTrue(len(seeds) > 1, "no host-owned seed to withhold -- this would pass on nothing")
        withheld, kept = seeds[0], seeds[-1]
        (host / withheld).unlink()
        marker = (host / kept).read_text(encoding="utf-8")
        planned = self.kit(source, host, "upgrade", "--mode", "referenced", "--plan")
        self.assertEqual(0, planned.returncode, said(planned))
        self.assertIn(f"create {withheld}", planned.stdout)
        carried = self.kit(source, host, "upgrade", "--mode", "referenced", "--approve", "acceptance-suite")
        self.assertEqual(0, carried.returncode, said(carried))
        self.assertTrue((host / withheld).is_file(), f"{withheld} was not created")
        self.assertEqual(marker, (host / kept).read_text(encoding="utf-8"), "a held truth was rewritten")
        self.assertEqual(0, self.kit(source, host, "check").returncode)

    def test_566_changed_bytes_under_the_same_version_stay_drift(self):
        host, source = self.referenced()
        declaration = source / "adapters" / "stack-kit" / "capability.json"
        declaration.write_bytes(declaration.read_bytes() + b"\n")
        git(source, "commit", "--quiet", "-am", "same version, other bytes")
        drift = self.kit(source, host, "upgrade", "--mode", "referenced", "--approve", "acceptance-suite")
        self.assertNotEqual(0, drift.returncode)
        self.assertIn(f"[{provenance.ProvenanceRefused.code}]", drift.stderr)

    def test_567_only_a_vendored_mode_asked_by_name_returns_the_copies(self):
        host, source = self.referenced()
        held = json.loads((host / SEAT).read_text(encoding="utf-8"))[reference.FIELD]
        back = self.kit(source, host, "upgrade", "--mode", "vendored", "--approve", "acceptance-suite")
        self.assertEqual(0, back.returncode, said(back))
        self.assertNotIn(reference.FIELD, json.loads((host / SEAT).read_text(encoding="utf-8")))
        self.assertTrue((host / TREE).is_dir(), "the vendored kit was not delivered")
        for take in held["takes"]:
            self.assertTrue((host / TAKEN_PLANE / take["id"]).is_dir(), f"{take['id']} was not copied")
        self.assertEqual(0, self.run_kit(host / TREE, host, "check").returncode)

if __name__ == "__main__":
    unittest.main()
