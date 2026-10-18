"""Acceptance: a published starter carries an empty repository to a served, checked install (ADR-023).

Every act a new host needs has its own door; a STARTER declares the walk once and `start` walks it
under one name. Each starter published beside the kit is held to:

  1. it honours the starter schema, and every directory it takes declares a capability;
  2. `--plan` and an unapproved start write nothing;
  3. approved, on an empty repository, the walk ends with `check` green, composed as
     `kit <v> + taken: <every id it takes>`, and the served settings it activates read ACTIVE;
  4. a starter that takes a directory declaring no capability is refused by its code, and nothing
     is written.

Every path, id and code is read from the starter, the schema or the module that owns it.
"""

from __future__ import annotations

import json
import unittest

from harness import KIT, REPO, Fixtures, host_digest

import validation
from errors import PendingApproval
from manifest import Manifest
from test_pinned_kit import said
from test_retake import FILE
import manifest as manifest_port
from verbs.start import SCHEMA, StartError

CORE = Manifest(KIT)
DECLARATION = next(i for c in CORE.capabilities for i in c.installs
                   if i["mode"] == manifest_port.TAKEN_MODE)["declaration"]
STARTERS = sorted((REPO / "starters").glob("*.json"))
SHAPE = json.loads((KIT / json.loads((KIT / "MANIFEST.json").read_text(encoding="utf-8"))["schemas"][SCHEMA])
                   .read_text(encoding="utf-8"))


def _starter(path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Start(Fixtures, unittest.TestCase):

    def start(self, host, starter, *flags):
        return self.run_kit(KIT, host, "start", "--path", str(starter), *flags)

    def test_407_every_published_starter_honours_its_schema_and_takes_only_capabilities(self):
        self.assertTrue(STARTERS, "ADR-023 publishes at least one starter")
        for path in STARTERS:
            with self.subTest(starter=path.name):
                value = _starter(path)
                self.assertEqual([], validation.validate(value, SHAPE))
                for rel in value["takes"]:
                    self.assertTrue((path.parent / rel / DECLARATION).is_file(), rel)

    def test_408_a_starter_walks_an_empty_repository_to_a_green_check_and_only_through_its_door(self):
        for path in STARTERS:
            value = _starter(path)
            with self.subTest(starter=value["id"]):
                host = self.host()
                before = host_digest(host)
                self.assertEqual(0, self.start(host, path, "--plan").returncode)
                self.assertEqual(PendingApproval.exit_code, self.start(host, path).returncode)
                self.assertEqual(before, host_digest(host), "a plan or an unapproved start wrote")

                ran = self.start(host, path, "--approve", "acceptance-suite")
                self.assertEqual(0, ran.returncode, said(ran))
                # One line per act is printed and the rest is kept, never dropped (CWE-222): the walk
                # names where, keeps every act's whole output there, and shows the closing check's own
                # verdict -- which is the walk's one check, never repeated on the same bytes.
                kept = ran.stdout.rsplit("Every act's whole output: ", 1)[1].strip()
                log = (host / kept).read_text(encoding="utf-8")
                self.assertIn("$ take --path", log)
                self.assertTrue(log.rstrip().endswith("gate(s) failed"), log[-400:])
                self.assertIn("  check: 0 gate(s) failed", ran.stdout)
                self.assertNotIn("[check exit", ran.stdout)
                checked = self.run_kit(KIT, host, "check")
                self.assertEqual(0, checked.returncode, said(checked))
                ids = sorted(json.loads((path.parent / rel / DECLARATION).read_text(
                    encoding="utf-8"))["id"] for rel in value["takes"])
                self.assertIn(f"kit {CORE.version} + taken: {', '.join(ids)}", checked.stdout)
                for surface in value["activate"]:
                    self.assertIn(f"{surface}: ACTIVE", checked.stdout)

    def test_410_a_host_that_already_answered_is_walked_again_to_green(self):
        # Its own run record would stand open across every act it starts, and each act's check would
        # read it as a run that died: a walk is observed through its acts (ADR-023 amendment 1).
        host = self.host()
        for _ in range(2):
            ran = self.start(host, STARTERS[0], "--approve", "acceptance-suite")
            self.assertEqual(0, ran.returncode, said(ran))
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode)
        # The second walk wrote no runtime over the host's own, and says so -- never as if it had.
        runtimes = _starter(STARTERS[0])["runtimes"]
        if runtimes:
            self.assertIn(f"[runtimes written: none; the host's own kept: {', '.join(r['id'] for r in runtimes)}]",
                          ran.stdout)

    def test_411_an_answered_host_whose_reading_moved_is_walked_to_green(self):
        # The opening acts are for a host with no kit; on one that has accepted its answer they would
        # judge a stale reading before the walk could retake it (ADR-023 amendment 4).
        host = self.host()
        self.assertEqual(0, self.start(host, STARTERS[0], "--approve", "acceptance-suite").returncode)
        moved = host / "apps" / FILE
        moved.parent.mkdir(parents=True)
        moved.write_text("{}\n", encoding="utf-8")
        ran = self.start(host, STARTERS[0], "--approve", "acceptance-suite")
        self.assertEqual(0, ran.returncode, said(ran))
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode)

    def test_409_a_starter_that_takes_no_capability_is_refused_and_nothing_is_written(self):
        host = self.host()
        bad = self._temp("starter") / "bad.json"
        bad.write_text(json.dumps({**_starter(STARTERS[0]), "takes": ["."]}), encoding="utf-8")
        before = host_digest(host)
        ran = self.start(host, bad, "--approve", "acceptance-suite")
        self.assertIn(f"[{StartError.code}]", said(ran))
        self.assertEqual(before, host_digest(host))
