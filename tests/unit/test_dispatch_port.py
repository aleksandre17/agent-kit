"""Unit: the dispatch PORT refuses, and the refusal belongs to the port (ADR-017 C2).

Four properties, and only these -- everything a refusal needs a whole installed host to reach is
exercised where it belongs, in the acceptance suite:

  1. what a caller hands over is read by the PORT, so a caller holding a dict and a caller holding
     a line of text meet the same words. Nothing here goes through a verb, a hook or a CLI: the
     gate is reached the way a runtime that wanted to skip it would reach it;
  2. an argv a declaration states is filled only with placeholders the port PROVIDES; an unknown
     one is refused BY NAME and a provided one this task states no value for is refused as that --
     never substituted with an empty string;
  3. the task vocabulary has ONE home: every state the port names is declared by the `task` schema.
     A constant quietly restating an enum is the drift the whole project exists against, so it is
     measured rather than trusted;
  4. the packet shape is the schema's to state, and an incomplete packet names every missing part
     at once -- read from the schema, never listed here.

No packet fixture is hand-written as a shape: the complete one below is built FROM the schema's own
required list, so a test cannot go on passing after the contract has moved.
"""

from __future__ import annotations

import json
import sys
import types
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
KIT = REPO / "kit"

sys.dont_write_bytecode = True
for extra in [KIT / "interpreters", *sorted(p for p in (KIT / "interpreters").iterdir()
                                            if p.is_dir() and not p.name.startswith("_"))]:
    sys.path.insert(0, str(extra))

import dispatch_port  # noqa: E402
from manifest import Manifest  # noqa: E402

MANIFEST = Manifest(KIT)
PACKET_SCHEMA = MANIFEST.schema(dispatch_port.PACKET)
TASK_SCHEMA = MANIFEST.schema(dispatch_port.TASK)


def ctx() -> types.SimpleNamespace:
    """The only part of a context these properties touch: the schemas. A host is not installed to
    ask whether a word means what the schema says it means."""
    return types.SimpleNamespace(manifest=MANIFEST)


def complete_packet() -> dict:
    """A packet carrying exactly what the schema requires, with a value the schema admits for each
    -- generated from the contract, so there is no second statement of the contract here."""
    built = {}
    for name in PACKET_SCHEMA["required"]:
        declared = PACKET_SCHEMA["properties"][name]
        if "const" in declared:
            built[name] = declared["const"]
        else:
            built[name] = "c2-acceptance-name"
    return built


class DispatchPortRefusals(unittest.TestCase):

    # == 1. the reading is the port's ==========================================================
    def test_the_port_reads_what_a_caller_hands_over_and_refuses_what_states_no_task(self):
        packet = complete_packet()
        self.assertEqual(packet, dispatch_port.packet_from(packet))
        self.assertEqual(packet, dispatch_port.packet_from(json.dumps(packet)))
        for handed in ("", "   ", "not json at all", "[1, 2]", '"a string"', "null", 17, None):
            with self.subTest(handed=handed):
                with self.assertRaises(dispatch_port.DispatchRefused) as refused:
                    dispatch_port.packet_from(handed)
                self.assertTrue(str(refused.exception))

    # == 2. a declaration is filled only with what the port provides ============================
    def test_an_argv_is_filled_only_with_provided_placeholders_and_never_with_a_blank(self):
        provided = dispatch_port.PROVIDED[0]
        filled = dispatch_port._argv(["run", "{" + provided + "}"], {provided: "a-value"}, where="a declaration")
        self.assertEqual(["run", "a-value"], filled)

        with self.assertRaises(dispatch_port.DispatchUnserved) as unserved:
            dispatch_port._argv(["run", "{nobody_provides_this}"], {}, where="a declaration")
        self.assertIn("nobody_provides_this", str(unserved.exception))

        with self.assertRaises(dispatch_port.DispatchRefused) as blank:
            dispatch_port._argv(["run", "{" + provided + "}"], {provided: None}, where="a declaration")
        self.assertIn(provided, str(blank.exception))

    # == 3. one home for the task vocabulary ====================================================
    def test_every_state_the_port_names_is_declared_by_the_task_schema(self):
        declared = TASK_SCHEMA["properties"]["state"]["enum"]
        self.assertEqual(declared, dispatch_port.vocabulary(ctx()))
        for state in (dispatch_port.SUBMITTED, dispatch_port.WORKING,
                      dispatch_port.COMPLETED, dispatch_port.FAILED):
            self.assertIn(state, declared)

    def test_a_port_naming_a_state_the_schema_does_not_declare_is_refused_before_any_write(self):
        """The congruence check BITES: pointed at a schema that has moved, it names the state."""
        moved = json.loads(json.dumps(TASK_SCHEMA))
        moved["properties"]["state"]["enum"] = [s for s in moved["properties"]["state"]["enum"]
                                                if s != dispatch_port.WORKING]
        shim = types.SimpleNamespace(manifest=types.SimpleNamespace(schema=lambda _name: moved))
        with self.assertRaises(dispatch_port.VocabularyDrift) as drift:
            dispatch_port.vocabulary(shim)
        self.assertIn(dispatch_port.WORKING, str(drift.exception))

    # == 4. the packet's completeness is the schema's statement =================================
    def test_an_incomplete_packet_is_refused_and_every_missing_part_is_named_at_once(self):
        self.assertEqual(complete_packet(), dispatch_port.complete(ctx(), complete_packet()))
        for name in PACKET_SCHEMA["required"]:
            with self.subTest(missing=name):
                short = {k: v for k, v in complete_packet().items() if k != name}
                with self.assertRaises(dispatch_port.DispatchRefused) as refused:
                    dispatch_port.complete(ctx(), short)
                self.assertIn(name, str(refused.exception))
        empty = dict(complete_packet(), id="")
        with self.assertRaises(dispatch_port.DispatchRefused):
            dispatch_port.complete(ctx(), empty)


if __name__ == "__main__":
    unittest.main()
