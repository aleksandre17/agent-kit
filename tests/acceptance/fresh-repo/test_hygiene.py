"""Acceptance: hygiene -- a SENSOR over the installed surface, that names and never removes.

Everything proved before this suite concerns what the kit WRITES. Hygiene is the first capability
whose subject is what merely ENDS UP somewhere: a folder named after how its contents were made, a
release record vendored into a host that never ran those versions, a chapter of dead doctrine no
reader can date. The layout study ruled those out by name; until now that ruling was prose, and
prose gates nothing.

So the five things this suite exists to prove are the five a scanner most often fails:

  1. every declared rule proves what it SEES and states what it TOLERATES, before it is believed;
  2. an uncalibrated rule stops the scan -- the tree is not read on the word of an unmeasured sensor;
  3. a planted instance of every declared genre is NAMED, and the lookalike beside it is not;
  4. a red gate removed nothing -- not one byte of the host moved;
  5. a host may declare a genre of its own, and it costs the interpreter nothing.

Nothing here restates the kit's genres. The rules are READ from the declaration and the suite is
driven by them, because a test that carries its own copy of the default set stops measuring the
kit and starts agreeing with a snapshot of it.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from harness import KIT, Fixtures, host_digest, sha

#: The one place this suite learns what hygiene declares.
RESIDENCE = json.loads(
    (KIT / "capabilities/hygiene/residence.json").read_text(encoding="utf-8"))
LOCAL = ".agents/project/hygiene/residence.json"
PROJECTION = ".agents/generated/hygiene/RESIDENCE.md"

INTERPRETERS = KIT / "interpreters"


def rules() -> list:
    return RESIDENCE["genres"]


def interpreter_sources() -> list:
    return sorted(p for p in INTERPRETERS.rglob("*.py"))


def interpreter_digest() -> dict:
    return {p.relative_to(KIT).as_posix(): sha(p) for p in interpreter_sources()}


class Hygiene(Fixtures, unittest.TestCase):

    # -- authoring -----------------------------------------------------------------------------
    def plant(self, host: Path, rel: str) -> Path:
        """A file as it ARRIVES in a host: put somewhere plausible by someone who meant well.
        Nothing in the kit ever writes one of these -- that is why a sensor is needed at all."""
        path = host / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {Path(rel).name}\n\nput here by a host, in good faith.\n",
                        encoding="utf-8")
        return path

    def declare_locally(self, host: Path, genre: dict) -> None:
        document = json.loads((host / LOCAL).read_text(encoding="utf-8"))
        document["genres"].append(genre)
        (host / LOCAL).write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    # == 1. the sensor is measured before it is believed ========================================
    def test_61_every_declared_rule_carries_the_proof_of_what_it_sees(self):
        """The calibration is in the DECLARATION, not in this file. Each rule states one path it
        must catch and one lookalike it must let through; a rule that cannot do both has no
        measured edge, and a rule with no edge eventually names everything."""
        self.assertTrue(rules(), "a hygiene capability that declares no rule gates nothing")
        for rule in rules():
            pattern = re.compile(rule["pattern"])
            self.assertTrue(pattern.search(rule["proves"]),
                            f"{rule['id']} cannot see {rule['proves']!r}, which it claims to catch")
            self.assertIsNone(pattern.search(rule["admits"]),
                              f"{rule['id']} also catches {rule['admits']!r}, which it tolerates")
        self.assertEqual(0, self.run_kit(KIT, self.installed(), "check").returncode,
                         "a fresh host carries none of these genres and must be green")

    def test_62_an_uncalibrated_rule_stops_the_scan_instead_of_reporting_on_its_word(self):
        """The failure this project has already paid for: a sensor trusted before it was measured,
        recording confidently about a world it was never pointed at. A rule whose pattern no longer
        sees its own evidence is itself the finding -- and the tree is not scanned at all, which is
        proved by planting a genuine instance of ANOTHER genre and watching it go unmentioned."""
        blinded, witness = rules()[0], rules()[1]

        def blind_the_first_rule(kit: Path):
            self.edit_json(kit, "capabilities/hygiene/residence.json",
                           lambda doc: doc["genres"][0].__setitem__(
                               "pattern", "(^|/)nothing-of-this-name-exists/"))

        # The host is installed by the CALIBRATED kit and then met by the blinded one: an `init`
        # ends in `check`, so a kit whose sensor cannot prove itself can never finish an install
        # -- which is itself the right outcome, and would leave nothing to observe here.
        kit = self.fixture_kit("uncalibrated", blind_the_first_rule)
        host = self.installed()
        self.assertEqual(0, self.run_kit(kit, host, "render").returncode)
        self.plant(host, witness["proves"])

        result = self.run_kit(kit, host, "check")
        self.assertEqual(1, result.returncode)
        self.assertIn("FAIL  FF-RESIDENCE", result.stdout)
        self.assertIn("UNCALIBRATED", result.stdout)
        self.assertIn(blinded["id"], result.stdout)
        self.assertNotIn(witness["proves"], result.stdout,
                         "the tree was scanned on the word of a sensor that had not proved itself")

    # == 2. the bite, driven by the declaration =================================================
    def test_63_every_declared_genre_is_named_where_it_sits_and_its_lookalike_is_not(self):
        """Both halves, for every rule the kit ships: the thing it exists to catch is caught by
        name and told where it belongs, and the lookalike beside it passes untouched. A scanner
        proved only on what it flags is not proved -- the interesting half is what it lets be."""
        for rule in rules():
            with self.subTest(genre=rule["id"]):
                host = self.installed()

                self.plant(host, rule["admits"])
                self.assertEqual(0, self.run_kit(KIT, host, "check").returncode,
                                 f"{rule['id']} named {rule['admits']}, which it declares legitimate")

                self.plant(host, rule["proves"])
                caught = self.run_kit(KIT, host, "check")
                self.assertEqual(1, caught.returncode)
                self.assertIn("FAIL  FF-RESIDENCE", caught.stdout)
                self.assertIn(rule["proves"], caught.stdout)
                self.assertIn(rule["id"], caught.stdout)
                self.assertIn(rule["instead"], caught.stdout,
                              "a finding that says only NO tells an operator nothing")
                self.assertNotIn(rule["admits"], caught.stdout)

    def test_64_a_red_residence_gate_removed_nothing(self):
        """The rule that made this capability a sensor and not a broom. The gate runs, goes red,
        names what it found -- and every byte of the host is where it was. A deletion is a decision,
        a decision has an author, and no machine may be that author."""
        host = self.installed()
        planted = [self.plant(host, rule["proves"]) for rule in rules()]
        before = host_digest(host)

        result = self.run_kit(KIT, host, "check")
        self.assertEqual(1, result.returncode)
        for rule in rules():
            self.assertIn(rule["proves"], result.stdout, "a finding was dropped from the report")
        for path in planted:
            self.assertTrue(path.is_file(), "the gate removed what it was only asked to name")
        self.assertEqual(before, host_digest(host),
                         "a reporting gate moved a byte, which is a machine deciding")

    # == 3. the host's own rules, and the interpreter's silence =================================
    def test_65_a_host_may_declare_a_genre_of_its_own_with_no_interpreter_edit(self):
        """The proof slices B, C and D each earned again, in hygiene's vocabulary: a genre this
        kit never heard of bites, because a rule is a row in a document the HOST owns.

        `render` is run before `check` on purpose. The projection over a host-authored declaration
        is stale the instant the host authors, and only `render` closes it -- honest, and still an
        edge a host meets without being told about it."""
        before = interpreter_digest()
        host = self.installed()
        self.declare_locally(host, {
            "id": "host-scratch-notes",
            "pattern": "(^|/)scratch/",
            "because": "this host keeps working notes that outlive their moment and bind nobody.",
            "instead": "in the record the work is actually kept in.",
            "proves": ".agents/project/scratch/thought.md",
            "admits": ".agents/project/knowledge/scratching-the-surface.md",
        })
        self.plant(host, ".agents/project/scratch/thought.md")
        self.plant(host, ".agents/project/knowledge/scratching-the-surface.md")
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)

        result = self.run_kit(KIT, host, "check")
        self.assertEqual(1, result.returncode)
        self.assertIn("host-scratch-notes", result.stdout)
        self.assertIn(".agents/project/scratch/thought.md", result.stdout)
        self.assertNotIn("scratching-the-surface", result.stdout)
        self.assertEqual(before, interpreter_digest(),
                         "a host's own rule cost an interpreter edit, so the rule is not declared")

    def test_66_no_interpreter_module_names_a_declared_genre(self):
        """The fitness function under the slice. A genre spelled in the machine's own source is a
        judgement with two homes, and the one a host can change is no longer the one that decides."""
        offenders = []
        for path in interpreter_sources():
            text = path.read_text(encoding="utf-8")
            for rule in rules():
                for spelling in (rule["id"], rule["pattern"]):
                    if re.search(rf"""['"]{re.escape(spelling)}['"]""", text):
                        offenders.append(f"{path.relative_to(KIT).as_posix()} names {spelling!r}")
        self.assertEqual([], offenders,
                         "an interpreter that spells a genre is an interpreter that decides")

    # == 4. the surface says what is being held =================================================
    def test_67_the_projection_states_both_planes_and_declares_the_empty_one(self):
        """Capability discovery, and Cardinal V at the surface: a host that has declared no rules
        of its own reads that as a DECLARED state, never as a blank; the moment it declares one,
        the same page carries it beside the kit's."""
        host = self.installed()
        page = (host / PROJECTION).read_text(encoding="utf-8")
        for rule in rules():
            self.assertIn(f"### {rule['id']}", page)
            self.assertIn(rule["pattern"], page)
            self.assertIn(rule["instead"], page)
        self.assertIn("declared no residence rules of its own", page,
                      "an empty host plane must read as a state, not as a missing section")

        self.declare_locally(host, {
            "id": "host-declared-genre", "pattern": "(^|/)nowhere/",
            "because": "this host says so.", "instead": "somewhere it is read.",
            "proves": ".agents/project/nowhere/a.md", "admits": ".agents/project/nowhere-near.md",
        })
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        page = (host / PROJECTION).read_text(encoding="utf-8")
        self.assertIn("### host-declared-genre", page)
        self.assertNotIn("declared no residence rules of its own", page)
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode,
                         "a declared-but-unbroken rule is not a finding")
