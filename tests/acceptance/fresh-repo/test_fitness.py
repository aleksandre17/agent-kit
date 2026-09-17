"""Acceptance: the ARROW (ADR-017 link C, slice C1c) -- a host declares its layers, the direction a
dependency may run and how a dependency is read; the kit enforces it generically.

  1. `check` names every edge in the tree that runs against the declared arrow (file -> file, rule);
  2. the ONE edit judge refuses an edit whose introduced text adds such an edge, and admits a
     lookalike in the allowed direction and an edit that leaves an old edge untouched (a ratchet);
  3. an uncalibrated reading or rule fails `check` and is named unjudged, never trusted;
  4. the interpreter holds no dependency syntax of any language: the dependency syntax used here is
     invented for this test, so a pass proves it arrived only as the host's data.
"""

from __future__ import annotations

import io
import json
import re
import tokenize
import unittest
from pathlib import Path

from harness import KIT, Fixtures
from manifest import Manifest

import test_enforcement as enforcement
from test_enforcement import _event

CORE = Manifest(KIT)
FITNESS = next(c for c in CORE.capabilities if any(g["kind"] == "arrow-held" for g in c.gates))
ARROW_FILE = next(i["target"] for i in FITNESS.installs if i.get("validates") == "arrow")
GATE_ID = next(g["id"] for g in FITNESS.gates)

#: A dependency syntax no language has: `needs <name>;` -- so nothing in the kit can already know it.
READING = {
    "id": "needs-line", "files": r"\.dep$", "reference": r"^\s*needs\s+([\w.]+);",
    "separator": ".", "locates": ["app/{ref}.dep"],
    "proves": {"text": "needs low.a;\nneeds high.b;", "yields": ["low.a", "high.b"]},
    "admits": {"text": "# needs low.a; is a comment"},
}
LAYERS = [
    {"id": "high", "within": "app/high", "paths": r"^app/high/"},
    {"id": "low", "within": "app/low", "paths": r"^app/low/"},
]
RULE = {
    "id": "low-never-reaches-high", "from": "low", "may": ["low"],
    "because": "the stable depends on nothing volatile.", "instead": "invert: declare a port in low.",
    "proves": {"path": "app/low/x.dep", "to": "app/high/y.dep"},
    "admits": {"path": "app/low/x.dep", "to": "app/low/y.dep"},
}


class Fitness(Fixtures, unittest.TestCase):
    # Enforcement's served host and judge, borrowed without inheriting its tests.
    setUpClass = enforcement.Enforcement.__dict__["setUpClass"]
    served_host = enforcement.Enforcement.served_host
    judge = enforcement.Enforcement.judge

    def arrowed_host(self, readings=(READING,), rules=(RULE,), backward=True) -> Path:
        host = self.served_host()
        (host / ARROW_FILE).parent.mkdir(parents=True, exist_ok=True)
        (host / ARROW_FILE).write_text(json.dumps({"schema_version": 1, "imports": list(readings),
                                                   "layers": LAYERS, "rules": list(rules)}) + "\n",
                                       encoding="utf-8")
        files = {"app/high/b.dep": "needs low.a;\n", "app/low/c.dep": "x\n",
                 "app/low/a.dep": ("needs high.b;\n" if backward else "needs low.c;\n")}
        for rel, text in files.items():
            (host / rel).parent.mkdir(parents=True, exist_ok=True)
            (host / rel).write_text(text, encoding="utf-8")
        return host

    def test_300_check_names_every_edge_against_the_arrow(self):
        checked = self.run_kit(self.kit, self.arrowed_host(), "check")
        self.assertIn(f"FAIL  {GATE_ID}", checked.stdout)
        self.assertIn(f"app/low/a.dep -> app/high/b.dep  {RULE['id']}", checked.stdout)
        self.assertNotIn("app/high/b.dep -> app/low/a.dep", checked.stdout)
        clean = self.run_kit(self.kit, self.arrowed_host(backward=False), "check")
        self.assertIn(f"PASS  {GATE_ID}", clean.stdout)

    def test_301_the_one_judge_refuses_a_backward_edge_and_admits_its_lookalikes(self):
        host = self.arrowed_host(backward=False)
        for surface in self.surfaces:
            hands, no = surface["hands"], surface["hands"]["refusal"]["exit"]
            with self.subTest(surface=surface["id"]):
                refused = self.judge(host, surface, _event(hands, "app/low/a.dep", "needs high.b;"))
                self.assertEqual(no, refused.returncode, refused.stdout + refused.stderr)
                self.assertIn(RULE["id"], refused.stderr)
                self.assertIn("app/high/b.dep", refused.stderr)
                for path, text in (("app/low/a.dep", "needs low.c;"),       # allowed direction
                                   ("app/high/b.dep", "needs low.a;"),      # a layer no rule binds
                                   ("app/low/a.dep", "# needs high.b;"),    # not a dependency
                                   ("app/low/a.dep", "needs high.nowhere;")):  # located nowhere
                    admitted = self.judge(host, surface, _event(hands, path, text))
                    self.assertEqual(0, admitted.returncode, f"{path} {text!r}: {admitted.stderr}")

    def test_302_an_uncalibrated_reading_or_rule_fails_check_and_is_not_trusted(self):
        broken_rule = {**RULE, "admits": RULE["proves"]}
        broken_reading = {**READING, "proves": {"text": "needs low.a;", "yields": ["other"]}}
        for readings, rules, named in (((READING,), (broken_rule,), RULE["id"]),
                                       ((broken_reading,), (RULE,), READING["id"])):
            with self.subTest(named=named):
                host = self.arrowed_host(readings, rules)
                checked = self.run_kit(self.kit, host, "check")
                self.assertIn(f"FAIL  {GATE_ID}", checked.stdout)
                self.assertIn(f"{named}: UNCALIBRATED", checked.stdout)
                surface = self.surfaces[0]
                judged = self.judge(host, surface, _event(surface["hands"], "app/low/a.dep", "needs high.b;"))
                self.assertIn(named, judged.stderr)
                self.assertIn("NOT APPLIED", judged.stderr)

    def test_303_the_interpreter_spells_no_dependency_syntax_and_the_kit_ships_no_arrow(self):
        seed = next(i["source"] for i in FITNESS.installs if i.get("validates") == "arrow")
        shipped = json.loads((KIT / seed).read_text(encoding="utf-8"))
        self.assertEqual(([], [], []), (shipped["imports"], shipped["layers"], shipped["rules"]))
        syntax = re.compile(r"\bimport\s|\brequire\s*\(|#include|\busing\s|\buse\s|needs\s")
        for rel in ("interpreters/gates/arrow.py", "interpreters/verbs/judge.py",
                    "interpreters/gates/edits.py"):
            source = (KIT / rel).read_text(encoding="utf-8")
            strings = [tok.string for tok in tokenize.generate_tokens(io.StringIO(source).readline)
                       if tok.type == tokenize.STRING]
            with self.subTest(file=rel):
                self.assertEqual([], [s for s in strings if syntax.search(s)])


if __name__ == "__main__":
    unittest.main()
