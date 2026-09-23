"""Unit: a WORK section that is a PROJECTION, a hand-written restatement that is REPORTED, and two
passages a machine decides.

ADR-020 decisions 4, 8 and 9, S4. What is proved here is a FIRING in both directions, against the
declarations the kit actually ships: the provenance vocabulary is the one the kit publishes, the
machine fact is read off its row rather than off a word, the shape is the schema the manifest
registers, and the two computed passages are resolved through the one registry a criterion's proof
is resolved through -- never a second decider.

The walk:

  1. a section whose provenance says its content is computed is RENDERED from the records, and the
     line each record becomes is the declaration's, never this kit's;
  2. delete the rendered span and fill again -- it comes back character for character;
  3. a section a hand owns is untouched, and so is every line outside any computed span: not
     preserved by care, but unreachable;
  4. a computed section with no span, and one with two, are refused and nothing is written;
  5. a computed section naming rows this host does not compute is refused rather than rendered as
     an emptiness nobody declared;
  6. the fill goes through S1's one writer: the before-image is journalled before the artifact is
     replaced;
  7. a hand-written line that restates a record's field is REPORTED with its line number, and the
     same line inside a computed span is not -- what is computed is not a second home;
  8. an appetite found spent carries the record into the state the lifecycle declares, as a
     COMPUTED passage, and nothing is extended, cancelled or resumed;
  9. the same passage on a record still within its appetite is REFUSED, and so is one whose
     appetite nothing can read -- an unreadable limit never passes;
 10. a record that has waited past the number its reference names expires by a declared passage,
     and one that has not is refused.
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
import criteria  # noqa: E402
import derivation  # noqa: E402
import eviction  # noqa: E402
import lifecycle as lifecycle_module  # noqa: E402
import restatement  # noqa: E402
from manifest import Manifest  # noqa: E402

MANIFEST = Manifest(KIT)

#: The provenance vocabulary this kit ships, found by the contract it keeps and never by its path.
VOCABULARY = next(c.documents[d["id"]] for c in MANIFEST.capabilities
                  for d in c.raw.get("documents", []) if d["validates"] == "record-keeping")
SOURCES = VOCABULARY["section_sources"]

#: The two words, resolved from the vocabulary by the MACHINE FACT each row carries. Spelling
#: either of them into this file would be the defect the fact exists to prevent.
BY_HAND = next(r["id"] for r in SOURCES if r["derived"] is False)
COMPUTED = next(r["id"] for r in SOURCES if r["derived"] is True)

#: A host's shape declaration, as a host would author it: the kit ships no rows and no lines.
SHAPE = {
    "schema_version": 1,
    "id": "steering-surface",
    "artifact": "work/HERE.md",
    "sections": [
        {"id": "intent", "holds": "why this exists at all", "source": BY_HAND,
         "audience": "author"},
        {"id": "work", "holds": "what is open right now", "source": COMPUTED,
         "audience": "author",
         "projects": {"over": "columns",
                      "line": "{{#items}}- {{id}} -- {{title}}\n{{/items}}",
                      "empty": "Nothing is open. This is a declared nothing, not a blank."}},
    ],
}

CARDS = [
    {"id": "c-1", "title": "the spine is built", "state": "open"},
    {"id": "c-2", "title": "the surface stops lying", "state": "open"},
]

VIEW = {"columns": [{"id": "open", "items": CARDS}]}

ARTIFACT = (
    "# Here\n"
    "\n"
    "## Intent\n"
    "This paragraph is the one home of something no record owns.\n"
    "\n"
    "## Work\n"
    "<!-- kit:begin work -->\n"
    "whatever somebody typed here last\n"
    "<!-- kit:end work -->\n"
    "\n"
    "## After\n"
    "A closing line.\n"
)


class _Clock:
    def __init__(self, moment: str) -> None:
        self._moment = moment

    def now(self) -> str:
        return self._moment


class _Ctx:
    """Everything these passages are allowed to reach: a manifest and a clock, both handed in."""

    def __init__(self, moment="2026-09-24T12:00:00+00:00") -> None:
        self.manifest = MANIFEST
        self.clock = _Clock(moment)


# -- 1, 2, 3: the section is a projection, and what a hand owns is unreachable -----------------
def test_a_computed_section_is_rendered_from_the_records():
    filled = derivation.filled(ARTIFACT, shape=SHAPE, sources=SOURCES, section="work", view=VIEW)
    assert "- c-1 -- the spine is built" in filled
    assert "- c-2 -- the surface stops lying" in filled
    assert "whatever somebody typed here last" not in filled


def test_deleting_the_span_and_filling_again_returns_it_byte_for_byte():
    once = derivation.filled(ARTIFACT, shape=SHAPE, sources=SOURCES, section="work", view=VIEW)
    emptied = "\n".join(
        line for line in once.split("\n")
        if derivation.marker_on(line) is not None or not line.startswith("- c-")
    )
    assert derivation.filled(emptied, shape=SHAPE, sources=SOURCES,
                             section="work", view=VIEW) == once
    assert derivation.filled(once, shape=SHAPE, sources=SOURCES, section="work", view=VIEW) == once


def test_everything_outside_the_span_is_returned_unchanged():
    filled = derivation.filled(ARTIFACT, shape=SHAPE, sources=SOURCES, section="work", view=VIEW)
    assert _outside(filled) == _outside(ARTIFACT)
    assert "This paragraph is the one home of something no record owns." in filled
    # a marker written loosely by hand comes back in the one canonical form, so the tolerance at
    # the boundary never compounds into two spellings that each go on matching
    assert derivation.OPENS.format(id="work") in filled


def _outside(text: str) -> list:
    keep, inside = [], False
    for line in text.split("\n"):
        edge = derivation.marker_on(line)
        if edge is not None:
            inside = edge[0] == "begin"
            continue
        if not inside:
            keep.append(line)
    return keep


def test_a_section_a_hand_owns_is_not_something_this_passage_can_address():
    with pytest.raises(derivation.NoSpanToFill) as refusal:
        derivation.filled(ARTIFACT, shape=SHAPE, sources=SOURCES, section="intent", view=VIEW)
    assert "intent" in str(refusal.value)
    assert "['work']" in str(refusal.value)


def test_an_empty_set_is_a_declared_nothing_and_never_a_blank():
    filled = derivation.filled(ARTIFACT, shape=SHAPE, sources=SOURCES, section="work",
                               view={"columns": []})
    assert "This is a declared nothing, not a blank." in filled


# -- 4, 5: the refusals ------------------------------------------------------------------------
def test_a_computed_section_with_no_span_is_refused_and_prints_the_two_lines():
    with pytest.raises(derivation.NoSpanToFill) as refusal:
        derivation.filled("# Here\nnothing marked out at all\n",
                          shape=SHAPE, sources=SOURCES, section="work", view=VIEW)
    assert "kit:begin work" in str(refusal.value)
    assert "kit:end work" in str(refusal.value)


def test_a_section_marked_out_twice_is_refused_rather_than_ordered():
    with pytest.raises(derivation.SectionPlacedTwice):
        derivation.filled(ARTIFACT + ARTIFACT, shape=SHAPE, sources=SOURCES,
                          section="work", view=VIEW)


def test_rows_this_host_does_not_compute_are_refused_rather_than_rendered_empty():
    with pytest.raises(derivation.NothingToProjectFrom) as refusal:
        derivation.filled(ARTIFACT, shape=SHAPE, sources=SOURCES, section="work", view={})
    assert "columns" in str(refusal.value)


# -- 6: the one writer -------------------------------------------------------------------------
def test_the_fill_is_journalled_before_the_artifact_is_replaced(tmp_path):
    order, journal = [], tmp_path / "journal.jsonl"
    written = {}

    def append(value):
        order.append("journal")
        eviction.appender(journal)(value)

    def write(text):
        order.append("artifact")
        written["text"] = text

    event = derivation.refresh(
        _Ctx(), shape=SHAPE, sources=SOURCES, section="work", view=VIEW, prior=ARTIFACT,
        append=append, write=write, at="2026-09-24T12:00:00+00:00")
    assert order == ["journal", "artifact"]
    assert "whatever somebody typed here last" in "".join(event[eviction.REMOVED])
    line = json.loads(journal.read_text(encoding="utf-8").splitlines()[0])
    assert MANIFEST.validate(line, eviction.SCHEMA) == []
    assert line["artifact"] == SHAPE["artifact"] and line["section"] == "work"
    assert "- c-1 -- the spine is built" in written["text"]


# -- 7: the restatement is reported, never refused and never removed ---------------------------
def test_a_hand_written_line_restating_a_record_is_reported_with_its_line_number():
    held = ARTIFACT.replace(
        "This paragraph is the one home of something no record owns.",
        "Remember that the spine is built before touching anything else.")
    found = restatement.restatements(held, SHAPE, SOURCES, CARDS, ["id", "title"])
    assert found == [(4, "title", "c-1")]
    assert "the spine is built" in held  # nothing was removed and nothing was rewritten


def test_the_same_words_inside_a_computed_span_are_not_a_second_home():
    filled = derivation.filled(ARTIFACT, shape=SHAPE, sources=SOURCES, section="work", view=VIEW)
    assert restatement.restatements(filled, SHAPE, SOURCES, CARDS, ["id", "title"]) == []


# -- 8, 9, 10: two passages a machine decides --------------------------------------------------
STOPPED = {"from": "carrying", "to": "stopped", "owner": "-", "exit": "the limit was spent",
           "computed": {"proof": {"kind": "appetite-spent"}}}
EXPIRES = {"from": "waiting", "to": "set-down", "owner": "-", "exit": "it waited too long",
           "computed": {"proof": {"kind": "waited-longer-than", "params": {"days": 30}}}}


def _resolved(edge, card, moment="2026-09-24T12:00:00+00:00"):
    return criteria.resolve(_Ctx(moment), lifecycle_module.decided_by(edge), card)


def test_an_appetite_found_spent_carries_the_record_into_the_stopped_state():
    card = {"id": "c-9", "state": "carrying", "owner": "the owner",
            "created_at": "2026-01-01T00:00:00+00:00",
            "appetite": {"amount": 5, "unit": "day"}}
    verdict = _resolved(STOPPED, card)
    assert verdict.holds is True
    lifecycle_module.refuse_uncomputed(card, STOPPED, verdict)  # nothing is raised
    moved = lifecycle_module.moved(
        _Governed(), card, STOPPED, "2026-09-24T12:00:00+00:00", "the machine")
    assert moved["state"] == "stopped"
    assert moved["appetite"] == card["appetite"]          # nothing was extended
    assert moved[lifecycle_module.HISTORY][-1]["from"] == "carrying"
    assert "5 'day' was undertaken" in verdict.reading


def test_a_record_within_its_appetite_may_not_take_that_passage():
    card = {"id": "c-10", "state": "carrying", "created_at": "2026-09-24T00:00:00+00:00",
            "appetite": {"amount": 5, "unit": "day"}}
    verdict = _resolved(STOPPED, card)
    assert verdict.holds is False
    with pytest.raises(lifecycle_module.UncomputedPassage) as refusal:
        lifecycle_module.refuse_uncomputed(card, STOPPED, verdict)
    assert "did not hold" in str(refusal.value)


def test_a_limit_nothing_can_read_never_passes_and_is_named_as_unread():
    card = {"id": "c-11", "state": "carrying", "created_at": "2026-01-01T00:00:00+00:00",
            "appetite": {"amount": 5, "unit": "a-unit-nothing-reads"}}
    verdict = _resolved(STOPPED, card)
    assert verdict.holds is None
    with pytest.raises(lifecycle_module.UncomputedPassage) as refusal:
        lifecycle_module.refuse_uncomputed(card, STOPPED, verdict)
    assert "could not be read" in str(refusal.value)


def test_a_record_that_declares_no_limit_is_not_reported_as_within_one():
    assert _resolved(STOPPED, {"id": "c-12", "state": "carrying",
                               "created_at": "2026-01-01T00:00:00+00:00"}).holds is None


def test_a_record_that_waited_past_the_declared_number_expires_by_the_passage():
    card = {"id": "c-13", "state": "waiting", "created_at": "2026-01-01T00:00:00+00:00"}
    verdict = _resolved(EXPIRES, card)
    assert verdict.holds is True
    moved = lifecycle_module.moved(
        _Governed(), card, EXPIRES, "2026-09-24T12:00:00+00:00", "the machine")
    assert moved["state"] == "set-down"
    assert "30" in verdict.reading and "reading taken at" in verdict.reading


def test_a_record_that_has_not_waited_long_enough_may_not_take_it():
    card = {"id": "c-14", "state": "waiting", "created_at": "2026-09-20T12:00:00+00:00"}
    assert _resolved(EXPIRES, card).holds is False


def test_a_reference_that_names_no_number_takes_no_reading_at_all():
    edge = {"from": "waiting", "to": "set-down", "owner": "-", "exit": "-",
            "computed": {"proof": {"kind": "waited-longer-than"}}}
    assert _resolved(edge, {"id": "c-15", "state": "waiting",
                            "created_at": "2020-01-01T00:00:00+00:00"}).holds is None


class _Governed:
    """Only what `moved` reads: the field a record's state lives in."""

    state_field = "state"


# -- the words: nothing an interpreter may not know -------------------------------------------
def test_no_interpreter_of_this_slice_spells_a_word_a_declaration_invented():
    words = [row["id"] for row in SOURCES]
    for module in (KIT / "interpreters" / "derivation.py",
                   KIT / "interpreters" / "gates" / "restatement.py",
                   KIT / "interpreters" / "proofs" / "appetite_spent.py",
                   KIT / "interpreters" / "proofs" / "waited.py"):
        text = module.read_text(encoding="utf-8")
        for word in words:
            assert word not in text, f"{module.name} spells {word!r}, which a declaration owns"
