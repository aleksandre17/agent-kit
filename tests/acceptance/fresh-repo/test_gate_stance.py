"""Acceptance: a gate's STANCE -- what its failure does to `check` -- is declared, and it matures
only by declaration (ADR-006).

Five things this suite exists to prove, each the way a stance mechanism most often fails:

  1. an unanswered gate stands in a DECLARED stance, named on the surface -- and with no host
     declaration at all, a failing gate still fails `check` exactly as it did before stances;
  2. an observed failure is shown, counted and named -- never a silent green;
  3. a gate that holds the kit's own integrity declares a FLOOR, and no host may lower it;
  4. the interpreter privileges nothing: no gate id and no stance name is spelled in it;
  5. maturation is a restated declaration, and the moment it lands the failure bites again.

Nothing here restates the vocabulary, a floor or a gate id. They are READ from the declarations,
because a suite holding its own copy would go on passing after the kit moved.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from harness import KIT, Fixtures  # noqa: I001  (it is what puts the interpreter on the path)

import gatekinds  # noqa: E402
import maturation  # noqa: E402
from manifest import Manifest  # noqa: E402
from stance import StanceError, vocabulary  # noqa: E402

MANIFEST = Manifest(KIT)
ROWS, UNANSWERED = vocabulary(MANIFEST)
#: The answers file, found by its install mode -- the same question the interpreter asks.
ANSWERS = next(i["target"] for c in MANIFEST.capabilities for i in c.installs
               if i["mode"] == "declaration")
#: The residence genres and the capability whose gate holds them: a failure a test can PLANT.
SENSOR = next(c for c in MANIFEST.capabilities
              if any("genres" in doc for doc in c.documents.values()))
GENRE = next(doc for doc in SENSOR.documents.values() if "genres" in doc)["genres"][0]
WATCHED = next(g["id"] for g in SENSOR.gates if "floor" not in g.get("stance", {}))
FLOORS = [(g["id"], g["stance"]["floor"]) for c in MANIFEST.capabilities for g in c.gates
          if "floor" in g.get("stance", {})]
GATE_IDS = sorted({g["id"] for c in MANIFEST.capabilities for g in c.gates})
LOWEST = min(ROWS.values(), key=lambda row: row["rank"])
QUIET = next(row["id"] for row in sorted(ROWS.values(), key=lambda r: r["rank"])
             if not row["fails"])
BITES = next(row["id"] for row in sorted(ROWS.values(), key=lambda r: -r["rank"]) if row["fails"])


#: Where this host writes what it undertakes, the class a place may confer, and the judgement one
#: of those undertakings caps -- every one read from the declaration that owns it. Nothing about
#: maturation is restated here: a suite that spelled the pairing would go on passing after it moved.
CORPUS = next((c, i) for c in MANIFEST.capabilities for i in c.installs
              if i.get("validates") == "corpus-map")
CLASS = next(c.documents[d["id"]]["kinds"][0]["id"] for c in MANIFEST.capabilities
             for d in c.raw.get("documents", []) if d["validates"] == "record-keeping")
PAIRED = gatekinds.registry(maturation.JUDGED_BY)
CAPPED = next(measure for measure in sorted(PAIRED)
              if any(g["kind"] == PAIRED[measure] for g in CORPUS[0].gates))
UNDERTAKEN = next(g["id"] for g in CORPUS[0].gates if g["kind"] == PAIRED[CAPPED])


def gate_line(stdout: str, gate_id: str) -> str:
    return next(line for line in stdout.splitlines()
                if re.match(rf"\s+(PASS|FAIL)\s+{re.escape(gate_id)}\s", line))


class GateStance(Fixtures, unittest.TestCase):

    def declare(self, host: Path, *rows: dict) -> None:
        """The host's own answer, written where the host writes it -- nothing in the kit does."""
        target = host / ANSWERS
        answers = json.loads(target.read_text(encoding="utf-8"))
        answers["stances"] = list(rows)
        target.write_text(json.dumps(answers, indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def row(gate: str, stance: str, at: str = "2026-09-11") -> dict:
        return {"gate": gate, "stance": stance, "by": "acceptance-suite", "at": at}

    def plant(self, host: Path) -> None:
        path = host / GENRE["proves"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# planted\n\nput here by a host, in good faith.\n", encoding="utf-8")

    def refused(self, result) -> None:
        self.assertNotEqual(0, result.returncode)
        self.assertIn(StanceError.code, result.stdout + result.stderr)

    # == 1. the unanswered gate is a declared state =============================================
    def test_187_an_unanswered_gate_stands_in_the_declared_default_and_a_failure_still_fails_check(self):
        """With no host stance at all, today's behaviour is reachable byte-for-byte in its verdict:
        the vocabulary's unanswered stance is one that fails, and every gate line names it as
        unanswered -- a declared state on the surface, never an absence the reader must infer."""
        self.assertTrue(ROWS[UNANSWERED]["fails"],
                        "the declared default no longer fails check; that is ADR-006's one-way door")
        host = self.installed()
        self.plant(host)
        result = self.run_kit(KIT, host, "check")
        self.assertEqual(1, result.returncode)
        for gate_id in (g["id"] for c in MANIFEST.capabilities for g in c.gates
                        if c.id in json.loads((host / ANSWERS).read_text())["capabilities"]):
            self.assertIn(f"[{UNANSWERED}: unanswered", gate_line(result.stdout, gate_id))
        self.assertIn(f"FAIL  {WATCHED}", result.stdout)

    # == 2. an observed failure is shown, counted and named =====================================
    def test_188_an_observed_failure_is_printed_named_and_counted_but_does_not_fail_check(self):
        host = self.installed()
        self.plant(host)
        self.declare(host, self.row(WATCHED, QUIET))
        result = self.run_kit(KIT, host, "check")
        self.assertEqual(0, result.returncode, "an observed failure failed check")
        self.assertIn(f"FAIL  {WATCHED}", result.stdout)
        self.assertIn(f"[{QUIET}: declared by acceptance-suite", gate_line(result.stdout, WATCHED))
        self.assertIn(GENRE["proves"], result.stdout, "the observed finding itself went unprinted")
        self.assertRegex(result.stdout, rf"check: 1 gate\(s\) failed under a stance that does not "
                                        rf"fail check: {re.escape(WATCHED)} \[{QUIET}\]")
        self.assertIn("check: 0 gate(s) failed", result.stdout)

    # == 3. a floor cannot be lowered by a host ================================================
    def test_189_every_declared_floor_refuses_a_host_that_lowers_it_and_every_floor_bites(self):
        self.assertTrue(FLOORS, "no gate declares a floor; the kit promises nothing about itself")
        host = self.installed()
        for gate_id, floor in FLOORS:
            with self.subTest(gate=gate_id):
                self.assertTrue(ROWS[floor]["fails"], f"{gate_id}'s floor {floor!r} fails nothing")
                below = [r["id"] for r in ROWS.values() if r["rank"] < ROWS[floor]["rank"]]
                self.assertIn(LOWEST["id"], below)
                self.declare(host, self.row(gate_id, LOWEST["id"]))
                result = self.run_kit(KIT, host, "check")
                self.refused(result)
                self.assertIn(gate_id, result.stdout + result.stderr)

    # == 4. the interpreter privileges nothing ==================================================
    def test_190_no_gate_id_and_no_stance_name_is_spelled_anywhere_in_the_interpreter(self):
        sources = {p: p.read_text(encoding="utf-8") for p in (KIT / "interpreters").rglob("*.py")}
        for path, text in sources.items():
            for gate_id in GATE_IDS:
                self.assertNotIn(gate_id, text, f"{path.name} privileges gate {gate_id}")
            for stance in ROWS:
                self.assertNotRegex(text, rf"[\"']{re.escape(stance)}[\"']",
                                    f"{path.name} spells stance {stance!r}")

    def test_191_a_stance_outside_the_vocabulary_or_a_gate_answered_twice_is_refused(self):
        host = self.installed()
        unknown = "-".join(sorted(ROWS)) + "-undeclared"
        for label, rows in (("unknown", (self.row(WATCHED, unknown),)),
                            ("twice", (self.row(WATCHED, QUIET), self.row(WATCHED, BITES)))):
            with self.subTest(case=label):
                self.declare(host, *rows)
                self.refused(self.run_kit(KIT, host, "check"))

    def test_192_a_stance_that_names_no_running_gate_is_shown_as_binding_nothing(self):
        host = self.installed()
        nowhere = "-".join(GATE_IDS)
        self.declare(host, self.row(nowhere, QUIET))
        result = self.run_kit(KIT, host, "check")
        self.assertEqual(0, result.returncode)
        self.assertRegex(result.stdout, rf"STANCE\s+{re.escape(nowhere)}\s.*binds nothing")

    # == 5. maturation is a declaration ========================================================
    def test_193_an_observed_gate_matures_only_when_the_host_restates_it_and_then_it_bites(self):
        host = self.installed()
        self.declare(host, self.row(WATCHED, QUIET))
        clean = self.run_kit(KIT, host, "check")
        self.assertEqual(0, clean.returncode)
        self.assertRegex(clean.stdout, rf"are clean: {re.escape(WATCHED)} \[{QUIET}\].*"
                                       rf"only the host makes")

        self.plant(host)
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode)

        self.declare(host, self.row(WATCHED, BITES, at="2026-09-12"))
        matured = self.run_kit(KIT, host, "check")
        self.assertEqual(1, matured.returncode, "a restated stance did not bite")
        self.assertIn(f"[{BITES}: declared by acceptance-suite at 2026-09-12]",
                      gate_line(matured.stdout, WATCHED))


    # == 6. an undertaking the host finished matures the judgement it bought grace from =========
    #: A place that holds a document declaring its own class -- so the count this host undertakes
    #: reads NOTHING -- and a second place the tree does not have, which is what the judgement over
    #: this corpus fails on. The two are deliberately separate: the failure under judgement must
    #: not be the count itself, or a matured run could not be told from a run over its budget.
    RESIDES, ABSENT = "docs/mapped/", "docs/nothing-resides-here/"

    def undertake(self, host: Path, ceiling: int) -> None:
        """The host's own undertaking, written where the host writes it. The kit writes nothing
        here and answers no gate: the only two declarations in play below are this one and the
        host's stance, and both are the host's."""
        resident = host / self.RESIDES / "declares-itself.md"
        resident.parent.mkdir(parents=True, exist_ok=True)
        resident.write_text(f"---\nkind: {CLASS}\n---\n\n# it says what it is\n",
                            encoding="utf-8", newline="\n")
        target = host / CORPUS[1]["target"]
        target.mkdir(parents=True, exist_ok=True)
        (target / "map.json").write_text(json.dumps({
            "schema_version": 1,
            "id": "acceptance",
            "places": [{"path": self.RESIDES, "holds": CLASS},
                       {"path": self.ABSENT, "holds": CLASS}],
            "budgets": [{"measures": CAPPED, "ceiling": ceiling, "measured": "2026-09-24"}],
        }, indent=2) + "\n", encoding="utf-8", newline="\n")
        self.run_kit(KIT, host, "render")

    def test_194_an_undertaking_reaching_its_terminal_value_matures_the_judgement_it_caps(self):
        """The maturation ADR-019 decision 9 promises and ADR-020's last slice lands: while the
        host is still working a count down, the stance it declared stands untouched; the moment the
        undertaking is *nothing of this*, the concession it bought is spent and the judgement stands
        where an unanswered one stands -- with the row that did it named on the line, so nobody has
        to take the surface's word for who decided."""
        host = self.installed()
        self.declare(host, self.row(UNDERTAKEN, QUIET))

        self.undertake(host, 1)
        working = self.run_kit(KIT, host, "check")
        self.assertEqual(0, working.returncode, "a watched judgement failed the run while the "
                                                "host was still working its undertaking down")
        self.assertIn(f"FAIL  {UNDERTAKEN}", working.stdout)
        self.assertIn(f"[{QUIET}: declared by acceptance-suite",
                      gate_line(working.stdout, UNDERTAKEN))

        self.undertake(host, 0)
        matured = self.run_kit(KIT, host, "check")
        line = gate_line(matured.stdout, UNDERTAKEN)
        self.assertIn(f"[{UNANSWERED}: matured", line)
        self.assertIn(CAPPED, line, "the undertaking that matured it is not named on the line")
        self.assertNotIn(f"[{QUIET}", line)
        self.assertNotIn(f"{UNDERTAKEN} [{QUIET}]", matured.stdout,
                         "a matured judgement is still being counted as one that does not fail")
        self.assertEqual(1, matured.returncode, "the maturation did not bite")
        self.assertIn("check: 1 gate(s) failed", matured.stdout)


if __name__ == "__main__":
    unittest.main()
