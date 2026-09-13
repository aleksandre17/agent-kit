"""Acceptance: runtime ADAPTERS -- the kit core carries no product, a host takes one (ADR-014).

ADR-013 put a product's name in the right KIND of declaration, a surface, and shipped that
declaration inside the kit. The owner's rule is that the framework is agnostic: no concrete brand
or project identity in it. ADR-014 keeps the kind and moves the residence -- every surface is
published in an ADAPTER beside the kit (`adapters/<id>/`), an ordinary capability a host takes
through the provenance door exactly as it takes a doctrine bundle (ADR-004, ADR-008) -- and
makes the served projection find surfaces by the CONTRACT their document keeps, so the set of
publishers is open. These tests hold that to its word:

  1. the shipped kit core names no product -- measured by a boundary row over what the kit ships,
     and shown to see a planted one;
  2. with no adapter taken, the kit renders and checks green and serves NOTHING -- a declared
     zero, never a default adapter -- and a descriptor naming a product fails its gate;
  3. an adapter is taken through the door: pinned, digested, its authenticity NOT ESTABLISHED;
  4. the open set: a third adapter nobody shipped is served with the kit core untouched;
  5. a served path is ACCOUNTED by `cede` -- never "this host was never given it";
  6. succession counts the paths a runtime reads as the kit's own surface.

Every path, field, word and code is read from the declaration or module that owns it. The only
product names this file ever meets arrive from the adapters' own declarations.
"""

from __future__ import annotations

import atexit
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from harness import KIT, REPO, Fixtures, ship

import boundary
import declared
import provenance
from manifest import Manifest
import runtime as runtime_port
from verbs.cede import CedeRefused

#: Where the adapters are published: beside the kit, never inside it.
ADAPTERS_HOME = REPO / "adapters"
ADAPTERS = sorted(p.parent for p in ADAPTERS_HOME.glob("*/capability.json"))

CORE = Manifest(KIT)
RUNTIMES = next(c for c in CORE.capabilities
                if any(i.get("shape") == runtime_port.SHAPE for i in c.installs))
SERVED_INSTALL = next(i for i in RUNTIMES.installs if i.get("shape") == runtime_port.SHAPE)
SPEC = SERVED_INSTALL["serves"]
SELECTOR = SPEC["surfaces"]["sources"]
LIST = SPEC["surfaces"]["list"]
ENABLING_FIELD = SPEC["enabled_by"]["field"]
RECORD = SERVED_INSTALL["target"]
DESCRIPTORS = next(i for i in RUNTIMES.installs
                   if i.get("reads_as") == RUNTIMES.raw["composes"]["instances"])["target"]
SURFACE_GATE = next(g["id"] for g in RUNTIMES.gates
                    if g["params"]["references"][0]["field"] == ENABLING_FIELD)
ROLES = next(c for c in CORE.capabilities if c.id == "roles")
OVERLAYS = next(i for i in ROLES.installs if i.get("reads_as") == "role_overlays")["target"]
A_CLASS = next(d for d in RUNTIMES.documents.values() if "classes" in d)["classes"][0]
BOUNDARY_ROW = next(r for r in boundary.rules("shipped"))
GOVERNANCE_ESTATE = next(item["target"] for c in CORE.capabilities for item in c.installs
                         if item["mode"] == "estate")


def _declaration(adapter: Path) -> dict:
    return json.loads((adapter / "capability.json").read_text(encoding="utf-8"))


def take(kit: Path, adapter: Path) -> None:
    """What a host does with a published adapter, and nothing else: its directory placed at
    `capabilities/<id>/` and a manifest row naming its declaration (the doctrine-bundle door)."""
    identity = _declaration(adapter)["id"]
    shutil.copytree(adapter, kit / "capabilities" / identity)
    Fixtures.edit_json(kit, "MANIFEST.json", lambda m: m["capabilities"].append(
        {"id": identity, "declaration": f"capabilities/{identity}/capability.json"}))


def adapted_kit(patch=None, extra=()) -> Path:
    """A copy of the REAL kit with every published adapter taken -- and any `extra` adapter
    directory besides. Built outside the suite's shared trash list, because a module-level fixture
    must outlive whichever test class tears down first."""
    base = Path(tempfile.mkdtemp(prefix="kit-adapted-")).resolve()
    atexit.register(shutil.rmtree, base, True)
    kit = ship(base / "kit")
    for adapter in [*ADAPTERS, *extra]:
        take(kit, adapter)
    if patch:
        patch(kit)
    return kit


