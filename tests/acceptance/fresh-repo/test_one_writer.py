"""Acceptance: one writer per host (ADR-007) -- every verb that writes the host holds it, and both
records a run leaves behind validate against the kit's own schemas.

The init slice proved the hold on the one verb that installs. It left two gaps, and each is the
kind that stays invisible from where it stands: an `upgrade`, a `move` or a `render` could still
walk into a host another runtime was writing, and the hold and the journal each named their own
shape in a docstring while every other host document validated through the manifest.

What is held is READ from the verbs' declarations -- `MUTATES`, and the subject it mutates -- and
never listed here. The one refusal that matters is exercised against a REAL second process: an
init killed where it stands, whose hold stays on disk because a killed process releases nothing.
"""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
import time
import unittest
from pathlib import Path

from harness import CLI, KIT, Fixtures, Manifest, host_digest

import ephemeral  # noqa: E402
import hostlock  # noqa: E402
import journal as journal_module  # noqa: E402
from journal import PENDING, UNSET  # noqa: E402

MANIFEST = Manifest(KIT)
PLANE = [p["root"].rstrip("/") for p in MANIFEST.planes if p["class"] == ephemeral.OBSERVED][0]
LOCK = f"{PLANE}/{hostlock.NAME}"
JOURNAL = f"{PLANE}/{journal_module.NAME}"
APPROVER = "acceptance-suite"

#: Every verb the entry point can run, discovered the way the entry point discovers them.
VERBS = {p.stem: importlib.import_module(p.stem)
         for p in sorted((CLI.parent / "verbs").glob("*.py")) if not p.stem.startswith("_")}
#: The held set, READ from declarations. Nothing in this suite names a verb that holds.
HELD = sorted(name for name, module in VERBS.items() if hostlock.holds(module))
#: Verbs that write something, and yet not the host -- each must say so by declaring its subject.
ELSEWHERE = sorted(name for name, module in VERBS.items()
                   if getattr(module, "MUTATES", False) and not hostlock.holds(module))


