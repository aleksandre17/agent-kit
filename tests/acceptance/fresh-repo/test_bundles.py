"""Acceptance: a doctrine bundle published BESIDE the kit is taken like any capability (ADR-021, slice S2).

ADR-004 keeps every opinion out of the shipped kit; ADR-021 decision 2 says where an opinion a
publisher DOES hold is published instead: `bundles/<id>/`, one complete capability per directory,
the same publication form as `adapters/`. This suite holds every bundle found there to that form:

  1. it is outside the issued manifest -- the shipped kit still publishes no doctrine;
  2. its published documents validate against the schema their declaration names;
  3. a fresh pinned host takes it through the ordinary door, enables it, and renders its roll --
     every document it published NAMED, each one UNANSWERED until the host declares a stance;
  4. `check` is green on that host, the composition stated as `kit <v> + taken: <id>`.

Every path, mode and word is read from the declaration that owns it.
"""

from __future__ import annotations

import json
import unittest

from harness import KIT, REPO, Fixtures

import manifest as manifest_port
import validation
from manifest import Manifest
from test_pinned_kit import pinned_cli, said

#: The DOCTRINE bundles: those whose documents keep the doctrine contract (the `cardinal` schema the
#: doctrine capability declares). A bundle of skills or evals is a bundle too, held by its own module.
_DOCTRINE = next(n for n in json.loads((KIT / "capabilities/doctrine/capability.json").read_text(encoding="utf-8"))
                 ["declares"]["schemas"] if n == "cardinal")
BUNDLES = sorted(p.parent for p in (REPO / "bundles").glob("*/capability.json")
                 if any(d["validates"] == _DOCTRINE
                        for d in json.loads(p.read_text(encoding="utf-8")).get("documents", [])))
CORE = Manifest(KIT)
ANSWERS = next(i for c in CORE.capabilities for i in c.installs if i["mode"] == "declaration")["target"]
PLANE = next(i for c in CORE.capabilities for i in c.installs if i["mode"] == manifest_port.TAKEN_MODE)
SCHEMAS = json.loads((KIT / "MANIFEST.json").read_text(encoding="utf-8"))["schemas"]


def declaration(bundle) -> dict:
    return json.loads((bundle / "capability.json").read_text(encoding="utf-8"))


def published(bundle) -> dict:
    """{document id: (records, schema name)} -- each document the bundle declares, read from the
    bundle's own directory by the route its declaration states (`capabilities/<id>/<rest>`)."""
    found = {}
    value = declaration(bundle)
    for document in value.get("documents", []):
        rest = document["source"].split(f"capabilities/{value['id']}/", 1)[1]
        found[document["id"]] = (json.loads((bundle / rest).read_text(encoding="utf-8")),
                                 document["validates"])
    return found


class PublishedBundles(Fixtures, unittest.TestCase):

    def test_320_a_bundle_lives_beside_the_kit_and_the_shipped_kit_still_publishes_none(self):
        self.assertTrue(BUNDLES, "ADR-021 decision 2 publishes at least the cardinals bundle")
        issued = {c.id for c in CORE.capabilities}
        for bundle in BUNDLES:
            with self.subTest(bundle=bundle.name):
                self.assertNotIn(declaration(bundle)["id"], issued,
                                 "a bundle in the issued manifest is an opinion shipped to every host")

    def test_321_every_published_document_validates_against_the_schema_its_declaration_names(self):
        for bundle in BUNDLES:
            for document, (records, schema) in published(bundle).items():
                with self.subTest(bundle=bundle.name, document=document):
                    shape = json.loads((KIT / SCHEMAS[schema]).read_text(encoding="utf-8"))
                    self.assertEqual([], validation.validate(records, shape))
                    bundle_id, version = declaration(bundle)["id"], declaration(bundle)["version"]
                    for record in records:
                        self.assertTrue(record["id"].startswith(f"{bundle_id}@{version}#"), record["id"])

    def test_322_a_taken_bundle_names_every_document_it_published_as_unanswered_and_check_is_green(self):
        for bundle in BUNDLES:
            value = declaration(bundle)
            with self.subTest(bundle=value["id"]):
                host = self.installed(KIT)
                # A bundle whose MUST rules name enforcers requires the published capabilities that hold
                # them; they are taken with it, found by the ids its declaration requires.
                published_dirs = {json.loads(p.read_text(encoding="utf-8"))["id"]: p.parent
                                  for p in REPO.glob("*/*/capability.json")}
                needed = [published_dirs[r["id"]] for r in value["requires"]
                          if r["kind"] == "capability" and r["id"] in published_dirs]
                took = pinned_cli(host, "take", "--path", ",".join(str(d) for d in [bundle, *needed]),
                                  "--approve", "acceptance-suite")
                self.assertEqual(0, took.returncode, said(took))
                self.assertTrue((host / PLANE["target"] / value["id"] / "capability.json").is_file())
                answers = json.loads((host / ANSWERS).read_text(encoding="utf-8"))
                answers["capabilities"] = sorted(set(answers["capabilities"]) | {value["id"]}
                                                 | {json.loads((d / "capability.json").read_text(encoding="utf-8"))["id"]
                                                    for d in needed})
                (host / ANSWERS).write_text(json.dumps(answers, indent=2) + "\n", encoding="utf-8", newline="\n")
                for verb, flags in (("init", ("--approve", "acceptance-suite")), ("render", ())):
                    ran = pinned_cli(host, verb, *flags)
                    self.assertEqual(0, ran.returncode, said(ran))
                roll = next(i["target"] for i in value["installs"] if i["mode"] == "projection")
                page = (host / roll).read_text(encoding="utf-8")
                records = [r for records, _schema in published(bundle).values() for r in records]
                for record in records:
                    self.assertIn(f"`{record['id']}`", page)
                self.assertEqual(len(records), page.count("UNANSWERED"),
                                 "a document this host said nothing about was not named as unanswered")
                ran = pinned_cli(host, "check")
                self.assertEqual(0, ran.returncode, said(ran))
                self.assertIn(f"kit {CORE.version} + taken: ", ran.stdout)
                self.assertIn(value["id"], ran.stdout.split("+ taken: ", 1)[1].split(" · ", 1)[0])


if __name__ == "__main__":
    unittest.main()
