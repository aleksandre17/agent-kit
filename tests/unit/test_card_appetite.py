"""Unit: an appetite is a DECLARED limit, its spend is READ, and an overrun stops at a door.

ADR-020 decision 9, first part. The breaker's transition and the expiry passage are not built
here and are not asserted here; what is proved is the declaration, the reading, and the shape of
what an overrun produces.

The walk:

  1. the grammar is closed -- a limit is an amount and a unit, and there is nowhere to type what
     has been spent, nowhere to record that a limit was raised, and nowhere to tick it off;
  2. the NUMBER is never the kit's: nothing this kit ships declares an appetite, at any amount,
     and the words a host may use are a vocabulary while the units this host can READ are the
     modules installed -- two truths, one home each, and every readable unit is a declared word;
  3. a limit not yet spent says nothing, and a record that declares NO limit is passed over
     entirely -- which is every record in existence on the day this ships;
  4. a limit measurably spent is REPORTED once, and the report names the door: the owner, on the
     record. Nothing is raised, nothing is ended, and the record is not touched;
  5. a limit nothing here can measure is reported DIFFERENTLY -- never as an overrun, never as a
     limit being kept -- because a limit nobody can measure reads exactly like one that is held;
  6. a world that cannot be read answers with no reading at all, and never with a zero;
  7. the registry of units is OPEN: every unit comes from a module in the directory, and the
     interpreter spells none of them.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
KIT = REPO / "kit"

for extra in [KIT / "interpreters", *sorted(p for p in (KIT / "interpreters").iterdir()
                                            if p.is_dir() and not p.name.startswith("_"))]:
    sys.path.insert(0, str(extra))

import appetite  # noqa: E402
import clock as clock_port  # noqa: E402
import collection  # noqa: E402
from manifest import Manifest  # noqa: E402

MANIFEST = Manifest(KIT)

#: The vocabulary this kit ships, found by what it DECLARES and never by its path.
VOCABULARY = next(c.documents[d["id"]] for c in MANIFEST.capabilities
                  for d in c.raw.get("documents", []) if d["validates"] == "record-keeping")
UNITS = [row[collection.IDENTITY] for row in VOCABULARY["appetite_units"]]

#: The capability that governs work and the schema its records are judged by -- read from the
#: declaration that owns them, so this file spells no path and no state.
GOVERNING = next(c for c in MANIFEST.capabilities if c.governs)
CARD_SCHEMA = next(i["validates"] for i in GOVERNING.installs
                   if collection.kind_of(i) == "collection" and i.get("validates"))

NOW = "2026-09-24T00:00:00+00:00"
BEGAN = "2026-09-01T00:00:00+00:00"          # 23 days before the reading below
GOOD_CARD = {"schema_version": 1, "id": "a-card", "title": "A card", "state": "-",
             "created_at": BEGAN}

#: A unit this host really reads, and one no module answers -- both taken from the registry
#: itself, so neither is a name this file invented.
READABLE = sorted(appetite.registry())[0]
UNREADABLE = "a-unit-no-module-answers"


class _Ctx:
    """As much of the world as this reading needs: a clock that states one moment."""

    def __init__(self, moment: str = NOW) -> None:
        self.clock = clock_port.FixedClock(moment)


@pytest.fixture()
def ctx() -> _Ctx:
    return _Ctx()


def _with(amount, unit, **fields) -> dict:
    return dict(GOOD_CARD, appetite={"amount": amount, "unit": unit}, **fields)


# == 1. the grammar is closed ==================================================================
def test_a_limit_is_an_amount_and_a_unit_and_there_is_nowhere_to_type_what_was_spent():
    assert not MANIFEST.validate(_with(30, READABLE), CARD_SCHEMA)
    assert not MANIFEST.validate(GOOD_CARD, CARD_SCHEMA), "a card with no appetite is legal"

    for typed in ("spent", "consumed", "remaining", "extended_to", "status"):
        card = _with(30, READABLE)
        card["appetite"][typed] = 1
        errors = MANIFEST.validate(card, CARD_SCHEMA)
        assert errors, f"a card typed {typed!r} beside its limit and the grammar admitted it"
        assert any(typed in error for error in errors)

    for missing in ("amount", "unit"):
        card = _with(30, READABLE)
        del card["appetite"][missing]
        assert MANIFEST.validate(card, CARD_SCHEMA), f"a limit with no {missing} was admitted"


# == 2. the number is never the kit's ==========================================================
def test_nothing_this_kit_ships_declares_an_appetite_at_any_amount():
    """The fitness function under decision 9. A default anywhere in the payload would be this kit
    answering, on a host's behalf, the one question only an owner can answer."""
    offenders = []
    for path in sorted(KIT.rglob("*.json")):
        if path.name == "card.schema.json":
            continue  # the GRAMMAR of a limit is not a limit
        text = path.read_text(encoding="utf-8")
        if f'"{appetite.APPETITE}"' not in text:
            continue
        declared = json.loads(text)
        offenders += [path.name] if _carries_a_limit(declared) else []
    assert [] == offenders, "the kit declared an appetite somewhere; the number is the host's"


