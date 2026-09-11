"""Acceptance: schema versions and change (ADR-009) -- every document states the version of its
kind, that version has exactly one home, and a reader meeting a version it does not read REFUSES.

Before ADR-009 twenty-odd schemas declared `schema_version` as a bare integer, so a document from
the future validated, and six modules each held a version of their own. Here every schema the
MANIFEST registers is iterated -- never a hand list -- and each set is asserted non-empty, so an
empty registry cannot pass by having nothing to check.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from harness import CLI, KIT, Fixtures, Manifest

import ephemeral  # noqa: E402
import hostlock  # noqa: E402
import journal as journal_module  # noqa: E402
import manifest as manifest_port  # noqa: E402

MANIFEST = Manifest(KIT)
VERSION = manifest_port.VERSION
#: Every schema the kit registers, READ from the manifest.
REGISTERED = json.loads((KIT / "MANIFEST.json").read_text(encoding="utf-8"))["schemas"]
#: The host document the host ANSWERS with, found by asking the declarations where it lives.
ANSWERS = next(i for c in MANIFEST.capabilities for i in c.installs if i["mode"] == "declaration")
#: Kinds the INTERPRETER writes on a host (no seed source), plus the hold and the journal.
WRITTEN = sorted({i["validates"] for c in MANIFEST.capabilities for i in c.installs
                  if i.get("validates") and "source" not in i} | {hostlock.SCHEMA, journal_module.SCHEMA})
PLANE_FILES = {hostlock.SCHEMA: hostlock.NAME, journal_module.SCHEMA: journal_module.NAME}


def carrier(schema: dict) -> dict:
    """Where a schema says a document's version lives: the document, or each of its records."""
    return schema["items"] if schema.get("type") == "array" else schema


def pin(kit: Path, name: str, const: int, required: bool = True) -> None:
    """Move one registered kind to `const` in a fixture kit, in its schema and nowhere else."""
    def mutate(schema):
        body = carrier(schema)
        body["properties"][VERSION] = {"type": "integer", "const": const}
        wanted = [k for k in body.get("required", []) if k != VERSION]
        body["required"] = ([VERSION] if required else []) + wanted
    Fixtures.edit_json(kit, REGISTERED[name], mutate)


