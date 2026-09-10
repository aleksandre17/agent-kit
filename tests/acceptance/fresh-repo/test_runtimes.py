"""Acceptance: runtimes -- a tool that is DECLARED, and a claim that can never become a fact.

The subject is the thing a host actually executes its agents on, and the failure under test is
not a missing feature. It is a BELIEF THAT READS AS A MEASUREMENT. A runtime's capabilities get
written down once, in a file somebody trusted, and from then on every reader takes them as
observed -- until the day one of them is exercised for real and turns out to have been assumed.
That has already happened here: an invocation shape was assumed, and a peer runtime later
reported all eight of its claimed capabilities as unproven and was right about every one.

So these tests are about what the surface CANNOT say:

  1. a host that runs nothing says so, and projects nothing -- the zero occupies space;
  2. a descriptor carries the class's body although no host file contains it;
  3. every declared capability is PLACED, for every runtime, in exactly one of three groups --
     nothing is omitted, because a short list of claims and a tool that needs nothing read
     identically to anyone shown only what is present;
  4. a claim cannot become a proof by being written confidently -- there is no field it could be
     written in, and the empty PROVEN group states that no instrument exists rather than printing
     a zero that would read as a measurement;
  5. a claim in a word nobody declared fails a gate, which is what keeps the absences countable;
  6. a descriptor naming a class nobody declares renders UNBOUND and fails a gate;
  7. a descriptor that restates the class's body is refused at the boundary, by the schema;
  8. the accounting FOLLOWS the vocabulary -- a word added to the one declaration re-places every
     runtime, which is the only evidence that rules out a copy;
  9. a runtime with no shipped ancestor is the same grammar, not an exception to it.

Nothing here restates what the kit declares. Every path, field name and state word is read from
the declaration or the module that owns it -- a test carrying its own copy of the vocabulary
stops measuring the kit and starts agreeing with a snapshot of it.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import composition

from harness import KIT, Fixtures

CAPABILITY = json.loads((KIT / "capabilities/runtimes/capability.json").read_text(encoding="utf-8"))
CLASSES = json.loads((KIT / "capabilities/runtimes/classes.json").read_text(encoding="utf-8"))
RUNTIME_SCHEMA = json.loads((KIT / "schemas/runtime.schema.json").read_text(encoding="utf-8"))

SPEC = CAPABILITY["composes"]
BASE_FIELD = SPEC["base"]["named_by"]
BASE_LIST = SPEC["base"]["list"]
SHARED_LIST = SPEC["shared"]["list"]
ACCOUNTS = SPEC["accounts"]
VOCABULARY = ACCOUNTS["vocabulary"]["list"]
CLAIMS_FIELD = ACCOUNTS["claimed"]["field"]
CLAIMS_NAMES = ACCOUNTS["claimed"]["names"]

#: The gate ids, read from the declarations that own them rather than spelled here.
GATES = {gate["params"]["references"][0]["field"]: gate["id"] for gate in CAPABILITY["gates"]}
CLASS_GATE = GATES[BASE_FIELD]
CLAIM_GATE = GATES[CLAIMS_FIELD]

SCHEMA_VERSION = 1


def install_named(name: str) -> dict:
    found = [item for item in CAPABILITY["installs"]
             if item.get("reads_as") == name or item["target"].endswith(name)]
    assert len(found) == 1, f"{name} does not resolve to exactly one install: {found}"
    return found[0]


DESCRIPTORS = install_named("runtime_descriptors")["target"]
HOST_CLASSES = install_named("host_runtime_classes")["target"]
ROLL = install_named("RUNTIMES.md")["target"]
EACH = [item for item in CAPABILITY["installs"] if item.get("each")][0]
PLANE = EACH["target"]
SUFFIX = EACH["each"].get("suffix", "")


def a_shipped_class() -> dict:
    """One class the kit declares. Which one is not the point and is never named here."""
    return CLASSES[BASE_LIST][0]


def a_shipped_capability() -> dict:
    return CLASSES[VOCABULARY][0]


class Runtimes(Fixtures, unittest.TestCase):

    # -- authoring, as a host does it -------------------------------------------------------
    def descriptor(self, host: Path, **fields) -> Path:
        record = {"schema_version": SCHEMA_VERSION, **fields}
        path = host / DESCRIPTORS / f"{record['id']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        return path

    def host_registry(self, host: Path, classes=(), capabilities=(), protocol=()) -> None:
        (host / HOST_CLASSES).write_text(json.dumps({
            "schema_version": SCHEMA_VERSION,
            SHARED_LIST: list(protocol),
            VOCABULARY: list(capabilities),
            BASE_LIST: list(classes),
        }, indent=2) + "\n", encoding="utf-8")

    def page(self, host: Path, runtime: str) -> str:
        return (host / PLANE.rstrip("/") / f"{runtime}{SUFFIX}").read_text(encoding="utf-8")

    def rendered(self, host: Path):
        result = self.run_kit(KIT, host, "render")
        self.assertEqual(0, result.returncode, result.stderr)
        return result

    # -- 1. the zero ------------------------------------------------------------------------
    def test_100_a_host_that_runs_nothing_says_so_and_projects_nothing(self):
        """A page that simply ended would read exactly like a page whose runtimes failed to
        render, so the roll states the absence in words -- and the plane holds nothing, which is
        the same fact told by the filesystem. The honest absence is a PASSING state."""
        host = self.installed()
        roll = (host / ROLL).read_text(encoding="utf-8")
        self.assertIn("declared no runtime", roll)
        plane = host / PLANE.rstrip("/")
        self.assertEqual([], sorted(p.name for p in plane.glob("*")) if plane.exists() else [])

        checked = self.run_kit(KIT, host, "check")
        self.assertEqual(0, checked.returncode, checked.stdout)
        for gate in (CLASS_GATE, CLAIM_GATE):
            self.assertIn(f"PASS  {gate}", checked.stdout)

    # -- 2. the body arrives from somewhere no host file holds -------------------------------
    def test_101_a_descriptor_carries_a_class_body_that_exists_in_no_file_the_host_authored(self):
        """The composition, and the proof that it IS one: the class's reach and the translation
        it declares reach the page, and appear in nothing the host wrote."""
        host = self.installed()
        base = a_shipped_class()
        self.descriptor(host, id="the-tool-this-host-runs", **{BASE_FIELD: base["id"]})
        self.rendered(host)

        page = self.page(host, "the-tool-this-host-runs")
        self.assertIn(base["reach"], page)
        self.assertIn(base["boundary"], page)
        for exemplar in base["reference_class"]:
            self.assertIn(exemplar, page)

        authored = [path for path in (host / ".agents/project").rglob("*") if path.is_file()]
        self.assertTrue(authored, "the binding plane is empty; this assertion would be vacuous")
        for path in authored:
            self.assertNotIn(base["reach"], path.read_text(encoding="utf-8"),
                             f"{path.name} holds a second home for the class's body")

    # -- 3. every declared capability is placed ----------------------------------------------
    def test_102_every_declared_capability_is_placed_and_none_is_omitted(self):
        """The accounting. One capability is claimed; every other declared word is ABSENT and is
        NAMED as such. The count is the measurement -- claimed plus proven plus absent is the
        whole vocabulary, always -- because a surface that showed only what was claimed would
        make a tool nobody has asked about indistinguishable from one that needs nothing."""
        host = self.installed()
        base = a_shipped_class()
        claimed = a_shipped_capability()
        believed = "the only reason this host has for believing it"
        self.descriptor(host, id="a-tool-with-one-claim", **{
            BASE_FIELD: base["id"],
            CLAIMS_FIELD: [{CLAIMS_NAMES: claimed["id"], "says": believed}],
        })
        self.rendered(host)

        page = self.page(host, "a-tool-with-one-claim")
        declared = CLASSES[VOCABULARY]
        for capability in declared:
            self.assertIn(capability["id"], page,
                          "a declared capability was omitted from the page, which is the one "
                          "thing an absence may never be")
        self.assertIn(believed, page, "the host's own words did not reach the surface")
        self.assertIn(claimed["observed_by"], page,
                      "a claim was rendered without what would have to happen to prove it")

        self.assertIn(f"{composition.CLAIMED.capitalize()} — 1 of {len(declared)}", page)
        self.assertIn(f"{composition.ABSENT.capitalize()} — {len(declared) - 1} of {len(declared)}",
                      page)
        self.assertIn(f"{composition.PROVEN.capitalize()} — 0 of {len(declared)}", page)

        roll = (host / ROLL).read_text(encoding="utf-8")
        self.assertIn(f"claimed 1, proven 0, absent {len(declared) - 1}", roll)

    # -- 4. a claim cannot become a proof ----------------------------------------------------
    def test_103_a_claim_cannot_become_a_proof_by_being_written_confidently(self):
        """The closure by ABSENCE, asserted where it lives. The descriptor schema declares no
        field in which an observation could be written and refuses what it did not declare, so
        the strongest thing an authored file can say is that somebody believes it.

        And the zero that follows is not printed as a measurement: with no record anywhere naming
        a runtime and a capability together, the page says that no source of proof exists at all.
        A count taken where there is no instrument is an attribution that cannot fail.
        """
        writable = set(RUNTIME_SCHEMA["properties"])
        for word in ("proven", "verified", "observed", "tested_at", "status", "proof"):
            self.assertNotIn(word, writable,
                             "the descriptor schema has a field a host could write a proof in")
        self.assertFalse(RUNTIME_SCHEMA["additionalProperties"],
                         "a descriptor open to undeclared properties can be given one")

        host = self.installed()
        declared = CLASSES[VOCABULARY]
        self.descriptor(host, id="a-tool-that-claims-everything", **{
            BASE_FIELD: a_shipped_class()["id"],
            CLAIMS_FIELD: [{CLAIMS_NAMES: capability["id"], "says": "stated with total confidence"}
                           for capability in declared],
        })
        self.rendered(host)

        page = self.page(host, "a-tool-that-claims-everything")
        self.assertIn(f"{composition.CLAIMED.capitalize()} — {len(declared)} of {len(declared)}",
                      page)
        self.assertIn(f"{composition.PROVEN.capitalize()} — 0 of {len(declared)}", page)
        self.assertIn("no source of proof is declared at all", page)
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode)

    # -- 5. a word nobody declared -----------------------------------------------------------
    def test_104_a_claim_in_a_word_nobody_declared_fails_a_gate_with_a_measured_edge(self):
        """What keeps an absence countable. A claim outside the vocabulary belongs to no column,
        so the count of what a runtime does not claim would go on reading as complete while being
        wrong -- and the reading would be wrong in the direction of reassurance."""
        host = self.installed()
        self.descriptor(host, id="a-tool-with-a-private-word", **{
            BASE_FIELD: a_shipped_class()["id"],
            CLAIMS_FIELD: [{CLAIMS_NAMES: "a-capability-nobody-declared",
                            "says": "invented in passing and never declared"}],
        })
        self.rendered(host)

        checked = self.run_kit(KIT, host, "check")
        self.assertEqual(1, checked.returncode)
        self.assertIn(f"FAIL  {CLAIM_GATE}", checked.stdout)
        self.assertIn("a-capability-nobody-declared", checked.stdout)

        # ... and the sensor's other edge: a claim in a declared word is not flagged, so the gate
        # has a measured edge rather than a habit of naming everything.
        self.descriptor(host, id="a-tool-with-a-declared-word", **{
            BASE_FIELD: a_shipped_class()["id"],
            CLAIMS_FIELD: [{CLAIMS_NAMES: a_shipped_capability()["id"], "says": "believed"}],
        })
        self.rendered(host)
        again = self.run_kit(KIT, host, "check")
        self.assertNotIn("a-tool-with-a-declared-word", again.stdout)

    # -- 6. a descriptor whose class is gone -------------------------------------------------
    def test_105_a_descriptor_naming_a_class_nobody_declares_renders_unbound_and_fails_a_gate(self):
        """Two readings of one fact, taken independently. The SURFACE says UNBOUND in words,
        because a descriptor alone reads exactly like a complete account of a runtime; the GATE
        says it with an exit code."""
        host = self.installed()
        self.descriptor(host, id="a-tool-whose-class-was-renamed",
                        **{BASE_FIELD: "a-class-nobody-declares"})
        self.rendered(host)

        page = self.page(host, "a-tool-whose-class-was-renamed")
        self.assertIn("UNBOUND", page)
        self.assertIn("a-class-nobody-declares", page)

        checked = self.run_kit(KIT, host, "check")
        self.assertEqual(1, checked.returncode)
        self.assertIn(f"FAIL  {CLASS_GATE}", checked.stdout)
        self.assertIn("a-tool-whose-class-was-renamed", checked.stdout)

        # ... and an UNBOUND runtime is still accounted: a page with no body would otherwise be a
        # page with no capabilities either, which reads as a tool that needs nothing.
        self.assertIn(f"of {len(CLASSES[VOCABULARY])}", page)

    # -- 7. the second body cannot be written ------------------------------------------------
    def test_106_a_descriptor_that_restates_the_class_body_is_refused_at_the_boundary(self):
        """The structural half. A host does not merely *should not* restate what a class says --
        the descriptor schema declares none of the class's vocabulary and refuses what it did not
        declare, so the two-homes state cannot be expressed. Asserted against the schema, so the
        closure is provably the reason, and against a run, so it is provably enforced."""
        declared = set(RUNTIME_SCHEMA["properties"])
        forbidden = set(a_shipped_class()) - {"id"}
        self.assertFalse(declared & forbidden,
                         "the descriptor schema shares vocabulary with the class it composes")

        host = self.installed()
        base = a_shipped_class()
        smuggled = sorted(forbidden)[0]
        self.descriptor(host, id="a-tool-with-opinions",
                        **{BASE_FIELD: base["id"], smuggled: base[smuggled]})
        result = self.run_kit(KIT, host, "render")
        self.assertNotEqual(0, result.returncode)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn(smuggled, result.stderr)

    # -- 8. the accounting follows the declaration -------------------------------------------
    def test_107_a_word_added_to_the_vocabulary_re_places_every_runtime_at_once(self):
        """The cure, measured. Presence alone would prove nothing -- a copy of the vocabulary in
        each descriptor looks identical from here. Only the MOVE distinguishes a projection from
        a duplicate: a capability nobody had heard of is declared once, and every runtime's
        absence count rises without a single descriptor being touched."""
        host = self.installed()
        base = a_shipped_class()
        for runtime in ("one-tool", "another-tool"):
            self.descriptor(host, id=runtime, **{BASE_FIELD: base["id"]})
        self.rendered(host)
        before = len(CLASSES[VOCABULARY])
        for runtime in ("one-tool", "another-tool"):
            self.assertIn(f"{composition.ABSENT.capitalize()} — {before} of {before}",
                          self.page(host, runtime))

        widened = {
            "id": "a-capability-only-this-host-cares-about",
            "means": "the one thing this repository needs to know about any tool it runs",
            "observed_by": "a run in which it is exercised and the reading is kept",
        }
        self.host_registry(host, capabilities=[widened])
        self.rendered(host)
        for runtime in ("one-tool", "another-tool"):
            page = self.page(host, runtime)
            self.assertIn(f"{composition.ABSENT.capitalize()} — {before + 1} of {before + 1}",
                          page, f"{runtime} did not follow the vocabulary it is supposed to "
                                f"project")
            self.assertIn(widened["id"], page)
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode)

    # -- 9. a runtime with no shipped ancestor -----------------------------------------------
    def test_108_a_host_declared_runtime_class_is_the_same_grammar_and_not_an_exception(self):
        """A kind of tool the kit never anticipated is not a special case: the host declares a
        class of its own, in the same shape, and a descriptor names it. And the same two-home
        defect one level up is refused -- an id declared by BOTH the kit and the host is not
        ordered by precedence, because whichever lost would go on reading as true."""
        host = self.installed()
        mine = {
            "id": "a-kind-of-tool-only-this-repository-runs",
            "reach": "reached in a way nobody outside this repository has to understand",
            "boundary": "whatever this repository has already measured about that gap",
            "reference_class": ["the mechanism this host has already proved works"],
        }
        self.host_registry(host, classes=[mine])
        self.descriptor(host, id="the-local-tool", **{BASE_FIELD: mine["id"]})
        self.rendered(host)

        page = self.page(host, "the-local-tool")
        self.assertIn(mine["reach"], page)
        self.assertNotIn("UNBOUND", page)
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode)

        self.host_registry(host, classes=[dict(a_shipped_class())])
        clash = self.run_kit(KIT, host, "render")
        self.assertNotEqual(0, clash.returncode)
        self.assertNotIn("Traceback", clash.stderr)
        self.assertIn(a_shipped_class()["id"], clash.stderr)
        self.assertIn("two homes for one judgement", clash.stderr)
