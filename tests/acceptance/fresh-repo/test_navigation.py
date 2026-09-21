"""Acceptance: NAVIGATION is a generated surface (ADR-019 decision 4; S4).

Two pages are projected from declarations the host already owns, and the whole point of them is
that no one keeps them. Four readings are walked, and each is a different way for a navigation
surface to become false:

  1. **The host that has mapped nothing.** Both pages exist on the day the capability ships, and
     they SAY that nothing was read. An empty catalog and a catalog of an unmapped corpus are
     different propositions, and only one of them is a statement about this repository.
  2. **The host with a real map.** Every declared place reaches the catalog, the triggers the map
     states reach the routes page, and `check` stays green -- a projection is not a gate.
  3. **The page somebody edited.** Refused by `FF-KIT-PROJECTION`, which is the existing drift
     judge and needed nothing added to it: hand-maintained navigation is not discouraged here, it
     is unrepresentable.
  4. **The same host rendered twice.** Identical bytes. A page carrying a clock or an order nobody
     declared would be a diff on every commit and would be read by no one within a week.

Nothing here spells a class, a plane, an authority word, a page title or a path: the capability is
found by the BLOCK it declares, its pages by the installs that carry them, the words by the rows of
the vocabulary that declares them, and the map's own field names by the module that reads them.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from harness import KIT, Fixtures
import corpus  # noqa: E402 -- the path is prepared by importing harness first
import declared  # noqa: E402
import resolution  # noqa: E402
from manifest import Manifest  # noqa: E402

MANIFEST = Manifest(KIT)

#: The capability that resolves a reading into its view, and the pages it projects from it.
READER = next(c for c in MANIFEST.capabilities if c.raw.get(resolution.BLOCK))
PARAMS = READER.raw[resolution.BLOCK][0][resolution.PARAMS]
PAGES = [i["target"] for i in READER.installs if i["class"] == "projection"]

#: Where the host writes its corpus map, read from the install that declares the space readable.
MAP_SPACE = next(i["target"] for i in READER.installs if i.get("validates") == "corpus-map")

#: The words, read from the document that owns them, and the entry flag from the declared filter.
VOCABULARY = next(c.documents[d["id"]] for c in MANIFEST.capabilities
                  for d in c.raw.get("documents", []) if d["validates"] == "record-keeping")
FLAG = PARAMS[corpus.ROOTS][declared.FIELD]
MARKED = PARAMS[corpus.ROOTS][declared.EQUALS]
TRIGGER = "a session arrives asking what this corpus is made of"


def a_class() -> str:
    return VOCABULARY["kinds"][0]["id"]


def mapped(host: Path) -> None:
    """A host that has authored a corpus map and the documents it places -- the ordinary state the
    day after a host adopts the plane."""
    space = host / MAP_SPACE
    space.mkdir(parents=True, exist_ok=True)
    (space / "map.json").write_text(json.dumps({
        "schema_version": 1,
        "id": "acceptance",
        "places": [
            {corpus.PATH: "steering/", corpus.HOLDS: a_class(), FLAG: MARKED,
             corpus.READ_WHEN: [TRIGGER]},
            {corpus.PATH: "papers/", corpus.HOLDS: a_class(),
             corpus.WRITER: VOCABULARY["writers"][0]["id"],
             corpus.LIFECYCLE: VOCABULARY["lifecycles"][0]["id"]},
        ],
    }, indent=2) + "\n", encoding="utf-8", newline="\n")
    for rel, text in {
        "steering/POSITION.md": "# where the work stands\n\n[onward](../papers/one.md)\n",
        "papers/one.md": "# reached at one hop\n",
        "papers/two.md": "# reached by nothing\n",
    }.items():
        whole = host / rel
        whole.parent.mkdir(parents=True, exist_ok=True)
        whole.write_text(text, encoding="utf-8", newline="\n")


class Navigation(Fixtures, unittest.TestCase):

    def test_an_unmapped_host_gets_both_pages_and_they_say_nothing_was_read(self):
        host = self.installed()
        for target in PAGES:
            page = (host / target)
            self.assertTrue(page.exists(), f"{target} was not projected into an unmapped host")
            text = page.read_text(encoding="utf-8")
            self.assertIn("NOTHING WAS READ", text,
                          f"{target} rendered as an empty catalog rather than as a page about a "
                          f"corpus nobody has mapped")
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode,
                         "a host with no corpus map is not green")

    def test_a_mapped_host_gets_its_places_its_triggers_and_stays_green(self):
        host = self.installed()
        mapped(host)
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode, "render refused a map")

        pages = {target: (host / target).read_text(encoding="utf-8") for target in PAGES}
        whole = "\n".join(pages.values())
        for place in ("steering/", "papers/"):
            self.assertIn(place, whole, f"the declared place {place!r} reached neither page")
        self.assertIn(TRIGGER, whole, "a declared retrieval trigger reached no page")
        self.assertNotIn("NOTHING WAS READ", whole, "a mapped corpus reported as unread")
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode,
                         "a projection refused something -- a projection is not a gate")

    def test_a_hand_edited_page_is_refused(self):
        host = self.installed()
        mapped(host)
        self.run_kit(KIT, host, "render")
        edited = host / PAGES[0]
        edited.write_text(edited.read_text(encoding="utf-8") + "\nA line somebody added.\n",
                          encoding="utf-8", newline="\n")

        result = self.run_kit(KIT, host, "check")
        self.assertNotEqual(0, result.returncode, "an edited navigation page passed check")
        self.assertIn(PAGES[0], result.stdout + result.stderr,
                      "the refusal does not name the page that was edited")

    def test_rendered_twice_the_pages_are_byte_identical(self):
        host = self.installed()
        mapped(host)
        self.run_kit(KIT, host, "render")
        first = {target: (host / target).read_bytes() for target in PAGES}
        self.run_kit(KIT, host, "render")

        self.assertEqual(first, {target: (host / target).read_bytes() for target in PAGES},
                         "a page rendered twice produced different bytes -- a clock, or an order "
                         "nobody declared")


if __name__ == "__main__":
    unittest.main()
