"""Unit: an undertaking that reaches the terminal value MATURES the judgement it caps -- and a
passage a party holds matures at no value at all (ADR-020 decision 11 row S5, decision 8; ADR-019
decision 9; ADR-006).

What is proved here is a FIRING in every direction the mechanism can fire, against the
declarations the kit actually ships -- the judgements out of the same discovery the verb uses, the
stance vocabulary out of the document that declares it, the passage out of the lifecycle the kit
distributes. Nothing is restated here: a suite holding its own copy of a gate id, a stance word or
a passage would go on passing after the kit moved.

  1. a cap at the terminal value matures the judgement that reads it, and the surface names the
     row that did it;
  2. the same cap one above the terminal value changes nothing at all;
  3. maturation only ever removes a CONCESSION -- it cannot lower what was declared;
  4. a cap that has matured cannot be raised again: the ratchet refuses it, which is what makes
     the terminal value terminal;
  5. a PASSAGE a declaration puts in a party's hands cannot be matured -- it is in no registry of
     judgements, the attempt is refused with `KIT0066`, and the declaration that carries it has no
     field a consequence could be written in;
  6. a count with no judgement beside it matures nothing and SAYS so;
  7. the dangerous case: a matured cap whose count can no longer be taken stays matured, because
     the fact is read from the host's declaration and never from the world.

The host fixture is this file's own, deliberately: the ratchet's suite builds a repository because
its subject is what HEAD holds, and this subject is what the tree DECLARES. The two hosts differ in
what they need to be, so neither is a copy of the other.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
KIT = REPO / "kit"

for extra in [KIT / "interpreters", *sorted(p for p in (KIT / "interpreters").iterdir()
                                            if p.is_dir() and not p.name.startswith("_"))]:
    sys.path.insert(0, str(extra))

import corpus  # noqa: E402
import gatekinds  # noqa: E402
import maturation  # noqa: E402
import ratchet  # noqa: E402
import stance as stance_of  # noqa: E402
from manifest import Manifest  # noqa: E402
from workspace import Workspace  # noqa: E402

MANIFEST = Manifest(KIT)
KINDS = gatekinds.registry()
MEASURES = gatekinds.registry(maturation.EXHAUSTED)
TAKEN = gatekinds.registry(ratchet.REGISTRY)
PAIRINGS = gatekinds.registry(maturation.JUDGED_BY)
ROWS, UNANSWERED = stance_of.vocabulary(MANIFEST)

#: The stance rungs, read from the vocabulary: the lowest that does not fail is the CONCESSION a
#: maturation spends, and the unanswered rung is where a matured judgement stands.
QUIET = next(row["id"] for row in sorted(ROWS.values(), key=lambda r: r["rank"]) if not row["fails"])

#: The capability that declares the corpus map readable -- found by what it declares.
CORPUS_MAPS = next((c, i) for c in MANIFEST.capabilities for i in c.installs
                   if i.get("validates") == "corpus-map")
VOCABULARY = next(c.documents[d["id"]] for c in MANIFEST.capabilities
                  for d in c.raw.get("documents", []) if d["validates"] == "record-keeping")

GATES = [g for c in MANIFEST.capabilities for g in c.gates]
RATCHET = next(g for g in GATES if g["kind"] == ratchet.KIND)

#: A count this kit both TAKES and PAIRS with a judgement of its own, and the gate row that
#: judgement runs under. Both are read out of the declarations, so a renamed pairing breaks this
#: file instead of passing it; and both are taken from the capability this fixture enables,
#: because a maturation over a judgement nobody is running is a different case, proved below.
CAPPED = next(measure for measure in sorted(PAIRINGS)
              if any(g["kind"] == PAIRINGS[measure] for g in CORPUS_MAPS[0].gates))
JUDGED = next(g for g in CORPUS_MAPS[0].gates if g["kind"] == PAIRINGS[CAPPED])

#: A count published with NO judgement beside it, if this kit has one -- the honest "matures
#: nothing" case. `None` where every count is paired, and the test says so rather than inventing.
UNPAIRED = next((measure for measure in sorted(TAKEN) if measure not in PAIRINGS), None)

_TRASH: list = []


def _class() -> str:
    return VOCABULARY["kinds"][0]["id"]


class Only:
    """A real capability with only the installs this subject needs."""

    def __init__(self, capability, installs) -> None:
        self.id, self.documents, self.raw = capability.id, capability.documents, capability.raw
        self.installs = installs
        self.gates = capability.gates


class Ctx:
    def __init__(self, root: Path) -> None:
        self.workspace = Workspace(root)
        self.manifest = MANIFEST
        owner, install = CORPUS_MAPS
        self._enabled = [Only(c, [install] if c.id == owner.id else [])
                         for c in MANIFEST.capabilities
                         if c.id in {owner.id} | {c2.id for c2 in MANIFEST.capabilities
                                                  if "record_keeping" in c2.documents}]

    def enabled_capabilities(self):
        return self._enabled


def _write_map(root: Path, budgets) -> None:
    target = root / CORPUS_MAPS[1]["target"]
    target.mkdir(parents=True, exist_ok=True)
    document = {"schema_version": 1, "id": "fixture",
                "places": [{corpus.PATH: "docs/", corpus.HOLDS: _class()}]}
    if budgets is not None:
        document["budgets"] = budgets
    (target / "map.json").write_text(json.dumps(document, indent=2) + "\n",
                                     encoding="utf-8", newline="\n")


def _budget(value: int, measure: str = None) -> dict:
    return {ratchet.MEASURE: measure or CAPPED, ratchet.CEILING: value,
            ratchet.MEASURED: "2026-09-24"}


def _host(budgets, documents: dict = None, commit: bool = False) -> Ctx:
    root = Path(tempfile.mkdtemp(prefix="maturation-"))
    _TRASH.append(root)
    for rel, text in (documents or {}).items():
        whole = root / rel
        whole.parent.mkdir(parents=True, exist_ok=True)
        whole.write_text(text, encoding="utf-8", newline="\n")
    _write_map(root, budgets)
    if commit:
        for argv in (["init", "-q", "."], ["add", "-A"],
                     ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "accepted"]):
            done = subprocess.run(["git", "-C", str(root), *argv], capture_output=True)
            assert done.returncode == 0, done.stderr.decode("utf-8", "replace")
    return Ctx(root)


def teardown_module(_module) -> None:
    for path in _TRASH:
        shutil.rmtree(path, ignore_errors=True)


def _answers(gate_id: str, stance: str) -> dict:
    """The host's own answer, in the shape the host writes it. Nothing in the kit writes one."""
    return {"stances": [{"gate": gate_id, "stance": stance, "by": "unit-suite", "at": "2026-09-24"}]}


