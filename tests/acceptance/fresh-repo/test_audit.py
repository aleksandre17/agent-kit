"""Acceptance: the whole-tree audit -- the violations already standing in a tree (ADR-024 decision 20).

An edit gate judges only the text a change introduces, so a violation committed before the gate is
never seen by `judge`. `audit` runs every calibrated edit gate in force over every tracked file:

  1. a pre-existing violation is found, as path:line, gate and `because`, and fails the audit;
  2. one acknowledged by declaration prints KNOWN with its tracking and passes;
  3. an acknowledgement whose `until` has passed is a finding again;
  4. an acknowledgement matching nothing is reported STALE;
  5. a secret-shaped finding is located and never repeated;
  6. `check` reports the counts on every run, and fails on them only when the host raises the stance.

Gate ids, paths and the acknowledgement file arrive from the declarations, never spelled twice.
"""

from __future__ import annotations

import json
import subprocess
import unittest

from harness import KIT, REPO, Fixtures
from manifest import Manifest

CORE = Manifest(KIT)
ENFORCEMENT = next(c for c in CORE.capabilities if any(g["kind"] == "tree-audited" for g in c.gates))
GATES_FILE = next(i["target"] for i in ENFORCEMENT.installs if i.get("validates") == "edit-gate")
KNOWN_FILE = next(i["target"] for i in ENFORCEMENT.installs if i.get("validates") == "known-violations")
AUDIT_GATE = next(g["id"] for g in ENFORCEMENT.gates if g["kind"] == "tree-audited")
ANSWERS = next(i["target"] for c in CORE.capabilities for i in c.installs if i["mode"] == "declaration")
SECRETS = json.loads((REPO / "policies" / "secrets" / "payload" / "edit-gates.json").read_text(encoding="utf-8"))
CLOUD_KEY = next(g for g in SECRETS["gates"] if g["id"] == "no-cloud-access-key")
HOST_GATE = {
    "id": "no-privileged-dimension",
    "paths": r"^src/",
    "forbids": r"ctx\.year",
    "because": "a privileged dimension.",
    "instead": "ctx.dims['time'].",
    "proves": {"path": "src/a.ts", "text": "const y = ctx.year"},
    "admits": {"path": "src/a.ts", "text": "const y = ctx.dims['time']"},
}
#: A cloud key id of the published shape, assembled so this file is not itself a specimen.
KEY = "AKIA" + "Q3EXAMPLE7KEY0ID"


class Audit(Fixtures, unittest.TestCase):

    def audited_host(self, files: dict, acknowledgements=(), gates=(HOST_GATE,)):
        host = self.installed()
        (host / GATES_FILE).write_text(json.dumps({"schema_version": 1, "gates": list(gates)}) + "\n",
                                       encoding="utf-8")
        (host / KNOWN_FILE).write_text(json.dumps({"schema_version": 1,
                                                   "acknowledgements": list(acknowledgements)}) + "\n",
                                       encoding="utf-8")
        for rel, text in files.items():
            (host / rel).parent.mkdir(parents=True, exist_ok=True)
            (host / rel).write_text(text, encoding="utf-8", newline="\n")
        subprocess.run(["git", "-C", str(host), "add", "--all"], check=True, capture_output=True)
        return host

    def test_564_a_violation_already_in_the_tree_is_found_with_its_line_and_its_because(self):
        host = self.audited_host({"src/a.ts": "const a = 1;\nconst b = 2;\nlet y = ctx.year;\n",
                                  "lib/b.ts": "let y = ctx.year;\n"})
        said = self.run_kit(KIT, host, "audit")
        self.assertEqual(1, said.returncode, said.stdout + said.stderr)
        self.assertIn(f"FINDING  src/a.ts:3  {HOST_GATE['id']} -- {HOST_GATE['because']}", said.stdout)
        self.assertNotIn("lib/b.ts", said.stdout, "a gate reaches only the paths it declares")
        self.assertIn("1 finding(s), 0 known, 0 expired, 0 stale", said.stdout)

    def test_565_an_acknowledged_violation_is_known_with_its_tracking_and_passes(self):
        host = self.audited_host({"src/a.ts": "let y = ctx.year;\n"},
                                 [{"gate": HOST_GATE["id"], "path": "src/a.ts", "tracking": "CARD-7",
                                   "until": "2999-12-31"}])
        said = self.run_kit(KIT, host, "audit")
        self.assertEqual(0, said.returncode, said.stdout + said.stderr)
        self.assertIn(f"KNOWN    src/a.ts:1  {HOST_GATE['id']} -- tracked as CARD-7 until 2999-12-31", said.stdout)

    def test_566_an_acknowledgement_past_its_until_is_a_finding_again(self):
        host = self.audited_host({"src/a.ts": "let y = ctx.year;\n"},
                                 [{"gate": HOST_GATE["id"], "path": "src/a.ts", "tracking": "CARD-7",
                                   "until": "2020-01-01"}])
        said = self.run_kit(KIT, host, "audit")
        self.assertEqual(1, said.returncode, said.stdout + said.stderr)
        self.assertIn("EXPIRED  src/a.ts:1", said.stdout)
        self.assertIn("0 finding(s), 0 known, 1 expired", said.stdout)

    def test_567_an_acknowledgement_that_matches_nothing_is_reported_stale(self):
        host = self.audited_host({"src/a.ts": "let y = ctx.dims['time'];\n"},
                                 [{"gate": HOST_GATE["id"], "path": "src/a.ts", "tracking": "CARD-9"}])
        said = self.run_kit(KIT, host, "audit")
        self.assertEqual(0, said.returncode, said.stdout + said.stderr)
        self.assertIn(f"STALE    src/a.ts  {HOST_GATE['id']} -- acknowledged as CARD-9", said.stdout)
        self.assertIn("1 stale acknowledgement(s)", said.stdout)

    def test_568_a_secret_the_audit_finds_is_located_and_never_printed(self):
        host = self.audited_host({"config/aws.json": '{\n  "key": "' + KEY + '"\n}\n'}, gates=[CLOUD_KEY])
        said = self.run_kit(KIT, host, "audit")
        self.assertEqual(1, said.returncode, said.stdout + said.stderr)
        self.assertIn(f"FINDING  config/aws.json:2  {CLOUD_KEY['id']}", said.stdout)
        self.assertNotIn(KEY, said.stdout + said.stderr)
        checked = self.run_kit(KIT, host, "check")
        self.assertNotIn(KEY, checked.stdout + checked.stderr)

    def test_569_check_reports_the_counts_and_fails_on_them_only_under_the_hosts_stance(self):
        host = self.audited_host({"src/a.ts": "let y = ctx.year;\n"})
        observed = self.run_kit(KIT, host, "check")
        line = next(l for l in observed.stdout.splitlines() if f" {AUDIT_GATE} " in l)
        self.assertTrue(line.startswith("  FAIL") and "[observe" in line, observed.stdout)
        self.assertIn("audit: 1 finding(s), 0 known", observed.stdout)
        answers = json.loads((host / ANSWERS).read_text(encoding="utf-8"))
        answers["stances"] = [{"gate": AUDIT_GATE, "stance": "enforce", "by": "acceptance-suite",
                               "at": "2026-10-16T00:00:00+00:00"}]
        (host / ANSWERS).write_text(json.dumps(answers, indent=2) + "\n", encoding="utf-8")
        enforced = self.run_kit(KIT, host, "check")
        self.assertNotEqual(0, enforced.returncode, enforced.stdout)
        self.assertIn(f"FAIL  {AUDIT_GATE}", enforced.stdout)


if __name__ == "__main__":
    unittest.main()