class OneWriterPerHost(Fixtures, unittest.TestCase):
    """ADR-007: the hold is the host's, every host writer takes it, and its shape has one home."""

    # -- reading the host -----------------------------------------------------------------------
    @staticmethod
    def read(host: Path, rel: str):
        path = host / rel
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:  # caught mid-replace by a poller; not an absence
            return None

    def held_by_a_killed_init(self) -> tuple:
        """An installed host with a hold standing on it, left by a real init process killed while
        it was inside a phase. No flag asks anything to pretend: the hold is what a dead writer
        leaves, and it is indistinguishable from what a slow one leaves."""
        host = self.installed()
        process = subprocess.Popen(
            [sys.executable, str(CLI), "init", "--root", str(host), "--kit", str(KIT),
             "--approve", APPROVER],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        caught, deadline = False, time.monotonic() + 30.0
        while time.monotonic() < deadline and process.poll() is None:
            record = self.read(host, JOURNAL)
            phases = [p["status"] for p in (record or {}).get("phases", [])]
            if record and not record.get("ended_at") and UNSET in phases and PENDING in phases:
                caught = True
                break
            time.sleep(0.001)
        alive = process.poll() is None
        process.kill()
        process.wait()
        self.assertTrue(caught and alive, "the init was never caught mid-run, so no hold was left "
                                          "standing by a process that died holding it")
        hold = None
        for _ in range(200):
            hold = self.read(host, LOCK)
            if hold is not None:
                break
            time.sleep(0.005)
        self.assertTrue(hostlock.standing(hold), "the killed init left no standing hold")
        return host, hold

    # == the held set ===========================================================================
    def test_196_every_verb_that_declares_it_writes_the_host_is_refused_at_a_host_a_killed_run_still_holds(self):
        """The refusal is the whole point, and it must be the same for every writer: a host held by
        a run that may still be alive is a DOOR, named in full -- who, where, which process, which
        verb, which run -- and passing it leaves the host exactly as it was, save the receipt that
        says this run was turned away."""
        self.assertIn("init", HELD, "the verb this mechanism was proved on no longer holds")
        self.assertGreater(len(HELD), 1, "only one verb holds the host; ADR-007 is not in force")
        for name in ELSEWHERE:
            self.assertTrue(getattr(VERBS[name], "SUBJECT", None),
                            f"{name} writes and declares no other subject, yet is not held")

        host, hold = self.held_by_a_killed_init()
        before = host_digest(host)
        for verb in HELD:
            with self.subTest(verb=verb):
                result = self.run_kit(KIT, host, verb)
                self.assertEqual(3, result.returncode,
                                 f"{verb} walked into a host another run is holding")
                for field in ("owner", "machine", "pid", "verb", "run_id", "started_at"):
                    self.assertIn(str(hold[field]), result.stderr,
                                  f"the refusal does not name the hold's {field}")
        after = host_digest(host)
        for rel in sorted(set(before) | set(after)):
            if before.get(rel) == after.get(rel):
                continue
            self.assertNotIn(rel, before, f"a refused run changed {rel}, which it found there")
            left = json.loads((host / rel).read_text(encoding="utf-8"))
            self.assertEqual([], MANIFEST.validate(left, "receipt"),
                             f"a refused run left {rel}, which is not the receipt of its refusal")
            self.assertEqual(3, left.get("exit_code"))
        self.assertEqual(hold, self.read(host, LOCK), "a refused run touched the hold it met")

    # == the hold is taken by the writer, under the run's own name ================================
    def test_197_a_writer_other_than_init_takes_the_hold_when_it_writes_and_closes_it_under_its_own_name(self):
        """A render is a writer of the host. It holds the host while it writes, under its OWN verb
        and run, and closes the hold with its ending -- a hold that still named the install before
        it would be a record describing a run that is not the one that wrote."""
        host = self.installed()
        installed = self.read(host, LOCK)
        result = self.run_kit(KIT, host, "render")
        self.assertEqual(0, result.returncode, result.stderr)
        hold = self.read(host, LOCK)
        self.assertEqual("render", hold["verb"], "render wrote the host without holding it")
        self.assertNotEqual(installed["run_id"], hold["run_id"])
        self.assertFalse(hostlock.standing(hold), "render walked away still holding the host")
        self.assertEqual(0, hold["exit_code"])

    def test_198_an_install_carried_out_by_an_upgrade_is_held_and_journalled_as_the_upgrade(self):
        """An upgrade writes through the installer; the run that holds the host is the upgrade,
        and so is the run the journal records. The installer is a step, not a run."""
        host = self.installed()
        result = self.run_kit(KIT, host, "upgrade")
        self.assertEqual(0, result.returncode, result.stderr)
        hold, book = self.read(host, LOCK), self.read(host, JOURNAL)
        self.assertEqual("upgrade", hold["verb"], "the hold names the step, not the run")
        self.assertEqual("upgrade", book["verb"], "the journal names the step, not the run")
        self.assertEqual(hold["run_id"], book["run_id"], "one run, two identities")
        self.assertFalse(hostlock.standing(hold))

    def test_199_a_plan_of_any_held_verb_takes_no_hold_and_leaves_the_last_one_as_it_was(self):
        """A guard that protects a write must not itself be the first write. A plan writes
        nothing, so it holds nothing -- the closed hold of the last writer stays byte-identical."""
        host = self.installed()
        before = (host / LOCK).read_bytes()
        for verb in HELD:
            with self.subTest(verb=verb):
                result = self.run_kit(KIT, host, verb, "--plan")
                self.assertEqual(before, (host / LOCK).read_bytes(),
                                 f"{verb} --plan wrote the hold (exit {result.returncode})")

    # == one home for each shape ==================================================================
    def test_200_the_hold_and_the_journal_are_written_to_their_kit_schemas_and_name_no_version_of_their_own(self):
        """Every other host document validates through the manifest; these two now do too, and the
        version each is written at is the one its schema declares -- read, never restated."""
        host = self.installed()
        for rel, schema, module in ((LOCK, hostlock.SCHEMA, hostlock),
                                    (JOURNAL, journal_module.SCHEMA, journal_module)):
            with self.subTest(schema=schema):
                record = self.read(host, rel)
                self.assertEqual([], MANIFEST.validate(record, schema))
                self.assertEqual(MANIFEST.schema(schema)["properties"]["schema_version"]["const"],
                                 record["schema_version"])
                self.assertFalse(hasattr(module, "SCHEMA_VERSION"),
                                 f"{module.__name__} still declares a second home for its version")

    def test_201_a_record_on_disk_that_does_not_honour_its_schema_is_refused_by_code_and_never_overwritten(self):
        """A hold nobody can read may still have somebody behind it, and a journal nobody can read
        is the only account of a dead run. Neither is replaced: the run stops, with the code."""
        cases = ((LOCK, "render", (), hostlock.LockError.code),
                 (JOURNAL, "init", ("--approve", APPROVER), journal_module.JournalError.code))
        for rel, verb, flags, code in cases:
            with self.subTest(record=rel):
                host = self.installed()
                record = self.read(host, rel)
                record["verdict_of_a_machine"] = "stale"  # a field no schema declares
                (host / rel).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
                planted = (host / rel).read_bytes()
                result = self.run_kit(KIT, host, verb, *flags)
                self.assertNotEqual(0, result.returncode, f"{verb} accepted a record that is not one")
                self.assertIn(f"[{code}]", result.stderr)
                self.assertEqual(planted, (host / rel).read_bytes(), f"{verb} overwrote {rel}")


if __name__ == "__main__":
    unittest.main()
