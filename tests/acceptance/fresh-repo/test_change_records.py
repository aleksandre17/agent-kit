"""Acceptance: change records cover a review range; an execution graph derives its units' obligations (ADR-024).

Both are opt-in bundles a host takes. Held here, on a started host that takes them:

  1. a VERIFIED record over a file, with its tests, evidence and source digests, keeps `check` green; when
     the file moves after it was verified the record is STALE and `check` fails by name;
  2. `review --base --head` on a clean checkout names a changed path no verified record covers, and
     passes once one does -- reporting coverage CHECKED and runtime conformance NOT_ASSERTED;
  3. a unit that writes a governed object owes the backup the REGISTRY says that write obliges, and
     `check` fails until the unit points at one.

Every path, field and code is read from the declarations and the modules that own them.
"""

from __future__ import annotations

import json
import subprocess
import unittest

from harness import KIT, REPO, Fixtures

import changes
from context import Context
from test_pinned_kit import said

STARTER = REPO / "starters" / "standard.json"
BUNDLES = [REPO / "bundles" / name for name in ("change-records", "execution-graph")]


def _installs(bundle, contract):
    value = json.loads((bundle / "capability.json").read_text(encoding="utf-8"))
    return next(i["target"] for i in value["installs"] if i.get("validates") == contract)


class ChangeRecords(Fixtures, unittest.TestCase):

    def started(self):
        host = self.host()
        starter = json.loads(STARTER.read_text(encoding="utf-8"))
        starter["takes"] = [str((STARTER.parent / t).resolve()) for t in starter["takes"]] + [str(b) for b in BUNDLES]
        written = self._temp("starter-") / "starter.json"
        written.write_text(json.dumps(starter), encoding="utf-8")
        ran = self.run_kit(KIT, host, "start", "--path", str(written), "--approve", "acceptance-suite")
        self.assertEqual(0, ran.returncode, said(ran))
        return host

    def git(self, host, *argv):
        return subprocess.run(["git", "-C", str(host), "-c", "user.email=s@invalid", "-c", "user.name=suite", *argv],
                              capture_output=True, text=True)

    def record(self, host, path, **fields):
        """A VERIFIED record over `path` and the two files the record itself brings (its evidence and
        the catalogue), with the digests of all three -- a change covers every path it touches."""
        ctx = Context(kit_root=KIT, host_root=host)
        catalogue = _installs(BUNDLES[0], changes.CATALOGUE[0]["validates"])
        (host / catalogue).write_text(json.dumps({"schema_version": 1, "requirements": [{"id": "R-1", "says": "x"}]}) + "\n",
                                      encoding="utf-8", newline="\n")
        (host / "evidence.txt").write_text("the run's output\n", encoding="utf-8", newline="\n")
        files = [path, "evidence.txt", catalogue]
        value = {"schema_version": 1, "id": "a-change", "status": changes.VERIFIED, "summary": "a fixture change",
                 "files": files, "requirements": {"R-1": {"decision": "APPLY", "reason": "it is code"}},
                 "tests": [{"command": "the suite", "exit_code": 0, "environment": "this machine"}],
                 "evidence": [{"path": "evidence.txt", "sha256": changes.digest(ctx, "evidence.txt")}],
                 "source_digests": {f: changes.digest(ctx, f) for f in files}, **fields}
        home = _installs(BUNDLES[0], changes.RECORDS[0]["validates"])
        (host / home).mkdir(parents=True, exist_ok=True)
        (host / home / "a-change.json").write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")

    def test_490_a_verified_record_holds_until_its_source_moves(self):
        host = self.started()
        (host / "src.txt").write_text("one\n", encoding="utf-8", newline="\n")
        self.record(host, "src.txt")
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode)
        (host / "src.txt").write_text("two\n", encoding="utf-8", newline="\n")
        checked = self.run_kit(KIT, host, "check")
        self.assertNotEqual(0, checked.returncode)
        self.assertIn("STALE", said(checked))

    def test_491_a_review_range_is_covered_by_verified_records(self):
        host = self.started()
        self.git(host, "add", "-A")
        self.git(host, "commit", "-q", "--no-verify", "-m", "the install")
        base = self.git(host, "rev-parse", "HEAD").stdout.strip()
        (host / "src.txt").write_text("one\n", encoding="utf-8", newline="\n")
        self.git(host, "add", "-A")
        self.git(host, "commit", "-q", "--no-verify", "-m", "a change")
        head = self.git(host, "rev-parse", "HEAD").stdout.strip()
        uncovered = self.run_kit(KIT, host, "review", "--base", base, "--head", head)
        self.assertEqual(1, uncovered.returncode, said(uncovered))
        self.assertIn("src.txt", uncovered.stdout)
        self.record(host, "src.txt")
        self.git(host, "add", "-A")
        self.git(host, "commit", "-q", "--no-verify", "-m", "its record")
        head = self.git(host, "rev-parse", "HEAD").stdout.strip()
        covered = self.run_kit(KIT, host, "review", "--base", base, "--head", head)
        self.assertEqual(0, covered.returncode, said(covered))
        report = json.loads(covered.stdout[covered.stdout.index("{"):])
        self.assertEqual((changes.CHECKED, changes.NOT_ASSERTED), (report["change_coverage"], report["runtime_conformance"]))

    def test_492_a_unit_owes_what_the_registry_obliges(self):
        host = self.started()
        graph = _installs(BUNDLES[1], "execution-graph")
        value = {"schema_version": 1, "objects": [{"id": "ledger", "obliges": {"write": ["backup"]}}],
                 "units": [{"id": "u1", "operations": [{"verb": "write", "object": "ledger"}]}]}
        (host / graph).write_text(json.dumps(value) + "\n", encoding="utf-8", newline="\n")
        owing = self.run_kit(KIT, host, "check")
        self.assertNotEqual(0, owing.returncode)
        self.assertIn("owes 'backup'", said(owing))
        (host / "backup.txt").write_text("a backup\n", encoding="utf-8")
        value["units"][0]["satisfies"] = {"backup": "backup.txt"}
        (host / graph).write_text(json.dumps(value) + "\n", encoding="utf-8", newline="\n")
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode)


if __name__ == "__main__":
    unittest.main()
