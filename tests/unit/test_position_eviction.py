"""Unit: WRITE-AHEAD EVICTION -- nothing leaves a bounded artifact without being written down first.

ADR-020 decision 2, S1. What is proved here is a FIRING in both directions, against the
declarations the kit actually ships: the event is validated by the kit's own manifest against the
schema it registers, the measure is found through the discovery the budget ratchet already uses,
and the front-matter field is held to the contract the kit publishes -- never to a constant spelled
in this file.

The walk, in the order the decision decides it:

  1. a write that removes text JOURNALS the text before the artifact is replaced, and the line on
     disk carries `removed_chars`, the prose itself, and a landing or `null`;
  2. a write whose journal append FAILS is refused, and the artifact is untouched -- the one
     firing that makes the ordering a mechanism instead of a convention;
  3. a write that removes nothing journals nothing and still happens;
  4. a removal that landed nowhere increments the artifact's unlanded counter; one that landed
     increments nothing, because it was a MOVE;
  5. an unreadable counter is refused, never read as zero;
  6. the counter is legal front matter as digits and refused as anything else;
  7. the count is published as a measure the budget ratchet can discover -- and no second ratchet
     is shipped beside it;
  8. the S0 vocabulary rows are in the document the kit ships, and it honours its schema.
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

import eviction  # noqa: E402
import gatekinds  # noqa: E402
import ratchet  # noqa: E402
from manifest import Manifest  # noqa: E402

MANIFEST = Manifest(KIT)

#: The vocabulary document this kit ships, found by what it DECLARES and never by its path.
VOCABULARY = next(c.documents[d["id"]] for c in MANIFEST.capabilities
                  for d in c.raw.get("documents", []) if d["validates"] == "record-keeping")

PRIOR = (
    "# position\n"
    "\n"
    "2026-09-23: the capsule refused five writes over the hot ceiling, and the cure each time\n"
    "was the deletion of true, dated history.\n"
    "\n"
    "next: the bleeding stops.\n"
)


class Ctx:
    """Everything the passage asks of a context, and nothing more: it reads the schema's version
    and validates against it, and it never touches a workspace -- the artifact and the journal
    both arrive as ports from the caller."""

    manifest = MANIFEST


def _artifact(tmp_path: Path) -> Path:
    path = tmp_path / "CONTINUE-HERE.md"
    path.write_text(PRIOR, encoding="utf-8", newline="")
    return path


def _writer(path: Path):
    def write(candidate: str) -> None:
        path.write_text(candidate, encoding="utf-8", newline="")
    return write


# -- 1. the firing: the text is written down, and only then does it leave ------------------------
def test_an_accepted_write_journals_the_text_it_removed_before_the_artifact_is_replaced(tmp_path):
    artifact, journal = _artifact(tmp_path), tmp_path / "journal" / "2026-09-23.claude-code.jsonl"
    candidate = PRIOR.replace(
        "2026-09-23: the capsule refused five writes over the hot ceiling, and the cure each time\n"
        "was the deletion of true, dated history.\n", "")

    event = eviction.accept(
        Ctx(), prior=artifact.read_text(encoding="utf-8"), candidate=candidate,
        append=eviction.appender(journal), write=_writer(artifact),
        at="2026-09-23T23:11:07Z", artifact="work/CONTINUE-HERE.md", section="position",
        rev=4911, runtime="claude-code")

    line = json.loads(journal.read_text(encoding="utf-8").splitlines()[0])
    assert line == event
    assert MANIFEST.validate(line, eviction.SCHEMA) == []
    assert line["removed_chars"] == sum(len(span) for span in line["removed"])
    assert "the deletion of true, dated history" in "".join(line["removed"])
    assert line["landing"] is None
    assert artifact.read_text(encoding="utf-8") == candidate
    assert "\r" not in journal.read_bytes().decode("utf-8")
    print("\nJOURNAL EVENT:\n" + json.dumps(line, indent=2, ensure_ascii=False))


# -- 2. the firing that makes it a mechanism -----------------------------------------------------
def test_a_write_whose_journal_append_fails_is_refused_and_the_artifact_is_untouched(tmp_path):
    artifact = _artifact(tmp_path)
    (tmp_path / "journal").write_text("this is a file, not a directory\n", encoding="utf-8")
    journal = tmp_path / "journal" / "2026-09-23.claude-code.jsonl"

    with pytest.raises(eviction.EvictionRefused) as refusal:
        eviction.accept(
            Ctx(), prior=artifact.read_text(encoding="utf-8"), candidate="# position\n",
            append=eviction.appender(journal), write=_writer(artifact),
            at="2026-09-23T23:12:41Z", artifact="work/CONTINUE-HERE.md")

    assert refusal.value.code == "KIT0056"
    assert artifact.read_text(encoding="utf-8") == PRIOR
    assert not journal.exists()
    print("\nREFUSAL " + refusal.value.code + ":\n" + str(refusal.value))


# -- 3. a write that removes nothing --------------------------------------------------------------
def test_a_write_that_only_adds_journals_nothing_and_still_happens(tmp_path):
    artifact, journal = _artifact(tmp_path), tmp_path / "journal" / "day.jsonl"
    candidate = PRIOR + "\nand one more line.\n"

    event = eviction.accept(
        Ctx(), prior=PRIOR, candidate=candidate, append=eviction.appender(journal),
        write=_writer(artifact), at="2026-09-23T23:13:00Z", artifact="work/CONTINUE-HERE.md")

    assert event is None
    assert not journal.exists()
    assert artifact.read_text(encoding="utf-8") == candidate


# -- 4. what the counter counts ---------------------------------------------------------------
def test_a_removal_that_landed_nowhere_is_counted_and_one_that_landed_is_a_move():
    nowhere = eviction.event(Ctx(), prior=PRIOR, candidate="# position\n",
                             at="2026-09-23T23:14:00Z", artifact="work/CONTINUE-HERE.md")
    landed = eviction.event(Ctx(), prior=PRIOR, candidate="# position\n",
                            at="2026-09-23T23:14:00Z", artifact="work/CONTINUE-HERE.md",
                            landing={"kind": "work-card", "at": "work/cards/C-0001.md"})

    assert nowhere["landing"] is None and landed["landing"]["kind"] == "work-card"
    assert eviction.restated("2", nowhere) == "3"
    assert eviction.restated("2", landed) == "2"
    assert eviction.restated(None, nowhere) == "1"
    assert eviction.restated("7", None) == "7"


# -- 5. a count that is not a count ---------------------------------------------------------------
def test_an_unreadable_counter_is_refused_and_never_read_as_zero():
    with pytest.raises(eviction.CounterUnreadable) as refusal:
        eviction.count("several", "work/CONTINUE-HERE.md")
    assert refusal.value.code == "KIT0057"
    assert eviction.count(None) == 0


# -- 6. the counter is legal front matter, as the grammar can carry it ---------------------------
def test_the_counter_is_declared_in_the_front_matter_contract_as_digits():
    assert MANIFEST.validate({eviction.UNLANDED: "12"}, "front-matter") == []
    assert MANIFEST.validate({eviction.UNLANDED: "twelve"}, "front-matter") != []
    assert MANIFEST.validate({eviction.UNLANDED: 12}, "front-matter") != []


# -- 7. the count is a measure, and there is no second ratchet -----------------------------------
def test_the_unlanded_count_is_published_as_a_measure_the_ratchet_discovers():
    measures = gatekinds.registry(ratchet.REGISTRY)
    assert eviction.UNLANDED in measures
    assert ratchet.KIND in gatekinds.registry()
    assert [k for k in gatekinds.registry() if k == ratchet.KIND] == [ratchet.KIND]


# -- 8. the S0 words -------------------------------------------------------------------------------
def test_the_vocabulary_ships_the_words_this_slice_needs():
    assert MANIFEST.validate(VOCABULARY, "record-keeping") == []
    assert "eviction-record" in {row["id"] for row in VOCABULARY["kinds"]}
    assert "append-only" in {row["id"] for row in VOCABULARY["lifecycles"]}
    assert {row["id"] for row in VOCABULARY["criterion_statuses"]} == {"proved", "failed",
                                                                      "unproven"}
    assert {row["id"] for row in VOCABULARY["transition_modes"]} == {"computed", "door"}
    assert VOCABULARY["appetite_units"]
