"""Acceptance: observability -- the LIFE of a run, and the one lie this slice exists to prevent.

Every capability proved before this one is about a SURFACE: what the kit wrote, what ended up
somewhere, what a name claims. This one is about a MOMENT that has already passed by the time
anybody looks. A run either left a trace of itself or it did not, and the case that matters is
exactly the case nobody is present for: a run that died half way, leaving artifacts that read
precisely like the artifacts of a run that finished.

So the seven things this suite exists to prove are the seven a run-recorder most often fails:

  1. every declared disposition proves what it MATCHES and states what it TOLERATES, before it is
     believed -- and the gate is applied to a set that is not empty, because a scan of nothing
     passes gloriously and reads exactly like a scan that looked;
  2. the record is on disk, saying that nothing has concluded, WHILE the run is still running --
     proved from inside the run itself, not inferred from the fact that a file exists afterwards;
  3. a run that is KILLED leaves that record open forever, and the gate names it;
  4. a run that was REFUSED is an ending and not a disappearance -- the two are distinguishable,
     which is the whole difference between a receipt and a rumour;
  5. a run that writes nothing leaves no record, because a record would then measure only itself;
  6. a host may declare a reading of its own, and it costs the interpreter nothing;
  7. the surface states the grammar, states the empty host plane as a STATE, and states the one
     number this framework has never declared instead of implying it was decided.

Nothing here restates the kit's dispositions. They are READ from the declaration and the suite is
driven by them, because a test that carries its own copy of the default set stops measuring the
kit and starts agreeing with a snapshot of it.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
import unittest
from pathlib import Path

from harness import CLI, KIT, Fixtures, host_digest, sha

#: The one place this suite learns what observability declares -- and where its records live. The
#: path is not written here: the capability already stated it once, when it declared the space it
#: owns, and the observation names that space by the name the install reads as.
CAPABILITY = json.loads(
    (KIT / "capabilities/observability/capability.json").read_text(encoding="utf-8"))
DISPOSITIONS = json.loads(
    (KIT / "capabilities/observability/observation.json").read_text(encoding="utf-8"))
RECEIPT_SCHEMA = json.loads((KIT / "schemas/receipt.schema.json").read_text(encoding="utf-8"))

LOCAL = ".agents/project/observability/observation.json"
PROJECTION = ".agents/generated/observability/RUNS.md"

INTERPRETERS = KIT / "interpreters"

#: The field a dispositions document carries its rows under, and the field a capability declares
#: its observations under. Read from the SCHEMAS, so this suite spells no word the contract does
#: not already give both sides.
ROWS = "dispositions"
WATCHES = "observes"


def rules() -> list:
    return DISPOSITIONS[ROWS]


def runs_root() -> str:
    """Where a run's record is written, derived from the declaration in two hops -- the
    observation names a readable, the install that owns that name states the path."""
    wanted = {watch["params"]["into"] for watch in CAPABILITY[WATCHES]}
    targets = sorted({item["target"] for item in CAPABILITY["installs"]
                      if item.get("reads_as") in wanted})
    assert len(targets) == 1, f"the records of a run have {len(targets)} homes: {targets}"
    return targets[0]


def interpreter_sources() -> list:
    return sorted(p for p in INTERPRETERS.rglob("*.py"))


def interpreter_digest() -> dict:
    return {p.relative_to(KIT).as_posix(): sha(p) for p in interpreter_sources()}


def a_receipt(identity: str, **fields) -> dict:
    """A record as the kit would have written one. Only the fields the SCHEMA requires are given
    a default; anything else is the caller's statement about the run being described."""
    record = {"schema_version": 1, "id": identity, "name": "a-run-that-happened-here",
              "status": "OK", "started_at": "2026-01-01T00:00:00+00:00"}
    record.update(fields)
    return record


