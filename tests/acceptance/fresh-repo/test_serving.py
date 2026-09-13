"""Acceptance: serving a runtime -- the files a runtime product reads, at the paths it reads them.

GAP-R1 was a kit that described runtimes and served none: a host could declare every tool it
runs, and not one of them would read a word the kit produced. ADR-013 closes it with a Runtime
PORT and one adapter per product that is pure DATA -- a SURFACE naming the paths the product
reads and the template each file takes there. These tests hold that design to what it promised:

  1. every declared surface, once a host's descriptor names it, gets every file it declares;
  2. a host that names no surface is served nothing, and its record says so;
  3. what is served is a PROJECTION of what the host owns -- its law page, its role
     definitions -- in a form the product can actually parse;
  4. bytes the kit did not write at a served path refuse the whole render, and nothing moves;
  5. a served file edited by hand is reported by `check` and refused by `render`;
  6. a runtime no longer served has its files removed -- only its files, only the kit's bytes;
  7. a third runtime is a surface row, and the interpreter is not touched;
  8. two served files claiming one path are refused, both named;
  9. a descriptor serving a surface nobody declares fails its gate and is served nothing.

Every path, field, surface and code is read from the declaration or the module that owns it. No
runtime and no product is named here.
"""

from __future__ import annotations

import json
import tomllib
import unittest
from pathlib import Path

from harness import KIT, Fixtures, host_digest

import runtime as runtime_port  # noqa: E402 -- reachable once the harness has placed the kit
from manifest import Manifest  # noqa: E402

MANIFEST = Manifest(KIT)
CAPABILITY = json.loads((KIT / "capabilities/runtimes/capability.json").read_text(encoding="utf-8"))
ROLES_CAPABILITY = json.loads((KIT / "capabilities/roles/capability.json").read_text(encoding="utf-8"))

SERVED = [item for item in CAPABILITY["installs"] if item.get("shape") == runtime_port.SHAPE]
assert len(SERVED) == 1, SERVED
SERVED = SERVED[0]
RECORD = SERVED["target"]
SPEC = SERVED["serves"]
ENABLING_FIELD = SPEC["enabled_by"]["field"]
SURFACES_DOC = next(d for d in CAPABILITY["documents"] if d["id"] in SPEC["surfaces"]["sources"])
SURFACES_REL = SURFACES_DOC["source"]
SURFACES = json.loads((KIT / SURFACES_REL).read_text(encoding="utf-8"))[SPEC["surfaces"]["list"]]
DESCRIPTORS = next(i for i in CAPABILITY["installs"] if i.get("reads_as") == "runtime_descriptors")["target"]
OVERLAYS = next(i for i in ROLES_CAPABILITY["installs"] if i.get("reads_as") == "role_overlays")["target"]
AN_ARCHETYPE = json.loads((KIT / "capabilities/roles/archetypes.json").read_text(encoding="utf-8"))["archetypes"][0]
A_CLASS = json.loads((KIT / "capabilities/runtimes/classes.json").read_text(encoding="utf-8"))["classes"][0]
SURFACE_GATE = next(g["id"] for g in CAPABILITY["gates"]
                    if g["params"]["references"][0]["field"] == ENABLING_FIELD)
BINDING_ROOT = next(p["root"] for p in MANIFEST.planes if p["class"] == "binding").rstrip("/") + "/"
LAW_SECTIONS = [s for v in SPEC["views"] for s in v.get("sections", []) if s["from"].startswith(BINDING_ROOT)]
INTERPRETERS = KIT / "interpreters"
#: The one plane a refusal may legitimately touch: a run records that it started and how it ended.
EPHEMERAL = next(p["root"] for p in MANIFEST.planes if p["class"] == "ephemeral").rstrip("/") + "/"


def durable(host: Path) -> dict:
    """The host as a later reader finds it, minus the record of the run that just refused."""
    return {rel: digest for rel, digest in host_digest(host).items() if not rel.startswith(EPHEMERAL)}


def files_of(surface: dict, role: str) -> list:
    """Every path a surface declares, for a host with exactly one role."""
    return [f"{r['target'].rstrip('/')}/{role}{r.get('suffix', '')}" if r["target"].endswith("/")
            else r["target"] for r in surface["renders"]]


def front_matter(text: str) -> dict:
    head = text.split("---\n")[1]
    return {k: json.loads(v) for k, v in (line.split(": ", 1) for line in head.strip().splitlines())}


