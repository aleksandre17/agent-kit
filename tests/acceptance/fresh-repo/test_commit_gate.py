"""Acceptance: the COMMIT GATE -- the runtime-independent return point (ADR-017 link C, slice C1c
part 3).

Whatever wrote a change -- a runtime with a pre-write hook, one without, a tool, a person -- the
change is recorded through a commit. A surface served for that return point projects a hook that
hands the STAGED change to the same one judge and the same host-declared gates, and a setting
outside the tree must name the served directory before git runs it at all. So:

  1. check READS that setting and names its state -- INACTIVE, ELSEWHERE, ACTIVE -- never assumes;
  2. the setting moves only through the `activate` door, which refuses to overwrite a setting it
     did not make and to switch off live hooks where git looks while it is unset;
  3. activated, git itself refuses a commit that introduces what a host gate forbids, and records
     a clean one and a pure deletion;
  4. withdrawal unsets the setting it made, and only that one.

Every repository here is a temporary fixture, removed with its configuration at teardown.
"""

from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path

import test_enforcement as enforcement  # first: it brings the harness, which places the kit's modules

import activate as activate_verb  # noqa: E402
import activated  # noqa: E402
import activation  # noqa: E402
import judge  # noqa: E402

HOST_GATE = enforcement.HOST_GATE
REFUSED = f"[{activation.ActivationRefused.code}]"
ACTIVE_GATE = next(g["id"] for c in enforcement.CORE.capabilities for g in c.gates if g["kind"] == activated.KIND)
VERB = Path(activate_verb.__file__).stem


def _git(host: Path, *argv, check=True) -> subprocess.CompletedProcess:
    env = dict(os.environ, GIT_AUTHOR_NAME="fixture", GIT_AUTHOR_EMAIL="fixture@example.invalid",
               GIT_COMMITTER_NAME="fixture", GIT_COMMITTER_EMAIL="fixture@example.invalid")
    ran = subprocess.run(["git", *argv], cwd=host, capture_output=True, text=True, env=env)
    if check and ran.returncode != 0:
        raise AssertionError(f"git {' '.join(argv)}: {ran.stderr}")
    return ran


