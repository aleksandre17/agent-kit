"""Acceptance: an entry file is the HOST's, with one span the kit serves (ADR-021 decision 5).

A runtime loads its entry file on every turn, so the file is two things at once: the host's own
instructions, which only the host can write, and a projection of what binds, which only the
declarations can say. Before this slice the kit served the whole file, and the host could write
nothing in it. The surface row now names a `span`; the file is written once from a `seed`, and
the kit owns only the text between the two markers -- the one marker grammar the kit already has.
Held here:

  1. a served entry is seeded once with the two markers, the kit's content between them, and the
     record names the span;
  2. the host's text outside the span survives every render and `check` is green on it;
  3. an edit INSIDE the span is reported by `check` and refused by `render`;
  4. a file the kit last served WHOLE -- before spans -- is converted, the kit's own bytes replaced;
  5. a page a runtime reads when a question arises is pointed to, not inlined;
  6. a surface no longer served withdraws only its span: an untouched seed goes, the host's text stays;
  7. the span's size is a measure a host budgets through the corpus plane, and a breach fails.

Every path, field and code is read from the declaration or module that owns it.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from harness import Fixtures

import derivation  # noqa: E402
import serving  # noqa: E402
from manifest import Manifest  # noqa: E402

from test_adapters import adapted_kit  # noqa: E402
from test_serving import (A_CLASS, AN_ARCHETYPE, DESCRIPTORS, ENABLING_FIELD, KIT, OVERLAYS, RECORD,  # noqa: E402
                          SPEC, SURFACES, durable)

import served as served_gate  # noqa: E402

SPANNED = [(s, r) for s in SURFACES for r in s["renders"] if r.get("span") and "scopes" not in next(
    v for v in SPEC["views"] if v["id"] == r["view"])]
SURFACE, ROW = SPANNED[0]
ENTRY, SPAN = ROW["target"], ROW["span"]
POINTED = [s for v in SPEC["views"] for s in v.get("sections", []) if s.get("points")]
CORPUS = next(i["target"] for c in Manifest(KIT).capabilities for i in c.installs
              if i.get("reads_as") == "corpus_maps")
HOST_TEXT = "Build with `make`; every change carries a test.\n"


def _unspanned(kit: Path) -> None:
    """The same kit as it served before spans: every render row whole."""
    for path in (kit / "capabilities").rglob("surfaces.json"):
        value = json.loads(path.read_text(encoding="utf-8"))
        spanned = False
        for surface in value.get("surfaces", []):
            for row in surface["renders"]:
                spanned = row.pop("span", None) is not None or spanned
                seed = row.pop("seed", None)
                if seed:
                    # A kit carries no file nothing declares: the seed leaves with the field naming it.
                    (kit / seed).unlink(missing_ok=True)
        if not spanned:
            continue
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")
        # ...at the version it was released at before: same version and other bytes is drift, which
        # no door re-pins, and a release that changed its bytes changed its version.
        declaration = path.parent / "capability.json"
        own = json.loads(declaration.read_text(encoding="utf-8"))
        major, minor, patch = own["version"].split(".")
        own["version"] = f"{major}.{int(minor) - 1}.{patch}"
        declaration.write_text(json.dumps(own, indent=2) + "\n", encoding="utf-8", newline="\n")


class EntryFiles(Fixtures, unittest.TestCase):

    def served_host(self, kit: Path = KIT) -> Path:
        host = self.installed(kit)
        (host / OVERLAYS).mkdir(parents=True, exist_ok=True)
        (host / OVERLAYS / f"{AN_ARCHETYPE['id']}.json").write_text(json.dumps(
            {"schema_version": 1, "id": AN_ARCHETYPE["id"], "archetype": AN_ARCHETYPE["id"]}) + "\n",
            encoding="utf-8")
        self.descriptor(host, "the-tool", SURFACE["id"])
        ran = self.run_kit(kit, host, "render")
        self.assertEqual(0, ran.returncode, ran.stderr)
        return host

    def descriptor(self, host: Path, runtime: str, surface: "str | None") -> None:
        path = host / DESCRIPTORS / f"{runtime}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        fields = {ENABLING_FIELD: surface} if surface else {}
        path.write_text(json.dumps({"schema_version": 1, "id": runtime, "class": A_CLASS["id"], **fields})
                        + "\n", encoding="utf-8")

    def entry(self, host: Path) -> str:
        return (host / ENTRY).read_text(encoding="utf-8")

    def test_340_a_served_entry_is_seeded_once_with_the_kits_span_between_two_markers(self):
        host = self.served_host()
        text = self.entry(host)
        held = derivation.span(text, SPAN)
        self.assertIsNotNone(held, "the entry marks out no span")
        self.assertTrue(held.strip(), "the span is empty")
        row = {r["path"]: r for r in json.loads((host / RECORD).read_text(encoding="utf-8"))["served"]}[ENTRY]
        self.assertEqual(SPAN, row["span"])

    def test_341_the_hosts_text_outside_the_span_survives_render_and_check(self):
        host = self.served_host()
        (host / ENTRY).write_text(self.entry(host) + "\n" + HOST_TEXT, encoding="utf-8", newline="\n")
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        self.assertIn(HOST_TEXT, self.entry(host))
        checked = self.run_kit(KIT, host, "check")
        self.assertEqual(0, checked.returncode, checked.stdout)

    def test_341b_the_hosts_own_edit_outside_the_span_needs_no_render_to_stay_green(self):
        # The served record is a projection: if it digested the whole file, every edit the host makes
        # to its own text would leave the record unreproducible until somebody ran `render`.
        host = self.served_host()
        (host / ENTRY).write_text(HOST_TEXT + "\n" + self.entry(host), encoding="utf-8", newline="\n")
        checked = self.run_kit(KIT, host, "check")
        self.assertEqual(0, checked.returncode, checked.stdout)

    def test_342_an_edit_inside_the_span_is_reported_by_check_and_refused_by_render(self):
        host = self.served_host()
        text = self.entry(host)
        held = derivation.span(text, SPAN)
        (host / ENTRY).write_text(derivation.spliced(text, SPAN, held + "\nan edit inside the span\n"),
                                  encoding="utf-8", newline="\n")
        checked = self.run_kit(KIT, host, "check")
        self.assertNotEqual(0, checked.returncode)
        self.assertIn(ENTRY, checked.stdout)
        refused = self.run_kit(KIT, host, "render")
        self.assertIn(serving.ServeCollision.code, refused.stderr + refused.stdout)
        self.assertIn("an edit inside the span", self.entry(host))

    def test_343_a_file_the_kit_last_served_whole_is_converted(self):
        host = self.served_host(adapted_kit(patch=_unspanned))
        self.assertIsNone(derivation.span(self.entry(host), SPAN), "the ancestor already served a span")
        # The adapters' bytes changed with the span, so the host walks the provenance door as an
        # upgrade does; the conversion itself is the render that upgrade ends in.
        ran = self.run_kit(KIT, host, "upgrade", "--approve", "acceptance-suite")
        self.assertEqual(0, ran.returncode, ran.stderr)
        self.assertIsNotNone(derivation.span(self.entry(host), SPAN))
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode)

    def test_344_a_page_read_when_a_question_arises_is_pointed_to_and_not_inlined(self):
        self.assertTrue(POINTED, "no section is served as a pointer")
        host = self.served_host()
        held = derivation.span(self.entry(host), SPAN)
        for section in POINTED:
            with self.subTest(section=section["id"]):
                self.assertIn(f"`{section['from']}`", held)
                page = (host / section["from"]).read_text(encoding="utf-8")
                self.assertNotIn(page.strip().splitlines()[0], held, "the page was inlined")

    def test_345_a_surface_no_longer_served_withdraws_only_its_span(self):
        host = self.served_host()
        self.descriptor(host, "the-tool", None)
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        self.assertFalse((host / ENTRY).exists(), "an untouched seed was left behind")

        host = self.served_host()
        (host / ENTRY).write_text(self.entry(host) + "\n" + HOST_TEXT, encoding="utf-8", newline="\n")
        self.descriptor(host, "the-tool", None)
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        left = self.entry(host)
        self.assertIn(HOST_TEXT, left)
        self.assertIsNone(derivation.span(left, SPAN), "the kit's span outlived its surface")

    def test_346_the_span_is_a_measure_a_host_budgets_and_a_breach_fails(self):
        host = self.served_host()
        size = len(derivation.span(self.entry(host), SPAN).encode("utf-8"))
        maps = host / CORPUS
        maps.mkdir(parents=True, exist_ok=True)
        for ceiling, code in ((size, 0), (size - 1, 1)):
            with self.subTest(ceiling=ceiling):
                (maps / "map.json").write_text(json.dumps({
                    "schema_version": 1, "id": "entry-budget",
                    "places": [{"path": "docs/decisions/", "holds": "decision"}],
                    "budgets": [{"measures": served_gate.SPAN_BYTES, "ceiling": ceiling,
                                 "measured": "2026-10-15"}]}, indent=2) + "\n",
                    encoding="utf-8", newline="\n")
                self.run_kit(KIT, host, "render")
                checked = self.run_kit(KIT, host, "check")
                self.assertEqual(code, checked.returncode, checked.stdout)
                if code:
                    self.assertIn(served_gate.SPAN_BYTES, checked.stdout)


if __name__ == "__main__":
    unittest.main()
