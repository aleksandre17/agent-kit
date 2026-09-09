"""Acceptance: install the kit into a repository that has never seen it.

This is the only test that measures the framework's central claim. A kit exercised only inside the
repository that grew it cannot tell UNIVERSAL from FAMILIAR: everything works there, and nothing
was measured. So the host here is an empty scratch git repository, created fresh, and the kit is
reached ONLY through `kit/` -- never through the framework's own tree.

Run:  python tests/acceptance/fresh-repo/test_fresh_repo.py
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
KIT = REPO / "kit"
CLI = KIT / "interpreters" / "cli.py"

for extra in (KIT / "interpreters", KIT / "interpreters" / "ports", KIT / "interpreters" / "verbs"):
    sys.path.insert(0, str(extra))

from manifest import Manifest  # noqa: E402
from workspace import Workspace, WriteScopeError  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(root: Path, rel: str) -> dict:
    base = root / rel
    out = {}
    for dirpath, _dirs, files in os.walk(base):
        for name in files:
            whole = Path(dirpath) / name
            out[whole.relative_to(root).as_posix()] = sha(whole)
    return out


class FreshRepo(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="kit-fresh-")).resolve()
        subprocess.run(["git", "init", "--quiet", str(cls.tmp)], check=True,
                       capture_output=True, text=True)
        cls.manifest = Manifest(KIT)
        cls.first = cls.run_verb("init")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    @classmethod
    def run_verb(cls, verb: str):
        result = subprocess.run(
            [sys.executable, str(CLI), verb, "--root", str(cls.tmp), "--kit", str(KIT)],
            capture_output=True, text=True,
        )
        print(f"\n$ python kit/interpreters/cli.py {verb} --root <scratch>\n"
              f"[exit {result.returncode}]\n{result.stdout}{result.stderr}")
        return result

    # -- the install ------------------------------------------------------------------------
    def test_01_init_succeeds_into_an_empty_git_repo(self):
        self.assertEqual(0, self.first.returncode, self.first.stderr)

    def test_02_bindings_exist_and_honour_their_schemas(self):
        for rel, schema in ((".agents/project/project.json", "project"),
                            (".agents/project/profile.json", "profile")):
            target = self.tmp / rel
            self.assertTrue(target.is_file(), f"{rel} was not created")
            errors = self.manifest.validate(json.loads(target.read_text(encoding="utf-8")), schema)
            self.assertEqual([], errors, f"{rel}: {errors}")

    def test_03_the_reading_states_when_it_was_taken(self):
        profile = json.loads((self.tmp / ".agents/project/profile.json").read_text(encoding="utf-8"))
        self.assertTrue(profile["taken_at"], "a reading with no moment cannot be contradicted")
        self.assertIn("+00:00", profile["taken_at"])
        self.assertTrue(profile["facts"].get("vcs.git"), "the host is a git repository and was measured as one")
        self.assertEqual(profile["boundary"]["path_separator"], "/")

    def test_04_every_produced_path_resolves_to_exactly_one_class(self):
        declared = [(p["root"].rstrip("/") + "/", p["class"]) for p in self.manifest.planes]
        for capability in self.manifest.capabilities:
            for item in capability.installs:
                declared.append((item["target"], item["class"]))
        produced = digest(self.tmp, ".agents")
        self.assertTrue(produced, "the kit produced nothing at all")
        for rel in produced:
            classes = {k for prefix, k in declared if rel == prefix or rel.startswith(prefix)}
            self.assertEqual(1, len(classes), f"{rel} resolves to {sorted(classes)}")

    def test_05_check_exits_zero(self):
        self.assertEqual(0, self.run_verb("check").returncode)

    # -- re-running -------------------------------------------------------------------------
    def test_06_second_init_mutates_no_binding_file(self):
        before = digest(self.tmp, ".agents/project")
        before[".agents/.gitignore"] = sha(self.tmp / ".agents/.gitignore")
        second = self.run_verb("init")
        self.assertEqual(0, second.returncode)
        after = digest(self.tmp, ".agents/project")
        after[".agents/.gitignore"] = sha(self.tmp / ".agents/.gitignore")
        self.assertEqual(before, after, "a second init rewrote host truth")
        self.assertIn("kept", second.stdout, "a second init should keep bindings, not create them")

    def test_07_render_is_byte_reproducible(self):
        before = digest(self.tmp, ".agents/generated")
        self.assertTrue(before, "nothing was projected")
        shutil.rmtree(self.tmp / ".agents/generated")
        self.assertEqual(0, self.run_verb("render").returncode)
        self.assertEqual(before, digest(self.tmp, ".agents/generated"),
                         "a deleted projection did not come back byte-identical")

    # -- the port that bounds every write ---------------------------------------------------
    def test_08_workspace_refuses_a_write_outside_declared_installs(self):
        capability = self.manifest.capabilities[0]
        scoped = Workspace(self.tmp).scoped(capability.targets())
        rogue = ".agents/project/rogue.md"
        self.assertNotIn(rogue, capability.targets())
        with self.assertRaises(WriteScopeError) as refusal:
            scoped.write_text(rogue, "a capability writing where nothing declared it may")
        print(f"\n[refusal] {refusal.exception}")
        self.assertFalse((self.tmp / rogue).exists(), "the refusal must precede the byte")
        # and the same port, scoped as the capability declared it, does write:
        declared = capability.targets()[0]
        scoped.write_text(declared, (self.tmp / declared).read_text(encoding="utf-8"))

    def test_09_escaping_the_root_is_refused_too(self):
        with self.assertRaises(Exception):
            Workspace(self.tmp).write_text("../outside.md", "x")

    # -- what the kit does where its requirements are NOT met --------------------------------
    def test_10_a_host_that_fails_a_requirement_is_told_so(self):
        plain = Path(tempfile.mkdtemp(prefix="kit-nogit-")).resolve()
        try:
            result = subprocess.run(
                [sys.executable, str(CLI), "init", "--root", str(plain), "--kit", str(KIT)],
                capture_output=True, text=True,
            )
            print(f"\n$ init into a directory that is not a repository\n"
                  f"[exit {result.returncode}]\n{result.stdout}{result.stderr}")
            self.assertNotEqual(0, result.returncode)
            self.assertIn("unavailable", result.stdout)
            self.assertNotIn("Traceback", result.stderr, "a known situation must not arrive as a stack trace")
        finally:
            shutil.rmtree(plain, ignore_errors=True)

    def test_11_a_malformed_binding_is_a_named_refusal_not_a_traceback(self):
        (self.tmp / ".agents/project/project.json").write_text('{"schema_version": 1}', encoding="utf-8")
        result = self.run_verb("check")
        self.assertEqual(1, result.returncode)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("does not honour schema", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
