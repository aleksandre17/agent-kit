"""Acceptance: a role is a profile, and the host's runtime settings reach its product's definition (ADR-024).

Held here, on a started host:

  1. every kit archetype declares a profile -- tools, what it may change, its context, its class of
     work -- and the published catalogue holds an orchestrator, an implementer, a reviewer and an
     explorer by their profiles, not by name;
  2. a role the host hires with its runtime's own settings (`runtime` rows: a model, a tool list) is
     served with those rows in every product's definition file, verbatim, and `check` stays green.

Every path and field is read from the declarations that own it.
"""

from __future__ import annotations

import json
import unittest

from harness import KIT, REPO, Fixtures

from manifest import Manifest
from test_adapters import ADAPTERS, surfaces_of

CORE = Manifest(KIT)
ARCHETYPES = json.loads((KIT / "roles" / "archetypes.json").read_text(encoding="utf-8"))["archetypes"]
OVERLAYS = next(i["target"] for c in CORE.capabilities for i in c.installs if i.get("validates") == "overlay")
STARTER = REPO / "starters" / "standard.json"
TAKEN = [(STARTER.parent / rel).resolve() for rel in json.loads(STARTER.read_text(encoding="utf-8"))["takes"]]
HOMES = [(r["target"], r.get("suffix", "")) for a in ADAPTERS if a.resolve() in TAKEN for s in surfaces_of(a)
         for r in s["renders"] if r["view"] == "role-definitions"]


class RoleProfiles(Fixtures, unittest.TestCase):

    def test_520_every_archetype_is_a_profile_and_the_catalogue_covers_the_four_profiles(self):
        self.assertTrue(all("profile" in a for a in ARCHETYPES))
        profiles = [a["profile"] for a in ARCHETYPES]
        self.assertTrue(any("delegate" in p["tools"] for p in profiles), "an orchestrating profile")
        self.assertTrue(any("edit" in p["tools"] and p["may_change"] != "nothing" for p in profiles), "an implementing one")
        self.assertTrue(any("run" in p["tools"] and p["may_change"] == "nothing" for p in profiles), "a verifying one")
        self.assertTrue(any(set(p["tools"]) <= {"read", "search"} for p in profiles), "an exploring one")

    def test_521_a_hired_roles_runtime_rows_reach_every_product_definition(self):
        host = self.started()
        archetype = next(a for a in ARCHETYPES if a["profile"]["may_change"] == "nothing" and "run" in a["profile"]["tools"])
        (host / OVERLAYS / "a-verifier.json").write_text(json.dumps({
            "schema_version": 1, "id": "a-verifier", "archetype": archetype["id"],
            "runtime": [{"id": "model", "value": "a-small-model"}]}) + "\n", encoding="utf-8", newline="\n")
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        self.assertTrue(HOMES)
        for target, suffix in HOMES:
            text = (host / f"{target}a-verifier{suffix}").read_text(encoding="utf-8")
            self.assertIn('"a-small-model"', text)
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode)


if __name__ == "__main__":
    unittest.main()
