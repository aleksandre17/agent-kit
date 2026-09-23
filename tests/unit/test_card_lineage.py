"""Unit: work has ONE root, a recursive edge, and a place it owns -- ADR-020 decisions 5 and 6.

The second half of S3, proved as a FIRING against the declarations the kit actually ships: the
card grammar is judged by the schema the manifest registers, the edge is read among the records
of the collection the capability declares it governs, the passage that reads what is below a card
is the one the shipped lifecycle declares, and the places are read through the corpus interpreter
that already reads places -- never by a second walk of the tree.

The walk, in the order the decisions decide it:

  1. a card hangs under ONE other card, to any depth, and the walk up from it ends at a root. No
     level is named anywhere: the same reading answers a card one below and a card three below;
  2. what is below a card is COMPUTED from the same edge read backwards -- there is no stored
     list of parts -- and the passage that reads it is refused while anything below has a
     criterion that does not hold, refused DIFFERENTLY when one of them cannot be read, and open
     for a card with nothing below it, which is every card on the day this ships;
  3. a card that names nothing justifying it is COUNTED and not refused -- the measure is
     published, the gate stays silent, and nothing is red on the first run;
  4. the two contradictions ARE refused: a parent no card answers to, and a card that is its own
     ancestor;
  5. a reference that resolves to no reading at all is reported in the resolver's own words,
     because a reference that points nowhere reads exactly like one that points home;
  6. evidence is a PLACE a card owns, declared as a row of the host's corpus map and read through
     the one corpus reading, with the card's proofs found as its residents;
  7. a place owned by a record that does not exist, and one record owning two places, are
     refused; a place nobody owns is untouched.
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

import ancestry  # noqa: E402
import collection  # noqa: E402
import corpus  # noqa: E402
import criteria  # noqa: E402
import lifecycle as lifecycle_module  # noqa: E402
import lineage  # noqa: E402
import owners  # noqa: E402
from manifest import Manifest  # noqa: E402

MANIFEST = Manifest(KIT)

#: The capability that GOVERNS work, and the one that declares where this host's places are --
#: both found by what they declare, so this file spells no capability name and no path.
GOVERNING = next(c for c in MANIFEST.capabilities if c.governs)
MAPPING = next(c for c in MANIFEST.capabilities
               for i in c.installs if i.get("validates") == "corpus-map")
VOCABULARY = next(c for c in MANIFEST.capabilities
                  for d in c.raw.get("documents", []) if d["validates"] == "record-keeping")
CARDS = next(i for i in GOVERNING.installs if i.get("reads_as") == GOVERNING.governs["collection"])
LIFECYCLE = GOVERNING.documents[GOVERNING.governs["lifecycle"]]

#: The passage of the shipped lifecycle that is decided by reading what is BELOW a card, found by
#: the kind of reference it names. Naming the states it runs between is what this suite may not do.
DESCENT = next(kind for kind in criteria.registry() if "descendants" in kind)
BELOW_EDGE = next(e for e in LIFECYCLE["transitions"]
                  if (e.get(lifecycle_module.COMPUTED) or {}).get("proof", {}).get("kind") == DESCENT)

#: The gates under test, taken from the declarations that own them rather than named here.
LINEAGE_GATE = next(g for c in MANIFEST.capabilities for g in c.gates
                    if g["kind"] in ancestry.KINDS)
OWNED_GATE = next(g for c in MANIFEST.capabilities for g in c.gates if g["kind"] in owners.KINDS)

HERE = ".agents/project/a-file-that-is-here.json"
NOWHERE = ".agents/project/a-file-that-is-not-here.json"
EVIDENCE = ".agents/project/evidence/one/"
PROOF_DOC = EVIDENCE + "a-run.md"
UNOWNED = ".agents/project/notes/"


class _Workspace:
    """As much of the port as these readings need: what is on the disk, and what it says."""

    def __init__(self, disk: dict) -> None:
        self.disk = disk

    def exists(self, rel: str) -> bool:
        """A file, or a directory something lives in -- the port answers for both, so a place
        that is a folder is not reported as absent the way a mistyped file is."""
        return rel in self.disk or any(k.startswith(rel.rstrip("/") + "/") for k in self.disk)

    def read_json(self, rel: str):
        return self.disk[rel]

    def read_text(self, rel: str) -> str:
        return self.disk[rel]

    def files_under(self, root: str) -> list:
        prefix = root.rstrip("/") + "/"
        return sorted(rel for rel in self.disk if rel.startswith(prefix))


class _Clock:
    def now(self) -> str:
        return "2026-09-24T00:00:00"


class _Ctx:
    def __init__(self, disk: dict, capabilities: list) -> None:
        self.workspace = _Workspace(disk)
        self.manifest = MANIFEST
        self.clock = _Clock()
        self._capabilities = capabilities

    def enabled_capabilities(self) -> list:
        return self._capabilities


def _card(identity: str, **extra) -> dict:
    return dict({"schema_version": 1, "id": identity, "title": identity.replace("-", " "),
                 "state": LIFECYCLE["initial"], "created_at": "2026-09-01T00:00:00"}, **extra)


def _criterion(identity: str, ref: str) -> dict:
    return {"id": identity, "statement": f"given the host, when read, then {identity}",
            "proof": {"kind": "artifact-present", "ref": ref}}


def _held(identity: str) -> dict:
    return _criterion(identity, HERE)


def _unread(identity: str) -> dict:
    return _criterion(identity, NOWHERE)


def _disk(cards: list, maps: dict = None) -> dict:
    root = CARDS["target"]
    disk = {HERE: {"a": "file"}}
    for item in GOVERNING.installs:
        if item.get("reads_as") and collection.kind_of(item) == "document":
            disk[item["target"]] = json.loads(
                (KIT / item["source"]).read_text(encoding="utf-8"))
    for card in cards:
        disk[root + card["id"] + ".json"] = card
    for name, value in (maps or {}).items():
        disk[next(i for i in MAPPING.installs
                  if i.get("validates") == "corpus-map")["target"] + name + ".json"] = value
    return disk


def _ctx(cards: list, maps: dict = None, extra_files: dict = None) -> _Ctx:
    disk = _disk(cards, maps)
    disk.update(extra_files or {})
    capabilities = [GOVERNING] if maps is None else [GOVERNING, MAPPING, VOCABULARY]
    if maps is not None:
        for item in MAPPING.installs + VOCABULARY.installs:
            if item.get("reads_as") and collection.kind_of(item) == "document":
                disk.setdefault(item["target"], json.loads(
                    (KIT / item["source"]).read_text(encoding="utf-8")))
    return _Ctx(disk, list(dict.fromkeys(capabilities)))


# == 1. the edge is recursive, and the walk up ends at a root ===================================
def test_a_card_resolves_its_parent_to_any_depth_and_no_level_is_named():
    records = [_card("one"), _card("two", parent="one"), _card("three", parent="two")]
    chain = lineage.chain_of(records, records[-1])
    assert chain.names == ["three", "two", "one"]
    assert chain.resolves and chain.depth == 2
    assert lineage.chain_of(records, records[0]).depth == 0, "a root hangs under nothing"
    assert [c["id"] for c in lineage.children_of(records, "one")] == ["two"]
    assert [c["id"] for c in lineage.descendants_of(records, "one")] == ["two", "three"]
    assert not lineage.unresolved(records)


def test_the_grammar_admits_the_edge_and_the_two_typed_references():
    card = _card("one", parent="two", origin={"kind": "artifact-present", "ref": HERE},
                 produced=[{"kind": "artifact-present", "ref": HERE}])
    assert not MANIFEST.validate(card, CARDS["validates"])
    assert MANIFEST.validate(_card("one", parent="Not An Id"), CARDS["validates"])
    assert not MANIFEST.validate(_card("one"), CARDS["validates"]), \
        "a card that hangs under nothing is a root and is legal"


# == 2. the parent is computed from what is below it ============================================
def _decide(ctx, card):
    deciding = lifecycle_module.decided_by(BELOW_EDGE)
    lifecycle_module.refuse_uncomputed(card, BELOW_EDGE, criteria.resolve(ctx, deciding, card))


def test_a_parent_is_computed_from_its_children_and_is_refused_while_one_does_not_hold():
    parent = _card("one", criteria=[_held("its-own")])
    child = _card("two", parent="one", criteria=[_unread("the-childs")])
    ctx = _ctx([parent, child])
    verdict = criteria.resolve(ctx, lifecycle_module.decided_by(BELOW_EDGE), parent)
    assert verdict.holds is None, "a child that cannot be read is not a refutation"
    assert "0 of 1" in verdict.reading and "'two'" in verdict.reading
    with pytest.raises(lifecycle_module.UncomputedPassage) as refusal:
        _decide(ctx, parent)
    assert refusal.value.code == "KIT0061"


def test_a_parent_holds_when_everything_below_it_holds_and_a_leaf_holds_with_nothing_below():
    parent = _card("one")
    below = [_card("two", parent="one", criteria=[_held("the-childs")]),
             _card("three", parent="two", criteria=[_held("the-grandchilds")])]
    ctx = _ctx([parent] + below)
    verdict = criteria.resolve(ctx, lifecycle_module.decided_by(BELOW_EDGE), parent)
    assert verdict.holds is True and "2 of 2" in verdict.reading
    _decide(ctx, parent)
    _decide(ctx, below[-1])
    leaf = criteria.resolve(ctx, lifecycle_module.decided_by(BELOW_EDGE), below[-1])
    assert leaf.holds is True and "nothing hangs under" in leaf.reading


def test_what_is_below_is_computed_and_no_card_stores_a_list_of_its_parts():
    assert MANIFEST.validate(_card("one", children=["two"]), CARDS["validates"]), \
        "a card declared its parts and the grammar admitted a second home for the edge"


# == 3. an orphan is COUNTED, never refused =====================================================
def test_a_card_that_names_no_origin_is_counted_and_the_gate_stays_silent():
    ctx = _ctx([_card("one"), _card("two", parent="one"),
                _card("three", origin={"kind": "artifact-present", "ref": HERE})])
    assert lineage.unjustified(ctx.workspace.disk and
                               lineage.among(ctx)) == ["one", "two"]
    assert ancestry.MEASURES[lineage.UNJUSTIFIED](ctx, LINEAGE_GATE["params"]) == 2
    assert ancestry.KINDS[LINEAGE_GATE["kind"]](ctx, LINEAGE_GATE["params"]) == [], \
        "an orphan was refused; every card in existence today is one"


def test_the_measure_is_an_unasked_question_where_no_collection_can_be_reached():
    assert ancestry.MEASURES[lineage.UNJUSTIFIED](_Ctx({}, []), {}) is None, \
        "a collection nobody could read was reported as a collection with nothing wrong in it"


# == 4-5. what IS refused =======================================================================
def test_a_parent_no_card_answers_to_and_a_card_that_is_its_own_ancestor_are_refused():
    ctx = _ctx([_card("one", parent="nobody"), _card("two", parent="three"),
                _card("three", parent="two")])
    failures = ancestry.KINDS[LINEAGE_GATE["kind"]](ctx, LINEAGE_GATE["params"])
    assert len(failures) == 3
    assert "no record of this collection answers to that name" in failures[0]
    assert "already on the way up from it" in failures[1]


def test_a_reference_that_reads_as_nothing_is_reported_in_the_resolvers_own_words():
    ctx = _ctx([_card("one", produced=[{"kind": "artifact-present", "ref": NOWHERE}]),
                _card("two", origin={"kind": "a-kind-no-module-answers", "ref": "anything"})])
    failures = ancestry.KINDS[LINEAGE_GATE["kind"]](ctx, LINEAGE_GATE["params"])
    assert len(failures) == 2
    assert "'produced'" in failures[0] and NOWHERE in failures[0]
    assert "'origin'" in failures[1] and "no resolver installed here reads" in failures[1]


# == 6-7. evidence is a place the card owns, read through the corpus plane ======================
def _place(path: str, **extra) -> dict:
    return dict({"path": path, "holds": "work-evidence",
                 "authority_ceiling": "supporting"}, **extra)


def _map(*places) -> dict:
    return {"schema_version": 1, "id": "map", "places": list(places)}


def _evidence_ctx(*places, cards=None):
    return _ctx(cards if cards is not None else [_card("one")],
                maps={"map": _map(*places)},
                extra_files={PROOF_DOC: "---\nkind: work-evidence\n---\n\na run.\n"})


def test_a_cards_evidence_is_a_place_it_owns_and_is_read_through_the_one_corpus_reading():
    ctx = _evidence_ctx(_place(EVIDENCE, owned_by={"collection": "cards", "id": "one"}),
                        _place(UNOWNED, holds="work-evidence"))
    reading = corpus.read(ctx, OWNED_GATE["params"])
    found = owners.owned(reading)
    assert [item.path for item in found] == [EVIDENCE], "a place nobody owns was claimed for one"
    assert [r.path for r in found[0].residents] == [PROOF_DOC]
    assert found[0].owner["id"] == "one" and found[0].holds == "work-evidence"
    assert owners.KINDS[OWNED_GATE["kind"]](ctx, OWNED_GATE["params"]) == []


def test_a_place_owned_by_a_record_that_does_not_exist_is_refused():
    ctx = _evidence_ctx(_place(EVIDENCE, owned_by={"collection": "cards", "id": "nobody"}))
    failures = owners.KINDS[OWNED_GATE["kind"]](ctx, OWNED_GATE["params"])
    assert len(failures) == 1 and "no record of that collection answers to that name" in failures[0]


def test_one_record_owning_two_places_is_refused():
    ctx = _evidence_ctx(_place(EVIDENCE, owned_by={"collection": "cards", "id": "one"}),
                        _place(UNOWNED, owned_by={"collection": "cards", "id": "one"}))
    failures = owners.KINDS[OWNED_GATE["kind"]](ctx, OWNED_GATE["params"])
    assert len(failures) == 1 and "owns both" in failures[0]


def test_a_place_owned_out_of_a_collection_nothing_here_declares_readable_is_refused():
    ctx = _evidence_ctx(_place(EVIDENCE, owned_by={"collection": "ledgers", "id": "one"}))
    failures = owners.KINDS[OWNED_GATE["kind"]](ctx, OWNED_GATE["params"])
    assert len(failures) == 1 and "declares a collection named 'ledgers' readable" in failures[0]


def test_the_binding_lives_on_the_row_and_the_card_carries_no_path():
    assert MANIFEST.validate(_card("one", evidence=EVIDENCE), CARDS["validates"]), \
        "a card wrote down where its evidence lives; a link is a claim about a file"
