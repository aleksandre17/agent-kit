"""Acceptance: delivery -- a COLLECTION the host authors, and a lifecycle it may not step outside.

Everything proved before this suite concerns files the KIT writes: one declaration, one target,
one reading. Delivery is the first capability whose subject is plural and host-authored -- a
directory the host fills with cards -- and plurality is where the interesting failures live: a
projection that quietly drops a record, an installer that reads a space as though it were a file,
a state name that ends up spelled once in a declaration and once in the machine.

So the four things this suite exists to prove are the four things nothing above it can:

  1. a card collection is a DECLARED collection, projected from a DIRECTORY -- never a file read;
  2. the states and the passages between them are DATA, and no interpreter module names one;
  3. an illegal passage is REFUSED, by a stable message and a non-zero exit, before any byte;
  4. changing the delivery POLICY changes the outcome with the interpreter bytes untouched.

Every host here is reached only through the CLI, as a host reaches it.
"""

from __future__ import annotations

import json
import re
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from harness import KIT, Fixtures, install_target, sha
from manifest import Manifest  # noqa: E402
import appetite as appetite_module  # noqa: E402 -- the one home for a unit of spend
import criteria as criteria_module  # noqa: E402 -- the one home for a kind of proof
import space as space_module  # noqa: E402 -- the one home for a declared empty space

#: The one place this suite learns what delivery declares. Read, never restated: a test carrying
#: its own copy of a lifecycle is a second home for it, and goes on passing after the real one has
#: moved -- both internally correct, and no longer describing the same system.
LIFECYCLE = json.loads((KIT / "capabilities/delivery/lifecycle.json").read_text(encoding="utf-8"))
CARDS = install_target("delivery", reads_as="cards").rstrip("/")
BOARD = install_target("delivery", mode="projection")
POLICY = install_target("delivery", reads_as="policy")

INTERPRETERS = KIT / "interpreters"


def state_ids() -> list:
    return [state["id"] for state in LIFECYCLE["states"]]


def interpreter_sources() -> list:
    return sorted(p for p in INTERPRETERS.rglob("*.py"))


def interpreter_digest() -> dict:
    return {p.relative_to(KIT).as_posix(): sha(p) for p in interpreter_sources()}


