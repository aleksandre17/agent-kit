"""Unit: the subagent ledger reads ANY product's sub-agent record through a declaration (ADR-024).

The `ledger` verb names no product: where a sub-agent-stop event names the finished agent and its
transcript, and how one transcript line carries a model turn, is the surface's `hands.ledger`. So a
product nobody ships, with its own key layout, is read by a declaration alone -- the open set, proven
with a fixture the kit does not carry:

  1. the last line of a turn key wins (a product that streams one turn as several lines repeats it);
  2. numbers are summed over turns, strings collected; lines outside `where` are not turns;
  3. a requested model the turns did not run on is a mismatch, named -- never smoothed over;
  4. a transcript that cannot be read is `reported: false`, never zeros presented as a measurement.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[2] / "kit"
INTERPRETERS = KIT / "interpreters"
for extra in [INTERPRETERS, *sorted(p for p in INTERPRETERS.iterdir() if p.is_dir() and not p.name.startswith("_"))]:
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from verbs import ledger  # noqa: E402

#: A product nobody ships, declared the way an adapter would declare it.
HAND = {"ledger": {
    "agent": ["run.id"], "name": ["run.kind"], "transcript": ["run.log"], "provider": "a-fixture-provider",
    "entries": {"where": {"kind": "turn"}, "key": "turn.n", "fields": {
        ledger.REQUESTED: "turn.asked", ledger.RESPONDED: "turn.ran",
        "gen_ai.usage.input_tokens": "turn.spent.in", "gen_ai.usage.output_tokens": "turn.spent.out"}}}}


def _turn(n, asked, ran, spent_in, spent_out):
    return json.dumps({"kind": "turn", "turn": {"n": n, "asked": asked, "ran": ran,
                                                "spent": {"in": spent_in, "out": spent_out}}})


class SubagentLedger(unittest.TestCase):

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="ledger-"))

    def event(self, lines):
        (self.root / "agent.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
        return {"run": {"id": "a1", "kind": "reviewer", "log": "agent.jsonl"}}

    def test_a_turn_streamed_twice_counts_once_and_its_last_line_wins(self):
        row = ledger.read(HAND, self.event([_turn(1, "m-small", "m-small", 5, 1), _turn(1, "m-small", "m-small", 5, 9),
                                            _turn(2, "m-small", "m-small", 3, 2), json.dumps({"kind": "note"})]),
                          self.root)
        self.assertEqual((2, 8, 11), (row["turns"], row["gen_ai.usage.input_tokens"], row["gen_ai.usage.output_tokens"]))
        self.assertEqual(("a1", "reviewer", "a-fixture-provider"),
                         (row[ledger.AGENT_ID], row[ledger.AGENT_NAME], row[ledger.PROVIDER]))
        self.assertIs(False, row["mismatch"])
        self.assertTrue(row["reported"])

    def test_a_requested_model_the_turns_did_not_run_on_is_named(self):
        row = ledger.read(HAND, self.event([_turn(1, "m-small", "m-large", 1, 1)]), self.root)
        self.assertEqual(("m-small", "m-large", True), (row[ledger.REQUESTED], row[ledger.RESPONDED], row["mismatch"]))

    def test_a_transcript_that_cannot_be_read_is_not_reported(self):
        row = ledger.read(HAND, {"run": {"id": "a2", "log": "absent.jsonl"}}, self.root)
        self.assertEqual((False, 0), (row["reported"], row["turns"]))
        self.assertNotIn("gen_ai.usage.input_tokens", row)


if __name__ == "__main__":
    unittest.main()