def _carries_a_limit(node) -> bool:
    if isinstance(node, dict):
        if isinstance(node.get(appetite.APPETITE), dict) \
                and appetite.AMOUNT in node[appetite.APPETITE]:
            return True
        return any(_carries_a_limit(value) for value in node.values())
    return isinstance(node, list) and any(_carries_a_limit(item) for item in node)


def test_every_unit_this_host_can_read_is_a_word_the_vocabulary_declares():
    """The two sets are different truths and each has one home: which units may be DECLARED is a
    vocabulary, which units can be READ is what is installed. A reading may be missing for a
    declared word -- that gap is reported, not hidden -- but a reading for a word nobody declared
    would be a second home for the vocabulary, growing where nothing can see it."""
    assert set(appetite.registry()) <= set(UNITS), "a unit was answered that nobody declared"
    assert UNITS, "the vocabulary declares no unit at all"


# == 3. a limit not yet spent, and no limit at all =============================================
def test_a_limit_not_yet_spent_says_nothing(ctx):
    assert [] == appetite.unkept(ctx, [_with(1000, READABLE)])


def test_a_record_that_declares_no_limit_is_passed_over_untouched(ctx):
    before = json.dumps(GOOD_CARD, sort_keys=True)
    assert [] == appetite.unkept(ctx, [GOOD_CARD])
    assert before == json.dumps(GOOD_CARD, sort_keys=True), "the reading wrote on the record"


# == 4. a limit spent is reported, and the report names the door ===============================
def test_a_limit_measurably_spent_is_reported_once_and_names_who_may_answer(ctx):
    owner = "the-owner"
    card = _with(1, READABLE, owner=owner)
    before = json.dumps(card, sort_keys=True)

    said, = appetite.unkept(ctx, [card])
    assert card[collection.IDENTITY] in said
    assert READABLE in said and "1" in said, "a report that does not state the limit is testimony"
    assert owner in said, "the report did not name the door it stops at"
    assert "decision by" in said
    assert json.dumps(card, sort_keys=True) == before, "the reading changed the record"


def test_an_overrun_is_reported_and_never_resolved(ctx):
    """The rejected alternatives of decision 9, asserted as absences: no field was written, no
    limit was raised, and nothing was ended. The only thing produced is a sentence."""
    card = _with(1, READABLE)
    produced = appetite.unkept(ctx, [card])
    assert [str] == list({type(item) for item in produced})
    assert appetite.AMOUNT not in card or card[appetite.APPETITE][appetite.AMOUNT] == 1
    assert set(card[appetite.APPETITE]) == {appetite.AMOUNT, appetite.UNIT}


def test_a_record_with_no_limit_stays_silent_beside_one_that_overran(ctx):
    """The two together, because the interesting failure is a reading that judges the whole
    collection by the loudest record in it."""
    said = appetite.unkept(ctx, [GOOD_CARD, dict(_with(1, READABLE), id="spent-it")])
    assert 1 == len(said) and "spent-it" in said[0]


# == 5. a limit nothing can measure ============================================================
def test_a_unit_no_module_reads_is_reported_as_unmeasured_and_never_as_an_overrun(ctx):
    said, = appetite.unkept(ctx, [_with(1, UNREADABLE)])
    assert UNREADABLE in said
    assert "Nothing was observed" in said
    assert "decision by" not in said, "an unread limit was reported as though it had been spent"
    for unit in appetite.registry():
        assert unit in said, "the report did not say what this host CAN read"


def test_the_reading_of_an_unknown_unit_is_no_reading_and_never_a_zero(ctx):
    reading = appetite.spent(ctx, GOOD_CARD, UNREADABLE)
    assert reading.amount is None, "an unasked question was answered with a number"
    assert reading.reading


# == 6. a degraded world answers with no reading, never with a zero ============================
@pytest.mark.parametrize("began", [None, "not-a-moment"])
def test_a_record_whose_beginning_cannot_be_read_answers_with_no_reading(ctx, began):
    card = dict(GOOD_CARD)
    card.pop("created_at") if began is None else card.update(created_at=began)
    reading = appetite.spent(ctx, card, READABLE)
    assert reading.amount is None, "a world that could not be read reported a spend of zero"
    said, = appetite.unkept(ctx, [dict(card, appetite={"amount": 1, "unit": READABLE})])
    assert "decision by" not in said, "an unreadable record was reported as an overrun"


def test_the_reading_states_the_moment_it_was_taken(ctx):
    reading = appetite.spent(ctx, GOOD_CARD, READABLE)
    assert reading.amount is not None
    assert NOW in reading.reading and BEGAN in reading.reading, \
        "a reading that does not say when it was taken cannot be contradicted, only believed"


# == 7. the registry is open ===================================================================
def test_every_unit_comes_from_a_module_in_the_directory_and_the_interpreter_spells_none():
    published: dict = {}
    for path in sorted(appetite.SPEND.glob("*.py")):
        module = __import__(path.stem)
        published.update(getattr(module, appetite.ENTRY, {}))
    assert published, "no module publishes a unit of spend"
    assert set(appetite.registry()) == set(published)
    source = (KIT / "interpreters" / "appetite.py").read_text(encoding="utf-8")
    for unit in published:
        assert f"'{unit}'" not in source and f'"{unit}"' not in source, \
            "the interpreter spells a unit it is supposed to discover"


