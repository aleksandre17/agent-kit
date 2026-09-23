"""Unit: COOLING -- a span leaves the position and lands in the record its own section declares.

ADR-020 decision 3, S2. S1 made a silent deletion impossible to perform; this is what gives the
removed span somewhere to GO. What is proved here is a FIRING in both directions, against the
declarations the kit actually ships -- the shape is judged by the schema the manifest registers,
the destination is a WORD from the vocabulary the kit publishes, and the event is the same
`eviction` line S1 writes, never a second shape.

The walk, in the order the decision decides it:

  1. a span cools to the destination ITS SECTION declares, lands there, and the journalled event
     carries the landing -- `landed` is no longer `null`;
  2. a span whose section declares no destination is REFUSED, and nothing moves: not the artifact,
     not the journal, not the destination. A guess is the one thing the passage will not make;
  3. a section the shape does not declare at all is refused too, and says which sections do;
  4. a write that removes nothing cools nothing and is not refused for it;
  5. a landing that comes back with no address is refused, and nothing is journalled;
  6. a cooled removal is a MOVE: it leaves S1's unlanded counter where it was, while the same
     removal with no landing increments it;
  7. the passage holds no section name, no path and no privileged case -- the same shape with the
     rows renamed cools exactly as well;
  8. the shape declaration is governed by a schema this kit registers, and the gate that judges it
     points at lists the shipped vocabulary actually carries.
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

import cooling  # noqa: E402
import eviction  # noqa: E402
from manifest import Manifest  # noqa: E402

MANIFEST = Manifest(KIT)

#: The vocabulary document this kit ships, found by what it DECLARES and never by its path.
VOCABULARY = next(c.documents[d["id"]] for c in MANIFEST.capabilities
                  for d in c.raw.get("documents", []) if d["validates"] == "record-keeping")

#: A host's shape declaration, as a host would author it: the kit ships no rows of its own.
SHAPE = {
    "schema_version": 1,
    "id": "continuity-capsule",
    "artifact": "work/CONTINUE-HERE.md",
    "sections": [
        {"id": "position", "holds": "where the work stands right now and the next move",
         "source": "authored", "audience": "author"},
        {"id": "ledger", "holds": "what was done tonight, dated",
         "source": "authored", "cools_to": "run-evidence", "audience": "steward"},
    ],
}

PRIOR = (
    "# position\n"
    "\n"
    "next: S2 gives the removed span somewhere to go.\n"
    "\n"
    "## ledger\n"
    "\n"
    "2026-09-23: the capsule refused five writes over the hot ceiling -- 403, 129, 9 and 191\n"
    "characters over -- and the cure each time was the deletion of true, dated history.\n"
)

COLD = (
    "2026-09-23: the capsule refused five writes over the hot ceiling -- 403, 129, 9 and 191\n"
    "characters over -- and the cure each time was the deletion of true, dated history.\n"
)


class Ctx:
    """Everything the passage asks of a context, and nothing more: it reads the schema's version
    and validates against it. The artifact, the journal and the destination all arrive as ports."""

    manifest = MANIFEST


def _artifact(tmp_path: Path) -> Path:
    path = tmp_path / "CONTINUE-HERE.md"
    path.write_text(PRIOR, encoding="utf-8", newline="")
    return path


def _writer(path: Path):
    def write(candidate: str) -> None:
        path.write_text(candidate, encoding="utf-8", newline="")
    return write


def _lander(root: Path, address: str = "work/evidence/2026-09-23.md"):
    """A `land` port, as a host would hand one in: it carries the prose to a record of the KIND it
    is given and returns the address a reader follows. Which path a kind lives at is the host's
    answer -- the passage is handed this closure and never computes one."""
    carried = {}

    def land(destination: str, spans: list) -> str:
        target = root / address
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "a", encoding="utf-8", newline="\n") as handle:
            handle.write("".join(spans))
        carried["destination"] = destination
        return address

    land.carried = carried
    return land


# -- 1. the firing: the span lands where its section says it belongs -----------------------------
def test_a_span_cools_to_the_destination_its_section_declares_and_the_event_carries_the_landing(
        tmp_path):
    artifact, journal = _artifact(tmp_path), tmp_path / "journal" / "2026-09-23.jsonl"
    land = _lander(tmp_path)
    candidate = PRIOR.replace(COLD, "")

    event = cooling.cool(
        Ctx(), shape=SHAPE, section="ledger",
        prior=artifact.read_text(encoding="utf-8"), candidate=candidate,
        land=land, append=eviction.appender(journal), write=_writer(artifact),
        at="2026-09-23T23:41:02Z", rev=4912, runtime="claude-code")

    line = json.loads(journal.read_text(encoding="utf-8").splitlines()[0])
    assert line == event
    assert MANIFEST.validate(line, eviction.SCHEMA) == []
    assert line["landing"] is not None
    assert line["landing"] == {"kind": "run-evidence", "at": "work/evidence/2026-09-23.md"}
    assert land.carried["destination"] == "run-evidence"
    assert "the deletion of true, dated history" in (
        tmp_path / "work/evidence/2026-09-23.md").read_text(encoding="utf-8")
    assert COLD not in artifact.read_text(encoding="utf-8")
    assert "\r" not in journal.read_bytes().decode("utf-8")
    print("\nCOOLED -- the span landed where its section declares:\n"
          + json.dumps(line, indent=2, ensure_ascii=False))


# -- 2. the refusal: a section that declares no destination ---------------------------------------
def test_a_span_whose_section_declares_no_destination_is_refused_and_nothing_moves(tmp_path):
    artifact, journal = _artifact(tmp_path), tmp_path / "journal" / "2026-09-23.jsonl"
    land = _lander(tmp_path)

    with pytest.raises(cooling.NowhereToCool) as refusal:
        cooling.cool(
            Ctx(), shape=SHAPE, section="position",
            prior=artifact.read_text(encoding="utf-8"),
            candidate=PRIOR.replace("next: S2 gives the removed span somewhere to go.\n", ""),
            land=land, append=eviction.appender(journal), write=_writer(artifact),
            at="2026-09-23T23:42:18Z")

    assert refusal.value.code == "KIT0058"
    assert artifact.read_text(encoding="utf-8") == PRIOR
    assert not journal.exists()
    assert not (tmp_path / "work").exists()
    assert land.carried == {}
    print("\nREFUSED " + refusal.value.code + ":\n" + str(refusal.value))


# -- 3. the same refusal, for a section the shape does not declare at all -------------------------
def test_a_section_the_shape_does_not_declare_is_refused_and_says_which_ones_do(tmp_path):
    artifact = _artifact(tmp_path)

    with pytest.raises(cooling.NowhereToCool) as refusal:
        cooling.cool(
            Ctx(), shape=SHAPE, section="decisions", prior=PRIOR, candidate="# position\n",
            land=_lander(tmp_path), append=eviction.appender(tmp_path / "j.jsonl"),
            write=_writer(artifact), at="2026-09-23T23:43:00Z")

    assert refusal.value.code == "KIT0058"
    assert "declares no section named 'decisions'" in str(refusal.value)
    assert "['ledger']" in str(refusal.value)
    assert artifact.read_text(encoding="utf-8") == PRIOR


# -- 4. a write that removes nothing --------------------------------------------------------------
def test_a_candidate_that_only_adds_cools_nothing_and_is_not_refused_for_naming_no_destination(
        tmp_path):
    artifact = _artifact(tmp_path)
    candidate = PRIOR + "\nand one more line.\n"

    event = cooling.cool(
        Ctx(), shape=SHAPE, section="position", prior=PRIOR, candidate=candidate,
        land=_lander(tmp_path), append=eviction.appender(tmp_path / "j.jsonl"),
        write=_writer(artifact), at="2026-09-23T23:44:00Z")

    assert event is None
    assert not (tmp_path / "j.jsonl").exists()
    assert artifact.read_text(encoding="utf-8") == candidate


# -- 5. a landing nobody can follow ---------------------------------------------------------------
def test_a_landing_that_returns_no_address_is_refused_and_nothing_is_journalled(tmp_path):
    artifact, journal = _artifact(tmp_path), tmp_path / "journal" / "2026-09-23.jsonl"

    with pytest.raises(cooling.LandingUnaddressed) as refusal:
        cooling.cool(
            Ctx(), shape=SHAPE, section="ledger", prior=PRIOR, candidate=PRIOR.replace(COLD, ""),
            land=lambda destination, spans: "", append=eviction.appender(journal),
            write=_writer(artifact), at="2026-09-23T23:45:00Z")

    assert refusal.value.code == "KIT0059"
    assert not journal.exists()
    assert artifact.read_text(encoding="utf-8") == PRIOR


# -- 6. what a cooled removal does to S1's counter -------------------------------------------------
def test_a_cooled_removal_is_a_move_and_leaves_the_unlanded_counter_where_it_was(tmp_path):
    cooled = cooling.cool(
        Ctx(), shape=SHAPE, section="ledger", prior=PRIOR, candidate=PRIOR.replace(COLD, ""),
        land=_lander(tmp_path), append=eviction.appender(tmp_path / "j.jsonl"),
        write=_writer(_artifact(tmp_path)), at="2026-09-23T23:46:00Z")
    uncooled = eviction.event(Ctx(), prior=PRIOR, candidate=PRIOR.replace(COLD, ""),
                              at="2026-09-23T23:46:00Z", artifact=SHAPE["artifact"])

    assert eviction.restated("3", cooled) == "3"
    assert eviction.restated("3", uncooled) == "4"


# -- 7. no section is privileged -------------------------------------------------------------------
def test_the_passage_holds_no_section_name_and_reads_only_what_the_declaration_says(tmp_path):
    renamed = json.loads(json.dumps(SHAPE))
    renamed["sections"][1]["id"] = "whatever-this-host-calls-it"
    renamed["sections"][1]["cools_to"] = "work-evidence"

    event = cooling.cool(
        Ctx(), shape=renamed, section="whatever-this-host-calls-it", prior=PRIOR,
        candidate=PRIOR.replace(COLD, ""), land=_lander(tmp_path),
        append=eviction.appender(tmp_path / "j.jsonl"), write=_writer(_artifact(tmp_path)),
        at="2026-09-23T23:47:00Z")

    assert event["landing"]["kind"] == "work-evidence"
    assert event["section"] == "whatever-this-host-calls-it"
    source = (KIT / "interpreters" / "cooling.py").read_text(encoding="utf-8")
    for privileged in ("ledger", "CONTINUE-HERE", "work-evidence", "run-evidence"):
        assert privileged not in source


# -- 8. the shape is a governed declaration, and the gate points at lists that exist ---------------
def test_the_shape_is_judged_by_a_registered_schema_and_the_gate_reads_declared_lists():
    assert MANIFEST.validate(SHAPE, cooling.SCHEMA) == []
    assert MANIFEST.validate({**SHAPE, "sections": []}, cooling.SCHEMA) == []
    assert MANIFEST.validate({**SHAPE, "sections": [{"id": "x"}]}, cooling.SCHEMA) != []

    governance = next(c for c in MANIFEST.capabilities if c.raw["id"] == "governance")
    reads_as = {i.get("reads_as") for i in governance.raw["installs"]}
    gate = next(g for g in governance.raw["gates"] if g["id"] == "FF-POSITION-SHAPE")

    assert gate["params"]["over"] in reads_as
    assert "stance" not in gate
    for reference in gate["params"]["references"]:
        assert reference["field"] == cooling.SECTIONS
        for source in reference["among"]["sources"]:
            assert reference["among"]["list"] in VOCABULARY
    assert {row["id"] for row in VOCABULARY["section_sources"]} == {"authored", "projected"}
    assert {row["id"] for row in VOCABULARY["audiences"]} == {"author", "steward", "system"}
