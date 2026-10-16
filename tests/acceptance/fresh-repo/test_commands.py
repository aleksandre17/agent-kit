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

import manifest as manifest_port
from manifest import Manifest
from test_detectors import materialise
from test_pinned_kit import said
from test_taken import surface_documents_of

CORE = Manifest(KIT)
EVALUATION = next(c for c in CORE.capabilities if c.raw.get("consumes"))
READINGS = next(d for d in EVALUATION.documents.values() if "readings" in d)["readings"]
STARTER = sorted((REPO / "starters").glob("*.json"))[0]
DECLARATION = next(i for c in CORE.capabilities for i in c.installs
                   if i["mode"] == manifest_port.TAKEN_MODE)["declaration"]


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
        declared_host, bare_host = self.host(), self.host()
        for detector in sorted(CORE.detectors, key=lambda d: d["id"]):
            if set(detector["emits"]) & facts:
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

    def test_412b_a_detector_a_taken_capability_declares_is_read_and_served(self):
        # A product's file is read by its own adapter's detector, never by one in the kit core.
        starter = json.loads(STARTER.read_text(encoding="utf-8"))
        brought = []
        for rel in starter["takes"]:
            declaration = json.loads((STARTER.parent / rel / DECLARATION).read_text(encoding="utf-8"))
            seat = f"capabilities/{declaration['id']}/"
            brought += [json.loads((STARTER.parent / rel / d["source"][len(seat):]).read_text(encoding="utf-8"))
                        for d in declaration.get("documents", []) if d["validates"] == "detector"]
        brought = [d for d in brought if set(d["emits"]) & {row["reads"] for row in READINGS}]
        self.assertTrue(brought, "the starter takes no capability that brings a command detector")
        self.assertFalse({d["id"] for d in brought} & {d["id"] for d in CORE.detectors},
                         "a brought detector is also in the kit core")
        host = self.host()
        for detector in brought:
            materialise(host, detector)
        for briefing in self.started(host):
            text = briefing.read_text(encoding="utf-8")
            for row in READINGS:
                if any(row["reads"] in d["emits"] for d in brought):
                    self.assertIn(f"- {row['means']}: `", text)


if __name__ == "__main__":
    unittest.main()
