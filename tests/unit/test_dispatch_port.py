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
import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
KIT = REPO / "kit"

for extra in [KIT / "interpreters", *sorted(p for p in (KIT / "interpreters").iterdir()
                                            if p.is_dir() and not p.name.startswith("_"))]:
    sys.path.insert(0, str(extra))

import admission  # noqa: E402
import dispatch_port  # noqa: E402
import dispatching  # noqa: E402
from manifest import Manifest  # noqa: E402

MANIFEST = Manifest(KIT)
PACKET_SCHEMA = MANIFEST.schema(dispatching.PACKET)
TASK_SCHEMA = MANIFEST.schema(dispatching.TASK)


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
        self.assertEqual(packet, dispatching.packet_from(packet))
        self.assertEqual(packet, dispatching.packet_from(json.dumps(packet)))
        for handed in ("", "   ", "not json at all", "[1, 2]", '"a string"', "null", 17, None):
            with self.subTest(handed=handed):
                with self.assertRaises(dispatching.DispatchRefused) as refused:
                    dispatching.packet_from(handed)
                self.assertTrue(str(refused.exception))

    # == 2. a declaration is filled only with what the port provides ============================
    def test_an_argv_is_filled_only_with_provided_placeholders_and_never_with_a_blank(self):
        provided = dispatching.PROVIDED[0]
        filled = dispatching.argv(["run", "{" + provided + "}"], {provided: "a-value"}, where="a declaration")
        self.assertEqual(["run", "a-value"], filled)

        with self.assertRaises(dispatching.DispatchUnserved) as unserved:
            dispatching.argv(["run", "{nobody_provides_this}"], {}, where="a declaration")
        self.assertIn("nobody_provides_this", str(unserved.exception))

        with self.assertRaises(dispatching.DispatchRefused) as blank:
            dispatching.argv(["run", "{" + provided + "}"], {provided: None}, where="a declaration")
        self.assertIn(provided, str(blank.exception))

    # == 3. one home for the task vocabulary ====================================================
    def test_every_state_the_port_names_is_declared_by_the_task_schema(self):
        declared = TASK_SCHEMA["properties"]["state"]["enum"]
        self.assertEqual(declared, dispatching.vocabulary(ctx()))
        for state in (dispatching.SUBMITTED, dispatching.WORKING, dispatching.INPUT_REQUIRED,
                      dispatching.COMPLETED, dispatching.FAILED):
            self.assertIn(state, declared)

    def test_a_port_naming_a_state_the_schema_does_not_declare_is_refused_before_any_write(self):
        """The congruence check BITES: pointed at a schema that has moved, it names the state."""
        moved = json.loads(json.dumps(TASK_SCHEMA))
        moved["properties"]["state"]["enum"] = [s for s in moved["properties"]["state"]["enum"]
                                                if s != dispatching.WORKING]
        shim = types.SimpleNamespace(manifest=types.SimpleNamespace(schema=lambda _name: moved))
        with self.assertRaises(dispatching.VocabularyDrift) as drift:
            dispatching.vocabulary(shim)
        self.assertIn(dispatching.WORKING, str(drift.exception))

    # == 4. the packet's completeness is the schema's statement =================================
    def test_an_incomplete_packet_is_refused_and_every_missing_part_is_named_at_once(self):
        self.assertEqual(complete_packet(), dispatching.complete(ctx(), complete_packet()))
        for name in PACKET_SCHEMA["required"]:
            with self.subTest(missing=name):
                short = {k: v for k, v in complete_packet().items() if k != name}
                with self.assertRaises(dispatching.DispatchRefused) as refused:
                    dispatching.complete(ctx(), short)
                self.assertIn(name, str(refused.exception))
        empty = dict(complete_packet(), id="")
        with self.assertRaises(dispatching.DispatchRefused):
            dispatching.complete(ctx(), empty)


