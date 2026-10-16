"""Acceptance: a packet names what ends the run, and is routed by the HOST's table (ADR-022, slice S1).

The dispatch port (ADR-017) started a worker on four facts: which task, where, what, on which branch.
The prior system learned at cost that this is not enough to run a team economically: a task with no
nameable deliverable cannot terminate, a route chosen by feeling puts the strongest mind on work a
cheap one would finish, and a worker that returns only text cannot say what it cost, what it found
or whether its brief was any good. Held here:

  1. the packet kind is at version 2 and a version-1 packet is refused by the reader rule (ADR-009);
  2. with no route table cell declared, a task is carried and the record SAYS nothing was judged;
  3. with cells declared, a packet whose pair has no cell, whose role or ceiling disagrees with its
     cell, or that names an undeclared verification profile is refused before a worker starts;
  4. a named verification profile runs in the worker's tree on return: passing, the task completes
     with the result recorded; failing, it closes FAILED by the profile's name;
  5. an adapter that declares an artifact CARRIES the return has it parsed and validated: a valid
     return is recorded; one missing its economy closes the task FAILED, by name.

Every path, version and code is read from the declaration or module that owns it.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from harness import KIT, Fixtures

import dispatch_port
import dispatching
from context import Context
from manifest import Manifest, OlderDocument

from test_adapters import ADAPTERS, adapted_kit
from test_dispatch import ADAPTER, DIAGNOSTIC, WROTE, fixture_adapter, packet

CORE = Manifest(KIT)
ROUTES = next(i["target"] for c in CORE.capabilities for i in c.installs
              if i.get("validates") == dispatching.ROUTES["validates"])
RESULT = "result"

#: A worker that hands back a STRUCTURED return on stdout. Its first argument is its dispatch id; its
#: instruction decides whether the return is complete -- the one switch a packet legitimately carries.
RETURNER = (
    "import json, pathlib, sys" "\n"
    f"pathlib.Path({WROTE!r}).write_text('returned', encoding='utf-8')" "\n"
    "full = dict(schema_version=1, id=sys.argv[1], deliverable=dict(status='delivered', at='" + WROTE + "'),"
    " economy=dict(calls=3, peak_context=4000, not_read=[dict(what='the archive', why='not needed')]),"
    " findings=[dict(what='a stale comment', relation='unrelated')],"
    " brief_quality=dict(grade='problem-and-goal', judgement=['chose the file name']))" "\n"
    "if sys.argv[2] == 'incomplete': full.pop('economy')" "\n"
    "print(json.dumps(full))" "\n"
)
RETURNING = fixture_adapter(
    "an-intelligence-that-returns",
    starts={"argv": [sys.executable, "-c", RETURNER, "{id}", "{instruction}"]},
    returns=[{"name": RESULT, "from": "stdout", "media_type": "application/json",
              "carries": dispatching.RETURN},
             {"name": DIAGNOSTIC, "from": "stderr"}],
)


class Routing(Fixtures, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.kit = adapted_kit(adapters=[*ADAPTERS, ADAPTER, RETURNING])
        cls.verb = next(p.stem for p in Path(dispatch_port.__file__).parent.parent.joinpath("verbs").glob("*.py")
                        if "dispatch" in p.stem)

    def repository(self) -> Path:
        host = self.installed(self.kit)
        env = dict(os.environ, GIT_AUTHOR_NAME="fixture", GIT_AUTHOR_EMAIL="f@example.invalid",
                   GIT_COMMITTER_NAME="fixture", GIT_COMMITTER_EMAIL="f@example.invalid")
        for argv in (["add", "-A"], ["commit", "-q", "--no-verify", "-m", "the installed host"]):
            ran = subprocess.run(["git", *argv], cwd=host, capture_output=True, text=True, env=env)
            self.assertEqual(0, ran.returncode, ran.stderr)
        return host

    def routes(self, host: Path, cells=(), profiles=()) -> None:
        (host / ROUTES).write_text(json.dumps({"schema_version": 1, "cells": list(cells),
                                                "profiles": list(profiles)}, indent=2) + "\n",
                                   encoding="utf-8", newline="\n")

    def dispatched(self, host: Path, handed: dict):
        result = subprocess.run(
            [sys.executable, str(Path(dispatch_port.__file__).parent.parent / "cli.py"), self.verb,
             "--root", str(host), "--kit", str(self.kit)],
            input=json.dumps(handed), capture_output=True, text=True)
        print(f"\n$ {self.verb} <<< {handed['id']}\n[exit {result.returncode}]\n{result.stdout}{result.stderr}")
        return result

    def record(self, host: Path, identity: str) -> dict:
        ctx = Context(kit_root=self.kit, host_root=host)
        return json.loads((host / dispatching.home(ctx, identity, "task.json")).read_text(encoding="utf-8"))

    # == 1. the version ==========================================================================
    def test_360_a_version_1_packet_is_refused_by_the_reader_rule(self):
        self.assertGreater(CORE.version_of(dispatching.PACKET), 1)
        host = self.repository()
        said = self.dispatched(host, packet("an-old-packet", schema_version=1))
        self.assertNotEqual(0, said.returncode)
        self.assertIn(f"[{OlderDocument.code}]", said.stderr)

    # == 2. the declared zero ====================================================================
    def test_361_with_no_cell_declared_a_task_is_carried_and_the_record_says_nothing_was_judged(self):
        host = self.repository()
        said = self.dispatched(host, packet("carried-unjudged"))
        self.assertEqual(0, said.returncode, said.stdout + said.stderr)
        task = self.record(host, "carried-unjudged")
        self.assertIsNone(task["route"]["cell"])
        self.assertIn("no route table cell", task["route"]["says"])

    # == 3. the table judges =====================================================================
    def test_362_a_packet_that_disagrees_with_its_cell_is_refused_before_a_worker_starts(self):
        host = self.repository()
        self.routes(host, cells=[{"id": "low-cheap", "decision_density": "low", "reversibility": "cheap",
                                  "role": "a-worker", "ceiling_chars": 12}],
                    profiles=[{"id": "passes", "argv": [sys.executable, "-c", "pass"], "timeout_s": 30}])
        refused = {
            "no cell holds the pair": packet("no-cell", decision_density="high"),
            "the role disagrees": packet("wrong-role", role="another-worker", instruction="short"),
            "the ceiling is passed": packet("too-long"),
            "the profile is undeclared": packet("unnamed-profile", instruction="short", profile="nobody"),
        }
        for why, handed in refused.items():
            with self.subTest(refusal=why):
                said = self.dispatched(host, handed)
                self.assertEqual(1, said.returncode, said.stdout + said.stderr)
                self.assertIn(f"[{dispatching.DispatchRefused.code}]", said.stderr)
        accepted = self.dispatched(host, packet("fits-its-cell", instruction="short"))
        self.assertEqual(0, accepted.returncode, accepted.stdout + accepted.stderr)
        self.assertEqual("low-cheap", self.record(host, "fits-its-cell")["route"]["cell"])

    # == 4. the profile ==========================================================================
    def test_363_a_named_profile_runs_in_the_workers_tree_and_its_failure_closes_the_task(self):
        host = self.repository()
        self.routes(host, profiles=[
            {"id": "finds-the-file", "timeout_s": 30,
             "argv": [sys.executable, "-c", f"import pathlib,sys; sys.exit(0 if pathlib.Path({WROTE!r}).is_file() else 3)"]},
            {"id": "always-fails", "timeout_s": 30, "argv": [sys.executable, "-c", "import sys; sys.exit(3)"]}])
        said = self.dispatched(host, packet("verified", profile="finds-the-file"))
        self.assertEqual(0, said.returncode, said.stdout + said.stderr)
        task = self.record(host, "verified")
        self.assertEqual(dispatching.COMPLETED, task["state"])
        self.assertTrue(task["verification"]["passed"])
        said = self.dispatched(host, packet("unverified", profile="always-fails"))
        self.assertNotEqual(0, said.returncode)
        task = self.record(host, "unverified")
        self.assertEqual(dispatching.FAILED, task["state"])
        self.assertIn("always-fails", task["status_message"])

    # == 5. the return ===========================================================================
    def test_364_a_carried_return_is_validated_and_an_incomplete_one_closes_the_task(self):
        host = self.repository()
        said = self.dispatched(host, packet("returns-whole", route=RETURNING.name, instruction="whole"))
        self.assertEqual(0, said.returncode, said.stdout + said.stderr)
        task = self.record(host, "returns-whole")
        self.assertEqual(dispatching.COMPLETED, task["state"])
        self.assertEqual("delivered", task["return"]["deliverable"]["status"])
        self.assertEqual("the archive", task["return"]["economy"]["not_read"][0]["what"])
        said = self.dispatched(host, packet("returns-short", route=RETURNING.name, instruction="incomplete"))
        self.assertNotEqual(0, said.returncode)
        task = self.record(host, "returns-short")
        self.assertEqual(dispatching.FAILED, task["state"])
        self.assertIn(dispatching.RETURN, task["status_message"])
        self.assertIn("economy", task["status_message"])

    # == 6. the ground the packet cites (S2) =====================================================
    def test_365_a_packet_citing_a_ground_that_moved_is_refused_before_a_worker_starts(self):
        host = self.repository()
        (host / "measured.txt").write_text("as it was\n", encoding="utf-8", newline="\n")
        ground = [sys.executable, str(Path(dispatch_port.__file__).parent.parent / "cli.py"), "ground",
                  "--root", str(host), "--kit", str(self.kit)]
        recorded = subprocess.run([*ground, "--key", "the-measured-file", "--fact", "one line",
                                   "--instrument", "read measured.txt", "--path", "measured.txt"],
                                  capture_output=True, text=True)
        self.assertEqual(0, recorded.returncode, recorded.stdout + recorded.stderr)
        cited = [{"fact": "one line", "instrument": "read measured.txt", "key": "the-measured-file"}]
        fresh = self.dispatched(host, packet("grounded-fresh", ground=cited))
        self.assertEqual(0, fresh.returncode, fresh.stdout + fresh.stderr)
        (host / "measured.txt").write_text("moved since\n", encoding="utf-8")
        stale = self.dispatched(host, packet("grounded-stale", ground=cited))
        self.assertEqual(1, stale.returncode, stale.stdout + stale.stderr)
        self.assertIn(f"[{dispatching.DispatchRefused.code}]", stale.stderr)
        self.assertIn("measured.txt", stale.stderr)

    # == 7. what the work cost (S3) ==============================================================
    def test_366_a_returned_economy_is_a_measure_a_host_budgets_and_a_breach_fails(self):
        import economy
        host = self.repository()
        said = self.dispatched(host, packet("returns-its-cost", route=RETURNING.name, instruction="whole"))
        self.assertEqual(0, said.returncode, said.stdout + said.stderr)
        peak = self.record(host, "returns-its-cost")["return"]["economy"]["peak_context"]
        maps = host / next(i["target"] for c in CORE.capabilities for i in c.installs
                           if i.get("reads_as") == "corpus_maps")
        maps.mkdir(parents=True, exist_ok=True)
        for ceiling, code in ((peak, 0), (peak - 1, 1)):
            with self.subTest(ceiling=ceiling):
                (maps / "map.json").write_text(json.dumps({
                    "schema_version": 1, "id": "economy-budget",
                    "places": [{"path": "docs/decisions/", "holds": "decision"}],
                    "budgets": [{"measures": economy.PEAK, "ceiling": ceiling, "measured": "2026-10-15"}]},
                    indent=2) + "\n", encoding="utf-8", newline="\n")
                cli = [sys.executable, str(Path(dispatch_port.__file__).parent.parent / "cli.py")]
                subprocess.run([*cli, "render", "--root", str(host), "--kit", str(self.kit)], capture_output=True)
                checked = subprocess.run([*cli, "check", "--root", str(host), "--kit", str(self.kit)],
                                         capture_output=True, text=True)
                self.assertEqual(code, checked.returncode, checked.stdout[-3000:])
                if code:
                    self.assertIn(economy.PEAK, checked.stdout)


if __name__ == "__main__":
    unittest.main()
