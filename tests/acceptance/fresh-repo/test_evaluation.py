"""Acceptance: evaluation -- whether it HIT, and the one thing a framework may say about that.

Every capability before this one measures something the framework can see for itself: a path, a
name, a record's own shape. This one is about a question the framework is structurally forbidden
to answer. Whether an answer was any good is a property of a domain, and no domain has ever been
handed to this kit -- so the whole slice is an exercise in shipping a GRAMMAR and refusing a
verdict, and the tests exist mostly to prove that the refusal held.

The eight things proved here are the eight an evaluation layer most often gets wrong:

  1. the sensors are calibrated, and they were pointed at a set that is not empty;
  2. the ZERO MEASURE is stated in those words -- on the projection and by the verb -- and a host
     that has judged something is DISTINGUISHABLE from one that never has, which is the single
     distinction this capability exists for;
  3. the blank is opened before anything judges, is idempotent, and a verdict is never overwritten;
  4. a verdict that cannot say who reached it, or when, is named -- and nothing is removed;
  5. a judgement pointing at something the host does not declare is named, and the lookalike
     beside it is not;
  6. a host may declare a reading of its own and it costs the interpreter nothing;
  7. the kit ships no case, no rubric, no criterion and no verdict -- T2, pointed at this slice;
  8. the two halves of L7 compose without either naming the other: an `evaluate` run leaves a run
     receipt, because a run receipt is declared over what a run IS, not over which verb it was.

Nothing here restates what the kit declares. Every rule, path and name is read from the
declaration, because a test that carries its own copy of the default set stops measuring the kit
and starts agreeing with a snapshot of it.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from harness import KIT, Fixtures, host_digest, sha

CAPABILITY = json.loads(
    (KIT / "capabilities/evaluation/capability.json").read_text(encoding="utf-8"))
DISPOSITIONS = json.loads(
    (KIT / "capabilities/evaluation/dispositions.json").read_text(encoding="utf-8"))
JUDGEMENT_SCHEMA = json.loads((KIT / "schemas/judgement.schema.json").read_text(encoding="utf-8"))
QUALITY_SCHEMA = json.loads((KIT / "schemas/quality.schema.json").read_text(encoding="utf-8"))

INTERPRETERS = KIT / "interpreters"

#: The words the CONTRACTS give both sides. Read from the schemas and the capability's own block,
#: so this suite spells nothing an instance invented.
ROWS = "dispositions"
SPEC = CAPABILITY["evaluates"]
VERDICT = "verdict"
UNJUDGED = "UNJUDGED"
PASSED = "PASS"

#: The sentence the whole capability exists to make impossible to miss. Read from the payload
#: rather than restated: if the words change, this suite follows them.
ZERO = "THE MEASURE IS ZERO"


def install_named(name: str) -> dict:
    [item] = [i for i in CAPABILITY["installs"] if i.get("reads_as") == name]
    return item


def gate_with(key: str) -> dict:
    [gate] = [g for g in CAPABILITY["gates"] if key in g.get("params", {})]
    return gate


def references() -> list:
    return gate_with("references")["params"]["references"]


def rules() -> list:
    return DISPOSITIONS[ROWS]


def local_readings_path() -> str:
    """Where a host declares readings of its own: the sources of the disposition gate, minus what
    the capability SHIPS, is the one the host owns. Derived, never written down twice."""
    shipped = {d["id"] for d in CAPABILITY["documents"]}
    # Every source any of this capability's gates reads, minus everything the capability itself
    # ships: what remains is host-authored. Read across the gates rather than from one of them,
    # because WHICH gate happens to carry a source is this capability's business and changes the
    # day it declares another -- as it did the day it began consuming a reading.
    [name] = {source for gate in CAPABILITY["gates"]
              for source in gate.get("params", {}).get("sources", [])
              if source not in shipped}
    return install_named(name)["target"]


DECLARATION = install_named(SPEC["declaration"])["target"]
JUDGEMENTS = install_named(SPEC["judgements"])["target"].rstrip("/")
PROJECTION = next(i["target"] for i in CAPABILITY["installs"] if i["class"] == "projection")

#: A host's own subject matter, authored HERE because it could never be authored in the kit. It is
#: deliberately trivial: what matters is that the framework carried it without ever having an
#: opinion about it.
A_RUBRIC = "does-it-answer-the-question"
A_CASE = "the-first-thing-this-host-cares-about"
A_JUDGE = "the-owner"


def a_declaration(**overrides) -> dict:
    value = {
        "schema_version": 1,
        SPEC["rubrics"]: [{
            "id": A_RUBRIC,
            "asks": "would the person who asked consider this an answer?",
            "criteria": [{"id": "it-answers", "asks": "is the question actually answered?"}],
        }],
        SPEC["cases"]: [{
            "id": A_CASE,
            "asks": "what happens here?",
            SPEC["judged_by"]: [A_RUBRIC],
        }],
        "judges": [{"id": A_JUDGE, "because": "this host reads its own subject."}],
    }
    value.update(overrides)
    return value


def interpreter_sources() -> list:
    return sorted(p for p in INTERPRETERS.rglob("*.py"))


def interpreter_digest() -> dict:
    return {p.relative_to(KIT).as_posix(): sha(p) for p in interpreter_sources()}


class Evaluation(Fixtures, unittest.TestCase):

    # -- reading and authoring the host ----------------------------------------------------------
    def judgements(self, host: Path) -> dict:
        root = host / JUDGEMENTS
        if not root.is_dir():
            return {}
        return {path.name: json.loads(path.read_text(encoding="utf-8"))
                for path in sorted(root.glob("*.json"))}

    def declare(self, host: Path, value: dict) -> None:
        (host / DECLARATION).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def rewrite(self, host: Path, name: str, **fields) -> dict:
        path = host / JUDGEMENTS / name
        record = json.loads(path.read_text(encoding="utf-8"))
        record.update(fields)
        path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        return record

    def judging_host(self) -> tuple:
        """An approved host that has declared one case, one rubric and one judge, and has had its
        blank opened. The state every later assertion starts from."""
        host = self.installed()
        self.declare(host, a_declaration())
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        result = self.run_kit(KIT, host, "evaluate")
        self.assertEqual(0, result.returncode, "evaluate refused a host that declared a case")
        [name] = list(self.judgements(host))
        return host, name

    # == 1. the sensors are measured, and they were pointed at something ==========================
    def test_78_every_reading_is_calibrated_and_the_gates_read_a_set_that_is_not_empty(self):
        """The ledger's rule in this slice's vocabulary, both halves. Each disposition states one
        judgement it must match and one lookalike it must let through; each declared reference
        states one record it must flag and one it must admit. And the SET is the dangerous half:
        a gate over an empty directory of judgements passes exactly as loudly as one that looked,
        so the host under test is required to hold a judgement before its green is believed.
        """
        self.assertTrue(rules(), "an evaluation capability that declares no reading gates nothing")
        for rule in rules():
            with self.subTest(disposition=rule["id"]):
                proves, admits = rule["proves"], rule["admits"]
                self.assertNotEqual(proves, admits,
                                    "a specimen and its lookalike that are the same reading "
                                    "measure no edge at all")
                for specimen in (proves, admits):
                    for required in JUDGEMENT_SCHEMA["required"]:
                        self.assertIn(required, specimen,
                                      "a calibration is measured on a judgement the kit could "
                                      "actually have written, or it measures a fiction")

        self.assertTrue(references(), "a referent gate with no references measures nothing")
        for reference in references():
            with self.subTest(reference=reference["id"]):
                self.assertIn(reference["field"], JUDGEMENT_SCHEMA["properties"],
                              "a reference points at a field of the record's own contract")
                self.assertIn(reference["among"]["list"], QUALITY_SCHEMA["properties"],
                              "a reference resolves against a list the host's contract declares")
                self.assertIn(reference["field"], reference["proves"],
                              "a specimen that names nothing cannot be a dangling reference")
                self.assertNotIn(reference["field"], reference["admits"],
                                 "the lookalike must be a record that CLAIMS nothing, because an "
                                 "absence is a state and only a claim can be false")

        host, _name = self.judging_host()
        self.assertTrue(self.judgements(host),
                        "no judgement was opened, so the gates below passed over an empty set")
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode,
                         "a host whose judgements are all honest blanks must be green")

    # == 2. the zero, and the distinction the whole capability exists for =========================
    def test_79_a_host_that_has_never_judged_says_so_and_is_not_a_host_that_judged_well(self):
        """Cardinal V at the one place an evaluation surface always lies. A blank host states its
        ZERO MEASURE in those words -- on the page and from the verb -- and a host that has
        actually judged something reads differently from one that never has. If those two ever
        printed the same thing, every guarantee in this capability would be decoration.
        """
        blank = self.installed()
        page = (blank / PROJECTION).read_text(encoding="utf-8")
        self.assertIn(ZERO, page, "a page over an empty declaration read as fine")
        self.assertIn("is not measured anywhere", page,
                      "an unmeasured judge that reads as measured is the trust hole this slice "
                      "was told to declare rather than fill")
        nothing = self.run_kit(KIT, blank, "evaluate")
        self.assertEqual(0, nothing.returncode, "a zero measure is a state, not a failure")
        self.assertIn(ZERO, nothing.stdout)

        host, name = self.judging_host()
        never = self.run_kit(KIT, host, "evaluate").stdout
        self.assertNotIn(ZERO, never, "a host that declared a case has no zero measure to state")
        self.assertIn("never judged", never)

        self.rewrite(host, name, **{VERDICT: PASSED, "judge": A_JUDGE,
                                    "judged_at": "2026-01-01T00:00:01+00:00"})
        judged = self.run_kit(KIT, host, "evaluate").stdout
        self.assertIn("1 carrying a verdict, 0 never judged", judged)
        self.assertNotEqual(never, judged,
                            "a host that has been judged printed exactly what a host that never "
                            "was printed, which is the one lie this capability exists to prevent")
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode,
                         "an honest verdict by a declared judge is not a finding")

    # == 3. the blank is opened once, and a verdict is never overwritten ==========================
    def test_80_the_blank_is_opened_before_anything_judges_and_a_verdict_is_never_rewritten(self):
        """The write-ahead order carried from a run's record to a case's. The blank exists before
        the judging, because a judging that never happens must still be visible afterwards; and
        the machine that opened it may never close it, because a machine that could rewrite a
        judgement could quietly clear a failing one.
        """
        host, name = self.judging_host()
        opened = self.judgements(host)[name]
        self.assertEqual(UNJUDGED, opened[VERDICT])
        self.assertTrue(opened["opened_at"], "a blank nobody can date is a blank nobody chases")
        self.assertNotIn("judge", opened, "the kit named a judge, which is the host's to name")
        self.assertNotIn("judged_at", opened, "nothing judged, so nothing may state a moment")
        self.assertEqual(A_CASE, opened["case"])
        self.assertEqual(A_RUBRIC, opened["rubric"])

        again = self.run_kit(KIT, host, "evaluate")
        self.assertEqual(0, again.returncode)
        self.assertEqual({name: opened}, self.judgements(host),
                         "a second run re-opened a pair that already had a judgement")

        verdict = self.rewrite(host, name, **{VERDICT: PASSED, "judge": A_JUDGE,
                                              "judged_at": "2026-01-01T00:00:01+00:00"})
        self.assertEqual(0, self.run_kit(KIT, host, "evaluate").returncode)
        self.assertEqual(verdict, self.judgements(host)[name],
                         "the kit rewrote a verdict it did not reach")

        before = host_digest(host)
        planned = self.run_kit(KIT, host, "evaluate", "--plan")
        self.assertEqual(0, planned.returncode)
        self.assertEqual(before, host_digest(host), "a plan touched a byte, and said it would not")

    # == 4. a verdict that cannot be questioned ==================================================
    def test_81_a_verdict_that_cannot_say_who_reached_it_or_when_is_named_and_nothing_is_removed(self):
        """What the kit's own readings ask of a judgement, and the only thing they ask: can this
        be questioned? Never whether the verdict was deserved -- that is the domain's, and the
        moment the kit had an opinion about it, it would have shipped one.

        The findings are read FROM the declaration, so this measures the kit's rules rather than a
        memory of them, and the host is digested before and after: a judgement is evidence, and
        evidence is not swept up by the thing being questioned.
        """
        host, name = self.judging_host()
        self.rewrite(host, name, **{VERDICT: PASSED})  # judged by nobody, at no moment

        before = host_digest(host)
        result = self.run_kit(KIT, host, "check")
        self.assertEqual(1, result.returncode, "a verdict with no author read as a healthy host")

        named = [rule for rule in rules() if rule["id"] in result.stdout]
        self.assertEqual(2, len(named),
                         "exactly the two readings that ask who and when should have fired; "
                         f"fired: {[r['id'] for r in named]}")
        for rule in named:
            self.assertIn(rule["instead"], result.stdout,
                          "a finding that says only NO tells an operator nothing")
        self.assertIn(name.removesuffix(".json"), result.stdout,
                      "the finding does not say WHICH judgement")
        self.assertEqual(before, host_digest(host),
                         "a reporting gate moved a byte, and a judgement is evidence")

    # == 5. a verdict about something nobody declared ============================================
    def test_82_a_judgement_that_points_at_what_this_host_does_not_declare_is_named(self):
        """The failure a well-formed record cannot show on its own face. A case is renamed, and
        every verdict about the old name goes on reading exactly like a case that passed -- so the
        referent is checked against what the host declares NOW, and the honest blank beside it is
        left alone, which is what proves the rule has an edge.
        """
        host, stale = self.judging_host()
        renamed = a_declaration()
        renamed[SPEC["cases"]][0]["id"] = A_CASE + "-under-its-new-name"
        self.declare(host, renamed)
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        self.assertEqual(0, self.run_kit(KIT, host, "evaluate").returncode,
                         "a renamed case must be opened afresh, not repaired in place")
        kept = [n for n in self.judgements(host) if n != stale]
        self.assertEqual(1, len(kept), "the renamed pair was not opened")

        result = self.run_kit(KIT, host, "check")
        self.assertEqual(1, result.returncode)
        [reference] = [r for r in references() if r["id"] in result.stdout]
        self.assertEqual("case", reference["field"])
        self.assertIn(stale.removesuffix(".json"), result.stdout)
        self.assertNotIn(kept[0].removesuffix(".json"), result.stdout,
                         "the honest blank beside it was named too, so the rule has no edge")
        self.assertTrue((host / JUDGEMENTS / stale).is_file(),
                        "the gate removed the evidence it was asked to name")

    # == 6. the host's own reading, and the interpreter's silence ================================
    def test_83_a_host_may_declare_a_reading_of_its_own_with_no_interpreter_edit(self):
        """The proof every slice earns, in this one's vocabulary: a way of reading a judgement the
        kit never heard of bites, because a disposition is a row in a document the HOST owns."""
        before = interpreter_digest()
        host, name = self.judging_host()
        readings = json.loads((host / local_readings_path()).read_text(encoding="utf-8"))
        readings[ROWS].append({
            "id": "a-blank-this-host-will-not-tolerate",
            "when": {VERDICT: UNJUDGED},
            "because": "this host has decided that an unread case is a finding here.",
            "instead": "judged, or withdrawn as a case.",
            "proves": {"schema_version": 1, "id": "9" * 32, "case": A_CASE, "rubric": A_RUBRIC,
                       VERDICT: UNJUDGED, "opened_at": "2026-01-01T00:00:00+00:00"},
            "admits": {"schema_version": 1, "id": "8" * 32, "case": A_CASE, "rubric": A_RUBRIC,
                       VERDICT: PASSED, "opened_at": "2026-01-01T00:00:00+00:00",
                       "judge": A_JUDGE, "judged_at": "2026-01-01T00:00:01+00:00"},
        })
        (host / local_readings_path()).write_text(json.dumps(readings, indent=2) + "\n",
                                                 encoding="utf-8")
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)

        result = self.run_kit(KIT, host, "check")
        self.assertEqual(1, result.returncode, "the host's own reading did not bite")
        self.assertIn("a-blank-this-host-will-not-tolerate", result.stdout)
        self.assertIn(name.removesuffix(".json"), result.stdout)

        self.rewrite(host, name, **{VERDICT: PASSED, "judge": A_JUDGE,
                                    "judged_at": "2026-01-01T00:00:01+00:00"})
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode,
                         "the host's reading has no edge: it named a judged case too")
        self.assertEqual(before, interpreter_digest(),
                         "a host's own reading cost an interpreter edit, so it is not declared")

    # == 7. T2, pointed at the easiest place in the kit to smuggle a domain in ====================
    def test_84_the_kit_ships_no_case_no_rubric_no_criterion_and_no_verdict(self):
        """The blank test, aimed where it would hurt most. This capability is the one place in the
        kit where a domain opinion would look like helpfulness: one plausible rubric, one obvious
        case, and every host that ever installs is judged by a standard nobody here could have
        known -- in a file written once and owned by the host forever after.

        So the seeded declaration is required to arrive with NO rows, and no interpreter is allowed
        to spell a reading's id: a judgement spelled in the machine is a judgement with two homes,
        and the one a host can change is no longer the one that decides.
        """
        seeded = [i for i in CAPABILITY["installs"] if i["mode"] == "seed"]
        self.assertTrue(seeded, "this capability seeds nothing, so this test measures nothing")
        for item in seeded:
            value = json.loads((KIT / item["source"]).read_text(encoding="utf-8"))
            for field, held in value.items():
                if isinstance(held, (list, dict)):
                    self.assertEqual(0, len(held),
                                     f"{item['source']} arrives with rows under {field!r}: the "
                                     f"framework's opinion wearing the host's signature")

        host = self.installed()
        # The pinned kit (ADR-016) is the KIT, carried verbatim -- its schemas declare the verdict
        # vocabulary, which is not a verdict. The kit half is measured above, over the payload;
        # this half is about what the host was GIVEN as its own, so the pinned tree is excluded by
        # the declaration that places it, never by a spelled path.
        import pin  # noqa: E402 -- the interpreter's path is set by the harness
        from manifest import Manifest  # noqa: E402
        pinned = [host / i["target"] for c in Manifest(KIT).capabilities
                  for i in c.installs if i["mode"] == pin.MODE]
        emitted = [p for p in (host / ".agents").rglob("*.json") if p.is_file()
                   and not any(p.is_relative_to(root) for root in pinned)]
        self.assertTrue(emitted, "a host that emitted no declaration measures nothing here")
        reached = [verdict for verdict in JUDGEMENT_SCHEMA["properties"][VERDICT]["enum"]
                   if verdict != UNJUDGED
                   for path in emitted
                   if verdict in path.read_text(encoding="utf-8", errors="replace")]
        self.assertEqual([], reached,
                         "a freshly installed host arrived already holding a verdict, which is "
                         "the framework judging a domain it has never met")

        offenders = []
        for path in interpreter_sources():
            text = path.read_text(encoding="utf-8")
            for identity in [rule["id"] for rule in rules()] + [r["id"] for r in references()]:
                if re.search(rf"""['"]{re.escape(identity)}['"]""", text):
                    offenders.append(f"{path.relative_to(KIT).as_posix()} names {identity!r}")
        self.assertEqual([], offenders,
                         "an interpreter that spells a reading is an interpreter that decides")

    # == 8. the two halves of L7, composing without knowing each other ============================
    def test_85_a_run_that_evaluates_leaves_a_run_receipt_without_either_half_naming_the_other(self):
        """LIFE and QUALITY are one level split in two, and the split holds only if neither knows
        the other exists. The receipt is declared over what a run IS -- it writes, it is not a
        plan -- so a verb invented long after that declaration is watched by it automatically. If
        either capability had to name the other, both would need editing for the next one.
        """
        watched = json.loads((KIT / "capabilities/observability/capability.json")
                             .read_text(encoding="utf-8"))
        self.assertNotIn("observab", json.dumps(CAPABILITY),
                         "the quality half names the life half, so it is coupled to it")
        self.assertNotIn("evaluat", json.dumps(watched),
                         "the life half names the quality half, so it would need editing for the "
                         "next verb that arrives")

        host, _name = self.judging_host()
        wanted = {w["params"]["into"] for w in watched["observes"]}
        [root] = sorted({i["target"] for i in watched["installs"] if i.get("reads_as") in wanted})
        names = {json.loads(p.read_text(encoding="utf-8"))["name"]
                 for p in (host / root.rstrip("/")).glob("*.json")}
        self.assertIn("evaluate", names,
                      "a mutating run left no record of itself, so the two halves did not compose")
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode)
