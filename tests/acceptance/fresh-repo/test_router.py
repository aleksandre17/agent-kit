"""Acceptance: a host's task router reaches every always-loaded briefing, and every product's briefing
says the same thing (ADR-024).

  1. a router section the host declares in its own briefing seed is served in every product's entry
     file, by declaration alone;
  2. every product's entry file carries the SAME section text -- one governance block, never two that
     drift.
"""

from __future__ import annotations

import json
import re
import unittest

from harness import KIT, REPO, Fixtures

import contextbudget
import derivation
from manifest import Manifest
from test_adapters import ADAPTERS, surfaces_of

CORE = Manifest(KIT)
STARTER = REPO / "starters" / "standard.json"
TAKEN = [(STARTER.parent / rel).resolve() for rel in json.loads(STARTER.read_text(encoding="utf-8"))["takes"]]
SEED = next(i["target"] for c in CORE.capabilities for i in c.installs
            if i.get("validates") == "briefing-section" and i["mode"] == "seed")
#: The layer an entry is loaded into on every turn, read from the module that measures it.
ALWAYS = next(layer for layer, _count in contextbudget.COUNTS.values())
ENTRIES = [(r["target"], r["span"]) for a in ADAPTERS if a.resolve() in TAKEN for s in surfaces_of(a)
           for r in s["renders"] if r.get("span") and r.get("layer") == ALWAYS]


def _sections(text: str, span: str) -> str:
    """The span's sections, without the one header line that names the product it is served to."""
    body = derivation.span(text, span)
    return re.sub(r"^\*Served to the runtime.*?\*\n", "", body, flags=re.S | re.M)


class Router(Fixtures, unittest.TestCase):

    def test_540_a_router_reaches_every_entry_and_every_entry_says_the_same(self):
        host = self.started()
        (host / SEED).write_text(json.dumps({"schema_version": 1, "sections": [
            {"id": "task-router", "heading": "Task router", "text": "When a schema changes, read `docs/fixture.md` and nothing else."}]}) + "\n",
            encoding="utf-8", newline="\n")
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        self.assertGreater(len(ENTRIES), 1)
        bodies = []
        for target, span in ENTRIES:
            text = (host / target).read_text(encoding="utf-8")
            self.assertIn("read `docs/fixture.md` and nothing else", text)
            bodies.append(_sections(text, span))
        self.assertEqual(1, len(set(bodies)), "two products are told two different things")
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode)


if __name__ == "__main__":
    unittest.main()