# == 8. the lifecycle says which stays spend (ADR-020 amendment 2) =============================
#: The states the shipped lifecycle marks as spending -- read from its declaration, so this file
#: spells none of them and a lifecycle that renamed them would still be the one tested.
SPENDING = sorted(s["id"] for s in GOVERNING.documents[GOVERNING.governs["lifecycle"]]["states"]
                  if s.get("spends"))
WAITING = next(s["id"] for s in GOVERNING.documents[GOVERNING.governs["lifecycle"]]["states"]
               if not s.get("spends") and not s.get("closed") and not s.get("defers"))
PARKED = next(s["id"] for s in GOVERNING.documents[GOVERNING.governs["lifecycle"]]["states"]
              if s.get("defers"))
CLOSED = next(s["id"] for s in GOVERNING.documents[GOVERNING.governs["lifecycle"]]["states"]
              if s.get("closed"))


class _Governed(_Ctx):
    """A world that can read the shipped lifecycle, as `check` and `move` can."""

    def enabled_capabilities(self):
        return [GOVERNING]


def _walked(*passages) -> dict:
    """A card captured at BEGAN that then moved through these (state, moment) pairs."""
    state, history = WAITING, []
    for to, at in passages:
        history.append({"at": at, "by": "test", "from": state, "to": to})
        state = to
    return dict(GOOD_CARD, state=state, history=history)


def test_the_shipped_lifecycle_marks_where_work_spends_and_closing_is_not_one_of_them():
    assert SPENDING, "a lifecycle that marks no spending state measures nothing it means"
    closed = [s["id"] for s in GOVERNING.documents[GOVERNING.governs["lifecycle"]]["states"] if s.get("closed")]
    assert not set(SPENDING) & set(closed), "finished work does not go on spending"
    assert PARKED not in SPENDING, "work deliberately not being done is not spending its appetite"


def test_the_shipped_delivery_lifecycle_spends_in_exactly_bet_in_flight_and_blocked():
    """Verification is evidence, not work: `verified` must not spend (ADR-020 amendment 3), and
    `blocked` must (a blocked cycle is still a cycle spent). The declaration itself is pinned here,
    so re-marking either way fails in the unit suite and not only in the slow acceptance run."""
    assert SPENDING == sorted(["bet", "in-flight", "blocked"])
    assert "verified" not in SPENDING


def test_a_card_that_goes_in_flight_then_blocked_and_stays_there_goes_red():
    card = _walked(("in-flight", "2026-09-10T00:00:00+00:00"), ("blocked", "2026-09-11T00:00:00+00:00"))
    reading = appetite.spent(_Governed(), card, READABLE)
    assert reading.amount == pytest.approx(14.0), "blocked time was not charged to the appetite"
    said, = appetite.unkept(_Governed(), [dict(card, appetite={"amount": 5, "unit": READABLE})])
    assert "decision by" in said


def test_a_card_that_waited_to_be_chosen_has_spent_nothing_until_it_was():
    card = _walked()  # captured 23 days ago and never moved past where cards wait
    reading = appetite.spent(_Governed(), card, READABLE)
    assert reading.amount == 0.0, "the time a card waited to be chosen was charged to its appetite"
    assert "has not entered" in reading.reading


def test_the_spend_starts_when_the_work_enters_a_state_that_spends():
    card = _walked((SPENDING[0], "2026-09-22T00:00:00+00:00"))  # two days before NOW
    reading = appetite.spent(_Governed(), card, READABLE)
    assert reading.amount == pytest.approx(2.0)
    said = appetite.unkept(_Governed(), [dict(card, appetite={"amount": 3, "unit": READABLE})])
    assert said == [], "a card two days into a three-day limit was reported spent"


def test_a_card_that_closed_stops_spending_the_moment_it_closed():
    card = _walked((SPENDING[0], "2026-09-02T00:00:00+00:00"), (CLOSED, "2026-09-02T00:05:13+00:00"))
    reading = appetite.spent(_Governed(), card, READABLE)
    assert reading.amount < 0.01, "a card kept spending after its work was finished"
    said = appetite.unkept(_Governed(), [dict(card, appetite={"amount": 1, "unit": READABLE})])
    assert said == [], "a card that landed five minutes in was reported past a one-day limit"


def test_a_card_parked_on_purpose_does_not_spend_while_it_waits():
    card = _walked((SPENDING[0], "2026-09-10T00:00:00+00:00"), (PARKED, "2026-09-11T00:00:00+00:00"))
    reading = appetite.spent(_Governed(), card, READABLE)
    assert reading.amount == pytest.approx(1.0), "the days a card stood parked were charged to it"


def test_without_a_lifecycle_to_read_the_older_reading_stands_and_says_so(ctx):
    reading = appetite.spent(ctx, _walked((SPENDING[0], "2026-09-22T00:00:00+00:00")), READABLE)
    assert reading.amount == pytest.approx(23.0)
    assert "the whole life of the record" in reading.reading
