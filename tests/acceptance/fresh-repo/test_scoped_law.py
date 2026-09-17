"""Acceptance: scoped law -- a module's own laws, declared ONCE, served to every runtime where it
reads nested instructions.

A law page is one grammar. A SCOPE adds one proposition to it -- the directory below which it
binds -- and every served runtime receives the page at that directory in the form its surface
declares. These tests hold that design to what it promised:

  1. a declared scope projects one file per served runtime at the declared directory;
  2. the content of every one of them comes from the one page the scope names;
  3. removing the declaration removes the files on the next render;
  4. a directory outside the host, missing, or inside a kit plane is refused before a byte moves;
  5. the kit core names no runtime's file: every such name lives in an adapter.

Every path, field, view and code is read from the declaration or the module that owns it.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from harness import Fixtures, host_digest

import runtime as runtime_port  # noqa: E402
from manifest import Manifest  # noqa: E402

from test_adapters import ADAPTERS, adapted_kit, surface_documents  # noqa: E402

KIT = adapted_kit()
MANIFEST = Manifest(KIT)
CAPABILITIES = [c.raw for c in MANIFEST.capabilities]
SERVED = next(i for c in CAPABILITIES for i in c["installs"] if i.get("shape") == runtime_port.SHAPE)
SPEC = SERVED["serves"]
SCOPED = next(v for v in SPEC["views"] if "scopes" in v)
SCOPE_INSTALL = next(i for c in CAPABILITIES for i in c["installs"]
                     if i.get("validates") == SCOPED["scopes"]["sources"]["validates"])
ENABLING_FIELD = SPEC["enabled_by"]["field"]
DESCRIPTORS = next(i for c in CAPABILITIES for i in c["installs"]
                   if i.get("reads_as") == "runtime_descriptors")
A_CLASS = json.loads((KIT / "runtimes/classes.json").read_text(encoding="utf-8"))["classes"][0]["id"]
_rel, SURFACES = surface_documents(KIT)
VENDOR = next(p["root"] for p in MANIFEST.planes if p["class"] == "vendor").rstrip("/")
EPHEMERAL = next(p["root"] for p in MANIFEST.planes if p["class"] == "ephemeral").rstrip("/") + "/"
NL = chr(10)
CANARY = "a law only this module obeys, in words no template contains"


def scoped_targets() -> list:
    return [r["target"] for s in SURFACES for r in s["renders"] if r["view"] == SCOPED["id"]]


class ScopedLaw(Fixtures, unittest.TestCase):

    def serving_host(self) -> Path:
        host = self.installed(KIT)
        for surface in SURFACES:
            path = host / DESCRIPTORS["target"] / f"{surface['id']}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"schema_version": 1, "id": surface["id"], "class": A_CLASS,
                                        ENABLING_FIELD: surface["id"]}) + NL, encoding="utf-8")
        return host

    def declare(self, host: Path, dir_: str, scopes=None) -> None:
        page = "law-pages/module.md"
        (host / "law-pages").mkdir(exist_ok=True)
        (host / page).write_text(f"# Module laws{NL}{NL}1. {CANARY}{NL}", encoding="utf-8", newline=NL)
        rows = [{"id": "module", SCOPED["scopes"]["at"]: dir_, "page": page}] if scopes is None else scopes
        (host / SCOPE_INSTALL["target"]).write_text(json.dumps(
            {"schema_version": 1, SCOPED["scopes"]["list"]: rows}) + NL, encoding="utf-8", newline=NL)

    def test_309_a_scope_projects_one_file_per_served_runtime_at_its_directory_from_the_one_page(self):
        self.assertTrue(len(set(scoped_targets())) >= 2, "fewer than two runtimes place scoped law")
        host = self.serving_host()
        (host / "src/module").mkdir(parents=True)
        self.declare(host, "src/module")
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        record = {r["path"] for r in json.loads((host / SERVED["target"]).read_text(encoding="utf-8"))["served"]}
        for name in scoped_targets():
            rel = f"src/module/{name}"
            self.assertIn(rel, record)
            text = (host / rel).read_text(encoding="utf-8")
            self.assertIn(CANARY, text)
            self.assertIn("src/module", text)
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode)

    def test_310_removing_the_declaration_removes_the_files_on_render(self):
        host = self.serving_host()
        (host / "src/module").mkdir(parents=True)
        (host / "src/module/code.txt").write_text("the host's own file" + NL, encoding="utf-8")
        self.declare(host, "src/module")
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        self.declare(host, "src/module", scopes=[])
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        for name in scoped_targets():
            self.assertFalse((host / "src/module" / name).exists(), name)
        self.assertTrue((host / "src/module").is_dir(), "a scope's removal never removes the host's directory")

    def test_311_a_directory_outside_the_host_missing_or_inside_a_kit_plane_is_refused_and_nothing_moves(self):
        for bad in ("../elsewhere", "/abs", "not/here", f"{VENDOR}/interpreters", "."):
            with self.subTest(dir=bad):
                host = self.serving_host()
                self.declare(host, bad)
                before = {k: v for k, v in host_digest(host).items() if not k.startswith(EPHEMERAL)}
                refused = self.run_kit(KIT, host, "render")
                self.assertNotEqual(0, refused.returncode)
                said = refused.stdout + refused.stderr
                if bad in ("/abs", "."):
                    # the schema's path grammar may refuse first; either way nothing is served
                    self.assertTrue(runtime_port.ScopeRefused.code in said or "law-scope" in said, said)
                else:
                    self.assertIn(runtime_port.ScopeRefused.code, said)
                after = {k: v for k, v in host_digest(host).items() if not k.startswith(EPHEMERAL)}
                self.assertEqual(before, after)

    def test_312_the_kit_core_names_no_runtime_file(self):
        names = {r["target"].rstrip("/") for adapter in ADAPTERS
                 for s in json.loads((Path(adapter) / "surfaces.json").read_text(encoding="utf-8"))["surfaces"]
                 for r in s["renders"]}
        self.assertTrue(names)
        core = Path(__file__).resolve().parents[3] / "kit"
        for path in core.rglob("*"):
            if path.is_file() and path.suffix in {".py", ".json", ".md", ".mustache"} and "__pycache__" not in path.parts:
                text = path.read_text(encoding="utf-8", errors="replace")
                for name in names:
                    self.assertNotIn(name, text, f"{path} names the runtime file {name}")


if __name__ == "__main__":
    unittest.main()
