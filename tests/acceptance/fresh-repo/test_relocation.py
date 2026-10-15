"""Acceptance: an install that MOVED is carried across verbatim by `upgrade` (ADR-021 decision 3).

The kit moved the work plane to `docs/work/` and the host's law into `project/doctrine/`, and said
so beside each install it moved: a `relocations` row naming where it used to live. A host installed
from the release BEFORE those moves -- built here by turning each declared relocation back, so the
ancestor is derived from the very rows under test -- is then upgraded and held to:

  1. `--plan` names every owed move and writes nothing;
  2. the upgrade moves each place as the same bytes under its new name, the old name is gone, the
     estate carries every row to the new name and records each move with an h1, and `check` is
     green on the result;
  3. a document the host authored that still points into a moved place stops the whole run with
     the exact restatement -- the kit never writes the host's words -- and once the owner has
     restated it, the move goes through;
  4. both places holding something is two homes: refused whole, nothing moved.

Every path is read from the declarations that own it.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from harness import KIT, Fixtures, host_digest

import estate  # noqa: E402
from manifest import Manifest  # noqa: E402
from relocation import RelocationRefused  # noqa: E402

CORE = Manifest(KIT)
MOVES = [{**row, "capability": c.id} for c in CORE.capabilities for row in c.raw.get("relocations", [])]
ESTATE = next(i["target"] for c in CORE.capabilities for i in c.installs if i["mode"] == estate.MODE)
SCOPES = next(i for c in CORE.capabilities for i in c.installs if i.get("reads_as") == "law_scopes")
#: The move a host document points into, and the field it points with -- read from the row.
REFERENCED = next(m for m in MOVES if m.get("referenced_by"))
FIELD = REFERENCED["referenced_by"][0]
#: A projection is recomputed after it moves, so its bytes are the new kit's and not the old ones.
PROJECTIONS = {i["target"] for c in CORE.capabilities for i in c.installs if i["mode"] == "projection"}
#: Where the scopes document lives on the ANCESTOR: its own relocation's old name, if it has one.
ANCESTRAL_SCOPES = next((m["from"] for m in MOVES if m["to"] == SCOPES["target"]), SCOPES["target"])
PAGE_TEXT = "# inner\n\n1. Say so.\n"
#: What a run leaves behind in the observed plane (its receipt) is not a write to the host's tree.
OBSERVED = tuple(p["root"] for p in CORE.planes if p["class"] == "ephemeral")


def tree(host: Path) -> dict:
    return {k: v for k, v in host_digest(host).items() if not k.startswith(OBSERVED)}


def _turned_back(value):
    """A declaration as it read before its relocations: every string naming a `to` names its `from`."""
    back = {m["to"]: m["from"] for m in MOVES}
    if isinstance(value, dict):
        return {k: _turned_back(v) for k, v in value.items() if k != "relocations"}
    if isinstance(value, list):
        return [_turned_back(v) for v in value]
    return back.get(value, value) if isinstance(value, str) else value


def ancestor(kit: Path) -> None:
    """Every declaration a capability ships -- its own and the documents beside it, the drawn floor
    among them -- read as it did before the moves."""
    def back(value):
        turned = _turned_back(value)
        value.clear()
        value.update(turned)
    for path in sorted((kit / "capabilities").rglob("*.json")):
        if isinstance(json.loads(path.read_text(encoding="utf-8")), dict):
            Fixtures.edit_json(kit, path.relative_to(kit).as_posix(), back)


def files_at(root: Path, rel: str) -> dict:
    base = root / rel
    if base.is_file():
        return {base.name: base.read_bytes()}
    return {p.relative_to(base).as_posix(): p.read_bytes() for p in base.rglob("*") if p.is_file()}


class Relocation(Fixtures, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.old = cls.fixture_kit("before-relocation", patch=ancestor)

    def ancestral_host(self) -> Path:
        host = self.installed(self.old)
        for move in MOVES:
            self.assertTrue((host / move["from"]).exists(), f"the ancestor did not install {move['from']}")
            self.assertFalse((host / move["to"]).exists(), f"the ancestor already holds {move['to']}")
        return host

    def scoped_law(self, host: Path, page: str) -> None:
        """A law scope as a host authors one, on the ancestor: a page in its scoped-law space and a
        row in its scopes document naming that page as `page`."""
        (host / "inner").mkdir(exist_ok=True)
        (host / REFERENCED["from"] / "inner.md").write_text(PAGE_TEXT, encoding="utf-8", newline="\n")
        scopes = json.loads((host / ANCESTRAL_SCOPES).read_text(encoding="utf-8"))
        scopes[FIELD["list"]] = [{"id": "inner", "dir": "inner", FIELD["field"]: page,
                                  "says": "a scope the suite authored"}]
        (host / ANCESTRAL_SCOPES).write_text(json.dumps(scopes, indent=2) + "\n", encoding="utf-8",
                                             newline="\n")

    # == 1. a plan ================================================================================
    def test_330_a_plan_names_every_owed_move_and_writes_nothing(self):
        host = self.ancestral_host()
        before = tree(host)
        ran = self.run_kit(KIT, host, "upgrade", "--plan")
        self.assertEqual(0, ran.returncode, ran.stderr)
        for move in MOVES:
            self.assertIn(f"{move['from']}  ->  {move['to']}", ran.stdout)
        self.assertEqual(before, tree(host), "a plan moved something")

    # == 2. the move ==============================================================================
    def test_331_each_place_moves_as_the_same_bytes_and_the_record_carries_it(self):
        host = self.ancestral_host()
        held = {m["from"]: files_at(host, m["from"]) for m in MOVES}
        ran = self.run_kit(KIT, host, "upgrade")
        self.assertEqual(0, ran.returncode, ran.stderr)
        record = json.loads((host / ESTATE).read_text(encoding="utf-8"))
        recorded = {r["from"]: r for r in record[estate.RELOCATED]}
        paths = {r["path"] for r in record["files"]}
        for move in MOVES:
            with self.subTest(move=move["from"]):
                self.assertFalse((host / move["from"]).exists(), "the old name still holds something")
                if move["to"] in PROJECTIONS:
                    self.assertTrue((host / move["to"]).is_file(), "a moved projection was not recomputed")
                else:
                    self.assertEqual(held[move["from"]], files_at(host, move["to"]), "the bytes changed")
                self.assertEqual(move["to"], recorded[move["from"]]["to"])
                self.assertTrue(recorded[move["from"]]["digest"].startswith("h1:"))
                self.assertNotIn(move["from"], paths, "the record still names the old place")
        ran = self.run_kit(KIT, host, "check")
        self.assertEqual(0, ran.returncode, ran.stdout + ran.stderr)

    # == 3. the host's own words ==================================================================
    def test_332_a_host_document_pointing_into_a_moved_place_stops_the_run_until_the_owner_restates_it(self):
        host = self.ancestral_host()
        self.scoped_law(host, REFERENCED["from"] + "inner.md")
        before = tree(host)
        ran = self.run_kit(KIT, host, "upgrade")
        self.assertNotEqual(0, ran.returncode)
        self.assertIn(f"[{RelocationRefused.code}]", ran.stderr)
        self.assertIn(repr(REFERENCED["to"] + "inner.md"), ran.stderr, "the restatement was not printed")
        self.assertEqual(before, tree(host), "a refused relocation wrote something")

        self.scoped_law(host, REFERENCED["to"] + "inner.md")
        ran = self.run_kit(KIT, host, "upgrade")
        self.assertEqual(0, ran.returncode, ran.stderr)
        self.assertEqual(PAGE_TEXT, (host / REFERENCED["to"] / "inner.md").read_text(encoding="utf-8"))
        ran = self.run_kit(KIT, host, "check")
        self.assertEqual(0, ran.returncode, ran.stdout + ran.stderr)

    # == 4. two homes =============================================================================
    def test_333_both_places_holding_something_is_refused_whole(self):
        host = self.ancestral_host()
        move = next(m for m in MOVES if m["from"].endswith("/"))
        (host / move["to"]).mkdir(parents=True)
        (host / move["to"] / "stray.txt").write_text("a second home\n", encoding="utf-8")
        before = tree(host)
        ran = self.run_kit(KIT, host, "upgrade")
        self.assertNotEqual(0, ran.returncode)
        self.assertIn(f"[{RelocationRefused.code}]", ran.stderr)
        self.assertEqual(before, tree(host))


if __name__ == "__main__":
    unittest.main()
