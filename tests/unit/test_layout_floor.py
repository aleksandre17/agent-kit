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

#: The host-side reading is shipped by the kit itself (governance's `host_layout` document).
#: Host #0 -- this repository's own `.agents/` -- reads the PINNED copy in its own tree: the same
#: file a freshly-installed host would read, never the kit's shipping source under `kit/`, and
#: never a second declaration kept only for this test.
#:
#: L3a flattened the pinned copy to `.agents/kit/` and REMOVED the separate vendor install at
#: `.agents/kit/HOST-LAYOUT.json`, so a host carries these bytes once instead of twice. The
#: reading moved with it; the property under test did not change.
HOST_DECLARATION = REPO / ".agents" / "kit" / "capabilities" / "governance" / "host-layout.json"


def _report(declaration: Path, workspace: Workspace, declaration_rel: str) -> tuple:
    failures, pending, _not_enabled = floor.evaluate(workspace, declaration_rel)
    doc = json.loads(declaration.read_text(encoding="utf-8"))
    print(f"floor: {declaration_rel} ({doc['side']}), {len(doc['entries'])} drawn path(s)")
    for entry in pending:
        print(f"  PENDING  {entry['path']}  (link {floor.link(entry)})  {entry.get('drawn_as', '')}")
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
    is the INSTALLED copy inside the host's pinned tree, not the kit's shipping source under
    `kit/` -- proving the shipped document is the one an arbitrary host would have on disk."""
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
    failures, pending, not_enabled = floor.evaluate(workspace, layout_rel)
    assert failures == []
    assert pending == []
    assert not_enabled == []

    # Remove ONE drawn path: the gate must fail on that path, and only that path.
    victim = fixture["entries"][0]
    victim_path = root / victim["path"]
    if victim["kind"] == "dir":
        victim_path.rmdir()
    else:
        victim_path.unlink()

    failures, _pending, _not_enabled = floor.evaluate(workspace, layout_rel)
    assert len(failures) == 1
    assert victim["path"] in failures[0]


def test_a_row_for_a_disabled_capability_is_skipped_and_printed_not_failed(tmp_path):
    """A row naming a `capability` this host has not enabled is neither missing nor `pending` --
    it is skipped and reported in `not_enabled`, and never counted as a floor failure."""
    fixture = {
        "schema_version": 1,
        "side": "host",
        "source": "fixture, for this test only",
        "entries": [
            {"path": "roles/", "kind": "dir", "drawn_as": "roles/", "capability": "roles"},
        ],
    }
    root = tmp_path / "host"
    root.mkdir()
    layout_rel = "layout.json"
    (root / layout_rel).write_text(json.dumps(fixture), encoding="utf-8")

    workspace = Workspace(root)
    # "roles/" does not exist on disk, and "roles" is not in the enabled set.
    failures, pending, not_enabled = floor.evaluate(workspace, layout_rel, enabled={"governance"})
    assert failures == []
    assert pending == []
    assert len(not_enabled) == 1
    assert not_enabled[0]["path"] == "roles/"
    assert not_enabled[0]["capability"] == "roles"


def _host_fixture(tmp_path, entries):
    root = tmp_path / "host"
    root.mkdir()
    (root / "layout.json").write_text(json.dumps(
        {"schema_version": 1, "side": "host", "source": "fixture, for this test only", "entries": entries}),
        encoding="utf-8")
    return Workspace(root), root


def test_a_realised_row_is_judged_at_its_realised_place(tmp_path):
    """ADR-021: the drawn path may be absent when a decision realised it elsewhere -- and the
    realised place must then exist, or the row fails naming both."""
    workspace, root = _host_fixture(tmp_path, [
        {"path": "roster.json", "kind": "file", "realised_as": {"path": "roles/", "decision": "ADR-021"}},
    ])
    failures, pending, _ = floor.evaluate(workspace, "layout.json")
    assert pending == []
    assert len(failures) == 1 and "roles/" in failures[0] and "ADR-021" in failures[0]

    (root / "roles").mkdir()
    failures, pending, _ = floor.evaluate(workspace, "layout.json")
    assert failures == [] and pending == []


def test_a_row_both_pending_and_realised_is_refused(tmp_path):
    workspace, root = _host_fixture(tmp_path, [
        {"path": "x/", "kind": "dir", "pending": "F", "realised_as": {"path": "y/", "decision": "ADR-021"}},
    ])
    (root / "y").mkdir()
    failures, pending, _ = floor.evaluate(workspace, "layout.json")
    assert pending == []
    assert len(failures) == 1 and "both pending" in failures[0]


def test_a_row_beyond_the_drawing_is_checked_like_a_drawn_one(tmp_path):
    workspace, root = _host_fixture(tmp_path, [
        {"path": "adapters/", "kind": "dir", "declared_by": "ADR-014"},
    ])
    failures, _, _ = floor.evaluate(workspace, "layout.json")
    assert len(failures) == 1 and "adapters/" in failures[0]
    (root / "adapters").mkdir()
    failures, _, _ = floor.evaluate(workspace, "layout.json")
    assert failures == []


def test_a_realised_form_still_to_be_built_is_pending_on_its_own_link(tmp_path):
    """ADR-021: the drawn form replaced by a decision whose form is not built yet waits on a link --
    printed pending, never failed, never green as present."""
    workspace, _root = _host_fixture(tmp_path, [
        {"path": "kit/doctrine/economy.md", "kind": "file",
         "realised_as": {"path": "bundles/conduct/", "decision": "ADR-021", "pending": "F"}},
    ])
    failures, pending, _ = floor.evaluate(workspace, "layout.json")
    assert failures == [] and [floor.link(e) for e in pending] == ["F"]


def test_a_closed_directory_names_every_tracked_child_no_row_covers():
    rows = [{"path": "kit/schemas/", "kind": "dir"}, {"path": "README.md", "kind": "file"},
            {"path": "x/doctrine/", "kind": "dir", "realised_as": {"path": "bundles/cardinals/", "decision": "d"}}]
    tracked = ["README.md", "kit/schemas/a.json", "kit/stray.json", "bundles/cardinals/capability.json",
               "loose/file.txt", "deep/under/open/dir.txt"]
    failures = floor.unclosed(rows, [".", "kit/"], tracked)
    named = sorted(f.split(":", 1)[0] for f in failures)
    assert named == ["deep/", "kit/stray.json", "loose/"]


def test_upstream_tree_declares_every_tracked_child_of_its_closed_directories():
    """ADR-021 decision 7: what exists beyond the drawing is declared, or it is a defect. The reading
    is what git TRACKS -- an untracked or ignored file is never a finding (decision 8)."""
    import subprocess
    doc = json.loads(DECLARATION.read_text(encoding="utf-8"))
    listed = subprocess.run(["git", "-C", str(REPO), "ls-files", "-z"], capture_output=True, check=True)
    tracked = [p for p in listed.stdout.decode("utf-8").split("\0") if p]
    failures = floor.unclosed(doc["entries"], doc.get("closed", []), tracked)
    assert not failures, failures
