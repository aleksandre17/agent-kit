"""Unit: the floor gate (ADR-015, amendment 1) reads a layout declaration and bites.

Two properties, and only these -- everything else about the gate is exercised through the real
declaration, never re-stated here:

  1. against the real UPSTREAM declaration and the real tree, the gate is either green or every
     unmet path is one this repository has declared `pending` at a named link -- never a silent
     gap;
  2. against a minimal fixture built FROM that same declaration, deleting one non-pending path
     makes the gate fail on exactly that path -- the gate bites, it does not just pass.

No sibling copy of the drawing lives here: both tests read `docs/reference/UPSTREAM-LAYOUT.json`,
the one declaration, and the schema that shapes it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
KIT = REPO / "kit"
DECLARATION = REPO / "docs" / "reference" / "UPSTREAM-LAYOUT.json"

for extra in [KIT / "interpreters", *sorted(p for p in (KIT / "interpreters").iterdir()
                                            if p.is_dir() and not p.name.startswith("_"))]:
    sys.path.insert(0, str(extra))

from workspace import Workspace  # noqa: E402
import floor  # noqa: E402

#: The host-side reading is shipped by the kit itself (governance's `host_layout` document,
#: vendored to `.agents/kit/HOST-LAYOUT.json`) so every installed host carries its own copy.
#: Host #0 -- this repository's own `.agents/` -- reads that installed copy: the same file a
#: freshly-installed host would read, never a second declaration kept only for this test.
HOST_DECLARATION = REPO / ".agents" / "kit" / "HOST-LAYOUT.json"


def _report(declaration: Path, workspace: Workspace, declaration_rel: str) -> tuple:
    failures, pending = floor.evaluate(workspace, declaration_rel)
    doc = json.loads(declaration.read_text(encoding="utf-8"))
    print(f"floor: {declaration_rel} ({doc['side']}), {len(doc['entries'])} drawn path(s)")
    for entry in pending:
        print(f"  PENDING  {entry['path']}  (link {entry['pending']})  {entry.get('drawn_as', '')}")
    for failure in failures:
        print(f"  MISSING  {failure}")
    met = len(doc["entries"]) - len(pending) - len(failures)
    print(f"floor: {met} present, {len(pending)} pending, {len(failures)} missing")
    return failures, pending


def test_upstream_tree_meets_the_floor_or_declares_why_not(capsys):
    workspace = Workspace(REPO)
    declaration_rel = DECLARATION.relative_to(REPO).as_posix()
    failures, _pending = _report(DECLARATION, workspace, declaration_rel)

    assert not failures, (
        "a drawn path is neither present nor declared pending -- "
        f"fix the tree or declare the gap: {failures}"
    )


def test_host_zero_meets_the_floor_or_declares_why_not(capsys):
    """Host #0 is this repository's own `.agents/`, installed from this kit. The declaration read
    is the INSTALLED copy (`.agents/kit/HOST-LAYOUT.json`), not the kit's shipping source --
    proving the shipped document is the one an arbitrary host would actually have on disk."""
    assert HOST_DECLARATION.exists(), (
        f"{HOST_DECLARATION}: host #0 has not taken the governance capability's `host_layout` "
        f"document -- run `upgrade --root .` first"
    )
    workspace = Workspace(REPO)
    declaration_rel = HOST_DECLARATION.relative_to(REPO).as_posix()
    failures, _pending = _report(HOST_DECLARATION, workspace, declaration_rel)

    assert not failures, (
        "a drawn HOST path is neither present nor declared pending -- "
        f"fix the tree or declare the gap: {failures}"
    )


def test_gate_bites_when_a_drawn_path_is_missing(tmp_path):
    doc = json.loads(DECLARATION.read_text(encoding="utf-8"))
    fixture = {
        "schema_version": 1,
        "side": "upstream",
        "source": "fixture, derived from the real declaration for this test only",
        "entries": [e for e in doc["entries"] if "pending" not in e][:3],
    }
    assert len(fixture["entries"]) >= 2, "fixture needs at least two non-pending drawn paths"

    root = tmp_path / "upstream"
    root.mkdir()
    layout_rel = "layout.json"
    (root / layout_rel).write_text(json.dumps(fixture), encoding="utf-8")

    # Every drawn path present: the gate is clean.
    for entry in fixture["entries"]:
        target = root / entry["path"]
        if entry["kind"] == "dir":
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("x", encoding="utf-8")

    workspace = Workspace(root)
    failures, pending = floor.evaluate(workspace, layout_rel)
    assert failures == []
    assert pending == []

    # Remove ONE drawn path: the gate must fail on that path, and only that path.
    victim = fixture["entries"][0]
    victim_path = root / victim["path"]
    if victim["kind"] == "dir":
        victim_path.rmdir()
    else:
        victim_path.unlink()

    failures, _pending = floor.evaluate(workspace, layout_rel)
    assert len(failures) == 1
    assert victim["path"] in failures[0]