class Delivery(Fixtures, unittest.TestCase):

    # -- authoring -----------------------------------------------------------------------------
    def card(self, host: Path, identity: str, state: str, **fields) -> Path:
        """A card as a HOST authors one: a file the host puts in the space the capability
        declared. Nothing in the kit ever writes one -- that is the point of a space.

        `created_at` defaults to NOW because a card authored a moment ago is the ordinary case,
        and the staleness rule is real: dating every fixture in the past would make every suite
        below trip a gate that is doing its job."""
        body = {"schema_version": 1, "id": identity, "title": f"card {identity}", "state": state,
                "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), **fields}
        path = host / CARDS / f"{identity}.json"
        path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
        return path

    def board(self, host: Path) -> str:
        return (host / BOARD).read_text(encoding="utf-8")

    def read_card(self, host: Path, identity: str) -> dict:
        return json.loads((host / CARDS / f"{identity}.json").read_text(encoding="utf-8"))

    # == 1. the collection =====================================================================
    def test_50_the_card_space_is_installed_empty_and_projected_as_a_collection(self):
        """The space is created and left EMPTY of CARDS -- a kit that seeded an example card would
        be authoring the host's content -- and the board projects it as a collection of records
        read from a DIRECTORY. The empty case is asserted first because it is the one a file read
        cannot survive: there is nothing there to mistake for a document.

        Empty of cards is not empty of files. The space holds one marker declaring its own
        emptiness, because a repository cannot carry an empty directory and the space would
        otherwise be gone from the next clone. It says nothing about delivery, about this host, or
        about any domain -- which is the test the blueprint's blank rule (T2) actually applies --
        so it is a declared state and not authored content."""
        host = self.installed()
        cards = host / CARDS
        self.assertTrue(cards.is_dir(), "the declared space was not created")
        self.assertEqual([space_module.marker(Manifest(KIT))], sorted(p.name for p in cards.iterdir()),
                         "the kit authored content into a host space")

        empty = self.board(host)
        for state in LIFECYCLE["states"]:
            self.assertIn(f"## {state['title']}", empty,
                          "a declared state with no cards must still be a column: an omitted "
                          "column is a surface saying the state does not exist")
        self.assertIn("_empty_", empty)

        self.card(host, "aa-first", "intake")
        self.card(host, "bb-second", "shaped")
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        filled = self.board(host)
        self.assertIn("**aa-first** — card aa-first", filled)
        self.assertIn("**bb-second** — card bb-second", filled)
        self.assertIn("## Intake — 1 card(s)", filled)
        self.assertIn("## Shaped — 1 card(s)", filled)
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode)

    def test_51_a_card_in_an_undeclared_state_is_named_never_dropped(self):
        """The projection's honesty case. A card whose state the lifecycle does not declare is
        REFUSED by name -- a board that simply omitted it would be a surface stating that a card
        this host authored does not exist."""
        host = self.installed()
        self.card(host, "stray", "somewhere-nobody-declared")
        result = self.run_kit(KIT, host, "render")
        self.assertNotEqual(0, result.returncode)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("'stray'", result.stderr)
        self.assertIn("which lifecycle", result.stderr)

    def test_52_two_files_claiming_one_card_identity_are_refused(self):
        """Plurality's own Cardinal III case: two records with one id is two homes for every truth
        that card carries, and both go on reading as correct while they disagree."""
        host = self.installed()
        self.card(host, "twin", "intake")
        (host / CARDS / "copy.json").write_text(
            (host / CARDS / "twin.json").read_text(encoding="utf-8"), encoding="utf-8")
        result = self.run_kit(KIT, host, "check")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("'twin'", result.stderr)
        self.assertIn("declared by two files", result.stderr)

    # == 2. the states are data ================================================================
    def test_53_no_interpreter_module_names_a_declared_state(self):
        """The fitness function under the whole slice. Every state and every passage is a row in
        a document; if the machine spelled one of those names in its own source, the declaration
        would have a second home and a host could no longer change it by declaring."""
        offenders = []
        for path in interpreter_sources():
            text = path.read_text(encoding="utf-8")
            for identity in state_ids():
                # A privileged name in code is a STRING LITERAL. Prose may discuss a state freely;
                # a comment cannot be dispatched on, and only what the machine compares against
                # can make a declaration unchangeable.
                if re.search(rf"""['"]{re.escape(identity)}['"]""", text):
                    offenders.append(f"{path.relative_to(KIT).as_posix()} names {identity!r}")
        self.assertEqual([], offenders,
                         "an interpreter that spells a state is an interpreter that decides")

    def test_54_a_lifecycle_the_host_changed_moves_the_board_with_no_interpreter_edit(self):
        """The declaration is the whole grammar. A fixture kit with an EXTRA state and an extra
        passage produces a new column and a legal move -- and the interpreter bytes are identical
        to the ones that never heard of it."""
        before = interpreter_digest()

        def add_a_state(kit: Path):
            def mutate(doc):
                doc["states"].append({"id": "rehearsed", "title": "Rehearsed", "owner": "doer",
                                      "intent": "A state this host invented by declaring it."})
                doc["transitions"].append({"from": "intake", "to": "rehearsed", "owner": "doer",
                                           "exit": "declared by the host, honoured by the machine"})
            self.edit_json(kit, "capabilities/delivery/lifecycle.json", mutate)

        kit = self.fixture_kit("extra-state", add_a_state)
        host = self.installed(kit)
        self.assertIn("## Rehearsed", self.board(host))

        self.card(host, "new-shape", "intake")
        moved = self.run_kit(kit, host, "move", "--card", "new-shape",
                             "--to", "rehearsed", "--by", "acceptance-suite")
        self.assertEqual(0, moved.returncode, moved.stderr)
        self.assertEqual("rehearsed", self.read_card(host, "new-shape")["state"])
        self.assertIn("**new-shape**", self.board(host).split("## Rehearsed")[1])
        self.assertEqual(before, interpreter_digest(),
                         "a new state cost an interpreter edit, so the grammar is not declared")

    # == 3. the refusals =======================================================================
    def test_55_an_undeclared_passage_is_refused_and_names_the_declared_way(self):
        """A stable message, a non-zero exit, and the card untouched. The refusal names the route
        the host was supposed to walk: a message that says only *no* tells an operator nothing
        about the door they were meant to pass through."""
        host = self.installed()
        self.card(host, "hasty", "intake")
        state_before = self.read_card(host, "hasty")

        result = self.run_kit(KIT, host, "move", "--card", "hasty",
                              "--to", "landed", "--by", "acceptance-suite")
        self.assertNotEqual(0, result.returncode)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("may not move intake -> landed", result.stderr)
        self.assertIn("is not a declared passage", result.stderr)
        self.assertIn("the declared way from 'intake' to 'landed' is:", result.stderr)
        self.assertIn("DOOR", result.stderr)
        self.assertEqual(state_before, self.read_card(host, "hasty"),
                         "a refused move must not have touched the card")

    def test_56_a_move_naming_a_state_nobody_declared_is_refused_with_the_declared_ones(self):
        host = self.installed()
        self.card(host, "adrift", "intake")
        result = self.run_kit(KIT, host, "move", "--card", "adrift",
                              "--to", "shipped-it", "--by", "acceptance-suite")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("'shipped-it' is not a state", result.stderr)
        for identity in state_ids():
            self.assertIn(identity, result.stderr, "the refusal must name what IS declared")

    def test_57_a_door_may_not_be_opened_by_a_machine_and_records_who_opened_it(self):
        """The declaration marks `shaped -> bet` a door. Asked without a name, the kit does not
        fail -- it STALLS, with its own exit code, because waiting for a human is a declared state
        and not a breakage. Walked with a name, the passage carries who accepted it and when."""
        host = self.installed()
        self.card(host, "waiting", "shaped")

        stalled = self.run_kit(KIT, host, "move", "--card", "waiting",
                               "--to", "bet", "--by", "acceptance-suite")
        self.assertEqual(3, stalled.returncode, stalled.stderr)
        self.assertNotIn("Traceback", stalled.stderr)
        self.assertIn("this is a DOOR", stalled.stderr)
        self.assertEqual("shaped", self.read_card(host, "waiting")["state"])

        walked = self.run_kit(KIT, host, "move", "--card", "waiting",
                              "--to", "bet", "--approve", "the-owner")
        self.assertEqual(0, walked.returncode, walked.stderr)
        card = self.read_card(host, "waiting")
        self.assertEqual("bet", card["state"])
        passage = card["history"][-1]
        self.assertEqual("the-owner", passage["signed_by"])
        self.assertTrue(passage["signed_at"])
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode)

    def test_58_a_guarded_passage_is_open_only_to_the_class_that_declared_it(self):
        """`shaped -> in-flight` is declared open only to a card whose class is the pre-approved
        one. The guard is a row in the declaration, and both halves are proved: refused without
        the class, permitted with it -- same kit, same command, different card."""
        guard = next(e for e in LIFECYCLE["transitions"] if e.get("when"))
        field, permitted = guard["when"]["field"], guard["when"]["equals"]

        host = self.installed()
        self.card(host, "ordinary", guard["from"])
        refused = self.run_kit(KIT, host, "move", "--card", "ordinary",
                               "--to", guard["to"], "--by", "acceptance-suite")
        self.assertNotEqual(0, refused.returncode)
        self.assertIn(f"open only when {field}={permitted!r}", refused.stderr)

        self.card(host, "pre-approved", guard["from"], **{field: permitted})
        allowed = self.run_kit(KIT, host, "move", "--card", "pre-approved",
                               "--to", guard["to"], "--by", "acceptance-suite")
        self.assertEqual(0, allowed.returncode, allowed.stderr)
        self.assertEqual(guard["to"], self.read_card(host, "pre-approved")["state"])

    # == 4. the policy is the host's, and costs no interpreter edit ============================
    def test_59_the_hosts_own_capacity_declaration_decides_and_the_machine_never_moves(self):
        """The proof slices B and C earned, in delivery's vocabulary. The limit lives in a file
        the HOST owns; the kit refuses the move that would exceed it, the gate reports the same
        breach in the same words, and raising the limit -- a one-line change to a declaration --
        reverses both outcomes with every interpreter byte untouched."""
        before = interpreter_digest()
        host = self.installed()
        # The limit is authored HERE, by the host, because the kit seeds none -- a number arriving
        # in a create-once file is an answer this host would never be asked to give, and reading
        # it back out of the seed would be this test agreeing with the kit instead of measuring
        # it. The state comes from the lifecycle, which is where states are declared.
        state = next(passage["to"] for passage in LIFECYCLE["transitions"]
                     if passage["from"] == "bet" and "door" not in passage)
        limit = 1
        policy = json.loads((host / POLICY).read_text(encoding="utf-8"))
        policy["wip_limit"][state] = limit
        (host / POLICY).write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")

        # fill the state to exactly its declared limit, by authoring -- the host's own act
        for index in range(limit):
            self.card(host, f"held-{index}", state)
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode,
                         "a host at its declared limit is not over it")

        # the move that would exceed it is refused BEFORE the byte, naming the host's declaration
        self.card(host, "one-too-many", "bet")
        refused = self.run_kit(KIT, host, "move", "--card", "one-too-many",
                               "--to", state, "--by", "acceptance-suite")
        self.assertNotEqual(0, refused.returncode)
        self.assertIn("may not enter", refused.stderr)
        self.assertIn("this host declared a limit", refused.stderr)
        self.assertEqual("bet", self.read_card(host, "one-too-many")["state"])

        # ... and the gate says the same thing about the same declaration, in the same words
        self.card(host, "over-the-line", state)
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        breached = self.run_kit(KIT, host, "check")
        self.assertEqual(1, breached.returncode)
        self.assertIn("FAIL  FF-DELIVERY-WIP", breached.stdout)
        self.assertIn("declared a limit", breached.stdout)

        # the host raises its own limit: a declaration edit, and nothing else
        policy["wip_limit"][state] = limit + 1
        (host / POLICY).write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")
        # the board carries the limit too, so it is re-projected -- a surface that kept printing
        # the old limit would be a second reading of a declaration the host has already changed
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        self.assertIn(f"limit {limit + 1}", self.board(host))
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode,
                         "the limit is the host's declaration, not the kit's opinion")
        self.assertEqual(before, interpreter_digest(),
                         "a policy change cost an interpreter edit, so the policy is not declared")

    def test_60_a_card_that_has_sat_too_long_is_reported_with_its_moment_never_moved(self):
        """The host's other declared limit, and the one rule that depends on a clock. A stale card
        is REPORTED, and the report states WHEN it was read -- a reading that does not say when it
        was taken is a claim about the present that will go on sounding true. It is never moved:
        a passage records who made it, and no machine may be that who."""
        host = self.installed()
        # Authored by the host, for the same reason as the limit above: how long this host will
        # let a card sit is a thing only this host knows, and the kit that seeded a number would
        # have answered it in a file nothing will ever revisit.
        state, days = state_ids()[0], 7
        policy = json.loads((host / POLICY).read_text(encoding="utf-8"))
        policy["max_age_days"][state] = days
        (host / POLICY).write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")
        stale = datetime.now(timezone.utc) - timedelta(days=days + 1)
        self.card(host, "long-sat", state, created_at=stale.isoformat(timespec="seconds"))
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)

        result = self.run_kit(KIT, host, "check")
        self.assertEqual(1, result.returncode)
        self.assertIn("FAIL  FF-DELIVERY-AGE", result.stdout)
        self.assertIn("'long-sat'", result.stdout)
        self.assertIn("reading at", result.stdout)
        self.assertEqual(state, self.read_card(host, "long-sat")["state"],
                         "the gate moved a card, which is a machine deciding")

    def test_61_a_limit_the_host_declared_on_one_card_is_read_and_an_overrun_stops_at_a_door(self):
        """ADR-020 decision 9, first part, walked end to end through the CLI.

        The limit is the HOST's -- amount and unit authored on the card, because the kit ships the
        words and never a number. What has been spent is READ from the receipt the record already
        carries; nothing is run twice and nothing is written down beside the limit. An overrun is
        REPORTED with the owner named, and that is all that happens: the card is not moved, the
        limit is not raised, and the work is not ended. A card that declares no limit at all is
        not mentioned, which is every card in existence on the day this ships.
        """
        unit = sorted(appetite_module.registry())[0]
        began = datetime.now(timezone.utc) - timedelta(days=4)
        waiting = state_ids()[0]
        # Work spends only while it stands in a state its lifecycle marks as spending (ADR-020 amendment 2):
        # the cards that spend are walked into one, four days ago, by a passage they record.
        spending = next(s["id"] for s in LIFECYCLE["states"] if s.get("spends"))
        walked = [{"at": began.isoformat(timespec="seconds"), "by": "the-doer", "from": waiting, "to": spending}]
        host = self.installed()

        self.card(host, "no-limit-at-all", waiting)
        self.card(host, "well-within-it", spending, created_at=began.isoformat(timespec="seconds"),
                  history=walked, appetite={"amount": 400, "unit": unit})
        # Captured four days ago with a one-day limit and never chosen: it has spent nothing, because
        # the time a card waits to be chosen is not the time its work takes.
        self.card(host, "still-waiting", waiting, created_at=began.isoformat(timespec="seconds"),
                  appetite={"amount": 1, "unit": unit})
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode,
                         "a limit nobody has spent, a card that declared none, and one never chosen are green")

        self.card(host, "spent-it", spending, owner="the-owner",
                  created_at=began.isoformat(timespec="seconds"), history=walked,
                  appetite={"amount": 1, "unit": unit})
        before = self.read_card(host, "spent-it")
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)

        result = self.run_kit(KIT, host, "check")
        self.assertEqual(1, result.returncode)
        self.assertIn("FAIL  FF-DELIVERY-APPETITE", result.stdout)
        self.assertIn("'spent-it'", result.stdout)
        self.assertIn("the-owner", result.stdout, "the report did not name the door it stops at")
        self.assertIn("decision by", result.stdout)
        self.assertNotIn("'no-limit-at-all'", result.stdout, "a card that bet nothing was judged")
        self.assertNotIn("'well-within-it'", result.stdout)
        self.assertNotIn("'still-waiting'", result.stdout, "the days a card waited to be chosen were charged")
        self.assertEqual(before, self.read_card(host, "spent-it"),
                         "the reading raised a limit, moved a card or wrote a spend")

    def test_62_verified_and_landed_cards_stop_spending_appetite(self):
        """Verification is evidence, not ongoing work: time after the verified passage must not
        keep an appetite red, whether the card is waiting to land or has already landed."""
        unit = sorted(appetite_module.registry())[0]
        now = datetime.now(timezone.utc)
        began = now - timedelta(days=4)
        entered_flight = now - timedelta(days=3, hours=23)
        verified = now - timedelta(days=3, hours=22)
        landed = now - timedelta(hours=1)

        history = [
            {"at": entered_flight.isoformat(timespec="seconds"), "by": "the-doer",
             "from": "bet", "to": "in-flight"},
            {"at": verified.isoformat(timespec="seconds"), "by": "the-verifier",
             "from": "in-flight", "to": "verified"},
        ]
        host = self.installed()
        self.card(host, "verified-stops", "verified", created_at=began.isoformat(timespec="seconds"),
                  history=history, appetite={"amount": 1, "unit": unit})
        self.card(host, "landed-stops", "landed", created_at=began.isoformat(timespec="seconds"),
                  history=history + [{"at": landed.isoformat(timespec="seconds"), "by": "the-doer",
                                      "from": "verified", "to": "landed"}],
                  appetite={"amount": 1, "unit": unit})

        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        result = self.run_kit(KIT, host, "check")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertNotIn("'verified-stops'", result.stdout)
        self.assertNotIn("'landed-stops'", result.stdout)

    def test_63_a_limit_in_a_unit_nothing_here_reads_is_said_out_loud_not_passed_over(self):
        """The other half of the same honesty. A limit this host cannot measure reads exactly
        like a limit that is being kept -- the one failure invisible from where the reader stands
        -- so it is reported, and reported DIFFERENTLY from an overrun, because the cure is a
        reading or another unit rather than an owner's decision."""
        host = self.installed()
        self.card(host, "unmeasurable", state_ids()[0],
                  appetite={"amount": 3, "unit": "a-unit-no-module-answers"})
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)

        result = self.run_kit(KIT, host, "check")
        self.assertEqual(1, result.returncode)
        self.assertIn("FAIL  FF-DELIVERY-APPETITE", result.stdout)
        self.assertIn("'a-unit-no-module-answers'", result.stdout)
        self.assertIn("Nothing was observed", result.stdout)
        self.assertNotIn("decision by", result.stdout,
                         "a limit nobody could read was reported as one that had been spent")
        for unit in appetite_module.registry():
            self.assertIn(unit, result.stdout, "the report did not say what this host CAN read")

    def test_63_the_boards_counts_are_computed_from_the_cards_and_survive_no_hand_edit(self):
        """The board's N/M. Every number on the board is resolved at the moment the surface is
        written, from the cards and the tree they point at -- never read off a field, because
        there is no field to read it off. Changing what a card points at changes the count with
        no interpreter edit; changing the SURFACE is caught."""
        before = interpreter_digest()
        kind = next(k for k in criteria_module.registry() if k == "artifact-present")
        here, nowhere = POLICY, "a/place/that/is/not/here.json"

        host = self.installed()
        self.card(host, "two-stated", state_ids()[0], criteria=[
            {"id": "reachable", "statement": "given the host, when read, then it is there",
             "proof": {"kind": kind, "ref": here}},
            {"id": "not-yet", "statement": "given the host, when read, then it is there",
             "proof": {"kind": kind, "ref": nowhere}}])
        self.card(host, "none-stated", state_ids()[0])
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)

        board = self.board(host)
        self.assertIn("criteria 1/2 proved", board, "the count is not the one the tree supports")
        self.assertIn("criteria 0/0 proved", board,
                      "a card that stated nothing must count nothing of nothing, not vanish")
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode)

        # the host points the second criterion at something that IS there: the count follows the
        # records, not a number anybody typed, and no interpreter byte moves
        card = self.read_card(host, "two-stated")
        card["criteria"][1]["proof"]["ref"] = here
        (host / CARDS / "two-stated.json").write_text(
            json.dumps(card, indent=2) + "\n", encoding="utf-8")
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        self.assertIn("criteria 2/2 proved", self.board(host))
        self.assertEqual(before, interpreter_digest(),
                         "a change in what a card points at cost an interpreter edit")

        # and the surface may not be argued with by hand
        (host / BOARD).write_text(self.board(host).replace("2/2", "9/9"), encoding="utf-8")
        edited = self.run_kit(KIT, host, "check")
        self.assertEqual(1, edited.returncode)
        self.assertIn("FF-KIT-PROJECTION", edited.stdout)
        self.assertIn(BOARD, edited.stdout)