def _resolved(ctx, answers: dict):
    matured, idle = maturation.spent(ctx, ctx.enabled_capabilities())
    resolved, _unbound = stance_of.resolve(MANIFEST, answers, ctx.enabled_capabilities(), matured)
    return next(r for (_cap, gate_id), r in resolved.items() if gate_id == JUDGED["id"]), idle


CORPUS = {"docs/a.md": "# says nothing\n", "docs/b.md": "# says nothing either\n"}


# --------------------------------------------------------------------------------------------
# 1-3. The terminal value spends a concession, and nothing else moves.
# --------------------------------------------------------------------------------------------
def test_an_undertaking_at_the_terminal_value_matures_the_judgement_it_caps():
    ctx = _host([_budget(ratchet.TERMINAL)], CORPUS)

    held, _idle = _resolved(ctx, _answers(JUDGED["id"], QUIET))

    assert held.stance == UNANSWERED, held.stance
    assert held.fails, "a matured judgement did not fail the run it was supposed to start failing"
    assert CAPPED in held.source and "matured" in held.source, held.source
    assert "map.json" in held.source, ("the row that caused the maturation is not named; a "
                                       "consequence with no source is a machine deciding")


def test_an_undertaking_above_the_terminal_value_leaves_the_judgement_exactly_as_it_was():
    ctx = _host([_budget(ratchet.TERMINAL + 1)], CORPUS)

    held, idle = _resolved(ctx, _answers(JUDGED["id"], QUIET))

    assert held.stance == QUIET, held.stance
    assert not held.fails
    assert "declared by unit-suite" in held.source, held.source
    assert idle == [], idle


def test_maturation_removes_a_concession_and_can_never_lower_what_was_declared():
    ctx = _host([_budget(ratchet.TERMINAL)], CORPUS)
    highest = max(ROWS.values(), key=lambda row: row["rank"])["id"]

    held, _idle = _resolved(ctx, _answers(JUDGED["id"], highest))

    assert held.stance == highest, held.stance
    assert "declared by unit-suite" in held.source, (
        "a maturation overwrote a declaration that already stood at or above the unanswered rung")


# --------------------------------------------------------------------------------------------
# 4. The terminal value is terminal: it cannot be raised afterwards.
# --------------------------------------------------------------------------------------------
def test_an_undertaking_that_has_matured_can_no_longer_be_raised(capsys):
    ctx = _host([_budget(ratchet.TERMINAL)], CORPUS, commit=True)
    _write_map(ctx.workspace.path("."), [_budget(ratchet.TERMINAL + 1)])

    findings = KINDS[ratchet.KIND](ctx, RATCHET["params"])
    print(capsys.readouterr().out)
    print("\n".join(findings))

    raise_refused = f"raised from {ratchet.TERMINAL} to {ratchet.TERMINAL + 1}"
    assert any(raise_refused in finding for finding in findings), findings
    assert any(CAPPED in finding for finding in findings), findings


