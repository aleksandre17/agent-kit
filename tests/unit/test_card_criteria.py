"""Unit: a criterion's status is COMPUTED by resolving the proof it names, and nothing types it.

ADR-020 decisions 7 and 8, first half of S3. What is proved here is a FIRING in all three
directions plus the refusal, against the declarations the kit actually ships -- the card grammar
is judged by the schema the manifest registers, the status WORDS come from the vocabulary the kit
publishes, and the resolvers are found by the registry rather than named by this file.

The walk, in the order the decision decides it:

  1. a criterion whose reference resolves and holds is computed to the word whose machine fact
     says it held -- and no field anywhere was written to say so;
  2. a criterion whose reference resolves and does NOT hold is computed to the word for a
     refutation, and carries the findings that refuted it;
  3. a criterion whose referent is ABSENT, and a criterion whose kind no resolver answers, are
     both computed to the word for no reading at all -- never the first, never the second;
  4. a hand-written status is REFUSED by the grammar: there is no place to put one;
  5. the registry is OPEN -- every kind comes from a module in the directory, nothing enumerates
     them, and the interpreter holds no kind of its own;
  6. a passage a machine decides is refused while the reference that decides it does not hold,
     is refused DIFFERENTLY when the reference cannot be read, and is open when a card declares
     no criterion at all -- which is a legal state on the day this ships;
  7. a passage may not declare both a principal and a computation, and a reference that stands on
     its own reading is not followed.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
KIT = REPO / "kit"

for extra in [KIT / "interpreters", *sorted(p for p in (KIT / "interpreters").iterdir()
                                            if p.is_dir() and not p.name.startswith("_"))]:
    sys.path.insert(0, str(extra))

import collection  # noqa: E402
import criteria  # noqa: E402
import lifecycle as lifecycle_module  # noqa: E402
from manifest import Manifest  # noqa: E402

MANIFEST = Manifest(KIT)

#: The vocabulary this kit ships, found by what it DECLARES and never by its path.
VOCABULARY = next(c.documents[d["id"]] for c in MANIFEST.capabilities
                  for d in c.raw.get("documents", []) if d["validates"] == "record-keeping")
STATUSES = VOCABULARY["criterion_statuses"]

#: The capability that governs work, its lifecycle, and the schema its cards are judged by -- all
#: read from the declaration that owns them, so this file spells no path and no state.
GOVERNING = next(c for c in MANIFEST.capabilities if c.governs)
LIFECYCLE = GOVERNING.documents[GOVERNING.governs["lifecycle"]]
CARD_SCHEMA = next(i["validates"] for i in GOVERNING.installs
                   if collection.kind_of(i) == "collection" and i.get("validates"))

#: The passage decided by the card's own criteria -- found by what decides it, never by its position in
#: the lifecycle: a declaration that gains a computed passage earlier in its list is not a different test.
#: Naming the states it runs between is exactly what this suite may not do.
COMPUTED_EDGE = next(e for e in LIFECYCLE["transitions"]
                     if e.get(lifecycle_module.COMPUTED, {}).get("proof", {}).get("kind") == "criteria-all-hold")

#: A rule of a kind this kit really answers, borrowed from a real declaration: it reads one file
#: through one schema, which makes it a rule that can be made to hold or not to hold by what is
#: on the disk in front of it.
FILE_RULE = next(g for c in MANIFEST.capabilities for g in c.gates
                 if {"file", "schema"} <= set(g.get("params") or {}))

HERE = "a/place/that/is/here.json"
NOWHERE = "a/place/that/is/not/here.json"
GOOD_CARD = {"schema_version": 1, "id": "a-card", "title": "A card", "state": "-",
             "created_at": "2026-09-24T00:00:00"}


class _Workspace:
    """As much of the port as a reading needs: what is on the disk, and what it says."""

    def __init__(self, disk: dict) -> None:
        self.disk = disk

    def exists(self, rel: str) -> bool:
        return rel in self.disk

    def read_json(self, rel: str):
        return self.disk[rel]


class _Capability:
    def __init__(self, identity: str, gates: list) -> None:
        self.id = identity
        self.gates = gates


class _Ctx:
    def __init__(self, disk: dict, capabilities: list) -> None:
        self.workspace = _Workspace(disk)
        self.manifest = MANIFEST
        self._capabilities = capabilities

    def enabled_capabilities(self) -> list:
        return self._capabilities


def _rule(identity: str, target: str) -> dict:
    return {"id": identity, "kind": FILE_RULE["kind"],
            "params": {"file": target, "schema": CARD_SCHEMA}}


@pytest.fixture()
def ctx() -> _Ctx:
    """A host with one file on it, and two rules: one that holds over it, one that cannot."""
    return _Ctx({HERE: GOOD_CARD},
                [_Capability("a-capability", [_rule("a-rule-that-holds", HERE),
                                              _rule("a-rule-that-does-not", NOWHERE)])])


def _word(verdict) -> str:
    return criteria.status_of(verdict, STATUSES)


def _criterion(identity: str, kind: str, ref: str) -> dict:
    return {"id": identity, "statement": f"given the host, when read, then {identity}",
            "proof": {"kind": kind, "ref": ref}}


def _with(*items) -> dict:
    return dict(GOOD_CARD, criteria=list(items))


# == 1-3. the three readings, each computed from a real resolution ==============================
def test_a_reference_that_resolves_and_holds_is_computed_to_the_word_for_a_proof(ctx):
    card = _with(_criterion("the-rule-holds", "declared-rule-holds", "a-rule-that-holds"))
    (item, verdict), = criteria.read(ctx, card, "criteria")
    assert verdict.holds is True
    assert _word(verdict) == next(r["id"] for r in STATUSES if r["holds"] is True)
    assert "a-rule-that-holds" in verdict.reading
    assert "status" not in item, "a criterion carried a status; nothing may write one"


def test_a_reference_that_resolves_and_does_not_hold_is_computed_to_the_word_for_a_refutation(ctx):
    card = _with(_criterion("the-rule-fails", "declared-rule-holds", "a-rule-that-does-not"))
    (_item, verdict), = criteria.read(ctx, card, "criteria")
    assert verdict.holds is False
    assert _word(verdict) == next(r["id"] for r in STATUSES if r["holds"] is False)
    assert NOWHERE in verdict.reading, "a refutation that does not say what was read is testimony"


def test_an_absent_referent_and_an_unanswered_kind_are_both_the_word_for_no_reading(ctx):
    card = _with(_criterion("points-at-nothing", "artifact-present", NOWHERE),
                 _criterion("nobody-reads-this", "a-kind-no-module-answers", "anything"))
    unnamed = next(r["id"] for r in STATUSES if r["holds"] is None)
    for _item, verdict in criteria.read(ctx, card, "criteria"):
        assert verdict.holds is None
        assert _word(verdict) == unnamed
    assert unnamed != next(r["id"] for r in STATUSES if r["holds"] is False)


def test_a_present_referent_holds_and_the_two_absences_never_collapse_into_one(ctx):
    card = _with(_criterion("points-at-something", "artifact-present", HERE))
    (_item, verdict), = criteria.read(ctx, card, "criteria")
    assert verdict.holds is True
    assert len({r["holds"] is None for r in STATUSES}) == 2, "the vocabulary lost a reading"


# == 4. there is nowhere to type a status =======================================================
def test_a_hand_written_status_is_refused_by_the_grammar_itself():
    typed = _with(dict(_criterion("typed", "artifact-present", HERE),
                       status=next(r["id"] for r in STATUSES if r["holds"] is True)))
    errors = MANIFEST.validate(typed, CARD_SCHEMA)
    assert errors, "a card typed its own status and the grammar admitted it"
    assert any("status" in e for e in errors)
    assert not MANIFEST.validate(_with(_criterion("typed", "artifact-present", HERE)), CARD_SCHEMA)
    assert not MANIFEST.validate(GOOD_CARD, CARD_SCHEMA), "a card with no criteria is legal"


# == 5. the registry is open ====================================================================
def test_every_kind_comes_from_a_module_in_the_directory_and_nothing_enumerates_them():
    published: dict = {}
    for path in sorted(criteria.PROOFS.glob("*.py")):
        module = __import__(path.stem)
        published.update(getattr(module, criteria.ENTRY, {}))
    assert published, "no module publishes a kind of proof"
    assert set(criteria.registry()) == set(published)
    source = (KIT / "interpreters" / "criteria.py").read_text(encoding="utf-8")
    for kind in published:
        assert f"'{kind}'" not in source and f'"{kind}"' not in source, \
            "the interpreter spells a kind it is supposed to discover"


# == 6-7. the passage a machine decides =========================================================
def _decide(ctx, card):
    deciding = lifecycle_module.decided_by(COMPUTED_EDGE)
    lifecycle_module.refuse_uncomputed(card, COMPUTED_EDGE, criteria.resolve(ctx, deciding, card))


def test_a_computed_passage_is_open_when_every_criterion_holds_and_when_none_is_declared(ctx):
    _decide(ctx, _with(_criterion("the-rule-holds", "declared-rule-holds", "a-rule-that-holds")))
    _decide(ctx, GOOD_CARD)


def test_a_computed_passage_is_refused_while_a_criterion_does_not_hold(ctx):
    with pytest.raises(lifecycle_module.UncomputedPassage) as refusal:
        _decide(ctx, _with(_criterion("fails", "declared-rule-holds", "a-rule-that-does-not")))
    assert "was read and did not hold" in str(refusal.value)
    assert "a fact about the work" in str(refusal.value)
    assert "Nothing was observed" not in str(refusal.value)
    assert refusal.value.code == "KIT0061"


def test_a_computed_passage_refused_for_an_unreadable_reference_says_so_differently(ctx):
    with pytest.raises(lifecycle_module.UncomputedPassage) as refusal:
        _decide(ctx, _with(_criterion("absent", "artifact-present", NOWHERE)))
    assert "the reference that decides it could not be read" in str(refusal.value)
    assert "Nothing was observed" in str(refusal.value)
    assert "a fact about the work" not in str(refusal.value)


def test_a_passage_may_not_be_both_a_judgement_and_a_computation():
    both = dict(COMPUTED_EDGE, **{lifecycle_module.DOOR: "somebody"})
    with pytest.raises(lifecycle_module.LifecycleError):
        lifecycle_module.decided_by(both)
    assert lifecycle_module.decided_by({"from": "-", "to": "-"}) is None


def test_a_reference_that_stands_on_its_own_reading_is_not_followed(ctx):
    circular = _with({"id": "itself", "statement": "given itself, when read, then itself",
                      "proof": dict(COMPUTED_EDGE[lifecycle_module.COMPUTED]["proof"])})
    (_item, verdict), = criteria.read(ctx, circular, "criteria")
    assert verdict.holds is None
    assert "itself" in verdict.reading


# == 8. what a surface may COUNT about a record, computed and never typed =======================
def test_the_tally_counts_what_was_proved_out_of_what_was_declared(ctx):
    """ADR-020 decision 11, the S3 row: N of M, computed from the records at the moment the
    surface is. One of these three is proved, one is refuted and one cannot be read -- so the
    count is one of three, and the two that are not proved are not claimed in either direction."""
    card = _with(_criterion("holds", "declared-rule-holds", "a-rule-that-holds"),
                 _criterion("does-not", "declared-rule-holds", "a-rule-that-does-not"),
                 _criterion("unreadable", "artifact-present", NOWHERE))
    assert {criteria.HELD: 1, criteria.DECLARED: 3} == criteria.tally(ctx, card, "criteria")


def test_a_record_that_declares_no_criterion_counts_nothing_of_nothing(ctx):
    assert {criteria.HELD: 0, criteria.DECLARED: 0} == criteria.tally(ctx, GOOD_CARD, "criteria")


def test_an_unreadable_criterion_is_never_counted_as_proved(ctx):
    for kind, ref in (("artifact-present", NOWHERE), ("a-kind-no-module-answers", "anything")):
        card = _with(_criterion("unreadable", kind, ref))
        assert 0 == criteria.tally(ctx, card, "criteria")[criteria.HELD], \
            "an absence was promoted to a proof by the count"


def test_the_board_carries_the_count_only_where_something_counts(ctx):
    """The counter is HANDED to the lifecycle, and a collection whose declaration names no field
    to count over is counted about by nothing -- a complete state, and not a missing column."""
    plain = lifecycle_module.columns(_governed_over([GOOD_CARD]))
    assert criteria.HELD not in _only_item(plain)
    counted = lifecycle_module.columns(_governed_over([GOOD_CARD]),
                                       lambda record: criteria.tally(ctx, record, "criteria"))
    assert 0 == _only_item(counted)[criteria.DECLARED]


def _governed_over(cards: list):
    """A governed collection assembled from the shipped declaration, so this file states no
    state, no title and no policy of its own."""
    state = LIFECYCLE["states"][0]["id"]
    members = type("R", (), {"value": [dict(card, state=state) for card in cards]})()
    return lifecycle_module.Governed(
        None, dict(GOVERNING.governs), LIFECYCLE, members, {})


def _only_item(built: list) -> dict:
    return next(item for column in built for item in column["items"])