class PublishedDispatchAdapters(unittest.TestCase):
    """Every intelligence this repository publishes a dispatch adapter for, held to the PORT's
    contract -- without a host, without a runtime, and without that product being installed.

    This is ADR-017 decision 2 measured rather than asserted. The claim is that a new intelligence
    joins by a DECLARATION and that no interpreter, port or schema enum is edited to admit it; the
    way to measure it is to take every published adapter, whichever product it happens to name,
    and hold it to exactly what the port provides. No product is named here: the documents are
    found by the CONTRACT they keep, which is how the port itself finds them.
    """

    @staticmethod
    def published() -> list:
        """(adapter directory, row) for every published dispatch adapter, found the port's way."""
        found = []
        for capability in sorted((REPO / "adapters").glob("*/capability.json")):
            declaration = json.loads(capability.read_text(encoding="utf-8"))
            for document in declaration.get("documents", []):
                if document.get("validates") != dispatching.ADAPTERS["validates"]:
                    continue
                beside = capability.parent / Path(document["source"]).name
                for row in json.loads(beside.read_text(encoding="utf-8"))[dispatching.ADAPTER_LIST]:
                    found.append((capability.parent.name, row))
        return found

    def test_more_than_one_intelligence_is_published_and_the_port_was_not_edited_for_either(self):
        """A second adapter is the whole proof: one could be the port's own shape in disguise."""
        published = self.published()
        self.assertGreater(len(published), 1, "only one dispatch adapter is published, so nothing "
                                              "here can show that a second intelligence costs a "
                                              "declaration and not an edit")
        for _where, row in published:
            with self.subTest(adapter=row["id"]):
                self.assertEqual([], MANIFEST.validate(
                    {"schema_version": 1, dispatching.ADAPTER_LIST: [row]},
                    dispatching.ADAPTERS["validates"]))

    def test_every_published_adapter_names_only_what_the_port_provides(self):
        """A placeholder or a channel the port does not provide is refused BY NAME, and is refused
        here rather than at the moment a worker would otherwise have been started blank. Held to
        the PORT's own door check, whole -- a suite that re-stated which blocks to inspect would
        go on passing over the next block an adapter may declare."""
        for where, row in self.published():
            with self.subTest(adapter=row["id"]):
                dispatching.coherent(row)
                blanks = {name: "a-value" for name in dispatching.PROVIDED}
                if "stdin" in row["starts"]:
                    dispatching.argv([row["starts"]["stdin"]], blanks, where=where)
                for part in row["returns"]:
                    self.assertIn(part["from"], dispatching.CHANNELS,
                                  f"{row['id']} returns {part['name']!r} from a channel the port "
                                  f"does not provide; an artifact read from nowhere is a fabricated one")

    def test_an_adapter_that_answers_in_a_file_is_given_one_by_the_port_and_never_its_own(self):
        """The file channel exists exactly so that an ARTIFACT comes back as a file with a declared
        shape instead of a transcript somebody parsed. The port provides the path; an adapter that
        named a path of its own would put the host's layout into a second home."""
        self.assertIn(dispatching.FILE, dispatching.CHANNELS)
        self.assertIn(dispatching.ARTIFACT, dispatching.PROVIDED)
        for _where, row in self.published():
            if any(part["from"] == dispatching.FILE for part in row["returns"]):
                with self.subTest(adapter=row["id"]):
                    self.assertIn("{" + dispatching.ARTIFACT + "}", " ".join(row["starts"]["argv"]),
                                  "this adapter returns an artifact from a file and is never told "
                                  "which file, so nothing it wrote could be read back")


