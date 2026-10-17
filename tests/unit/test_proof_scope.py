"""What proves a push: its areas as published, their downstream, and a scale nobody loosens unseen (ADR-025
amendment 4) -- and the drafts `areas` makes, and the stances a new bundle version leaves orphaned."""

from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
KIT = REPO / "kit"
sys.path.insert(0, str(KIT / "interpreters"))
sys.path.insert(0, str(KIT / "interpreters" / "gates"))
sys.path.insert(0, str(KIT / "interpreters" / "verbs"))

import weighing  # noqa: E402
import norms as norms_gate  # noqa: E402
import areas as areas_verb  # noqa: E402

CLASSES = json.loads((KIT / "capabilities" / "delivery" / "work-classes.json").read_text(encoding="utf-8"))


def host(*rows, **extra):
    return {"schema_version": 1, "default_undo": "reversible", "max_areas": {},
            "areas": [{"id": i, "paths": p, "undo": "reversible", "because": "a fixture", **x} for i, p, x in rows],
            **extra}


# -- L4 ------------------------------------------------------------------------------------------
def test_a_catalogue_in_which_no_class_owes_a_decision_proves_by_everything_and_says_so():
    flat = copy.deepcopy(CLASSES)
    for row in flat["classes"]:
        row["requires"] = [r for r in row["requires"] if r != "decision"]
    commands, why = weighing.proof_for(["web/a.ts"], flat, host(("web", "^web/", {"proved_by": ["k:web"]})))
    assert commands is None and "no class of this catalogue owes a decision" in why


# -- H3 ------------------------------------------------------------------------------------------
def test_a_downstream_area_is_proved_with_the_change_that_feeds_it():
    shape = host(("api", "^api/", {"proved_by": ["k:api"], "feeds": ["web"]}), ("web", "^web/", {"proved_by": ["k:web"]}))
    commands, why = weighing.proof_for(["api/a.cs"], CLASSES, shape)
    assert commands == ["k:api", "k:web"] and "feeds web" in why
    shape["areas"][1].pop("proved_by")
    commands, why = weighing.proof_for(["api/a.cs"], CLASSES, shape)
    assert commands is None and "web (downstream)" in why


# -- H2 ------------------------------------------------------------------------------------------
def test_narrowing_a_proof_or_rewriting_a_command_is_loosening():
    before = host(("lib", "^lib/", {"proved_by": ["host:lib"]}))
    after = host(("lib", "^lib/", {"proved_by": []}))
    assert weighing.loosened(CLASSES, before, after) == ["area lib proved_by ['host:lib'] -> []"]
    assert weighing.loosened(CLASSES, after, before) == [], "widening a proof is anyone's act"
    unproved = host(("lib", "^lib/", {}))
    assert weighing.loosened(CLASSES, unproved, before), "everything -> some commands is narrower"
    assert weighing.loosened(CLASSES, before, unproved) == [], "some commands -> everything is stricter"
    defaulted = host(("lib", "^lib/", {"proved_by": ["host:lib"]}), default_proved_by=[])
    assert any(s.startswith("default_proved_by") for s in weighing.loosened(CLASSES, before, defaulted))
    added = host(("lib", "^lib/", {"proved_by": ["host:lib"]}), ("new", "^new/", {"proved_by": []}))
    assert any("area new added proved by []" in s for s in weighing.loosened(CLASSES, before, added))
    said = weighing.loosened(CLASSES, before, before, ({"host:lib": "pytest", "host:x": "a"}, {"host:lib": "exit 0"}))
    assert said == ["command host:lib rewritten ('pytest' -> 'exit 0')", "command host:x removed"]


# -- M2 ------------------------------------------------------------------------------------------
def test_the_kits_own_asserted_prose_is_proved_by_the_unit_suite():
    kit_areas = json.loads((REPO / ".agents" / "project" / "delivery" / "areas.json").read_text(encoding="utf-8"))
    for path in ("docs/guide/setup.md", "kit/README.md", "docs/reference/UPSTREAM-LAYOUT.json"):
        commands, why = weighing.proof_for([path], CLASSES, kit_areas)
        assert commands is None or "host:unit" in commands, (path, why)
    assert weighing.proof_for(["docs/notes/idea.md"], CLASSES, kit_areas)[0] == [], "plain prose stays check alone"


# -- M3 ------------------------------------------------------------------------------------------
class _Cap:
    def __init__(self, installs=(), floor=()):
        self.installs, self.raw = list(installs), {"floor": list(floor)}