def surface_documents(kit: Path) -> tuple:
    """(kit-relative path of the first surface document, every surface) -- found by the contract
    the served projection selects on, exactly as the interpreter finds them."""
    capabilities = Manifest(kit).capabilities
    names = declared.named(capabilities, SELECTOR)
    rels = [d["source"] for c in capabilities for d in c.raw.get("documents", []) if d["id"] in names]
    surfaces = [row for c in capabilities for name in names if name in c.documents
                for row in c.documents[name][LIST]]
    return (rels[0] if rels else None), surfaces


def said(result) -> str:
    return result.stdout + result.stderr


class Adapters(Fixtures, unittest.TestCase):

    def descriptor(self, host: Path, runtime: str, **fields) -> None:
        path = host / DESCRIPTORS / f"{runtime}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"schema_version": 1, "id": runtime, "class": A_CLASS["id"],
                                    **fields}) + "\n", encoding="utf-8")

    def hired(self, kit: Path) -> Path:
        host = self.installed(kit)
        archetype = json.loads((KIT / "capabilities/roles/archetypes.json").read_text(
            encoding="utf-8"))["archetypes"][0]["id"]
        (host / OVERLAYS).mkdir(parents=True, exist_ok=True)
        (host / OVERLAYS / f"{archetype}.json").write_text(json.dumps(
            {"schema_version": 1, "id": archetype, "archetype": archetype}) + "\n", encoding="utf-8")
        return host

    def record(self, host: Path) -> dict:
        return {r["path"]: r for r in json.loads((host / RECORD).read_text(encoding="utf-8"))["served"]}

    # == 1. the kit core names no product ======================================================
    def test_267_the_shipped_kit_core_names_no_product_and_the_row_that_says_so_sees_a_planted_one(self):
        """The owner's rule as a boundary row over everything the kit states it ships. The row
        is calibrated like every row; the planted kit proves it is pointed at the files that
        matter, not at an empty set that reads exactly like a clean one."""
        self.assertEqual([], boundary.scan("shipped", boundary.World(self)))
        spoken = re.search(BOUNDARY_ROW["pattern"], _declaration(ADAPTERS[0])["id"])
        self.assertTrue(spoken, "the row does not see the name of the product an adapter serves")
        planted = self.fixture_kit("planted", patch=lambda k: self.edit_json(
            k, f"capabilities/{RUNTIMES.id}/capability.json",
            lambda v: v.update(summary=v["summary"] + " Served first to " + spoken.group(0) + ".")))
        found = boundary.scan("shipped", boundary.World(self, kit=planted))
        self.assertTrue(any(spoken.group(0) in line for line in found), found)

    # == 2. a declared zero, never a default adapter ===========================================
    def test_268_with_no_adapter_taken_the_kit_serves_nothing_checks_green_and_a_product_surface_fails_its_gate(self):
        self.assertEqual([], declared.named(CORE.capabilities, SELECTOR),
                         "the kit core itself publishes a surface -- a default adapter")
        self.assertTrue(ADAPTERS, "no adapter is published, so the named surface below is invented")
        _rel, published = surface_documents(adapted_kit())
        host = self.hired(KIT)
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        self.assertEqual({}, self.record(host))
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode)
        self.descriptor(host, "the-tool", **{ENABLING_FIELD: published[0]["id"]})
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        self.assertEqual({}, self.record(host), "a surface no adapter was taken for was served")
        checked = self.run_kit(KIT, host, "check")
        self.assertEqual(1, checked.returncode)
        self.assertIn(f"FAIL  {SURFACE_GATE}", checked.stdout)

    # == 3. an adapter is taken through the door ===============================================
    def test_269_every_published_adapter_is_taken_through_the_door_pinned_and_its_authenticity_not_established(self):
        self.assertTrue(ADAPTERS, "no adapter is published, so this would pass by pinning nothing")
        kit = adapted_kit()
        host = self.host()
        drafted = self.run_kit(kit, host, "init")
        self.assertEqual(3, drafted.returncode)
        self.assertIn("FIRST-CONTACT", drafted.stdout)
        self.assertEqual(0, self.run_kit(kit, host, "init", "--approve", "the-owner").returncode)
        pins = {p["capability"]: p for p in
                json.loads((host / GOVERNANCE_ESTATE).read_text(encoding="utf-8"))["taken"]}
        for adapter in ADAPTERS:
            with self.subTest(adapter=adapter.name):
                pin = pins[_declaration(adapter)["id"]]
                self.assertRegex(pin["digest"], r"h1:[A-Za-z0-9+/]{43}=")
                self.assertEqual(provenance.UNSIGNED, pin["authenticity"]["state"])
        self.assertIn("NOT ESTABLISHED", self.run_kit(kit, host, "check").stdout)

    # == 4. the open set =========================================================================
    def test_270_a_third_adapter_nobody_shipped_is_served_and_the_kit_core_is_not_touched(self):
        third = Path(tempfile.mkdtemp(prefix="adapter-third-")).resolve() / "a-product-nobody-shipped"
        atexit.register(shutil.rmtree, third.parent, True)
        shutil.copytree(ADAPTERS[0], third)
        before = _declaration(ADAPTERS[0])
        identity = third.name
        declaration = json.loads(json.dumps(before).replace(f"capabilities/{before['id']}/",
                                                            f"capabilities/{identity}/"))
        declaration["id"] = identity
        for item in declaration["installs"]:
            item["target"] = item["target"].replace(before["id"], identity)
        for document in declaration["documents"]:
            document["id"] = f"{document['id']}_third"
            rel = third / document["source"].split(f"capabilities/{identity}/", 1)[1]
            value = json.loads(rel.read_text(encoding="utf-8"))
            for surface in value[LIST]:
                surface["id"] = identity
                for rendered in surface["renders"]:
                    rendered["template"] = rendered["template"].replace(
                        f"capabilities/{before['id']}/", f"capabilities/{identity}/")
                    tail = "/" if rendered["target"].endswith("/") else ""
                    rendered["target"] = f".{identity}/{rendered['view']}{tail}"
            rel.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        (third / "capability.json").write_text(json.dumps(declaration, indent=2) + "\n", encoding="utf-8")
        kit = adapted_kit(extra=[third])
        for rel in [f"capabilities/{RUNTIMES.id}/capability.json",
                    *[p.relative_to(KIT).as_posix() for p in (KIT / "interpreters").rglob("*.py")]]:
            self.assertEqual((KIT / rel).read_bytes(), (kit / rel).read_bytes(), rel)
        host = self.hired(kit)
        self.descriptor(host, "the-third", **{ENABLING_FIELD: identity})
        self.assertEqual(0, self.run_kit(kit, host, "render").returncode)
        served = self.record(host)
        self.assertTrue(served)
        self.assertTrue(all(path.startswith(f".{identity}/") for path in served), served)
        for path in served:
            self.assertTrue((host / path).is_file(), path)
        self.assertEqual(0, self.run_kit(kit, host, "check").returncode)

    # == 5. cede accounts for a served path =====================================================
    def test_271_ceding_a_served_path_is_accounted_as_served_and_never_as_a_path_the_host_was_not_given(self):
        kit = adapted_kit()
        _rel, published = surface_documents(kit)
        surface = published[0]
        entry = next(r["target"] for r in surface["renders"] if not r["target"].endswith("/"))
        host = self.hired(kit)
        self.descriptor(host, "the-tool", **{ENABLING_FIELD: surface["id"]})
        self.assertEqual(0, self.run_kit(kit, host, "render").returncode)
        self.assertIn(entry, self.record(host))
        ceded = self.run_kit(kit, host, "cede", "--path", entry, "--approve", "the-owner")
        self.assertNotEqual(0, ceded.returncode)
        self.assertIn(CedeRefused.code, said(ceded))
        self.assertIn("SERVED", said(ceded))
        self.assertNotIn("was never given it", said(ceded),
                         "a file carrying the kit's recorded bytes was called one the host never had")
        self.assertIn(entry, self.record(host), "a refused cede moved the record")

    # == 6. succession counts the paths a runtime reads =========================================
    def test_272_succession_counts_every_path_a_taken_surface_reads_as_the_kits_own_surface(self):
        kit = adapted_kit()
        _rel, published = surface_documents(kit)
        host = self.host()
        read = self.run_kit(kit, host, "inherit")
        self.assertEqual(0, read.returncode)
        roots = {line.split()[1] for line in read.stdout.splitlines()
                 if line.strip().startswith("boundary ")}
        for surface in published:
            for rendered in surface["renders"]:
                with self.subTest(surface=surface["id"], target=rendered["target"]):
                    self.assertIn(rendered["target"].rstrip("/"), roots)


if __name__ == "__main__":
    unittest.main()