class AnAdapterThatAsks(unittest.TestCase):
    """The round-trip's DECLARATION, held at the door (ADR-017 C4).

    A worker that cannot proceed returns its question, and how it says so is the adapter's to
    state. Everything below is therefore a property of reading a DECLARATION -- no host, no
    runtime, no worker -- and each one is refused BEFORE anything is leased, because the worst
    moment to discover that a resume argv names a placeholder nobody provides is the moment an
    operator has finally answered.

    No product is named. The rows are built here, which is the point: the port serves an
    intelligence nobody shipped, and an adapter that asks is still just an adapter.
    """

    @staticmethod
    def row(**declared) -> dict:
        return dict({
            "id": "an-intelligence", "says": "a fixture",
            "starts": {"argv": ["a-program", "{instruction}"]},
            "returns": [{"name": "result", "from": "file"}, {"name": "session", "from": "stdout"}],
            "completed_on": {"exit": 0},
        }, **declared)

    ASKS = {"exit": 7, "question": "result", "reentry": "session"}
    RESUMES = {"argv": ["a-program", "resume", "{reentry}", "{answer}"]}

    def test_the_two_values_a_resume_needs_are_values_the_port_provides(self):
        """`{answer}` and `{reentry}` are the port's to provide, like every other placeholder: an
        adapter widens nothing by naming them, and one that names something else is refused."""
        self.assertIn(dispatching.ANSWER, dispatching.PROVIDED)
        self.assertIn(dispatching.REENTRY, dispatching.PROVIDED)
        asking = self.row(**{dispatching.ASKS: self.ASKS, dispatching.RESUMES: self.RESUMES})
        self.assertEqual([], MANIFEST.validate({"schema_version": 1, "adapters": [asking]},
                                               dispatching.ADAPTERS["validates"]))
        self.assertIs(asking, dispatching.coherent(asking))

    def test_an_adapter_may_declare_neither_block_and_nothing_about_it_changes(self):
        """The round-trip is a capability an adapter DECLARES, never one the port assumes: the
        rows that existed before C4 are still whole adapters and still pass the same door."""
        self.assertEqual([], MANIFEST.validate({"schema_version": 1, "adapters": [self.row()]},
                                               dispatching.ADAPTERS["validates"]))
        dispatching.coherent(self.row())

    def test_one_ending_may_not_mean_both_finished_and_needs_input(self):
        with self.assertRaises(dispatching.DispatchUnserved) as refused:
            dispatching.coherent(self.row(**{dispatching.ASKS: dict(self.ASKS, exit=0),
                                               dispatching.RESUMES: self.RESUMES}))
        self.assertIn("two states", str(refused.exception))

    def test_a_question_is_read_from_a_channel_the_adapter_declared_and_never_from_nowhere(self):
        for role in (dispatching.QUESTION, dispatching.REENTRY):
            with self.subTest(carries=role):
                with self.assertRaises(dispatching.DispatchUnserved) as refused:
                    dispatching.coherent(self.row(
                        **{dispatching.ASKS: dict(self.ASKS, **{role: "an-artifact-nobody-declares"}),
                           dispatching.RESUMES: self.RESUMES}))
                self.assertIn("an-artifact-nobody-declares", str(refused.exception))

    def test_a_question_and_the_way_back_in_may_not_be_the_one_text(self):
        with self.assertRaises(dispatching.DispatchUnserved) as refused:
            dispatching.coherent(self.row(
                **{dispatching.ASKS: dict(self.ASKS, reentry=self.ASKS["question"]),
                   dispatching.RESUMES: self.RESUMES}))
        self.assertIn(self.ASKS["question"], str(refused.exception))

    def test_a_resume_argv_is_held_to_what_the_port_provides_before_anything_is_leased(self):
        with self.assertRaises(dispatching.DispatchUnserved) as refused:
            dispatching.coherent(self.row(**{
                dispatching.ASKS: self.ASKS,
                dispatching.RESUMES: {"argv": ["a-program", "{nobody_provides_this}"]}}))
        self.assertIn("nobody_provides_this", str(refused.exception))
        self.assertIn(dispatching.RESUMES, str(refused.exception))

    def test_the_exchange_a_record_keeps_is_a_shape_the_task_schema_declares(self):
        """Both turns, held to the record's own contract -- the question the port builds from a
        declaration, and the answer an operator hands over. A turn the schema does not admit would
        be discovered at the first flush, on a record that already had a worker standing behind it."""
        artifacts = [{"name": "result", "from": "file", "text": "which of the two did you mean?"},
                     {"name": "session", "from": "stdout", "text": "a-session\n"}]
        asked = dispatch_port._question(self.row(**{dispatching.RESUMES: self.RESUMES}),
                                        self.ASKS, artifacts, "a-moment")
        self.assertEqual("a-session", asked[dispatching.REENTRY])
        self.assertNotIn("unresumable", asked)
        unresumable = dispatch_port._question(self.row(), self.ASKS, artifacts, "a-moment")
        self.assertIn(self.row()["id"], unresumable["unresumable"])

        empty = dispatch_port._question(
            self.row(), self.ASKS,
            [{"name": "result", "from": "file", "text": "   "},
             {"name": "session", "from": "stdout", "text": ""}], "a-moment")
        self.assertNotIn("text", empty, "an empty question was recorded as a question")
        self.assertTrue(empty["absent"] and empty["reentry_absent"])

        declared = TASK_SCHEMA["properties"][dispatching.HISTORY]["items"]
        for turn in (asked, unresumable, empty,
                     {"role": dispatching.OPERATOR, "at": "a-moment", "text": "an answer",
                      "by": "an-operator"}):
            for field in turn:
                self.assertIn(field, declared["properties"])
            for field in declared["required"]:
                self.assertIn(field, turn)
            self.assertIn(turn["role"], declared["properties"]["role"]["enum"])


