"""Unit: the BUDGET RATCHET -- the gate that turns a corpus count into a verdict (ADR-019 9; S3).

What is proved here is a FIRING in both directions, against the declarations the kit actually
ships: the gate row is read out of the knowledge capability by id, its stance out of the same row,
the measures out of the same discovery the gate uses, and every fixture host is a real git
repository -- because the whole mechanism rests on what HEAD holds, and a test that faked the
previous accepted state would prove the fake.

The walk, in the order decision 9 decides it:

  1. a budget LOWERED is an ordinary edit and passes;
  2. a budget RAISED is refused, and the refusal names both numbers;
  3. a budget row ACCEPTED and then DELETED is refused -- a raise to infinity written as an absence;
  4. a measured count ABOVE its ceiling is refused, and lowering the ceiling cannot answer it;
  5. a budget declared for the FIRST time has no baseline, is printed as its own, and passes --
     which is why this gate can ship at `enforce` on day one;
  6. a host with no corpus map, and a map with no budget row, are both GREEN and say what they
     therefore did not judge;
  7. a budget over a measure nothing publishes is REFUSED with KIT0055, never passed forever;
  8. two map files capping one measure are refused -- one measure, one ceiling;
  9. the working tree is NOT the baseline: an uncommitted raise is still a raise.
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
import ratchet  # noqa: E402
from manifest import Manifest  # noqa: E402
from workspace import Workspace  # noqa: E402

MANIFEST = Manifest(KIT)
KINDS = gatekinds.registry()
MEASURES = gatekinds.registry(ratchet.REGISTRY)

#: The capability that declares the corpus map readable, and the vocabulary owner. Found by what
#: they DECLARE, never by a name spelled here.
CORPUS_MAPS = next((c, i) for c in MANIFEST.capabilities for i in c.installs
                   if i.get("validates") == "corpus-map")
VOCABULARY = next(c.documents[d["id"]] for c in MANIFEST.capabilities
                  for d in c.raw.get("documents", []) if d["validates"] == "record-keeping")

#: The gate row this slice ships, read from the declaration that carries it.
GATES = {g["id"]: g for c in MANIFEST.capabilities for g in c.gates}
RATCHET = next(g for g in GATES.values() if g["kind"] == ratchet.KIND)

#: The measure this file budgets against: the one the census already counts. Named through the
#: module that publishes it, so a renamed measure breaks this file instead of passing it.
UNCLASSIFIED = "unclassified_documents"


def _class() -> str:
    return VOCABULARY["kinds"][0]["id"]


# -- a host, a git history over it, and a context ------------------------------------------------
class Only:
    """A real capability with only the installs a test's subject needs."""

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


_TRASH: list = []


def _git(root: Path, *argv: str) -> None:
    done = subprocess.run(["git", "-C", str(root), *argv], capture_output=True)
    assert done.returncode == 0, done.stderr.decode("utf-8", "replace")


def _write_map(root: Path, budgets, places, name: str = "map.json", identity: str = "fixture"):
    target = root / CORPUS_MAPS[1]["target"]
    target.mkdir(parents=True, exist_ok=True)
    document = {"schema_version": 1, "id": identity, "places": places}
    if budgets is not None:
        document["budgets"] = budgets
    (target / name).write_text(json.dumps(document, indent=2) + "\n",
                               encoding="utf-8", newline="\n")


def _budget(value: int, measure: str = UNCLASSIFIED) -> dict:
    return {ratchet.MEASURE: measure, ratchet.CEILING: value, ratchet.MEASURED: "2026-09-21"}


def _host(accepted, documents: dict, mapped: bool = True, commit: bool = True) -> Ctx:
    """A scratch host that is a real repository: the map as ACCEPTED is committed, and whatever a
    test does afterwards is an unaccepted edit -- which is the only honest way to test a gate whose
    baseline is HEAD."""
    root = Path(tempfile.mkdtemp(prefix="ratchet-"))
    _TRASH.append(root)
    places = [{corpus.PATH: "docs/", corpus.HOLDS: _class()}]
    for rel, text in documents.items():
        whole = root / rel
        whole.parent.mkdir(parents=True, exist_ok=True)
        whole.write_text(text, encoding="utf-8", newline="\n")
    if mapped:
        _write_map(root, accepted, places)
    if commit:
        _git(root, "init", "-q", ".")
        _git(root, "add", "-A")
        _git(root, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "accepted")
    return Ctx(root)


