"""Acceptance: a change is weighed before it is walked (ADR-025).

  1. a host that declared no area weighs every change `standard`: its commit is its whole record;
  2. one path in an irreversible area makes the working change `major`, with what it owes;
  3. a declared class lighter than the computed one is refused by name, a heavier one admitted;
  4. an area that names an undo cost nobody declared is refused rather than guessed at.

Reached only through the CLI, on a host that walked the door.
"""

from __future__ import annotations

import json
import subprocess
import unittest

from harness import KIT, Fixtures, install_target

AREAS = install_target("delivery", reads_as="areas")


class Weigh(Fixtures, unittest.TestCase):

    def declare(self, host, *rows, **extra):
        body = {"schema_version": 1, "default_undo": "reversible", "max_areas": {}, **extra,
                "areas": [{"id": i, "paths": p, "undo": u, "because": "a fixture"} for i, p, u in rows]}
        (host / AREAS).write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8", newline="\n")

    def test_10_a_host_with_no_areas_weighs_a_change_standard(self):
        host = self.installed()
        self.assertTrue((host / AREAS).is_file(), "the areas seed was not installed")
        said = self.run_kit(KIT, host, "weigh", "--path", "src/app.py")
        self.assertEqual(0, said.returncode, said.stderr)
        self.assertIn("weigh: standard", said.stdout)
        self.assertIn("requires: commit\n", said.stdout)

    def test_20_one_irreversible_path_makes_the_working_change_major(self):
        host = self.installed()
        self.declare(host, ("migrations", r"^db/migrations/", "irreversible"))
        (host / "db" / "migrations").mkdir(parents=True)
        (host / "db" / "migrations" / "0001.sql").write_text("create table t (id int);\n", encoding="utf-8")
        said = self.run_kit(KIT, host, "weigh")
        self.assertEqual(0, said.returncode, said.stderr)
        self.assertIn("weigh: major", said.stdout)
        self.assertIn("area migrations (irreversible): 1 path(s)", said.stdout)
        self.assertIn("decision", said.stdout)
        self.assertIn("door:", said.stdout)

    def test_30_a_lighter_declaration_is_refused_and_a_heavier_one_admitted(self):
        host = self.installed()
        self.declare(host, ("contracts", r"^api/", "costly"))
        refused = self.run_kit(KIT, host, "weigh", "--path", "api/orders.json", "--class", "standard")
        self.assertNotEqual(0, refused.returncode)
        self.assertIn("KIT0086", refused.stdout + refused.stderr)
        self.assertIn("'normal'", refused.stdout + refused.stderr)
        admitted = self.run_kit(KIT, host, "weigh", "--path", "api/orders.json", "--class", "major")
        self.assertEqual(0, admitted.returncode, admitted.stderr)

    def test_40_an_undo_cost_nobody_declared_is_refused(self):
        host = self.installed()
        self.declare(host, ("a", r"^a/", "fatal"))
        said = self.run_kit(KIT, host, "weigh", "--path", "a/x")
        self.assertNotEqual(0, said.returncode)
        self.assertIn("KIT0085", said.stdout + said.stderr)

    def test_50_a_range_is_weighed_from_git(self):
        host = self.installed()
        self.declare(host, ("migrations", r"^db/migrations/", "irreversible"))
        git = lambda *a: subprocess.run(["git", "-C", str(host), *a], check=True, capture_output=True, text=True)
        git("add", "-A"); git("commit", "-q", "-m", "base")
        (host / "db" / "migrations").mkdir(parents=True)
        (host / "db" / "migrations" / "0002.sql").write_text("alter table t add c int;\n", encoding="utf-8")
        git("add", "-A"); git("commit", "-q", "-m", "migrate")
        said = self.run_kit(KIT, host, "weigh", "--base", "HEAD~1", "--head", "HEAD")
        self.assertEqual(0, said.returncode, said.stderr)
        self.assertIn("weigh: major", said.stdout)


    def test_70_a_card_that_declares_a_class_keeps_what_it_owes_and_a_classless_one_is_passed_over(self):
        host = self.installed()
        cards = host / install_target("delivery", reads_as="cards")
        cards.mkdir(parents=True, exist_ok=True)

        def card(identity, **fields):
            body = {"schema_version": 1, "id": identity, "title": identity, "state": "in-flight",
                    "created_at": "2026-10-17T00:00:00+00:00", **fields}
            (cards / f"{identity}.json").write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8", newline="\n")

        card("classless")
        self.assertIn("PASS  FF-WORK-CLASSES", self._failed(host))
        card("bare-major", **{"class": "major"})
        card("too-light", **{"class": "normal", "uncertainty": "complex"})
        failed = self._failed(host)
        self.assertIn("bare-major: a major card owes its criteria", failed)
        self.assertIn("bare-major: a major card owes its appetite", failed)
        self.assertIn("too-light: shaped normal, but complex work walks at least program", failed)
        self.assertNotIn("classless", failed)

    def _failed(self, host) -> str:
        said = self.run_kit(KIT, host, "check")
        return said.stdout + said.stderr


import test_commit_gate as commit_gate  # noqa: E402 -- its fixtures: a served host whose git hooks are live


class WorkClassFloor(commit_gate.CommitGate):
    """5. activated, git itself refuses a commit that owes a card it does not name, and records it
    once the card is named and being built -- and a standard commit pays nothing."""

    locals().update({name: None for name in dir(commit_gate.CommitGate) if name.startswith("test_")})

    def test_60_git_refuses_a_heavy_commit_without_its_card_and_records_it_with_one(self):
        surface = self.activating[0]
        host = self.repository()
        self.assertEqual(0, self.activate(host, surface, "--approve", "fixture-owner").returncode)
        areas = {"schema_version": 1, "default_undo": "reversible", "max_areas": {},
                 "areas": [{"id": "migrations", "paths": "^db/migrations/", "undo": "irreversible",
                            "because": "a fixture"}]}
        (host / AREAS).write_text(json.dumps(areas, indent=2) + "\n", encoding="utf-8", newline="\n")
        commit_gate._git(host, "add", "-A")
        light = commit_gate._git(host, "commit", "-m", "chore: declare the areas", check=False)
        self.assertEqual(0, light.returncode, light.stdout + light.stderr)

        (host / "db" / "migrations").mkdir(parents=True)
        (host / "db" / "migrations" / "0001.sql").write_text("create table t (id int);\n", encoding="utf-8", newline="\n")
        commit_gate._git(host, "add", "-A")
        refused = commit_gate._git(host, "commit", "-m", "feat: the first table", check=False)
        self.assertNotEqual(0, refused.returncode, refused.stdout + refused.stderr)
        self.assertIn("KIT0086", refused.stderr)
        self.assertIn("owes a card", refused.stderr)

        cards = host / install_target("delivery", reads_as="cards")
        cards.mkdir(parents=True, exist_ok=True)
        (cards / "first-table.json").write_text(json.dumps(
            {"schema_version": 1, "id": "first-table", "title": "the first table", "state": "in-flight",
             "class": "major", "created_at": "2026-10-17T00:00:00+00:00"}, indent=2) + "\n",
            encoding="utf-8", newline="\n")
        commit_gate._git(host, "add", "-A")
        named = commit_gate._git(host, "commit", "-m", "feat: the first table\n\nCard: first-table", check=False)
        self.assertEqual(0, named.returncode, named.stdout + named.stderr)


if __name__ == "__main__":
    unittest.main()
