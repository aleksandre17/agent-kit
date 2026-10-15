"""Acceptance: the lesson returns -- a host's finding, addressed upstream and carried by a person.

A framework cannot learn from the repositories it is installed in unless something it finds there
can travel back. Everything about HOW it travels is the design, and this suite exists to hold the
three constraints that make the difference between a proposal and a leak:

  1. **never a dependency** -- what leaves is TEXT on a stream. No network, no publisher, no write
     of any kind: not upstream, not in the host, not in the kit. The record that was read is
     byte-identical afterwards, and the verb cannot even be asked for a plan, because it has
     nothing to plan.
  2. **never automatic** -- nothing produces it but being asked for it. No gate reads it, no
     projection shows it, and no other module of the machine so much as imports the one that
     reads it. That is asserted structurally here, because a schedule nobody added today is a
     schedule somebody adds next month.
  3. **seen twice first** -- one occasion is an observation. A claim asked for by name that has
     been made once is REFUSED, and the refusal names exactly what is missing, including the
     records that speak about the subject and do not count, with the reason each one does not.

Nothing in this file names a state, a word or a number. The state that means the work is over is
DERIVED from the shape of the declared lifecycle -- in the suite's own words, so a disagreement
with the machine is a finding rather than a tautology -- and the last test patches a fixture kit
so that a passage leads out of that state, which must make the same two records stop counting.
"""

from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from harness import KIT, Fixtures, host_digest, install_target, sha

VOCABULARY = json.loads((KIT / "capabilities/delivery/lesson.json").read_text(encoding="utf-8"))
LIFECYCLE = json.loads((KIT / "capabilities/delivery/lifecycle.json").read_text(encoding="utf-8"))
CARDS = install_target("delivery", reads_as="cards").rstrip("/")
BOARD = install_target("delivery", mode="projection")
INTERPRETERS = KIT / "interpreters"


def word(beyond: bool) -> dict:
    """A published word of the declared kind, READ from the vocabulary rather than spelled. A
    suite that typed the word would go on passing after the publisher renamed it, testing a
    vocabulary nobody uses any more."""
    return next(row for row in VOCABULARY["extents"] if row["beyond"] is beyond)


def leaves() -> set:
    return {edge["from"] for edge in LIFECYCLE["transitions"]}


def over() -> str:
    """The state this lifecycle declares no passage out of -- the shape that means the work is
    done teaching. Derived here exactly as the machine derives it, and in different words."""
    return next(state["id"] for state in LIFECYCLE["states"] if state["id"] not in leaves())


def kit_digest() -> dict:
    return {p.relative_to(KIT).as_posix(): sha(p)
            for p in sorted(KIT.rglob("*")) if p.is_file()}


