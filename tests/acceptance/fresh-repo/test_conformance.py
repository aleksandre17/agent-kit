"""Acceptance: "meets the standard" is a row with evidence, never prose (ADR-024).

  1. a conformant row whose evidence exists keeps `check` green;
  2. a conformant row citing evidence the host does not have is refused by `check`, by its row id;
  3. a gap, a mapping or a non-goal is an honest row, needing only its reason.
"""

from __future__ import annotations

import json
import unittest

from harness import KIT, REPO, Fixtures

import conformance
from manifest import Manifest
from test_pinned_kit import said

CORE = Manifest(KIT)
STARTER = REPO / "starters" / "standard.json"
SEAT = next(i["target"] for c in CORE.capabilities for i in c.installs if i.get("validates") == conformance.MAP[0]["validates"])


def _row(identity, status, *evidence):
    return {"id": identity, "standard": "a fixture standard", "clause": "1", "mechanism": "a fixture",
            "evidence": list(evidence), "status": status, "why": "a fixture reason"}


class Conformance(Fixtures, unittest.TestCase):

    def test_550_a_conformant_row_needs_evidence_that_exists_and_a_gap_is_an_honest_row(self):
        host = self.host()
        ran = self.run_kit(KIT, host, "start", "--path", str(STARTER), "--approve", "acceptance-suite")
        self.assertEqual(0, ran.returncode, said(ran))
        (host / "evidence.txt").write_text("measured\n", encoding="utf-8")
        rows = [_row("held", conformance.CONFORMANT, "path:evidence.txt"), _row("an-honest-gap", "gap"),
                _row("organisational", "mapping"), _row("not-worth-it", "non-goal")]
        (host / SEAT).write_text(json.dumps({"schema_version": 1, "rows": rows}) + "\n", encoding="utf-8", newline="\n")
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode)
        rows.append(_row("claimed", conformance.CONFORMANT, "gate:A-GATE-NOBODY-DECLARES"))
        (host / SEAT).write_text(json.dumps({"schema_version": 1, "rows": rows}) + "\n", encoding="utf-8", newline="\n")
        checked = self.run_kit(KIT, host, "check")
        self.assertNotEqual(0, checked.returncode)
        self.assertIn("claimed: conformant", checked.stdout)


if __name__ == "__main__":
    unittest.main()
