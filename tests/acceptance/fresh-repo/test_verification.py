"""Acceptance: a capability CONSUMES a fact, and the surface it projects cannot lie about it.

Until this slice the kit measured and nobody read: every fact in the profile was produced,
recorded, dated -- and consumed by nothing. Three readings are walked here, and each is a
different way for a consuming surface to become false:

  1. **The host that declares the thing.** The projection must carry the value the host ITSELF
     spelled, with the moment it was read beside it. A page that printed a command this kit chose
     would be publishing a method of proof into a host that never picked one.

  2. **The host that declares nothing.** The projection must say so IN THE WORDS THE DECLARATION
     AUTHORED, and `check` must stay green: an absence is a legal state, and the one thing that
     may never happen is an empty section, a plausible default, or a silent skip -- each of which
     reads exactly like a host that is fine.

  3. **The record and the tree disagreeing.** `check` must REPORT it, with both values and both
     moments, and must change NEITHER: not the profile, not the page. A reading that quietly
     updates itself destroys the only evidence that anything moved.

And one sensor on the declaration itself: a row naming a fact no detector can emit would print
its gap on every host forever, indistinguishable from an honest absence.

Nothing here names a fact, a detector, a file, a page or a command. The consuming capability is
found by the block it declares, its rows are read from the document it ships, the fixture host is
MATERIALISED from the evidence of whichever detector emits the fact the row names, and the words
asserted are the declaration's own. A test that spelled any of them would go on passing after the
declaration had moved.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from harness import KIT, Fixtures
from manifest import Manifest
from test_detectors import materialise

MANIFEST = Manifest(KIT)

#: The capability that consumes a reading, found by the block it declares -- never by its name.
CONSUMER = next(c for c in MANIFEST.capabilities if c.raw.get("consumes"))
CONSUMES = CONSUMER.raw["consumes"]
ROWS = [row for name in CONSUMES["sources"] for row in CONSUMER.documents[name][CONSUMES["list"]]]

#: Where the host's own reading is recorded, and which plane the surfaces are projected into --
#: both read from the declarations that own them.
READING = next(i["target"] for c in MANIFEST.capabilities for i in c.installs
               if i["mode"] == "reading")
PROJECTED = next(p["root"] for p in MANIFEST.planes if p["class"] == "projection")


def detector_emitting(fact: str) -> dict:
    """The declared detector that emits this fact. A row consuming a fact nothing emits is the
    defect a gate in this kit judges; this suite asserts on a row that can actually be bound."""
    return next(d for d in MANIFEST.detectors if fact in d["emits"])


def evidence_for(fact: str) -> dict:
    """The one evidence item whose capture becomes this fact -- located through the detector's own
    `$N` capture declaration, so this suite never spells a path, a pointer or a kind."""
    detector = detector_emitting(fact)
    index = int(str(detector["emits"][fact]).lstrip("$")) - 1
    return detector["evidence"][index]


def respell(root: Path, fact: str, value: str) -> None:
    """Rewrite, in the host's own tree, the thing the fact is read from -- the tree moving under a
    recorded reading, which is the whole of what drift is."""
    spec = evidence_for(fact)
    if spec["kind"] != "json_path":  # pragma: no cover -- the walked row's evidence is this kind
        raise AssertionError(f"this suite cannot respell evidence of kind {spec['kind']!r}")
    target = root / spec["path"]
    value_tree = json.loads(target.read_text(encoding="utf-8"))
    cursor = value_tree
    steps = spec["pointer"].split(".")
    for step in steps[:-1]:
        cursor = cursor.setdefault(step, {})
    cursor[steps[-1]] = value
    target.write_text(json.dumps(value_tree, indent=2) + "\n", encoding="utf-8", newline="\n")


def surface(host: Path) -> str:
    """Every byte this host projects, as one text. WHICH page carries a reading is the
    declaration's business; that the surface states it, and states it honestly, is this suite's."""
    plane = host / PROJECTED
    return "\n".join(path.read_text(encoding="utf-8")
                     for path in sorted(plane.rglob("*")) if path.is_file())


class ConsumedReadings(Fixtures, unittest.TestCase):

    @classmethod
    def installed_on(cls, prepare=None, kit: Path = KIT) -> Path:
        host = cls.host()
        if prepare:
            prepare(host)
        drafted = cls.run_kit(kit, host, "init")
        assert drafted.returncode == 3, f"init did not stall at the door: {drafted.stderr}"
        approved = cls.run_kit(kit, host, "init", "--approve", "acceptance-suite")
        assert approved.returncode == 0, f"an approved init did not install: {approved.stderr}"
        return host

    def recorded(self, host: Path) -> dict:
        return json.loads((host / READING).read_text(encoding="utf-8"))

    # -- 1. the host that declares it ---------------------------------------------------------
    def test_a_host_that_declares_the_thing_is_projected_saying_what_it_declared(self):
        for row in ROWS:
            with self.subTest(reading=row["id"]):
                fact = row[CONSUMES["names"]]
                host = self.installed_on(
                    lambda root, fact=fact: materialise(root, detector_emitting(fact)))
                reading = self.recorded(host)
                self.assertIn(fact, reading["facts"],
                              "a tree built from the detector's own evidence emitted nothing")
                projected = surface(host)
                self.assertIn(str(reading["facts"][fact]), projected,
                              "the surface does not carry the value the host itself declared")
                self.assertIn(reading["taken_at"], projected,
                              "the surface states a measured value without the moment it was read")
                self.assertNotIn(row["gap"], projected,
                                 "a bound reading was ALSO projected as a declared gap")
                self.assertEqual(0, self.run_kit(KIT, host, "check").returncode,
                                 "a host that declares the thing is not green")

    # -- 2. the host that declares nothing ----------------------------------------------------
    def test_a_host_that_declares_nothing_gets_a_gap_that_says_so_and_stays_green(self):
        host = self.installed_on()
        projected = surface(host)
        for row in ROWS:
            with self.subTest(reading=row["id"]):
                fact = row[CONSUMES["names"]]
                self.assertNotIn(fact, self.recorded(host)["facts"],
                                 "a bare host emitted the fact anyway; this walk proves nothing")
                self.assertIn(row["gap"], projected,
                              "an absence was projected as something other than its declared gap")
                self.assertIn(row["means"], projected,
                              "the reading that is missing is not even named on the surface")
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode,
                         "an honest absence was treated as a failure")

    # -- 3. the record and the tree disagreeing -----------------------------------------------
    def test_check_reports_a_reading_that_the_tree_no_longer_agrees_with_and_repairs_nothing(self):
        row = ROWS[0]
        fact = row[CONSUMES["names"]]
        host = self.installed_on(lambda root: materialise(root, detector_emitting(fact)))
        reading = self.recorded(host)
        was = str(reading["facts"][fact])
        moved = was + "-moved"
        respell(host, fact, moved)

        record_before = (host / READING).read_bytes()
        surface_before = surface(host)
        checked = self.run_kit(KIT, host, "check")
        said = checked.stdout + checked.stderr

        self.assertNotEqual(0, checked.returncode, "a reading the tree contradicts passed silently")
        self.assertIn(was, said, "the drift report does not carry the value that was recorded")
        self.assertIn(moved, said, "the drift report does not carry the value the tree now says")
        self.assertIn(reading["taken_at"], said,
                      "the drift report does not state when the recorded reading was taken")
        self.assertEqual(record_before, (host / READING).read_bytes(),
                         "the recorded reading was rewritten by the act of reporting it")
        self.assertEqual(surface_before, surface(host),
                         "the surface was re-rendered from a probe nobody recorded")
        self.assertIn(was, surface(host),
                      "the projection quietly followed the tree instead of its recorded reading")

    # -- the sensor on the declaration itself -------------------------------------------------
    def test_a_row_consuming_a_fact_no_detector_emits_is_refused_and_named(self):
        source = next(d["source"] for d in CONSUMER.raw["documents"]
                      if d["id"] == CONSUMES["sources"][0])
        unknown = "a.fact.no.detector.emits"

        def unbindable(document):
            document[CONSUMES["list"]][0][CONSUMES["names"]] = unknown

        kit = self.fixture_kit("unbindable-consumption",
                               patch=lambda k: self.edit_json(k, source, unbindable))
        host = self.host()
        self.assertEqual(3, self.run_kit(kit, host, "init").returncode,
                         "init did not stall at the door")
        # The refusal arrives at the FIRST reading this kit takes of a host -- the check that
        # closes the install -- rather than being carried silently into a rendered surface.
        refused = self.run_kit(kit, host, "init", "--approve", "acceptance-suite")
        said = refused.stdout + refused.stderr
        self.assertNotEqual(0, refused.returncode,
                            "a consumption nothing can ever satisfy was read as an honest gap")
        checked = self.run_kit(kit, host, "check")
        said += checked.stdout + checked.stderr
        self.assertNotEqual(0, checked.returncode,
                            "the refusal did not survive into a later reading of the same host")
        self.assertIn(unknown, said, "the refusal does not name the fact nobody emits")
        self.assertIn(ROWS[0]["id"], said, "the refusal does not name the row that cannot bind")


if __name__ == "__main__":
    unittest.main()