def _restate(ctx: Ctx, budgets, name: str = "map.json", identity: str = "fixture") -> None:
    """The edit under judgement: the map as it stands in the working tree, uncommitted."""
    _write_map(ctx.workspace.path("."), budgets,
               [{corpus.PATH: "docs/", corpus.HOLDS: _class()}], name, identity)


def teardown_module(_module) -> None:
    for path in _TRASH:
        shutil.rmtree(path, ignore_errors=True)


def _run(ctx) -> list:
    return KINDS[RATCHET["kind"]](ctx, RATCHET["params"])


QUIET = {"docs/a.md": "# says nothing\n", "docs/b.md": "# says nothing either\n"}


# --------------------------------------------------------------------------------------------
# 1-2. The two directions: a budget falls in an ordinary edit, and never rises.
# --------------------------------------------------------------------------------------------
def test_a_budget_lowered_is_an_ordinary_edit(capsys):
    ctx = _host([_budget(4)], QUIET)
    _restate(ctx, [_budget(3)])

    findings = _run(ctx)
    said = capsys.readouterr().out
    print(said)
    assert findings == [], findings
    assert "previously 4" in said and "ceiling 3" in said


def test_a_budget_raised_is_refused_and_both_numbers_are_named(capsys):
    ctx = _host([_budget(4)], QUIET)
    _restate(ctx, [_budget(5)])

    findings = _run(ctx)
    print(capsys.readouterr().out)
    print("\n".join(findings))
    assert len(findings) == 1, findings
    assert "raised from 4 to 5" in findings[0], findings
    assert UNCLASSIFIED in findings[0]


# --------------------------------------------------------------------------------------------
# 3. A deletion is a raise written as an absence.
# --------------------------------------------------------------------------------------------
def test_a_budget_row_accepted_and_then_deleted_is_refused(capsys):
    ctx = _host([_budget(4)], QUIET)
    _restate(ctx, None)

    findings = _run(ctx)
    said = capsys.readouterr().out
    print(said, "\n".join(findings))
    assert len(findings) == 1, findings
    assert "no longer declared" in findings[0] and UNCLASSIFIED in findings[0]
    assert "AND SOMETHING WAS" in said, (
        "a map that dropped its only budget reported a green absence beside a refusal"
    )


# --------------------------------------------------------------------------------------------
# 4. The second refusal decision 9 names: the count is over the ceiling that was to cap it.
# --------------------------------------------------------------------------------------------
def test_a_measured_count_above_its_declared_budget_is_refused(capsys):
    ctx = _host([_budget(1)], QUIET)

    findings = _run(ctx)
    print(capsys.readouterr().out, "\n".join(findings))
    assert len(findings) == 1, findings
    assert "measures 2 against a declared ceiling of 1" in findings[0], findings


def test_a_measured_count_within_its_budget_passes(capsys):
    ctx = _host([_budget(2)], QUIET)

    findings = _run(ctx)
    said = capsys.readouterr().out
    print(said)
    assert findings == [], findings
    assert "measures 2" in said


# --------------------------------------------------------------------------------------------
# 5. Day one: a first budget row is its own baseline, which is why this gate can ship enforcing.
# --------------------------------------------------------------------------------------------
def test_a_budget_declared_for_the_first_time_has_no_baseline_and_passes(capsys):
    ctx = _host(None, QUIET)
    _restate(ctx, [_budget(2)])

    findings = _run(ctx)
    said = capsys.readouterr().out
    print(said)
    assert findings == [], findings
    assert "first declared here" in said


def test_a_host_with_no_history_at_all_is_green_and_says_there_is_no_baseline(capsys):
    ctx = _host([_budget(2)], QUIET, commit=False)

    findings = _run(ctx)
    said = capsys.readouterr().out
    print(said)
    assert findings == [], findings
    assert "THERE IS NO PREVIOUS ACCEPTED STATE" in said
    assert "measures 2" in said, "the half of the verdict that needs no history was skipped"