# --------------------------------------------------------------------------------------------
# 5. A passage a party holds is not a judgement, and no value matures one.
# --------------------------------------------------------------------------------------------
def _passages() -> list:
    """Every passage the kit's own declarations put in a party's hands, read from the documents
    that declare them. The field that names the party is read from the SCHEMA, so this test knows
    no lifecycle word of its own."""
    schema = json.loads((KIT / "schemas" / "lifecycle.schema.json").read_text(encoding="utf-8"))
    shape = schema["properties"]["transitions"]["items"]
    held = next(name for name, prop in shape["properties"].items()
                if "machine" in prop.get("description", "") and prop.get("type") == "string")
    found = []
    for capability in MANIFEST.capabilities:
        for document in capability.documents.values():
            for row in (document.get("transitions") or []) if isinstance(document, dict) else []:
                if held in row:
                    found.append((row, held, shape))
    return found


def test_a_passage_a_party_holds_is_in_no_registry_this_mechanism_can_address():
    passages = _passages()
    assert passages, "this kit declares no passage in a party's hands; the refusal below proves nothing"
    for row, held, shape in passages:
        name = f"{row['from']}-{row['to']}"
        assert name not in KINDS and row[held] not in KINDS, (
            f"the passage {name!r} is reachable as a judgement; a party's passage must be in no "
            f"registry a cap can address")
        assert shape["additionalProperties"] is False, (
            "a passage's declaration is open; a consequence could be written onto it")
        assert not ({"stance", "ships", "floor"} & set(shape["properties"])), (
            "a passage's declaration has a field a stance could be written in -- the immunity of a "
            "door would then be a check somebody remembered, instead of a shape")


def test_an_undertaking_pointed_at_a_passage_is_refused_at_any_value():
    row, held, _shape = _passages()[0]
    passage = f"{row['from']}-{row['to']}"

    for value in (ratchet.TERMINAL, ratchet.TERMINAL - 1):
        with pytest.raises(maturation.MaturationError) as refusal:
            maturation.honoured({CAPPED: f"a map, capping at {value}"}, {CAPPED: passage},
                                KINDS, set(KINDS))
        said = str(refusal.value)
        assert maturation.MaturationError.code == "KIT0066"
        assert passage in said and "only a judgement" in said, said
        assert row[held] not in said, (
            "the refusal names the party that holds the passage; this mechanism describes why it "
            "cannot reach one, and never handles the party itself")


# --------------------------------------------------------------------------------------------
# 6. A count with no judgement matures nothing, and says so.
# --------------------------------------------------------------------------------------------
@pytest.mark.skipif(UNPAIRED is None, reason="every count this kit takes is paired")
def test_a_count_with_no_judgement_beside_it_matures_nothing_and_says_so():
    ctx = _host([_budget(ratchet.TERMINAL, UNPAIRED)], CORPUS)

    matured, idle = maturation.spent(ctx, ctx.enabled_capabilities())

    assert matured == {}, matured
    assert len(idle) == 1 and UNPAIRED in idle[0], idle
    assert "matures nothing" in idle[0], idle[0]


# --------------------------------------------------------------------------------------------
# 7. The dangerous case: the world stops being readable, the undertaking still stands.
# --------------------------------------------------------------------------------------------
def test_an_undertaking_that_matured_stays_matured_when_the_count_can_no_longer_be_taken():
    ctx = _host([_budget(ratchet.TERMINAL)])  # a mapped place with nothing in it: nothing to read

    assert TAKEN[CAPPED](ctx, RATCHET["params"]) is None, (
        "this fixture no longer reproduces an unreadable world; the case below proves nothing")
    held, idle = _resolved(ctx, _answers(JUDGED["id"], QUIET))

    assert held.fails and "matured" in held.source, (
        "a judgement handed its concession back on the day the world became unreadable -- silently, "
        "and on a green surface")
    assert idle == [], idle


# --------------------------------------------------------------------------------------------
# The pairings themselves: every one names a count this kit takes and a judgement it publishes.
# --------------------------------------------------------------------------------------------
def test_every_published_pairing_names_a_count_that_is_taken_and_a_judgement_that_is_published():
    assert PAIRINGS, "no count is paired with a judgement; nothing can mature"
    for measure, kind in sorted(PAIRINGS.items()):
        assert measure in TAKEN, f"{measure!r} is paired and no module takes that count"
        assert kind in KINDS, f"{measure!r} is paired with {kind!r}, which judges nothing"
