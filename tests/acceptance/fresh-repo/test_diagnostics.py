"""Acceptance: every refusal carries a stable diagnostic code (ADR-005).

A published code is a one-way door: once a consumer matches on it, its meaning can never change
and it can never be handed to a second situation. So the registry `kit/diagnostics.json` is the
ONE home of what a code means, the refusal class only NAMES its code, and these tests hold the
registry append-only: nothing is duplicated, nothing reused, nothing silently removed, and no
refusal reaches the operator without one. Every expectation is READ from the registry and from
the interpreter's own classes -- nothing here names a code by hand.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import json
import re
import unittest
from pathlib import Path

from harness import KIT, Fixtures

import validation  # noqa: E402  -- the path is prepared by importing harness first
from errors import KitError  # noqa: E402

INTERPRETERS = KIT / "interpreters"
#: Both homes are READ from the manifest that ships them, never restated here.
_MANIFEST = json.loads((KIT / "MANIFEST.json").read_text(encoding="utf-8"))
REGISTRY_PATH = KIT / next(a["root"] for a in _MANIFEST["ships"]["accounts"] if a["id"] == "diagnostics")
SCHEMA_PATH = KIT / _MANIFEST["schemas"]["diagnostics"]


def registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def interpreter_files() -> list:
    return sorted(p for p in INTERPRETERS.rglob("*.py") if "__pycache__" not in p.parts)


def refusal_classes() -> list:
    """Every KitError subclass the interpreter declares, discovered by importing every module the
    way the entry point does (by stem) -- never listed, so a new refusal cannot hide from this."""
    for path in interpreter_files():
        module = importlib.import_module(path.stem)
        assert Path(module.__file__).resolve() == path.resolve(), (
            f"{path} is shadowed by {module.__file__}: one stem, two modules")
    # Keyed by the DECLARATION (file + qualname), not the class object: a module reachable by two
    # import names yields two class objects for one declaration, and a code attaches to the
    # declaration. Counting objects would report one situation as two.
    found, stack = {}, list(KitError.__subclasses__())
    while stack:
        cls = stack.pop()
        found.setdefault(named(cls), cls)
        stack.extend(cls.__subclasses__())
    return [found[key] for key in sorted(found)]


def named(cls) -> str:
    where = Path(inspect.getsourcefile(cls)).resolve().relative_to(INTERPRETERS.resolve())
    return f"{where.as_posix()}::{cls.__qualname__}"


class DiagnosticCodes(Fixtures, unittest.TestCase):

    def test_178_every_refusal_class_names_a_code_the_registry_holds_as_active(self):
        active = {row["code"] for row in registry()["codes"] if row["status"] == "active"}
        classes = refusal_classes()
        self.assertTrue(classes, "no refusal class was discovered; the discovery itself is broken")
        for cls in classes:
            self.assertIn("code", cls.__dict__, f"{named(cls)} inherits its code instead of owning one")
            self.assertIn(cls.code, active,
                          f"{named(cls)} names {cls.code!r}, which the registry does not hold as active")

    def test_179_no_two_refusal_classes_answer_to_one_code(self):
        owners: dict = {}
        for cls in refusal_classes():
            owners.setdefault(cls.code, []).append(named(cls))
        shared = {code: who for code, who in owners.items() if len(who) > 1}
        self.assertEqual({}, shared, "one code, several situations: a consumer can no longer tell them apart")

    def test_180_the_registry_is_dense_to_its_high_water_mark_and_no_row_was_ever_deleted(self):
        doc = registry()
        codes = [row["code"] for row in doc["codes"]]
        self.assertEqual(len(codes), len(set(codes)), f"a code is declared twice: {sorted(codes)}")
        expected = [f"{doc['prefix']}{n:04d}" for n in range(1, doc["issued"] + 1)]
        self.assertEqual(expected, codes,
                         "codes must run densely, in order, from 1 to `issued`: a gap is a deleted "
                         "row, and a deleted row is a published code free to be reused")

    def test_181_a_retired_code_is_raised_by_nothing_and_states_when_and_why(self):
        raised = {cls.code for cls in refusal_classes()}
        for row in registry()["codes"]:
            if row["status"] == "retired":
                self.assertIn("retired", row, f"{row['code']} is retired without saying when or why")
                self.assertNotIn(row["code"], raised, f"{row['code']} is retired and raised again: reuse")
            else:
                self.assertNotIn("retired", row, f"{row['code']} is active but carries a retirement")

    def test_182_every_active_code_is_raised_by_a_refusal_class_or_it_must_be_retired(self):
        raised = {cls.code for cls in refusal_classes()}
        orphaned = [row["code"] for row in registry()["codes"]
                    if row["status"] == "active" and row["code"] not in raised]
        self.assertEqual([], orphaned, "an active code nothing raises means nothing; retire it")

    def test_183_the_registry_honours_the_schema_that_declares_it(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual([], validation.validate(registry(), schema))

    def test_184_no_raise_site_in_the_interpreter_raises_the_uncoded_root(self):
        bare = []
        for path in interpreter_files():
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Raise) and node.exc is not None:
                    target = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
                    if isinstance(target, ast.Name) and target.id == KitError.__name__:
                        bare.append(f"{path.relative_to(KIT).as_posix()}:{node.lineno}")
        self.assertEqual([], bare, "a bare KitError reaches the operator with no code")

    def test_185_a_refusal_reaches_the_operator_with_its_code_ahead_of_its_prose(self):
        from errors import PendingApproval
        rows = {row["code"]: row for row in registry()["codes"]}
        self.assertIn(PendingApproval.code, rows)
        result = self.run_kit(KIT, self.host(), "init")
        self.assertEqual(PendingApproval.exit_code, result.returncode, result.stderr)
        line = next(l for l in result.stderr.splitlines() if l.startswith("kit: "))
        self.assertRegex(line, rf"^kit: \[{re.escape(PendingApproval.code)}\] \S",
                         "the code must lead the refusal, bracketed, before the prose")


if __name__ == "__main__":
    unittest.main()
