"""Acceptance: a host's laws have ONE source -- its numbered rules (ADR-024 decision 21).

  1. a fresh host is seeded no law page; the law list is rendered from the rules carrying `law`, in
     law order: bold title, what it says, the enforcement note and the enforcers;
  2. a host still holding the deprecated page has it reported as the source in force;
  3. a host authoring both sources, or numbers with a gap, fails FF-LAWS;
  4. `upgrade --mode laws` moves each numbered law into a rule, removes the page and renders, and the
     moved rules are then named by FF-NORMS until the host completes them.

Paths and gate ids arrive from the declarations.
"""

from __future__ import annotations

import json
import unittest

from harness import KIT, Fixtures
from manifest import Manifest

CORE = Manifest(KIT)
DOCTRINE = next(c for c in CORE.capabilities if any(g["kind"] == "laws-one-source" for g in c.gates))
GATE = next(g for g in DOCTRINE.gates if g["kind"] == "laws-one-source")
PAGE = GATE["params"]["deprecated"]
NORMS = next(i["target"] for i in DOCTRINE.installs if i.get("reads_as") == GATE["params"]["rules_from"])
RENDERED = next(i["target"] for i in DOCTRINE.installs if i["source"].endswith("LAWS.md.mustache"))
LEGACY = """<!-- a host's own law page -->
1. **BioStar is read, never written.** No statement writes a `TB_*` table
   (AIR-003). *Edit gate `no-write-to-biostar`.*
2. **A behaviour change is proven.** It carries a test that fails without it.
"""


def rule(n: int, **extra) -> dict:
    return {"schema_version": 1, "id": f"host@1.0.0#law-{n}", "genre": "rule", "title": f"Law {n}.",
            "says": f"what law {n} says.", "publisher": "acceptance-suite", "law": n, **extra}


class Laws(Fixtures, unittest.TestCase):

    def host_with(self, norms=None, page=None):
        host = self.installed()
        if norms is not None:
            (host / NORMS).write_text(json.dumps(norms, indent=2) + "\n", encoding="utf-8")
        if page is not None:
            (host / PAGE).write_text(page, encoding="utf-8", newline="\n")
        return host

    def gate_line(self, stdout: str) -> str:
        return next(l for l in stdout.splitlines() if f" {GATE['id']} " in l)

    def test_570_the_law_list_is_rendered_from_the_numbered_rules_in_law_order(self):
        host = self.host_with([rule(1, enforcement_note="Edit gate `g`.", enforced_by=["verb:check"]),
                               {"schema_version": 1, "id": "host@1.0.0#other", "genre": "doctrine",
                                "title": "t", "says": "s", "publisher": "p"},
                               rule(2)])
        self.assertFalse((host / PAGE).exists(), "a fresh host is still seeded the deprecated law page")
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        self.assertEqual("1. **Law 1.** what law 1 says. *Edit gate `g`.* `verb:check`\n"
                         "2. **Law 2.** what law 2 says.\n", (host / RENDERED).read_text(encoding="utf-8"))
        checked = self.run_kit(KIT, host, "check")
        self.assertTrue(self.gate_line(checked.stdout).startswith("  PASS"), checked.stdout)
        self.assertIn("laws: 2 law(s) served from this host's numbered rules", checked.stdout)

    def test_571_a_host_still_holding_the_page_has_it_reported_as_the_source_in_force(self):
        host = self.host_with(page=LEGACY)
        checked = self.run_kit(KIT, host, "check")
        self.assertTrue(self.gate_line(checked.stdout).startswith("  PASS"), checked.stdout)
        self.assertIn(f"laws: served from the DEPRECATED page {PAGE}", checked.stdout)

    def test_572_both_sources_authored_or_a_gap_in_the_numbers_fails(self):
        both = self.run_kit(KIT, self.host_with([rule(1)], LEGACY), "check")
        self.assertTrue(self.gate_line(both.stdout).startswith("  FAIL"), both.stdout)
        self.assertIn("two sources for this host's laws", both.stdout)
        gap = self.run_kit(KIT, self.host_with([rule(1), rule(3)]), "check")
        self.assertTrue(self.gate_line(gap.stdout).startswith("  FAIL"), gap.stdout)
        self.assertIn("carry laws [1, 3]", gap.stdout)

    def test_573_upgrade_moves_each_numbered_law_into_a_rule_and_retires_the_page(self):
        host = self.host_with(page=LEGACY)
        planned = self.run_kit(KIT, host, "upgrade", "--mode", "laws", "--plan")
        self.assertEqual(0, planned.returncode, planned.stderr)
        self.assertTrue((host / PAGE).exists(), "a plan wrote")
        refused = self.run_kit(KIT, host, "upgrade", "--mode", "laws")
        self.assertNotEqual(0, refused.returncode, "the move ran without an approval")
        moved = self.run_kit(KIT, host, "upgrade", "--mode", "laws", "--approve", "acceptance-suite")
        self.assertEqual(0, moved.returncode, moved.stdout + moved.stderr)
        self.assertFalse((host / PAGE).exists())
        rules = json.loads((host / NORMS).read_text(encoding="utf-8"))
        self.assertEqual([1, 2], [r["law"] for r in rules])
        self.assertEqual("BioStar is read, never written.", rules[0]["title"])
        self.assertEqual("No statement writes a `TB_*` table (AIR-003).", rules[0]["says"])
        self.assertEqual("Edit gate `no-write-to-biostar`.", rules[0]["enforcement_note"])
        self.assertNotIn("enforcement_note", rules[1])
        self.assertIn("1. **BioStar is read, never written.**", (host / RENDERED).read_text(encoding="utf-8"))
        checked = self.run_kit(KIT, host, "check")
        self.assertTrue(self.gate_line(checked.stdout).startswith("  PASS"), checked.stdout)
        self.assertIn("NT-ORPHAN host@1.0.0#law-1", checked.stdout)


if __name__ == "__main__":
    unittest.main()
