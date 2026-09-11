"""Acceptance: the two mechanisms that guard the INSIDE of an install -- the journal and the hold.

Every other suite here asks what a run produced. This one asks what a run that never came back
left behind, and what the next runtime is allowed to do about it. Those are the two failures an
installer cannot survive quietly:

  1. a run dies half way. The tree now holds part of an install and reads exactly like a tree that
     holds a finished one. Without a record written BEFORE each phase, there is nothing on disk
     that can tell the two apart -- and a record written only at the end is written by exactly the
     runs that did not need it.
  2. two runtimes install into one host at once. Both are correct; both are writing; neither can
     see the other. The hold makes the second one refuse -- and the hold that matters is the one
     left by the process that was KILLED, because that is the hold nobody will ever release.

The second is where locks usually go wrong, so it is stated plainly: a hold left by a dead run and
a hold held by a slow run are INDISTINGUISHABLE from the disk. Anything that breaks one on its age
breaks the other on its age, and then two writers are in one tree with a reassuring message on the
screen. So the break is a human DECLARATION, by name, and this suite proves that no other way past
exists -- not a flag meaning probably, not a number of minutes.

Nothing here writes a path of its own. The plane is read from the manifest that declares it and
the two document names from the interpreters that write them, so this suite spells no word the kit
does not already own.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
import unittest
from pathlib import Path

from harness import CLI, KIT, Fixtures, Manifest, host_digest

#: Read, never restated: WHERE observed state lives is the manifest's declaration, and WHAT the two
#: documents are called belongs to the interpreters that write them.
import ephemeral  # noqa: E402
import hostlock  # noqa: E402
import init as init_verb  # noqa: E402
import journal as journal_module  # noqa: E402
from journal import ERROR, OK, PENDING, UNSET  # noqa: E402

PLANE = [p["root"].rstrip("/") for p in Manifest(KIT).planes
         if p["class"] == ephemeral.OBSERVED][0]
JOURNAL = f"{PLANE}/{journal_module.NAME}"
LOCK = f"{PLANE}/{hostlock.NAME}"

#: One name for every acceptance this suite signs, so that a record's owner is never this suite's
#: own accident. It is a NAME on a door, and it is the same one every time.
APPROVER = "acceptance-suite"


class Initialization(Fixtures, unittest.TestCase):
    """P-init: a run that dies, and a host two runtimes both want."""

    # -- reading the host -----------------------------------------------------------------------
    def journal(self, host: Path):
        """The journal as it stands right now -- and None while it is mid-rewrite.

        The kit rewrites this document in place at every transition, so a reader polling a LIVE
        run will sometimes catch it truncated. That is a property of the one way this kit writes
        files and not of the journal: the cure is an atomic replace in the workspace port, which
        is named in this slice's report and is not this suite's to invent. A torn read is treated
        as *not yet readable*, never as an absence -- the caller polls again.
        """
        path = host / JOURNAL
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None

    def lock(self, host: Path):
        path = host / LOCK
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

    def phases(self, record, *statuses) -> list:
        return [p["id"] for p in record["phases"] if p["status"] in statuses]

    def killed_mid_init(self, host: Path, *flags) -> dict:
        """Start an init and destroy it where it stands, once its journal says it is inside a
        phase and has not reached the rest.

        Not a simulation, and deliberately not a flag: a flag that asks the interpreter to pretend
        to die tests the pretending. The condition waited for is the one this whole slice exists
        to produce -- a run that has concluded some phases, is inside one, and will never say
        another word about any of them.
        """
        process = subprocess.Popen(
            [sys.executable, str(CLI), "init", "--root", str(host), "--kit", str(KIT),
             "--approve", APPROVER, *flags],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        caught, deadline = None, time.monotonic() + 30.0
        while time.monotonic() < deadline:
            record = self.journal(host)
            if record and self.phases(record, UNSET) and self.phases(record, PENDING):
                caught = record
                break
            if process.poll() is not None:
                break
            time.sleep(0.001)
        alive = process.poll() is None
        process.kill()
        process.wait()
        for _ in range(200):  # the last write may have been torn by the kill itself
            if self.journal(host) is not None:
                break
            time.sleep(0.005)
        self.assertIsNotNone(
            caught, "no journal ever showed a run inside a phase with phases still ahead of it, "
                    "so nothing here was measured: a record written later proves nothing about a "
                    "run that never gets later")
        self.assertTrue(alive, "the init finished before it could be killed, so this test watched "
                               "a healthy run and would have passed either way")
        return self.journal(host)

    # == the journal ============================================================================
    def test_161_every_phase_of_an_init_is_declared_before_the_first_one_runs_and_concluded_after(self):
        """The ordering, measured on a run that survived. Every phase the verb declares is on disk
        the moment the run begins, holding the word for *not entered*; by the end each carries a
        beginning, an ending and a status. A journal that listed only the phases that happened
        could never say which ones did not."""
        host = self.installed()
        record = self.journal(host)

        self.assertEqual([p["id"] for p in init_verb.PHASES],
                         [p["id"] for p in record["phases"]],
                         "the journal's phases are not the phases the verb declares")
        self.assertEqual([], self.phases(record, PENDING, UNSET),
                         "a finished run left a phase saying it never concluded")
        for phase in record["phases"]:
            self.assertEqual(OK, phase["status"])
            self.assertTrue(phase["started_at"] and phase["ended_at"],
                            "a phase with no moments cannot be placed against anything")
            self.assertTrue(phase["does"], "a phase that cannot say what it does names nothing")
        self.assertEqual(OK, record["status"])
        self.assertEqual(0, record["exit_code"])
        self.assertTrue(record["ended_at"])

    def test_162_a_run_that_writes_nothing_takes_no_hold_and_leaves_no_journal(self):
        """A plan touches no byte, so it is not an install and must not read like one. A journal
        of a run that did nothing would measure only itself, and a hold taken for a plan would
        lock a host against a run that was never going to write to it."""
        host = self.host()
        before = host_digest(host)
        result = self.run_kit(KIT, host, "init", "--plan")

        self.assertEqual(0, result.returncode)
        self.assertIsNone(self.journal(host), "a run that wrote nothing left a record of writing")
        self.assertIsNone(self.lock(host), "a plan took a hold on a host it never touched")
        self.assertEqual(before, host_digest(host))

    def test_163_an_init_that_is_killed_leaves_a_journal_naming_the_phase_it_died_inside(self):
        """The hardest case, and the one the mechanism was built inside of. The process is
        destroyed. It never reaches its own close, so its journal says -- permanently -- which
        phase it was in and which phases it never reached. That is the mechanism working."""
        host = self.host()
        dead = self.killed_mid_init(host)

        self.assertNotIn("ended_at", dead, "a run that never ended declared an ending")
        self.assertNotIn("exit_code", dead)
        self.assertEqual(UNSET, dead["status"])

        inside = self.phases(dead, UNSET)
        ahead = self.phases(dead, PENDING)
        self.assertTrue(inside, "the journal does not say which phase the run died inside")
        self.assertTrue(ahead, "the journal does not say which phases were never reached")
        for phase in dead["phases"]:
            if phase["id"] in inside:
                self.assertTrue(phase["started_at"])
                self.assertNotIn("ended_at", phase)
            if phase["id"] in ahead:
                self.assertNotIn("started_at", phase,
                                 "a phase that was never entered claims a beginning")

    def test_164_a_run_that_stalls_at_the_human_door_takes_no_hold_and_journals_nothing(self):
        """Where the mechanism appears is DECLARED, and this is the case that proves the
        declaration is doing the deciding. A run that stops at the human door has written exactly
        the draft it declared: one create-once document, which a killed process leaves either whole
        or absent and never half-interpretable. There is nothing for a journal to disambiguate and
        nothing for a hold to protect -- so neither is written, and a stalled install goes on
        leaving behind precisely what it says it left behind."""
        host = self.host()
        result = self.run_kit(KIT, host, "init")
        self.assertEqual(3, result.returncode, "the draft did not stall at the door")

        self.assertIsNone(self.journal(host), "a run that wrote only its own draft journalled")
        self.assertIsNone(self.lock(host), "a run that wrote only its own draft held the host")

        approved = self.run_kit(KIT, host, "init", "--approve", APPROVER)
        self.assertEqual(0, approved.returncode)
        record = self.journal(host)
        self.assertTrue(record and record["ended_at"],
                        "the run that DID install left no ending, so it reads as dead")
        self.assertTrue(self.lock(host)["released_at"],
                        "the run that DID install walked away still holding the host")

    # == the hold ===============================================================================
    def test_165_a_hold_left_by_a_killed_run_refuses_the_next_runtime_at_a_door(self):
        """Two runtimes, one host. The first was killed and will never release anything. The
        second is refused -- with the whole hold described, because the person about to break it
        needs every fact the disk has: who, which machine, which pid, since when."""
        host = self.host()
        self.killed_mid_init(host)
        hold = self.lock(host)
        self.assertNotIn("released_at", hold, "a killed run released its hold, which it cannot do")

        before = host_digest(host)
        result = self.run_kit(KIT, host, "init", "--approve", APPROVER)

        self.assertEqual(3, result.returncode, "a second runtime walked into a held host")
        self.assertIn("already held", result.stderr)
        for fact in ("owner", "machine", "pid", "started_at"):
            self.assertIn(str(hold[fact]), result.stderr,
                          f"the refusal does not say {fact}, so nobody can check the holder")
        self.assertIn("--break-lock", result.stderr,
                      "a refusal that does not say how to get past it is a dead end")
        self.assertEqual(before, host_digest(host),
                         "a run refused at the hold wrote to the host anyway")

    def test_166_no_amount_of_elapsed_time_breaks_a_hold_and_only_a_name_does(self):
        """The rule the whole design turns on. A hold from a dead run and a hold from a slow run
        are the same bytes; anything that breaks one on its age breaks the other on its age, and
        then there are two writers in one tree. So the hold is dated far in the past and asked
        again -- and refused again -- and then broken by a NAME, which is recorded where it will
        outlive the hold it broke."""
        host = self.installed()
        self.killed_mid_init(host)

        aged = self.lock(host)
        aged["started_at"] = "1970-01-01T00:00:00+00:00"
        (host / LOCK).write_text(json.dumps(aged, indent=2) + "\n", encoding="utf-8")

        stale = self.run_kit(KIT, host, "init", "--approve", APPROVER)
        self.assertEqual(3, stale.returncode,
                         "a hold was broken because it looked old, which resurrects a run that "
                         "was merely slow and puts two writers in one tree")
        self.assertIn("already held", stale.stderr)

        broken = self.run_kit(KIT, host, "init", "--break-lock", "a-named-person",
                              "--approve", APPROVER)
        self.assertNotEqual(3, broken.returncode,
                            "breaking the hold by name did not let the init proceed")
        self.assertNotEqual(aged["run_id"], self.lock(host)["run_id"],
                            "the hold was never re-taken, so nothing here was broken")
        self.assertEqual("a-named-person", self.lock(host)["broke"]["by"])
        declared = self.journal(host)["broke_lock"]
        self.assertEqual("a-named-person", declared["by"])
        self.assertEqual(aged["run_id"], declared["previous"]["run_id"],
                         "the record of the break does not say WHICH hold was broken")
        self.assertTrue(declared["at"], "a declaration with no moment cannot be placed")

    def test_167_the_run_after_a_dead_one_resumes_from_its_record_and_says_what_it_inherited(self):
        """A re-run is not a fresh run and must never read like one. It reads the dead run's
        journal, states which phase that run was inside, what it had concluded and what it never
        reached, and carries the whole superseded record forward rather than overwriting it into
        silence. What it does NOT do is skip work on the strength of a document: every init phase
        is idempotent by construction, so continuing means replaying from the record."""
        host = self.installed()
        dead = self.killed_mid_init(host)

        result = self.run_kit(KIT, host, "init", "--break-lock", "a-named-person",
                              "--approve", APPROVER)
        self.assertIn("resuming", result.stdout,
                      "the run after a dead one says nothing about the run it followed")

        resumed = self.journal(host)["resumed_from"]
        self.assertEqual(dead["run_id"], resumed["run_id"])
        self.assertEqual(self.phases(dead, UNSET), resumed["interrupted_in"])
        self.assertEqual(self.phases(dead, PENDING), resumed["never_reached"])
        self.assertEqual(self.phases(dead, OK, ERROR), resumed["concluded"])
        self.assertEqual(dead, resumed["record"],
                         "the superseded record was not carried, so a dead run's evidence was "
                         "destroyed by the run that read it")
        self.assertNotEqual(dead["run_id"], self.journal(host)["run_id"],
                            "the resuming run adopted the dead run's identity")

        ended = self.journal(host)
        self.assertTrue(ended["ended_at"] and ended["status"],
                        "the run that read a dead one left no ending of its own")

        again = self.run_kit(KIT, host, "init", "--approve", APPROVER)
        self.assertNotIn("resuming", again.stdout,
                         "a run that followed a run which ENDED reported a resumption anyway")
        self.assertIsNone(self.journal(host).get("resumed_from"))


if __name__ == "__main__":
    unittest.main()