class AdmissionOnReturn(unittest.TestCase):
    """What a worker's tree came back with is ADMITTED or REFUSED -- and never passed over.

    These properties are the ones that hold with NO gate declared at all, which is deliberately the
    most dangerous case: a host with no edit gates must still refuse a return it could not read.
    A verdict of `admitted` that means 'nothing was found' is the exact silence ADR-017 decision 5
    exists to close, because it reads identically to a change that was judged and passed.
    """

    PROVIDER = {"id": "a-provider", "says": "a fixture",
                "isolate": {"argv": ["true"]}, "withdraw": {"argv": ["true"]},
                admission.RETURNED: {"argv": ["true"], admission.NAMES: r"^..[ ](.+)$"}}

    def ctx(self):
        """A host with no gate declared: `judgement` is reached for real and finds nothing to say."""
        return types.SimpleNamespace(manifest=MANIFEST, enabled_capabilities=lambda: [],
                                     clock=types.SimpleNamespace(now=lambda: "a-moment"))

    @staticmethod
    def ran(code=0, out="", err=""):
        def run(_argv, cwd, stdin):
            return types.SimpleNamespace(returncode=code, stdout=out, stderr=err)
        return run

    def tree(self) -> Path:
        home = Path(tempfile.mkdtemp(prefix="admission-")).resolve()
        self.addCleanup(shutil.rmtree, home, True)
        return home

    def verdict(self, tree, run) -> dict:
        """The verdict, and the ONE thing every verdict must satisfy whatever it says: it is a
        shape the `task` schema declares, so a record carrying it is still a task record."""
        found = admission.of(self.ctx(), self.PROVIDER, tree, ["a-report"], run)
        self.assertIn(found["verdict"],
                      TASK_SCHEMA["properties"]["admission"]["properties"]["verdict"]["enum"])
        for field in TASK_SCHEMA["properties"]["admission"]["required"]:
            self.assertIn(field, found)
        for field in found:
            self.assertIn(field, TASK_SCHEMA["properties"]["admission"]["properties"])
        return found

    def test_a_tree_that_cannot_say_what_changed_is_refused_and_never_admitted(self):
        found = self.verdict(self.tree(), self.ran(code=128, err="not a working tree"))
        self.assertEqual(admission.REFUSED, found["verdict"])
        self.assertIn("not a working tree", found["because"])
        self.assertEqual([], found["judged"])

    def test_a_returned_path_whose_text_cannot_be_read_is_refused_rather_than_skipped(self):
        tree = self.tree()
        (tree / "a-file").write_bytes(b"\xff\xfe\x00 not decodable as text \x80")
        found = self.verdict(tree, self.ran(out="?? a-file\n"))
        self.assertEqual(admission.REFUSED, found["verdict"])
        self.assertIn("a-file", found["unreadable"])

    def test_a_change_the_tree_reports_outside_the_tree_it_was_given_is_refused(self):
        found = self.verdict(self.tree(), self.ran(out="?? ../elsewhere/a-file\n"))
        self.assertEqual(admission.REFUSED, found["verdict"])
        self.assertTrue(found["unreadable"])

    def test_a_clean_return_is_admitted_and_names_every_path_it_judged(self):
        tree = self.tree()
        (tree / "a-file").write_text("ordinary text", encoding="utf-8")
        found = self.verdict(tree, self.ran(out="?? a-file\nnot a line this grammar matches\n"))
        self.assertEqual(admission.ADMITTED, found["verdict"])
        self.assertEqual(["a-file"], found["judged"])
        self.assertEqual("a-moment", found["at"])

    def test_a_deleted_path_introduces_no_text_and_is_recorded_rather_than_passed_over(self):
        found = self.verdict(self.tree(), self.ran(out=" D a-file\n"))
        self.assertEqual(admission.ADMITTED, found["verdict"])
        self.assertEqual(["a-file"], found["deleted"])

    def test_a_provider_that_cannot_report_a_return_cannot_be_dispatched_through(self):
        """Refused at the DOOR: a worker is never started where its return could not be judged."""
        self.assertTrue(admission.declares(self.PROVIDER))
        self.assertFalse(admission.declares(
            {k: v for k, v in self.PROVIDER.items() if k != admission.RETURNED}))


if __name__ == "__main__":
    unittest.main()