class CommitGate(enforcement.Enforcement):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.activating = [s for s in cls.surfaces if "activation" in s and s["hands"].get("carries") == judge.CARRIES_PATCH]
        if not cls.activating:
            raise AssertionError("no taken adapter declares an activated patch-carrying surface -- "
                                 "this suite would pass on nothing")

    # The parent's own tests are its to run; here they are not collected a second time.
    locals().update({name: None for name in dir(enforcement.Enforcement) if name.startswith("test_")})

    def repository(self) -> Path:
        host = self.served_host([HOST_GATE])
        if not (host / ".git").exists():
            _git(host, "init", "-q")
        _git(host, "add", "-A")
        _git(host, "commit", "-q", "--no-verify", "-m", "the installed host")
        return host

    def activate(self, host, surface, *flags):
        return self.run_kit(self.kit, host, VERB, "--surface", surface["id"], *flags)

    def setting(self, host, surface) -> str:
        return _git(host, *surface["activation"]["read"][1:], check=False).stdout.strip()

    def test_292_check_reads_the_setting_and_names_inactive_elsewhere_and_active(self):
        for surface in self.activating:
            with self.subTest(surface=surface["id"]):
                host = self.repository()
                checked = self.run_kit(self.kit, host, "check")
                self.assertIn(f"{surface['id']}: {activation.INACTIVE}", checked.stdout)
                self.assertNotEqual(0, checked.returncode)

                _git(host, "config", "--local", surface["activation"]["setting"], "somewhere-else")
                checked = self.run_kit(self.kit, host, "check")
                self.assertIn(f"{surface['id']}: {activation.ELSEWHERE}", checked.stdout)
                self.assertIn("somewhere-else", checked.stdout)
                _git(host, "config", "--local", "--unset", surface["activation"]["setting"])

                self.assertEqual(0, self.activate(host, surface, "--approve", "fixture-owner").returncode)
                checked = self.run_kit(self.kit, host, "check")
                self.assertIn(f"{surface['id']}: {activation.ACTIVE}", checked.stdout)
                self.assertNotIn(f"FAIL  {ACTIVE_GATE}", checked.stdout)

    def test_293_the_door_plans_refuses_unapproved_and_never_clobbers(self):
        for surface in self.activating:
            with self.subTest(surface=surface["id"]):
                host = self.repository()
                planned = self.activate(host, surface, "--plan")
                self.assertEqual(0, planned.returncode, planned.stdout + planned.stderr)
                self.assertEqual("", self.setting(host, surface), "a plan changed the setting")
                unapproved = self.activate(host, surface)
                self.assertNotEqual(0, unapproved.returncode)
                self.assertEqual("", self.setting(host, surface), "an unwalked door changed the setting")

                _git(host, "config", "--local", surface["activation"]["setting"], "theirs")
                clobber = self.activate(host, surface, "--approve", "fixture-owner")
                self.assertNotEqual(0, clobber.returncode)
                self.assertIn(REFUSED, clobber.stderr)
                self.assertEqual("theirs", self.setting(host, surface))
                withdraw = self.activate(host, surface, "--to", activate_verb.TO_INACTIVE, "--approve", "fixture-owner")
                self.assertIn(REFUSED, withdraw.stderr)
                self.assertEqual("theirs", self.setting(host, surface), "the kit withdrew a setting it did not make")
                _git(host, "config", "--local", "--unset", surface["activation"]["setting"])

                hooks = Path(_git(host, *surface["activation"]["occupied"]["read"][1:]).stdout.strip())
                live = (hooks if hooks.is_absolute() else host / hooks) / "pre-commit"
                live.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8", newline="\n")
                occupied = self.activate(host, surface, "--approve", "fixture-owner")
                self.assertIn(REFUSED, occupied.stderr)
                self.assertIn("pre-commit", occupied.stderr)
                self.assertEqual("", self.setting(host, surface))

    def test_294_activated_git_refuses_a_violating_commit_and_records_a_clean_one(self):
        for surface in self.activating:
            with self.subTest(surface=surface["id"]):
                host = self.repository()
                self.assertEqual(0, self.activate(host, surface, "--approve", "fixture-owner").returncode)
                before = _git(host, "rev-parse", "HEAD").stdout.strip()
                (host / "src").mkdir(exist_ok=True)

                (host / "src" / "a.ts").write_text("let y = ctx.year;\n", encoding="utf-8", newline="\n")
                _git(host, "add", "src/a.ts")
                refused = _git(host, "commit", "-m", "a violation", check=False)
                self.assertNotEqual(0, refused.returncode, refused.stdout + refused.stderr)
                self.assertIn(HOST_GATE["id"], refused.stderr)
                self.assertEqual(before, _git(host, "rev-parse", "HEAD").stdout.strip())

                (host / "src" / "a.ts").write_text("let y = ctx.dims['time'];\n", encoding="utf-8", newline="\n")
                _git(host, "add", "src/a.ts")
                clean = _git(host, "commit", "-m", "clean", check=False)
                self.assertEqual(0, clean.returncode, clean.stdout + clean.stderr)

                _git(host, "rm", "-q", "src/a.ts")
                deletion = _git(host, "commit", "-m", "a pure deletion", check=False)
                self.assertEqual(0, deletion.returncode, deletion.stdout + deletion.stderr)

    def test_295_withdrawal_unsets_the_setting_it_made(self):
        for surface in self.activating:
            with self.subTest(surface=surface["id"]):
                host = self.repository()
                self.assertEqual(0, self.activate(host, surface, "--approve", "fixture-owner").returncode)
                self.assertEqual(surface["activation"]["points_at"].rstrip("/"), self.setting(host, surface))
                withdrawn = self.activate(host, surface, "--to", activate_verb.TO_INACTIVE, "--approve", "fixture-owner")
                self.assertEqual(0, withdrawn.returncode, withdrawn.stdout + withdrawn.stderr)
                self.assertEqual("", self.setting(host, surface))
                self.assertIn(f"{surface['id']}: {activation.INACTIVE}", self.run_kit(self.kit, host, "check").stdout)


if __name__ == "__main__":
    unittest.main()