class Serving(Fixtures, unittest.TestCase):

    def descriptor(self, host: Path, runtime: str, **fields) -> None:
        path = host / DESCRIPTORS / f"{runtime}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"schema_version": 1, "id": runtime, "class": A_CLASS["id"],
                                    **fields}) + "\n", encoding="utf-8")

    def hired(self, kit: Path = KIT) -> Path:
        host = self.installed(kit)
        (host / OVERLAYS).mkdir(parents=True, exist_ok=True)
        (host / OVERLAYS / f"{AN_ARCHETYPE['id']}.json").write_text(json.dumps(
            {"schema_version": 1, "id": AN_ARCHETYPE["id"], "archetype": AN_ARCHETYPE["id"]}) + "\n",
            encoding="utf-8")
        return host

    def record(self, host: Path) -> dict:
        return {r["path"]: r for r in json.loads((host / RECORD).read_text(encoding="utf-8"))["served"]}

    def test_258_every_declared_surface_serves_every_file_it_declares_once_a_descriptor_names_it(self):
        self.assertTrue(SURFACES, "no surface is declared, so this would pass by looking at nothing")
        for surface in SURFACES:
            with self.subTest(surface=surface["id"]):
                host = self.hired()
                self.descriptor(host, "the-tool", **{ENABLING_FIELD: surface["id"]})
                self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
                expected = files_of(surface, AN_ARCHETYPE["id"])
                self.assertTrue(expected)
                record = self.record(host)
                for rel in expected:
                    self.assertTrue((host / rel).is_file(), rel)
                    self.assertEqual(runtime_port._file_digest(self._ctx(host), rel), record[rel]["sha256"])
                self.assertEqual(sorted(expected), sorted(record))
                self.assertEqual(0, self.run_kit(KIT, host, "check").returncode)

    def _ctx(self, host: Path):
        class _Ctx:
            pass
        from workspace import Workspace
        ctx = _Ctx()
        ctx.workspace = Workspace(host)
        return ctx

    def test_259_a_host_that_names_no_surface_is_served_nothing_and_its_record_says_so(self):
        host = self.hired()
        self.descriptor(host, "the-tool")
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        self.assertEqual({}, self.record(host), "a record that is present and empty IS the zero")
        for surface in SURFACES:
            for rel in files_of(surface, AN_ARCHETYPE["id"]):
                self.assertFalse((host / rel).exists(), rel)

    def test_260_an_entry_carries_the_hosts_own_law_page_and_a_role_file_carries_its_definition_parseably(self):
        self.assertTrue(LAW_SECTIONS, "no briefing section reads a binding the host owns")
        for surface in SURFACES:
            with self.subTest(surface=surface["id"]):
                host = self.hired()
                canary = "the one law only this host declared, in words no template contains"
                for section in LAW_SECTIONS:
                    with open(host / section["from"], "a", encoding="utf-8", newline="\n") as f:
                        f.write(f"\n1. {canary}\n")
                self.descriptor(host, "the-tool", **{ENABLING_FIELD: surface["id"]})
                self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
                role_projection = next(p for p in (host / ".agents").rglob(f"{AN_ARCHETYPE['id']}.md")
                                       if "generated" in p.parts).read_text(encoding="utf-8")
                for rendered in surface["renders"]:
                    if not rendered["target"].endswith("/"):
                        self.assertIn(canary, (host / rendered["target"]).read_text(encoding="utf-8"))
                        continue
                    rel = f"{rendered['target']}{AN_ARCHETYPE['id']}{rendered.get('suffix', '')}"
                    text = (host / rel).read_text(encoding="utf-8")
                    # Parsed as the product parses it -- a file the product cannot read serves nothing.
                    fields = tomllib.loads(text) if rel.endswith(".toml") else front_matter(text)
                    self.assertEqual(AN_ARCHETYPE["id"], fields["name"])
                    self.assertEqual(AN_ARCHETYPE[next(v for v in SPEC["views"]
                                                       if v["id"] == rendered["view"])["describes"]],
                                     fields["description"])
                    body = next((v for v in fields.values() if v == role_projection), None) \
                        or text.split("---\n", 2)[-1]
                    self.assertEqual(role_projection, body)

    def test_261_bytes_the_kit_did_not_write_at_a_served_path_refuse_the_whole_render_and_nothing_moves(self):
        surface = SURFACES[0]
        host = self.hired()
        self.descriptor(host, "the-tool", **{ENABLING_FIELD: surface["id"]})
        rel = files_of(surface, AN_ARCHETYPE["id"])[0]
        (host / rel).parent.mkdir(parents=True, exist_ok=True)
        (host / rel).write_text("a prior system's own instructions\n", encoding="utf-8")
        before = durable(host)
        refused = self.run_kit(KIT, host, "render")
        self.assertNotEqual(0, refused.returncode)
        self.assertIn(runtime_port.ServeCollision.code, refused.stderr + refused.stdout)
        self.assertIn(rel, refused.stderr + refused.stdout)
        self.assertEqual(before, durable(host), "a refusal must leave the host as it was found")

    def test_262_a_served_file_edited_by_hand_is_reported_by_check_and_refused_by_render(self):
        surface = SURFACES[0]
        host = self.hired()
        self.descriptor(host, "the-tool", **{ENABLING_FIELD: surface["id"]})
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        rel = files_of(surface, AN_ARCHETYPE["id"])[0]
        with open(host / rel, "a", encoding="utf-8", newline="\n") as f:
            f.write("an edit somebody made by hand\n")
        checked = self.run_kit(KIT, host, "check")
        self.assertNotEqual(0, checked.returncode)
        self.assertIn(rel, checked.stdout)
        refused = self.run_kit(KIT, host, "render")
        self.assertIn(runtime_port.ServeCollision.code, refused.stderr + refused.stdout)
        self.assertIn("an edit somebody made by hand", (host / rel).read_text(encoding="utf-8"))

    def test_263_a_runtime_no_longer_served_loses_its_files_and_only_its_files(self):
        self.assertGreaterEqual(len(SURFACES), 2, "needs two surfaces to tell one from the other")
        leaving, staying = SURFACES[0], SURFACES[1]
        host = self.hired()
        self.descriptor(host, "leaving", **{ENABLING_FIELD: leaving["id"]})
        self.descriptor(host, "staying", **{ENABLING_FIELD: staying["id"]})
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        self.descriptor(host, "leaving")
        planned = self.run_kit(KIT, host, "render", "--plan").stdout
        for rel in files_of(leaving, AN_ARCHETYPE["id"]):
            self.assertRegex(planned, rf"remove\s.*{rel.replace('.', '[.]')}")
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        for rel in files_of(leaving, AN_ARCHETYPE["id"]):
            self.assertFalse((host / rel).exists(), rel)
        for rel in files_of(staying, AN_ARCHETYPE["id"]):
            self.assertTrue((host / rel).is_file(), rel)
        self.assertEqual(sorted(files_of(staying, AN_ARCHETYPE["id"])), sorted(self.record(host)))
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode)

    def test_264_a_third_runtime_is_a_surface_row_and_the_interpreter_is_not_touched(self):
        template_of = {r["view"]: r["template"] for r in SURFACES[0]["renders"]}
        third = {"id": "a-product-nobody-shipped", "says": "declared by this test alone",
                 "renders": [{"view": view, "template": source,
                              "target": ".a-product/" if view != "briefing" else ".a-product/READ-ME-FIRST.md",
                              **({"suffix": ".md"} if view != "briefing" else {})}
                             for view, source in template_of.items()]}
        kit = self.fixture_kit("third", patch=lambda k: self.edit_json(
            k, SURFACES_REL, lambda doc: doc[SPEC["surfaces"]["list"]].append(third)))
        for path in (kit / "interpreters").rglob("*.py"):
            self.assertEqual(path.read_bytes(), (INTERPRETERS / path.relative_to(kit / "interpreters")).read_bytes())
        host = self.hired(kit)
        self.descriptor(host, "the-third", **{ENABLING_FIELD: third["id"]})
        self.assertEqual(0, self.run_kit(kit, host, "render").returncode)
        for rel in files_of(third, AN_ARCHETYPE["id"]):
            self.assertTrue((host / rel).is_file(), rel)
        # And the machinery spells no surface it serves: a product's name in the interpreter is a
        # privileged case, and the next product would cost an edit.
        words = {s["id"] for s in SURFACES} | {r["target"].rstrip("/") for s in SURFACES for r in s["renders"]}
        self.assertTrue(words)
        for path in INTERPRETERS.rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            for word in words:
                self.assertNotIn(f'"{word}', source, f"{path.name} names {word}")

    def test_265_two_served_files_claiming_one_path_are_refused_and_nothing_is_written(self):
        host = self.hired()
        self.descriptor(host, "one", **{ENABLING_FIELD: SURFACES[0]["id"]})
        self.descriptor(host, "two", **{ENABLING_FIELD: SURFACES[0]["id"]})
        before = durable(host)
        refused = self.run_kit(KIT, host, "render")
        self.assertNotEqual(0, refused.returncode)
        self.assertIn(runtime_port.ServeConflict.code, refused.stderr + refused.stdout)
        self.assertEqual(before, durable(host))

    def test_266_a_descriptor_serving_a_surface_nobody_declares_fails_its_gate_and_is_served_nothing(self):
        host = self.hired()
        self.descriptor(host, "the-tool", **{ENABLING_FIELD: "a-surface-nobody-declares"})
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        self.assertEqual({}, self.record(host))
        checked = self.run_kit(KIT, host, "check")
        self.assertNotEqual(0, checked.returncode)
        self.assertIn(f"FAIL  {SURFACE_GATE}", checked.stdout)


if __name__ == "__main__":
    unittest.main()
