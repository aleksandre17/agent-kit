"""Acceptance: a register is a document of rows in statuses its kind declares (ADR-022 S7, amendment 3).

The prior system kept its findings, its visions, the standards it met and the questions its doctrine
could not answer as ledgers -- rows with a status vocabulary, history in git -- and it lost nothing
that was registered. Held here:

  1. a host that keeps no register is told so in words, and `check` is green;
  2. a register whose rows are in declared statuses and carry what those statuses require is green,
     and its rows are projected;
  3. a row in a status its kind does not declare, or missing a field its status requires, fails by
     the row's address;
  4. a row PROMOTED out of a register must name a place that cites it back -- one end alone fails.

Every place, kind and status is read from the declarations that own them.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from harness import KIT, Fixtures
from manifest import Manifest

import registers as registers_gate

CORE = Manifest(KIT)
OPERATING = next(c for c in CORE.capabilities if any(g["kind"] == "register-held" for g in c.gates))
SPACE = next(i["target"] for i in OPERATING.installs if i.get("validates") == "register")
PAGE = next(i["target"] for i in OPERATING.installs if i["mode"] == "projection" and "REGISTER" in i["target"])
GATE = next(g["id"] for g in OPERATING.gates if g["kind"] == "register-held")
KINDS = {k["id"]: k for k in OPERATING.documents["register_kinds"]["kinds"]}
#: A kind with a status that requires a promotion, read from the shipped vocabulary.
KIND, PROMOTED = next((k["id"], s["id"]) for k in KINDS.values() for s in k["statuses"]
                      if registers_gate.PROMOTED_TO in s.get("requires", []))
PLAIN = next(s["id"] for s in KINDS[KIND]["statuses"] if not s.get("requires"))


class Registers(Fixtures, unittest.TestCase):

    def register(self, host: Path, rows: list) -> None:
        (host / SPACE).mkdir(parents=True, exist_ok=True)
        (host / SPACE / "met.json").write_text(json.dumps({
            "schema_version": 1, "id": "met", "kind": KIND, "title": "What this host has met",
            "rows": rows}, indent=2) + "\n", encoding="utf-8", newline="\n")

    def checked(self, host: Path):
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        return self.run_kit(KIT, host, "check")

    def test_400_a_host_with_no_register_is_told_so_and_check_is_green(self):
        host = self.installed()
        self.assertIn("keeps no register", (host / PAGE).read_text(encoding="utf-8"))
        self.assertEqual(0, self.checked(host).returncode)

    def test_401_rows_in_declared_statuses_are_green_and_projected(self):
        host = self.installed()
        self.register(host, [{"id": "a-concept", "title": "a concept met", "status": PLAIN, "at": "2026-10-15"}])
        ran = self.checked(host)
        self.assertEqual(0, ran.returncode, ran.stdout)
        self.assertIn("`a-concept`", (host / PAGE).read_text(encoding="utf-8"))

    def test_402_an_undeclared_status_and_a_missing_required_field_fail_by_the_rows_address(self):
        host = self.installed()
        self.register(host, [{"id": "odd", "title": "t", "status": "nobody-declares-this", "at": "2026-10-15"},
                             {"id": "half", "title": "t", "status": PROMOTED, "at": "2026-10-15"}])
        ran = self.checked(host)
        self.assertEqual(1, ran.returncode, ran.stdout)
        self.assertIn(f"FAIL  {GATE}", ran.stdout)
        self.assertIn("met#odd", ran.stdout)
        self.assertIn("met#half", ran.stdout)

    def test_403_a_promotion_is_recorded_at_both_ends(self):
        host = self.installed()
        (host / "docs/decisions/a-law.md").write_text("# A law\n\nNothing cited.\n", encoding="utf-8")
        self.register(host, [{"id": "rose", "title": "t", "status": PROMOTED, "at": "2026-10-15",
                              registers_gate.PROMOTED_TO: "docs/decisions/a-law.md"}])
        ran = self.checked(host)
        self.assertEqual(1, ran.returncode, ran.stdout)
        self.assertIn("does not cite", ran.stdout)
        (host / "docs/decisions/a-law.md").write_text("# A law\n\nFrom met#rose.\n", encoding="utf-8")
        ran = self.checked(host)
        self.assertEqual(0, ran.returncode, ran.stdout)


if __name__ == "__main__":
    unittest.main()
