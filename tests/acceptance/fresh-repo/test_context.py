"""Acceptance: what every served surface makes a runtime read is measured, per layer (ADR-024).

Held here:

  1. on a started host `check` states, for every served surface that loads a context layer, each
     context measure in tokens with the file that sets it, and passes within the kit's defaults;
  2. an always-loaded law page grown past the kit's default fails the context gate by its measure, and
     a section inlined above the declared inline limit is reported as one a pointer would carry.

Every measure, path and limit is read from the module and the declarations that own it.
"""

from __future__ import annotations

import json
import unittest

from harness import KIT, REPO, Fixtures

import contextbudget
import serving
from manifest import Manifest
from test_adapters import ADAPTERS, surfaces_of
from test_pinned_kit import said

CORE = Manifest(KIT)
CONTEXT = next(c.documents[d["id"]] for c in CORE.capabilities for d in c.raw.get("documents", [])
               if d["validates"] == "context")
SPEC = next(i["serves"] for c in CORE.capabilities for i in c.installs if i.get("shape") == serving.SHAPE)
#: The first page a briefing INLINES: a section that points nowhere and is read from the host.
INLINED = next(s.get("deprecated_from", s["from"]) for v in SPEC["views"] for s in v.get("sections", []) if not s.get("points"))
#: The layer an entry briefing is loaded into (a document view of sections, unscoped), and the first
#: measure of that layer -- its whole cost on every turn.
BRIEFING = next(v["id"] for v in SPEC["views"] if v.get("sections") and "scopes" not in v)
LAYER = next(r["layer"] for a in ADAPTERS for s in surfaces_of(a) for r in s["renders"]
             if r["view"] == BRIEFING and r.get("layer"))
ALWAYS = next(m for m, (layer, _count) in contextbudget.COUNTS.items() if layer == LAYER)
STARTER = REPO / "starters" / "standard.json"


class Context(Fixtures, unittest.TestCase):

    def started(self):
        host = self.host()
        ran = self.run_kit(KIT, host, "start", "--path", str(STARTER), "--approve", "acceptance-suite")
        self.assertEqual(0, ran.returncode, said(ran))
        return host

    def test_440_every_served_layer_is_measured_and_a_started_host_is_within_the_defaults(self):
        host = self.started()
        checked = self.run_kit(KIT, host, "check")
        self.assertEqual(0, checked.returncode, said(checked))
        served = {row["surface"] for item in serving._records(CORE.capabilities) if (host / item["target"]).exists()
                  for row in json.loads((host / item["target"]).read_text(encoding="utf-8"))["served"]
                  if row.get("layer")}
        self.assertTrue(served)
        for surface in served:
            for measure in contextbudget.COUNTS:
                self.assertIn(f"CONTEXT {surface}: {measure} = ", checked.stdout)

    def test_441_a_law_page_past_the_default_fails_and_an_inlined_wall_is_reported(self):
        host = self.started()
        ceiling = CONTEXT["default_ceilings"][ALWAYS] * CONTEXT["estimator"]["bytes_per_token"]
        page = host / INLINED
        page.write_text("1. **A law.** " + "x" * ceiling + "\n", encoding="utf-8", newline="\n")
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        checked = self.run_kit(KIT, host, "check")
        self.assertNotEqual(0, checked.returncode)
        self.assertIn(ALWAYS, said(checked))
        self.assertIn("ADVICE", checked.stdout)


if __name__ == "__main__":
    unittest.main()