class Observability(Fixtures, unittest.TestCase):

    # -- reading the host ------------------------------------------------------------------------
    def records(self, host: Path) -> dict:
        root = host / runs_root()
        if not root.is_dir():
            return {}
        return {path.name: json.loads(path.read_text(encoding="utf-8"))
                for path in sorted(root.glob("*.json"))}

    def plant(self, host: Path, record: dict) -> Path:
        """A record as it ARRIVES: written by some earlier run of this kit and left behind. The
        gate reads what it finds; it has no memory of who wrote it."""
        path = host / runs_root().rstrip("/") / f"{record['id']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        return path

    def declare_locally(self, host: Path, disposition: dict) -> None:
        document = json.loads((host / LOCAL).read_text(encoding="utf-8"))
        document[ROWS].append(disposition)
        (host / LOCAL).write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    # == 1. the sensor is measured, and it was pointed at something ===============================
    def test_70_every_disposition_is_calibrated_and_the_gate_reads_a_set_that_is_not_empty(self):
        """Both halves of the ledger's rule, in one place. The calibration is in the DECLARATION:
        each disposition states one reading it must match and one lookalike it must let through,
        and a disposition that cannot do both has no measured edge.

        The second half is the dangerous one and it is never the assertion -- it is the SET. A
        gate over an empty collection passes exactly as loudly as a gate that looked, so the run
        that installed this host is required to have left its own record behind, and every
        specimen is required to be a real receipt rather than a shape invented for a test.
        """
        self.assertTrue(rules(), "an observability capability that declares no reading gates nothing")
        for rule in rules():
            with self.subTest(disposition=rule["id"]):
                proves, admits = dict(rule["proves"]), dict(rule["admits"])
                self.assertNotEqual(proves, admits,
                                    "a specimen and its lookalike that are the same reading "
                                    "measure no edge at all")
                for specimen in (proves, admits):
                    for required in RECEIPT_SCHEMA["required"]:
                        self.assertIn(required, specimen,
                                      "a calibration is measured on a record the kit could "
                                      "actually have written, or it measures a fiction")

        host = self.installed()
        found = self.records(host)
        self.assertTrue(found, "the run that installed this host left no record of itself, so "
                               "the gate below passed over an empty set")
        self.assertEqual(["init"], sorted({r["name"] for r in found.values()}))
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode,
                         "a host whose every run finished must be green")

    # == 2. the record exists WHILE the run is still running ======================================
    def test_71_the_record_says_nothing_has_concluded_while_the_run_is_still_running(self):
        """The guarantee, measured from inside the guarantee -- and the only way it can be
        measured without a race. A run's own record is on disk, holding the status that means
        *nothing has been concluded yet*, at the moment that run's own gates are reading the host.

        The witness is a disposition a fixture kit declares over the reading `in_flight`, which no
        record can carry and only the running process can know. The kit's own reading excludes a
        live record deliberately -- a run cannot judge its own liveness -- so this fixture inverts
        exactly that exclusion and demands that the thing being excluded is really there. An
        exclusion nobody can see the other side of is indistinguishable from a blind spot.
        """
        witness = {
            "id": "a-record-open-because-this-very-run-is-holding-it",
            "when": {"status": "UNSET", "in_flight": True},
            "because": "this fixture asks the sensor to name what the kit deliberately passes "
                       "over, so that the exclusion can be seen from both sides.",
            "instead": "excluded by the kit's own reading, which is what the real declaration does.",
            "proves": a_receipt("dddddddddddddddddddddddddddddd01", status="UNSET", in_flight=True),
            "admits": a_receipt("dddddddddddddddddddddddddddddd02", status="UNSET", in_flight=False),
        }

        def declare_the_witness(kit: Path):
            self.edit_json(kit, "capabilities/observability/observation.json",
                           lambda doc: doc[ROWS].append(witness))

        kit = self.fixture_kit("in-flight-witness", declare_the_witness)
        host = self.host()
        self.assertEqual(3, self.run_kit(kit, host, "init").returncode)
        result = self.run_kit(kit, host, "init", "--approve", "acceptance-suite")

        self.assertEqual(1, result.returncode,
                         "the run's own record was not on disk while the run was still running")
        self.assertIn("FAIL  FF-RUN-RECEIPT", result.stdout)
        self.assertIn(witness["id"], result.stdout)

        # and the record it named is that very run's, which then closed normally.
        [record] = list(self.records(host).values())
        self.assertEqual("init", record["name"])
        self.assertEqual("ERROR", record["status"], "a run that reported a failure ended badly")
        self.assertIn(record["id"], result.stdout)

    # == 3. a run that dies mid-way ==============================================================
    def killed_mid_run(self, kit: Path, host: Path, verb: str, *flags) -> dict:
        """Start a run, wait until it has stated that it began, and then kill it outright.

        Not a simulation. The process is destroyed where it stands, which is the only way to
        produce the artifact this whole capability exists for: work on disk that reads exactly
        like finished work, and one record that can tell the difference.

        Two things are ASSERTED rather than assumed, because both failure modes would leave this
        test quietly agreeing instead of measuring: that a record appeared at all while the run
        was alive, and that the run had not already finished by the time it was killed.
        """
        before = set(self.records(host))
        process = subprocess.Popen(
            [sys.executable, str(CLI), verb, "--root", str(host), "--kit", str(kit), *flags],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        opened, deadline = None, time.monotonic() + 30.0
        while time.monotonic() < deadline:
            appeared = set(self.records(host)) - before
            if appeared:
                opened = sorted(appeared)[0]
                break
            if process.poll() is not None:
                break
            time.sleep(0.001)
        alive = process.poll() is None
        process.kill()
        process.wait()
        self.assertIsNotNone(opened, "the run wrote no record before it did its work, so nothing "
                                     "here was measured: a record written later proves nothing "
                                     "about a run that never gets later")
        self.assertTrue(alive, "the run finished before it could be killed, so this test observed "
                               "a healthy run and would have passed either way")
        return self.records(host)[opened]

    def test_72_a_run_that_dies_mid_way_leaves_a_record_that_says_so_and_the_gate_names_it(self):
        """The hardest constraint in the design, and the one it was built inside of. A run is
        killed outright. It never reaches its own close, so its record still says that nothing
        was concluded -- and it will say that forever, which is the mechanism working.

        Then a LATER run reads the host and names it: not as a missing reading, not as a generic
        mismatch, but as the state it is, with what to do about it, and with nothing removed.
        """
        host = self.installed()
        dead = self.killed_mid_run(KIT, host, "init")

        self.assertEqual("UNSET", dead["status"])
        self.assertTrue(dead["started_at"], "a record with no moment cannot be contradicted")
        self.assertNotIn("ended_at", dead, "a run that never ended must state no end")
        self.assertNotIn("exit_code", dead)

        before = host_digest(host)
        result = self.run_kit(KIT, host, "check")
        self.assertEqual(1, result.returncode, "a run that died reads as a healthy host")
        self.assertIn("FAIL  FF-RUN-RECEIPT", result.stdout)
        self.assertIn(dead["id"], result.stdout, "the finding does not say WHICH run died")

        [named] = [r for r in rules() if r["id"] in result.stdout]
        self.assertEqual({"status": "UNSET", "in_flight": False}, named["when"])
        self.assertIn(named["instead"], result.stdout,
                      "a finding that says only NO tells an operator nothing")
        self.assertEqual(before, host_digest(host),
                         "a reporting gate moved a byte, and a run's record is evidence")

    # == 4. an ending is not a disappearance =====================================================
    def test_73_a_run_that_was_refused_is_an_ending_and_not_a_disappearance(self):
        """The distinction the whole design turns on. A run that failed said so, dated it, and is
        finished; a run that vanished said nothing and never will. A record that could not tell
        those apart would make every failure look like a death and every death look survivable.
        """
        host = self.installed()
        resident = json.loads(
            (KIT / "capabilities/hygiene/residence.json").read_text(encoding="utf-8"))["genres"][0]
        planted = host / resident["proves"]
        planted.parent.mkdir(parents=True, exist_ok=True)
        planted.write_text("# put here by a host, in good faith.\n", encoding="utf-8")

        before = set(self.records(host))
        failed = self.run_kit(KIT, host, "init")
        self.assertEqual(1, failed.returncode, "the run under test did not fail")
        [identity] = sorted(set(self.records(host)) - before)
        refused = self.records(host)[identity]

        self.assertEqual("ERROR", refused["status"])
        self.assertEqual(1, refused["exit_code"], "an exit code is recorded beside a status, "
                                                  "never in place of one")
        self.assertTrue(refused["ended_at"], "a failure that cannot be placed in time is read as "
                                             "current by every reader who ever finds it")

        planted.unlink()
        healthy = self.run_kit(KIT, host, "check")
        self.assertEqual(0, healthy.returncode,
                         "a run that ended badly and said when is not a run that died")
        self.assertNotIn(refused["id"], healthy.stdout)

    # == 5. what leaves no record, and why =======================================================
    def test_74_a_run_that_cannot_change_the_host_leaves_no_record_at_all(self):
        """Declared, not decided: the observation applies to runs that MUTATE and are not plans.
        A run that cannot change the host cannot leave it half-built, so its record would measure
        only itself -- and a plan promises to touch no byte, of which a record would be one.

        The condition is read from the declaration, so this measures the kit's rule rather than a
        memory of it: whatever a row says about the runs it watches, no run outside every row's
        `when` may leave a trace.
        """
        watched = [watch["when"] for watch in CAPABILITY[WATCHES]]
        self.assertTrue(all(when.get("mutates") is True and when.get("plan") is False
                            for when in watched),
                        "this test measures a rule the declaration no longer states")

        host = self.installed()
        before = self.records(host)
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode)
        self.assertEqual(before, self.records(host), "a run that writes nothing wrote a record")

        self.assertEqual(0, self.run_kit(KIT, host, "init", "--plan").returncode)
        self.assertEqual(before, self.records(host), "a plan touched a byte, and said it would not")

    # == 6. the host's own reading, and the interpreter's silence ================================
    def test_75_a_host_may_declare_a_reading_of_its_own_with_no_interpreter_edit(self):
        """The proof every earlier slice earned, in observability's vocabulary: a way of reading a
        run's record that this kit never heard of bites, because a disposition is a row in a
        document the HOST owns. `render` runs before `check` because a projection over a
        host-authored declaration is stale the instant the host authors -- honest, and still an
        edge a host meets without being told about it."""
        before = interpreter_digest()
        host = self.installed()
        self.declare_locally(host, {
            "id": "a-run-this-host-does-not-recognise",
            "when": {"name": "a-verb-nobody-here-runs"},
            "because": "this host reviews every record and knows what it runs.",
            "instead": "explained, or removed by whoever can explain it.",
            "proves": a_receipt("eeeeeeeeeeeeeeeeeeeeeeeeeeeeee01",
                                name="a-verb-nobody-here-runs", ended_at="2026-01-01T00:00:01+00:00"),
            "admits": a_receipt("eeeeeeeeeeeeeeeeeeeeeeeeeeeeee02",
                                ended_at="2026-01-01T00:00:01+00:00"),
        })
        kept = self.plant(host, a_receipt("eeeeeeeeeeeeeeeeeeeeeeeeeeeeee02",
                                          ended_at="2026-01-01T00:00:01+00:00"))
        strange = self.plant(host, a_receipt("eeeeeeeeeeeeeeeeeeeeeeeeeeeeee01",
                                             name="a-verb-nobody-here-runs",
                                             ended_at="2026-01-01T00:00:01+00:00"))
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)

        result = self.run_kit(KIT, host, "check")
        self.assertEqual(1, result.returncode)
        self.assertIn("a-run-this-host-does-not-recognise", result.stdout)
        self.assertIn(strange.name.removesuffix(".json"), result.stdout)
        self.assertNotIn(kept.name.removesuffix(".json"), result.stdout,
                         "the lookalike beside it was named too, so the rule has no edge")
        self.assertTrue(strange.is_file(), "the gate removed the evidence it was asked to name")
        self.assertEqual(before, interpreter_digest(),
                         "a host's own reading cost an interpreter edit, so it is not declared")

    def test_76_no_interpreter_module_names_a_declared_disposition(self):
        """The fitness function under the slice. A disposition spelled in the machine's own source
        is a judgement with two homes, and the one a host can change is no longer the one that
        decides. Only the IDS are read here: what a disposition MATCHES on is the receipt schema's
        own vocabulary, which the writer of a receipt is entitled to spell -- the wider question,
        of a term some instance invented reaching the machine, is measured by the boundary
        declaration against every module at once."""
        offenders = []
        for path in interpreter_sources():
            text = path.read_text(encoding="utf-8")
            for rule in rules():
                if re.search(rf"""['"]{re.escape(rule['id'])}['"]""", text):
                    offenders.append(f"{path.relative_to(KIT).as_posix()} names {rule['id']!r}")
        self.assertEqual([], offenders,
                         "an interpreter that spells a disposition is an interpreter that decides")

    # == 7. the surface says what is held, and what was never decided ============================
    def test_77_the_projection_states_the_grammar_the_empty_plane_and_the_undeclared_number(self):
        """Capability discovery and Cardinal V on one page. Every reading the kit ships is on it;
        a host that has declared none of its own reads that as a DECLARED state; and the threshold
        at which observing becomes enforcing -- which must be a number and has never been declared
        anywhere in this framework -- is stated as ABSENT rather than implied to have been decided.
        A surface that quietly held an unread tolerance field would read as enforced."""
        host = self.installed()
        page = (host / PROJECTION).read_text(encoding="utf-8")
        for rule in rules():
            self.assertIn(f"### {rule['id']}", page)
            self.assertIn(rule["instead"], page)
        self.assertIn("observe-then-enforce period; the first crossing is a finding", page,
                      "a threshold nobody declared must be stated, not left to be assumed")
        self.assertIn("declared no dispositions of its own", page,
                      "an empty host plane must read as a state, not as a missing section")

        self.declare_locally(host, {
            "id": "a-reading-this-host-added",
            "when": {"name": "a-verb-nobody-here-runs"},
            "because": "this host says so.", "instead": "explained by whoever can.",
            "proves": a_receipt("ffffffffffffffffffffffffffffff01",
                                name="a-verb-nobody-here-runs", ended_at="2026-01-01T00:00:01+00:00"),
            "admits": a_receipt("ffffffffffffffffffffffffffffff02",
                                ended_at="2026-01-01T00:00:01+00:00"),
        })
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        page = (host / PROJECTION).read_text(encoding="utf-8")
        self.assertIn("### a-reading-this-host-added", page)
        self.assertNotIn("declared no dispositions of its own", page)
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode,
                         "a declared-but-unbroken reading is not a finding")
