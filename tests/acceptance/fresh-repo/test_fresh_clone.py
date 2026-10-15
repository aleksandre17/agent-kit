"""Acceptance: the floor and the reading hold on a FRESH CLONE (ADR-021 decision 8, slice S5).

A host is a repository, and a repository is what a clone receives -- not the working copy it was
made from. Two things used to differ between them, and each read as a broken host on a clean clone:

  1. drawn places in the OBSERVED plane (a run's journal, its hold) exist only where a run left
     them, and no version control carries them -- the floor names them and never judges them;
  2. a probe read the filesystem, so a file the repository does not carry -- a dependency
     directory, a build output -- became a fact about the host, and the reading went stale on the
     next clean clone. A probe now reads what the repository carries.

Held here: an installed host, committed and cloned, checks green on the clone; and a project file
inside an ignored directory is never evidence. Every path, fact and detector is read from the
declaration that owns it.
"""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

from harness import KIT, Fixtures

from manifest import Manifest  # noqa: E402

CORE = Manifest(KIT)
#: A detector whose evidence is a pattern anywhere in the tree, and the fact it emits -- read from
#: the kit's own detector declarations, never named here.
DETECTOR = next(json.loads(p.read_text(encoding="utf-8")) for p in sorted((KIT / "detectors").glob("*.json"))
                if any(e["kind"] == "glob_any" and e["pattern"].startswith("**/") and not e.get("optional")
                       for e in json.loads(p.read_text(encoding="utf-8"))["evidence"]))
PATTERN = next(e["pattern"] for e in DETECTOR["evidence"] if e["kind"] == "glob_any" and not e.get("optional"))
FACT = next(k for k, v in DETECTOR["emits"].items() if v is True)
PROFILE = next(i["target"] for c in CORE.capabilities for i in c.installs if i.get("validates") == "profile")


def _git(root: Path, *argv: str) -> None:
    subprocess.run(["git", "-C", str(root), "-c", "user.email=suite@kit", "-c", "user.name=suite", *argv],
                   check=True, capture_output=True)


class FreshClone(Fixtures, unittest.TestCase):

    def test_350_an_installed_host_checks_green_on_a_fresh_clone(self):
        host = self.installed()
        _git(host, "add", "-A")
        _git(host, "commit", "-qm", "the host as installed")
        clone = self._temp("kit-clone-") / "host"
        subprocess.run(["git", "clone", "-q", str(host), str(clone)], check=True, capture_output=True)
        ran = self.run_kit(KIT, clone, "check")
        self.assertEqual(0, ran.returncode, ran.stdout + ran.stderr)
        self.assertIn("NOT MEASURED", ran.stdout, "the observed plane was not named on the clone")

    def test_351_a_file_the_repository_does_not_carry_is_never_evidence(self):
        ignored = "an-ignored-directory"
        for where, carried in ((f"{ignored}/nested/", False), ("src/", True)):
            with self.subTest(carried=carried):
                # Planted BEFORE the first reading: a reading is taken once and never restated.
                host = self.host()
                (host / ".gitignore").write_text(f"{ignored}/\n", encoding="utf-8", newline="\n")
                planted = host / PATTERN.replace("**/", where).replace("*", "planted")
                planted.parent.mkdir(parents=True, exist_ok=True)
                planted.write_text("a project file\n", encoding="utf-8")
                self.run_kit(KIT, host, "init")
                ran = self.run_kit(KIT, host, "init", "--approve", "acceptance-suite")
                self.assertEqual(0, ran.returncode, ran.stdout + ran.stderr)
                facts = json.loads((host / PROFILE).read_text(encoding="utf-8"))["facts"]
                if carried:
                    self.assertIn(FACT, facts, "a file the repository carries was not read")
                else:
                    self.assertNotIn(FACT, facts, f"a file inside {ignored}/ became a fact about the host")


    def test_352_a_space_opened_before_its_marker_is_completed_and_survives_the_clone(self):
        # A host installed before spaces carried a marker holds the bare directory: committed, it is
        # gone from the clone. The next init completes the space with its marker and nothing else.
        import space as space_module

        # Both doors that install complete it: `init` by its own foresight, `upgrade` by the
        # reconciliation that answers before the installer is asked (one rule: space.carried).
        target = next(i["target"] for c in CORE.capabilities for i in c.installs if i["mode"] in space_module.MODES)
        for verb in (("init", "--approve", "acceptance-suite"), ("upgrade",)):
            with self.subTest(verb=verb[0]):
                host = self.installed()
                marker = host / space_module.marker_in(CORE, target)
                marker.unlink()
                ran = self.run_kit(KIT, host, *verb)
                self.assertEqual(0, ran.returncode, ran.stdout + ran.stderr)
                self.assertTrue(marker.is_file(), f"{verb[0]} kept {target} without the marker that carries it")
                _git(host, "add", "-A")
                _git(host, "commit", "-qm", "the host as completed")
                clone = self._temp("kit-clone-") / "host"
                subprocess.run(["git", "clone", "-q", str(host), str(clone)], check=True, capture_output=True)
                ran = self.run_kit(KIT, clone, "check")
                self.assertEqual(0, ran.returncode, ran.stdout + ran.stderr)


if __name__ == "__main__":
    unittest.main()
