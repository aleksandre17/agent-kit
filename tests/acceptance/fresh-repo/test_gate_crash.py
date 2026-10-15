"""Acceptance: a gate that crashes FAILS under its own stance, and every other gate is still judged
(ADR-022 decision 8, slice S6).

A gate exists to deny; a gate whose decision is unknown therefore denies (Saltzer & Schroeder, fail-safe
defaults). Before this slice a kind that raised took `check` down whole -- every other gate's verdict was
lost with it, and the run read as a tool failure rather than as the finding it was.

Every path and word is read from the declarations that own it.
"""

from __future__ import annotations

import unittest

from harness import Fixtures


def _a_gate_whose_params_break_its_kind(kit) -> None:
    declaration = "capabilities/governance/capability.json"

    def add(value):
        kind = next(g["kind"] for g in value["gates"] if g.get("params", {}).get("file"))
        value["gates"].append({"id": "FF-A-GATE-THAT-CRASHES", "kind": kind, "params": {}})
    Fixtures.edit_json(kit, declaration, add)


class GateCrash(Fixtures, unittest.TestCase):

    def test_398_a_crashing_gate_fails_by_name_and_the_rest_are_still_judged(self):
        kit = self.fixture_kit("a-crashing-gate", patch=_a_gate_whose_params_break_its_kind)
        # Installed by hand: an init ends by running `check`, which now -- rightly -- fails on the
        # crashing gate, so the harness's "an approved init exits 0" cannot hold for this kit.
        host = self.host()
        self.run_kit(kit, host, "init")
        self.run_kit(kit, host, "init", "--approve", "acceptance-suite")
        checked = self.run_kit(kit, host, "check")
        self.assertEqual(1, checked.returncode, checked.stdout + checked.stderr)
        self.assertIn("FAIL  FF-A-GATE-THAT-CRASHES", checked.stdout)
        self.assertIn("an unjudged gate is not a passed one", checked.stdout)
        self.assertIn("check: 1 gate(s) failed", checked.stdout)
        self.assertGreater(checked.stdout.count("  PASS  "), 10, "the other gates were not judged")


if __name__ == "__main__":
    unittest.main()