def test_the_gate_this_slice_ships_runs_at_enforce_from_day_one():
    """Enforcing on day one, and the kit does not ship a host's stance to get there.

    `stances.json` says it in its own summary: the kit ships the VOCABULARY and the UNANSWERED
    DEFAULT, and when a gate is lowered or raised is the host's declaration (ADR-006, ADR-001
    point 4). That default is `enforce`, so a gate that declares nothing enforces -- which is
    exactly what ADR-019 decision 9 asks of the ratchet, reached without the kit answering for
    anybody. A `stance.ships` row here would be the defect S2a already paid for.
    """
    stances = next(c.documents[d["id"]] for c in MANIFEST.capabilities
                   for d in c.raw.get("documents", []) if d["validates"] == "stance")
    assert stances["unanswered"] == "enforce", stances["unanswered"]
    assert next(s for s in stances["stances"] if s["id"] == stances["unanswered"])["fails"] is True
    assert "stance" not in RATCHET, (
        "the kit shipped a stance on this gate -- the host's declaration, made by the publisher"
    )


# --------------------------------------------------------------------------------------------
# 6. The absences: nothing mapped, and nothing budgeted. Green, and never a silent pass.
# --------------------------------------------------------------------------------------------
def test_a_host_with_no_corpus_map_is_green_and_says_what_it_did_not_judge(capsys):
    ctx = _host(None, QUIET, mapped=False)

    findings = _run(ctx)
    said = capsys.readouterr().out
    print(said)
    assert findings == [], findings
    assert "NOTHING WAS RATCHETED" in said and "budgeted nothing" in said


def test_a_map_that_carries_no_budget_row_is_green_and_says_so(capsys):
    ctx = _host(None, QUIET)

    findings = _run(ctx)
    said = capsys.readouterr().out
    print(said)
    assert findings == [], findings
    assert "not one of them carries a budget row" in said


# --------------------------------------------------------------------------------------------
# 7. A budget nobody can measure is refused, with the code the registry means.
# --------------------------------------------------------------------------------------------
def test_a_budget_over_a_measure_nothing_publishes_is_refused_with_its_code():
    ctx = _host(None, QUIET)
    _restate(ctx, [_budget(3, "documents_nobody_counts")])

    with pytest.raises(ratchet.RatchetError) as refused:
        _run(ctx)
    assert ratchet.RatchetError.code == "KIT0055"
    registry = json.loads((KIT / "diagnostics.json").read_text(encoding="utf-8"))
    meant = {row["code"] for row in registry["codes"]}
    assert ratchet.RatchetError.code in meant, "a code was claimed in code and never registered"
    assert "documents_nobody_counts" in str(refused.value)
    assert UNCLASSIFIED in str(refused.value), "the published measures were not printed"


# --------------------------------------------------------------------------------------------
# 8. One measure, one ceiling.
# --------------------------------------------------------------------------------------------
def test_two_map_files_capping_one_measure_are_refused(capsys):
    ctx = _host([_budget(4)], QUIET)
    _restate(ctx, [_budget(9)], name="second.json", identity="second")

    findings = _run(ctx)
    print(capsys.readouterr().out, "\n".join(findings))
    assert any("already caps the same measure" in f for f in findings), findings


# --------------------------------------------------------------------------------------------
# 9. The baseline is what was ACCEPTED, not what is on disk.
# --------------------------------------------------------------------------------------------
def test_the_working_tree_is_not_the_baseline(capsys):
    ctx = _host([_budget(4)], QUIET)
    _restate(ctx, [_budget(5)])
    _run(ctx)
    capsys.readouterr()

    # The same unaccepted file is read a second time; an implementation that took its baseline
    # from disk would now be comparing 5 with 5 and reporting a clean ratchet.
    findings = _run(ctx)
    print(capsys.readouterr().out, "\n".join(findings))
    assert len(findings) == 1 and "raised from 4 to 5" in findings[0], (
        "an unaccepted edit was allowed to supply its own baseline"
    )


# --------------------------------------------------------------------------------------------
# The measures themselves: published by the modules that read them, absent where nothing was read.
# --------------------------------------------------------------------------------------------
def test_every_published_measure_answers_absence_with_nothing_rather_than_zero():
    ctx = _host(None, QUIET, mapped=False)
    assert UNCLASSIFIED in MEASURES, sorted(MEASURES)
    for name, measure in sorted(MEASURES.items()):
        taken = measure(ctx, RATCHET["params"])
        assert taken is None, (
            f"{name} reported {taken} over a host that declares no corpus map -- an unread corpus "
            f"was answered with a number"
        )