class SchemaVersions(Fixtures, unittest.TestCase):
    """ADR-009: one version per document kind, declared once, refused by name when not read."""

    def test_212_every_schema_the_manifest_registers_declares_its_version_as_one_integer_const(self):
        """A kind whose version is a bare integer cannot tell a future document from one it
        understands. Every registered schema pins it -- and past version 1 it must REQUIRE it."""
        self.assertTrue(REGISTERED, "the manifest registers no schemas; nothing would be checked")
        for name in sorted(REGISTERED):
            with self.subTest(schema=name):
                body = carrier(MANIFEST.schema(name))
                declared = body.get("properties", {}).get(VERSION)
                self.assertIsInstance(declared, dict, f"{name} declares no {VERSION}")
                self.assertEqual("integer", declared.get("type"))
                const = declared.get("const")
                self.assertTrue(isinstance(const, int) and not isinstance(const, bool) and const >= 1,
                                f"{name} does not pin its version as an integer const >= 1")
                if const > 1:
                    self.assertIn(VERSION, body.get("required", []))
                self.assertEqual(const, MANIFEST.version_of(name))

    def test_213_every_registered_kind_refuses_a_document_from_a_newer_version_before_judging_its_shape(self):
        """The reader rule is ONE mechanism for all kinds: a newer document is refused with the
        newer-document code, never handed to today's schema to be misread as a list of errors."""
        self.assertTrue(REGISTERED)
        for name in sorted(REGISTERED):
            with self.subTest(schema=name):
                record = {VERSION: MANIFEST.version_of(name) + 1}
                document = [record] if MANIFEST.schema(name).get("type") == "array" else record
                with self.assertRaises(manifest_port.NewerDocument) as refused:
                    MANIFEST.validate(document, name)
                self.assertEqual("KIT0033", refused.exception.code)

    def test_214_no_interpreter_module_holds_a_document_version_of_its_own(self):
        """The schema is the only home of a version. A module constant, or a literal version
        stamped into a document, is a second home that goes on reading 1 after the schema moves."""
        modules = sorted(CLI.parent.rglob("*.py"))
        self.assertTrue(modules, "no interpreter modules were found to inspect")
        second_home = re.compile(r"^\s*[A-Z_]*SCHEMA_VERSION\s*=|[\"']schema_version[\"']\s*:\s*\d", re.M)
        offenders = [p.relative_to(CLI.parent).as_posix() for p in modules
                     if second_home.search(p.read_text(encoding="utf-8"))]
        self.assertEqual([], offenders, "these modules hold a document version of their own")

    def test_215_a_kind_moved_to_version_two_in_its_schema_alone_is_written_at_two_by_every_writer(self):
        """Move every interpreter-written kind to version 2 in the SCHEMA only, change no code, and
        every document an approved install leaves states 2 -- the writers are projections."""
        self.assertTrue(WRITTEN)
        kit = self.fixture_kit("version-two", lambda k: [pin(k, n, 2) for n in WRITTEN])
        host = self.installed(kit)
        plane = next(p["root"].rstrip("/") for p in MANIFEST.planes if p["class"] == ephemeral.OBSERVED)
        found = {}
        for c in MANIFEST.capabilities:
            for item in c.installs:
                if item.get("validates") in WRITTEN:
                    target = host / item["target"]
                    paths = sorted(target.glob("*.json")) if target.is_dir() else [target]
                    for path in paths:
                        if path.is_file():
                            found[path] = item["validates"]
        for name, rel in PLANE_FILES.items():
            if (host / plane / rel).is_file():
                found[host / plane / rel] = name
        self.assertTrue(found, "an approved install left no interpreter-written document to read")
        for path, name in found.items():
            with self.subTest(document=path.name, schema=name):
                self.assertEqual(2, json.loads(path.read_text(encoding="utf-8"))[VERSION])

    def test_216_a_host_document_written_by_a_newer_kit_is_refused_by_code_and_left_untouched(self):
        """Terraform's rule: state from a newer tool is never read. The run stops with the code,
        and the document the newer kit wrote is exactly as it was."""
        host = self.installed()
        answers = host / ANSWERS["target"]
        value = json.loads(answers.read_text(encoding="utf-8"))
        value[VERSION] = MANIFEST.version_of(ANSWERS["validates"]) + 1
        answers.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        before = answers.read_bytes()
        result = self.run_kit(KIT, host, "check")
        self.assertNotEqual(0, result.returncode)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn(f"[{manifest_port.NewerDocument.code}]", result.stderr)
        self.assertEqual(before, answers.read_bytes(), "a document from a newer kit was rewritten")

    def test_217_a_host_document_at_an_older_version_with_no_declared_migration_is_refused_by_code(self):
        """A kit whose kind has moved on, meeting a host document at the old version, declares no
        migration pre-1.0 -- so it refuses by name instead of reading the old shape as the new."""
        host = self.installed()
        kind = ANSWERS["validates"]
        kit = self.fixture_kit("answers-moved-on", lambda k: pin(k, kind, MANIFEST.version_of(kind) + 1))
        before = (host / ANSWERS["target"]).read_bytes()
        result = self.run_kit(kit, host, "check")
        self.assertNotEqual(0, result.returncode)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn(f"[{manifest_port.OlderDocument.code}]", result.stderr)
        self.assertEqual(before, (host / ANSWERS["target"]).read_bytes())

    def test_218_a_kit_whose_schema_breaks_the_version_policy_refuses_to_load_at_all(self):
        """The policy is held where schemas are loaded: a bare-integer version, or a kind past
        version 1 that no longer requires the statement, stops the kit before it reads anything."""
        name = sorted(REGISTERED)[0]

        def bare(kit):
            Fixtures.edit_json(kit, REGISTERED[name], lambda s: carrier(s)["properties"].__setitem__(
                VERSION, {"type": "integer"}))

        cases = (("bare-version", bare), ("unrequired-past-one", lambda k: pin(k, name, 2, required=False)))
        for label, patch in cases:
            with self.subTest(case=label):
                result = self.run_kit(self.fixture_kit(label, patch), self.host(), "check")
                self.assertNotEqual(0, result.returncode)
                self.assertNotIn("Traceback", result.stderr)
                self.assertIn(f"[{manifest_port.ManifestError.code}]", result.stderr)
                self.assertIn("ADR-009", result.stderr)


if __name__ == "__main__":
    unittest.main()