class Lesson(Fixtures, unittest.TestCase):

    # -- authoring, as a host does it -----------------------------------------------------------
    def card(self, host: Path, identity: str, state: str, **fields) -> Path:
        body = {"schema_version": 1, "id": identity, "title": f"card {identity}", "state": state,
                "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), **fields}
        path = host / CARDS / f"{identity}.json"
        path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8", newline="\n")
        return path

    def taught(self, subject: str, statement: str, mark: str) -> dict:
        return {"lesson": {"subject": subject, "statement": statement, "extent": mark}}

    def twice(self, host: Path, kit: Path = KIT) -> str:
        """Two separate pieces of work, both over, both saying the same thing about the world."""
        mark = word(True)["id"]
        self.card(host, "aa-one", over(),
                  **self.taught("a-truth-about-any-repository",
                                "A projection over a host-authored binding is stale the instant "
                                "the host authors, and nothing says whose duty it is to close "
                                "that window.", mark))
        self.card(host, "bb-two", over(),
                  **self.taught("a-truth-about-any-repository",
                                "Met a second time: the same window, in a different capability, "
                                "worked around by rendering first in two tests.", mark))
        self.assertEqual(0, self.run_kit(kit, host, "render").returncode)
        return "a-truth-about-any-repository"

    # == 1. a claim seen twice is exported, whole ==============================================
    def test_90_a_claim_made_on_two_finished_records_is_exported_as_a_text_addressed_upstream(self):
        """The firing. A proposal a reader upstream can act on: what was learned, how far the
        host claims it holds WITH the publisher's own sentence for that word, and the occasions
        it was seen on, each with the path it can be opened at. Nothing in it has to be looked up
        in a vocabulary the reader does not have."""
        host = self.installed()
        subject = self.twice(host)
        asked = self.run_kit(KIT, host, "propose")
        self.assertEqual(0, asked.returncode)
        text = asked.stdout

        self.assertIn(subject, text)
        self.assertIn("A PROPOSAL FROM A HOST TO WHOEVER PUBLISHED ITS FRAMEWORK", text)
        self.assertIn(word(True)["means"], text,
                      "the mark travelled without the sentence that gives it meaning, so the "
                      "reader has to learn this host's vocabulary to read a proposal")
        for rel in (f"{CARDS}/aa-one.json", f"{CARDS}/bb-two.json"):
            self.assertIn(rel, text, "an occasion arrived without the record it can be checked in")
        self.assertIn("leads no passage out of that state", text,
                      "an occasion arrived without the reason it counts as finished work")
        self.assertIn(str(word(True)["seen_at_least"]), text)
        self.assertIn("Nothing was sent", text)

    # == 2. one occasion is refused, and the refusal says what is missing ======================
    def test_91_a_claim_made_once_is_refused_by_name_and_the_refusal_names_what_is_missing(self):
        """One sighting is an observation. Asked for by name it is REFUSED -- with a code, a
        non-zero exit, the count it stands at, the count its own word requires, and the fact that
        what is missing is another RECORD rather than another sentence on this one."""
        host = self.installed()
        self.card(host, "aa-one", over(),
                  **self.taught("a-truth-seen-once", "Seen once, and once is an observation.",
                                word(True)["id"]))
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)

        refused = self.run_kit(KIT, host, "propose", "--lesson", "a-truth-seen-once")
        self.assertNotEqual(0, refused.returncode)
        self.assertIn("[KIT0067]", refused.stderr)
        self.assertIn("seen on 1 record(s)", refused.stderr)
        self.assertIn(f"may be carried at {word(True)['seen_at_least']}", refused.stderr)
        self.assertIn("another record", refused.stderr)
        self.assertNotIn("A PROPOSAL FROM A HOST", refused.stdout,
                         "a weaker text was printed beside the refusal")

        # Asked for NOTHING in particular, the same host is not an error: a claim not yet carried
        # is an honest state of a working repository, and a verb that reddened on it would be
        # switched off within a week.
        reported = self.run_kit(KIT, host, "propose")
        self.assertEqual(0, reported.returncode)
        self.assertIn("WITHHELD  a-truth-seen-once", reported.stdout)

    def test_92_a_record_still_in_motion_is_not_a_second_occasion_and_the_refusal_says_so(self):
        """The interesting near-miss: a second record about the same subject whose work is not
        over. It is not counted -- an intention forwarded as a finding is how doctrine acquires
        clauses that were never true -- and it is NAMED in the refusal, so the reader is not sent
        looking for something that is already there."""
        host = self.installed()
        mark = word(True)["id"]
        self.card(host, "aa-one", over(),
                  **self.taught("a-truth-half-seen", "Seen once, finished.", mark))
        self.card(host, "bb-two", LIFECYCLE["initial"],
                  **self.taught("a-truth-half-seen", "Seen again, and still being worked on.", mark))
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)

        refused = self.run_kit(KIT, host, "propose", "--lesson", "a-truth-half-seen")
        self.assertNotEqual(0, refused.returncode)
        self.assertIn("seen on 1 record(s)", refused.stderr)
        self.assertIn(f"{CARDS}/bb-two.json carries the same claim and its work is not over",
                      refused.stderr)
        self.assertIn(LIFECYCLE["initial"], refused.stderr)

    def test_93_a_claim_that_says_it_holds_only_where_it_was_learned_is_never_carried(self):
        """The host's own statement is obeyed. Twice-seen is not enough: what a host says is its
        own business stays its own business, and the refusal says that rather than implying the
        subject does not exist."""
        host = self.installed()
        mark = word(False)["id"]
        for identity in ("aa-one", "bb-two"):
            self.card(host, identity, over(),
                      **self.taught("a-truth-about-this-place", "True here, about us.", mark))
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)

        asked = self.run_kit(KIT, host, "propose")
        self.assertEqual(0, asked.returncode)
        self.assertNotIn("A PROPOSAL FROM A HOST", asked.stdout)

        refused = self.run_kit(KIT, host, "propose", "--lesson", "a-truth-about-this-place")
        self.assertNotEqual(0, refused.returncode)
        self.assertIn("none of them claims it holds beyond this repository", refused.stderr)
        self.assertIn(mark, refused.stderr)

    def test_94_a_mark_no_vocabulary_declares_is_named_never_guessed_at(self):
        """A word nobody published says nothing. It is reported as unread -- not as a claim that
        holds here, and not as one that holds anywhere else -- because a reader that guessed
        would be inventing the claim it then carried on the host's behalf."""
        host = self.installed()
        self.card(host, "aa-one", over(),
                  **self.taught("a-truth-marked-strangely", "Marked in a private word.",
                                "a-word-nobody-published"))
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)

        asked = self.run_kit(KIT, host, "propose")
        self.assertEqual(0, asked.returncode)
        self.assertIn("UNREAD", asked.stdout)
        self.assertIn("a-word-nobody-published", asked.stdout)
        self.assertIn(f"{CARDS}/aa-one.json", asked.stdout)

    # == 3. never a dependency: nothing is written, here or anywhere ===========================
    def test_95_producing_the_text_writes_nothing_and_leaves_the_records_it_read_untouched(self):
        """The constraint that makes this a proposal rather than a leak. The whole host is
        digested before and after, the kit beside it, and the record that was quoted is compared
        byte for byte: a mechanism that carried a lesson by WRITING one would have made every
        host a supplier of something nobody bought."""
        host = self.installed()
        subject = self.twice(host)
        before_host, before_kit = host_digest(host), kit_digest()
        source = (host / CARDS / "aa-one.json").read_bytes()

        asked = self.run_kit(KIT, host, "propose")
        self.assertEqual(0, asked.returncode)
        self.assertIn(subject, asked.stdout)

        self.assertEqual(before_host, host_digest(host), "the host changed while being read")
        self.assertEqual(before_kit, kit_digest(), "the kit wrote into itself while reading a host")
        self.assertEqual(source, (host / CARDS / "aa-one.json").read_bytes(),
                         "the record that was quoted is not the record that was there")

        planned = self.run_kit(KIT, host, "propose", "--plan")
        self.assertEqual(2, planned.returncode,
                         "a verb that writes nothing answered a request for a plan, and an empty "
                         "plan reads exactly like nothing to do")

    # == 4. never automatic: nothing produces it but being asked ===============================
    def test_96_nothing_but_being_asked_produces_the_text(self):
        """Structural, not behavioural -- a schedule nobody added today is one somebody adds next
        month. The module that reads these claims is imported by exactly one verb; no gate, no
        projection and no judgement of this host's health mentions it; and a host carrying a
        claim ready to carry passes `check` with the claim nowhere in what `check` says."""
        readers = [path.relative_to(KIT).as_posix() for path in sorted(INTERPRETERS.rglob("*.py"))
                   if "import lesson" in path.read_text(encoding="utf-8")]
        self.assertEqual(["interpreters/verbs/propose.py"], readers,
                         "something other than the verb that is asked reads what a host learned")

        host = self.installed()
        subject = self.twice(host)
        checked = self.run_kit(KIT, host, "check")
        self.assertEqual(0, checked.returncode)
        self.assertNotIn(subject, checked.stdout + checked.stderr,
                         "the host's own instruments announce what it has to say upstream")
        self.assertNotIn(subject, (host / BOARD).read_text(encoding="utf-8"),
                         "a projection carries the claim, so it travels without being asked for")

    # == 5. the state that means the work is over is READ, never named =========================
    def test_97_a_lifecycle_that_grows_a_passage_out_of_that_state_stops_the_claim_counting(self):
        """The proof that nothing here holds a word for *over*. One fixture kit, identical to the
        real one but for a declared passage OUT of the state the work does not leave -- and the
        same two records stop being finished work. Nothing in the machine is touched."""
        leaving = over()

        def patch(kit: Path) -> None:
            def mutate(value):
                value["transitions"].append({
                    "from": leaving, "to": value["initial"], "owner": "doer",
                    "exit": "a fixture's passage, declared so that no state is terminal here",
                })
            self.edit_json(kit, "capabilities/delivery/lifecycle.json", mutate)

        kit = self.fixture_kit("lesson-no-terminal", patch=patch)
        host = self.installed(kit)
        subject = self.twice(host, kit)

        asked = self.run_kit(kit, host, "propose")
        self.assertEqual(0, asked.returncode)
        self.assertNotIn("A PROPOSAL FROM A HOST", asked.stdout,
                         "a claim was carried out of a state the lifecycle now leads out of, so "
                         "the machine is holding a word for *over* of its own")
        self.assertIn("WITHHELD", asked.stdout)

        refused = self.run_kit(kit, host, "propose", "--lesson", subject)
        self.assertNotEqual(0, refused.returncode)
        self.assertIn("seen on 0 record(s)", refused.stderr)
