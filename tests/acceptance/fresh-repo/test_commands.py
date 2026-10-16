"""Acceptance: the briefing every runtime reads says how a change is built and proven (ADR-023).

An agent that cannot find the project's test command cannot prove a change. The commands a host
declares, where a detector reads them, are served INLINE in the briefing -- one line each, read from
the reading -- and a command nobody declared is named as undeclared, never invented.

Every detector, fact, file and sentence is read from its declaration.
"""

from __future__ import annotations

import json
import unittest

from harness import KIT, REPO, Fixtures

from manifest import Manifest
from test_detectors import materialise
from test_pinned_kit import said
from test_taken import surface_documents_of

CORE = Manifest(KIT)
EVALUATION = next(c for c in CORE.capabilities if c.raw.get("consumes"))
READINGS = next(d for d in EVALUATION.documents.values() if "readings" in d)["readings"]
STARTER = sorted((REPO / "starters").glob("*.json"))[0]


def _briefings(host) -> list:
    """Every file a surface the host composes renders the briefing view into."""
    _rel, surfaces = surface_documents_of(host)
    return [host / r["target"] for surface in surfaces for r in surface["renders"] if r["view"] == "briefing"]


class Commands(Fixtures, unittest.TestCase):

    def started(self, host):
        ran = self.run_kit(KIT, host, "start", "--path", str(STARTER), "--approve", "acceptance-suite")
        self.assertEqual(0, ran.returncode, said(ran))
        return _briefings(host)

    def test_412_a_declared_command_is_served_inline_and_an_undeclared_one_is_named(self):
        facts = {row["reads"] for row in READINGS}
        detector = next(d for d in sorted(CORE.detectors, key=lambda d: d["id"])
                        if facts <= set(d["emits"]))
        declared_host, bare_host = self.host(), self.host()
        materialise(declared_host, detector)
        for host, declared in ((declared_host, True), (bare_host, False)):
            briefings = self.started(host)
            self.assertTrue(briefings)
            for briefing in briefings:
                text = briefing.read_text(encoding="utf-8")
                for row in READINGS:
                    with self.subTest(declared=declared, briefing=briefing.name, fact=row["reads"]):
                        if declared:
                            self.assertIn(f"- {row['means']}: `", text)
                        else:
                            self.assertIn(f"- {row['means']}: **not declared**", text)
                            self.assertIn(row["reads"], text)


if __name__ == "__main__":
    unittest.main()