def test_the_root_module_claims_only_what_no_other_area_claims_and_the_planes_stand_apart():
    mapdoc = {"id": "tool-modules", "path": "build.json", "pointer": "modules", "path_field": "path",
              "proof": "tool:test-{id}", "declarations": [r"^build\.json$", "^ops/"]}
    dirs = areas_verb.planes([_Cap([{"target": ".agents/project/x.json"}, {"target": "AGENTS.md"}]),
                              _Cap(floor=[{"path": ".github/workflows/"}, {"path": ".githooks/"}])], "kits/agent-kit")
    assert dirs == [".agents/", ".githooks/", ".github/", "kits/"]
    drafted = areas_verb.drafted([(mapdoc, {"web": {"path": "web"}, "api": {"path": "."}})], {"tool:test-web"}, dirs)
    by = {a["id"]: a for a in drafted}
    assert drafted[0]["id"] == areas_verb.PLANES_ID and by[areas_verb.PLANES_ID]["undo"] == "costly"
    root = re.compile(by["module-api"]["paths"])
    for path in ("README.md", "docs/x.md", "web/a.ts", ".agents/project/a.json", ".github/workflows/ci.yml",
                 "kits/agent-kit/x", "build.json", "ops/deploy.json", "sub/CLAUDE.md"):
        assert not root.search(path), path
    assert root.search("src/App.java") and root.search(".gitignore")
    claimed = [a["id"] for a in drafted if re.search(a["paths"], "README.md")]
    assert claimed == ["prose"], "README.md is claimed once"
    assert all(a["drafted_as"] == a["paths"] for a in drafted), "every drafted area says it is the draft's"
    waiting = areas_verb.drafted([(mapdoc, {"web": {"path": "web"}, "api": {"path": "."}})], set(), (), roots=False)
    assert "module-api" not in {a["id"] for a in waiting}, "a root module waits for the planes"


def test_a_marker_map_finds_its_modules_and_drafts_the_command_that_proves_each():
    doc = {"id": "node-packages", "markers": ["package.json"], "marker_pointer": "scripts.test",
           "proof": "host:test-{id}", "command": "npm --prefix {path} test"}
    files = {"web/package.json": {"scripts": {"test": "vitest"}}, "tools/package.json": {"scripts": {}},
             ".agents/kit/package.json": {"scripts": {"test": "x"}}}
    modules, commands = areas_verb.marked(doc, sorted(files) + ["web/a.ts"], files.__getitem__, [".agents/"])
    assert modules == {"web": {"path": "web"}} and commands == {"test-web": "npm --prefix web test"}


# -- the repository's own files ------------------------------------------------------------------
def test_the_kit_planes_hold_the_repositorys_own_files_the_vcs_port_names(tmp_path):
    import vcs
    (tmp_path / ".gitmodules").write_text("", encoding="utf-8")
    (tmp_path / ".gitignore").write_text("", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / ".gitattributes").write_text("", encoding="utf-8")
    own = vcs.own_files(tmp_path)
    assert own == [".gitignore", ".gitmodules"], "only the files the tree holds at its top"
    drafted = areas_verb.drafted([], set(), [".agents/"], own)
    planes = re.compile(drafted[0]["paths"])
    assert planes.search(".gitmodules") and planes.search(".gitignore") and planes.search(".agents/x.json")
    assert not planes.search("sub/.gitmodules.bak") and not planes.search(".gitmodules.d/x")


# -- L5 ------------------------------------------------------------------------------------------
def test_with_no_repository_a_glob_passes_over_the_kit_planes_vendored_kits_and_what_an_adapter_prunes(tmp_path):
    from probe import Probe
    from workspace import Workspace

    class Unversioned(Workspace):
        def carried(self):
            return None

    for rel in ("package.json", "web/package.json", "web/node_modules/x/package.json", ".agents/kit/package.json",
                "kits/other/package.json", "nested/package.json", "java/target/package.json"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text("{}", encoding="utf-8")
    (tmp_path / "kits" / "other" / "MANIFEST.json").write_text("{}", encoding="utf-8")
    (tmp_path / "nested" / ".git").mkdir()
    detector = json.loads((REPO / "adapters" / "node" / "node-workspace.json").read_text(encoding="utf-8"))
    assert "node_modules" in detector["prune"], "the node adapter names what a walk passes over"
    found = {}
    real = Probe._evaluate

    def caught(self, d):
        matched, captures = real(self, d)
        found[d["id"]] = captures
        return matched, captures
    Probe._evaluate = caught
    try:
        Probe(Unversioned(tmp_path), planes=lambda: ([".agents/kit"], ["MANIFEST.json"])).run([detector])
    finally:
        Probe._evaluate = real
    assert found[detector["id"]][0] == ["package.json", "package.json"], found


# -- M6 ------------------------------------------------------------------------------------------
def test_a_stance_a_new_bundle_version_orphaned_is_reported_and_readdressed():
    cardinals = json.loads((REPO / "bundles" / "cardinals" / "payload" / "cardinals.json").read_text(encoding="utf-8"))
    stances = [{"id": c["id"].replace("@1.1.0#", "@1.0.0#"), "stance": "adopts"} for c in cardinals]
    stances.append({"id": "elsewhere@1.0.0#unrelated", "stance": "adopts"})
    moves = norms_gate.readdressed(cardinals, stances)
    assert len(moves) == len(cardinals) and all(new.startswith("cardinals@1.1.0#") for new in moves.values())
    failures = norms_gate.judged(cardinals, stances, set(), "2026-01-01", set(), set())
    assert sum(f.startswith("NT-READDRESS") for f in failures) == len(cardinals)
    moved = [dict(s, id=moves.get(s["id"], s["id"])) for s in stances]
    assert not [f for f in norms_gate.judged(cardinals, moved, set(), "2026-01-01", set(), set())
                if f.startswith("NT-READDRESS")]
