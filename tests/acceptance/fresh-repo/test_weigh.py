"""Acceptance: a change is weighed before it is walked (ADR-025).

  1. a host that declared no area weighs every change `standard`: its commit is its whole record;
  2. one path in an irreversible area makes the working change `major`, with what it owes;
  3. a declared class lighter than the computed one is refused by name, a heavier one admitted;
  4. an area that names an undo cost nobody declared is refused rather than guessed at.

Reached only through the CLI, on a host that walked the door.
"""

from __future__ import annotations

import json
import os
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

    def test_80_a_criterion_that_needs_a_test_is_not_proved_by_a_file_being_there(self):
        host = self.installed()
        cards = host / install_target("delivery", reads_as="cards")
        cards.mkdir(parents=True, exist_ok=True)
        report = "docs/work/evidence/orders/tests.xml"
        (host / report).parent.mkdir(parents=True)
        (host / report).write_text('<testsuite tests="4" failures="0" errors="0"/>\n', encoding="utf-8")

        def card(kind):
            body = {"schema_version": 1, "id": "orders", "title": "orders", "state": "in-flight",
                    "created_at": "2026-10-17T00:00:00+00:00",
                    "criteria": [{"id": "suite-green", "statement": "the suite passes", "needs": "tested",
                                  "proof": {"kind": kind, "ref": report}}]}
            (cards / "orders.json").write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8", newline="\n")

        card("artifact-present")
        refused = self.run_kit(KIT, host, "move", "--card", "orders", "--to", "verified", "--by", "dev")
        self.assertNotEqual(0, refused.returncode)
        self.assertIn("needs tested", refused.stdout + refused.stderr)
        card("test-report-passed")
        moved = self.run_kit(KIT, host, "move", "--card", "orders", "--to", "verified", "--by", "dev")
        self.assertEqual(0, moved.returncode, moved.stdout + moved.stderr)

    def test_90_a_finding_is_one_card_in_the_initial_state_with_where_it_was_found(self):
        host = self.installed()
        cards = host / install_target("delivery", reads_as="cards")
        cards.mkdir(parents=True, exist_ok=True)
        (cards / "orders.json").write_text(json.dumps(
            {"schema_version": 1, "id": "orders", "title": "orders", "state": "in-flight",
             "created_at": "2026-10-17T00:00:00+00:00"}, indent=2) + "\n", encoding="utf-8", newline="\n")
        planned = self.run_kit(KIT, host, "capture", "--card", "slow-query", "--title", "a slow query",
                               "--by", "dev", "--from", "orders", "--plan")
        self.assertEqual(0, planned.returncode, planned.stderr)
        self.assertFalse((cards / "slow-query.json").exists(), "--plan wrote a byte")
        made = self.run_kit(KIT, host, "capture", "--card", "slow-query", "--title", "a slow query",
                            "--by", "dev", "--from", "orders")
        self.assertEqual(0, made.returncode, made.stderr)
        card = json.loads((cards / "slow-query.json").read_text(encoding="utf-8"))
        self.assertEqual("intake", card["state"])
        self.assertTrue(card["origin"]["ref"].endswith("orders.json"))
        again = self.run_kit(KIT, host, "capture", "--card", "slow-query", "--title", "x", "--by", "dev")
        self.assertNotEqual(0, again.returncode)
        self.assertIn("KIT0088", again.stdout + again.stderr)

    def test_95_a_deferral_is_due_when_its_trigger_holds_and_counted_when_it_has_none(self):
        host = self.installed()
        cards = host / install_target("delivery", reads_as="cards")
        cards.mkdir(parents=True, exist_ok=True)

        def parked(identity, **fields):
            body = {"schema_version": 1, "id": identity, "title": identity, "state": "parked",
                    "created_at": "2026-10-17T00:00:00+00:00", **fields}
            (cards / f"{identity}.json").write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8", newline="\n")

        parked("when-billing-exists", due_when={"kind": "artifact-present", "ref": "src/billing/README.md"})
        parked("someday")
        quiet = self._failed(host)
        self.assertIn("PASS  FF-WORK-DEFERRALS", quiet)
        self.assertIn("deferred with no trigger: 1 -- someday", quiet)
        (host / "src" / "billing").mkdir(parents=True)
        (host / "src" / "billing" / "README.md").write_text("billing\n", encoding="utf-8")
        due = self._failed(host)
        self.assertIn("when-billing-exists: DUE", due)

    def test_96_a_phase_starts_only_after_the_phases_before_it_and_finished_work_that_stops_holding_regresses(self):
        host = self.installed()
        cards = host / install_target("delivery", reads_as="cards")
        cards.mkdir(parents=True, exist_ok=True)

        def card(identity, state, **fields):
            body = {"schema_version": 1, "id": identity, "title": identity, "state": state,
                    "created_at": "2026-10-17T00:00:00+00:00", **fields}
            (cards / f"{identity}.json").write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8", newline="\n")

        card("protect", "in-flight")
        card("migrate", "bet", after=["protect"])
        held = self.run_kit(KIT, host, "move", "--card", "migrate", "--to", "in-flight", "--by", "dev")
        self.assertNotEqual(0, held.returncode)
        self.assertIn("protect (in-flight)", held.stdout + held.stderr)

        report = host / "docs" / "work" / "evidence" / "protect" / "suite.xml"
        report.parent.mkdir(parents=True)
        report.write_text('<testsuite tests="2" failures="0" errors="0"/>\n', encoding="utf-8")
        card("protect", "landed", criteria=[{"id": "suite", "statement": "the suite passes",
                                             "proof": {"kind": "test-report-passed",
                                                       "ref": "docs/work/evidence/protect/suite.xml"}}])
        moved = self.run_kit(KIT, host, "move", "--card", "migrate", "--to", "in-flight", "--by", "dev")
        self.assertEqual(0, moved.returncode, moved.stdout + moved.stderr)
        self.assertIn("PASS  FF-WORK-ORDER", self._failed(host))

        report.write_text('<testsuite tests="2" failures="1" errors="0"/>\n', encoding="utf-8")
        self.assertIn("protect: REGRESSED -- finished, and suite no longer holds; it came before migrate",
                      self._failed(host))

        card("a", "shaped", after=["b"])
        card("b", "shaped", after=["a"])
        self.assertIn("the order is a cycle", self._failed(host))

    def test_97_an_emergency_is_a_debt_with_a_clock_and_a_card_repays_it(self):
        host = self.installed()
        policy = host / install_target("delivery", reads_as="policy")
        body = json.loads(policy.read_text(encoding="utf-8"))
        policy.write_text(json.dumps({**body, "emergency_debt_days": 3}, indent=2) + "\n", encoding="utf-8", newline="\n")
        env = dict(os.environ, GIT_AUTHOR_NAME="f", GIT_AUTHOR_EMAIL="f@example.invalid", GIT_COMMITTER_NAME="f",
                   GIT_COMMITTER_EMAIL="f@example.invalid", GIT_COMMITTER_DATE="2026-01-01T00:00:00+00:00")
        git = lambda *a: subprocess.run(["git", "-C", str(host), *a], check=True, capture_output=True, text=True, env=env)
        git("add", "-A")
        git("commit", "-q", "--no-verify", "-m", "fix: restore service\n\nWork-Class: emergency")
        sha = git("rev-parse", "HEAD").stdout.strip()
        self.assertIn(f"{sha[:12]}: an emergency change", self._failed(host))
        cards = host / install_target("delivery", reads_as="cards")
        cards.mkdir(parents=True, exist_ok=True)
        (cards / "postmortem.json").write_text(json.dumps(
            {"schema_version": 1, "id": "postmortem", "title": "pay the restore", "state": "intake",
             "created_at": "2026-10-17T00:00:00+00:00", "repays": [sha[:10]]}, indent=2) + "\n",
            encoding="utf-8", newline="\n")
        self.assertIn("PASS  FF-WORK-EMERGENCY", self._failed(host))

    def test_98_the_board_counts_finished_work_whole_and_lists_only_its_newest(self):
        host = self.installed()
        policy = host / install_target("delivery", reads_as="policy")
        body = json.loads(policy.read_text(encoding="utf-8"))
        policy.write_text(json.dumps({**body, "board_recent": 1}, indent=2) + "\n", encoding="utf-8", newline="\n")
        cards = host / install_target("delivery", reads_as="cards")
        cards.mkdir(parents=True, exist_ok=True)
        for n in range(3):
            (cards / f"done-{n}.json").write_text(json.dumps(
                {"schema_version": 1, "id": f"done-{n}", "title": f"done {n}", "state": "landed",
                 "created_at": f"2026-10-1{n}T00:00:00+00:00"}, indent=2) + "\n", encoding="utf-8", newline="\n")
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        board = (host / install_target("delivery", mode="projection")).read_text(encoding="utf-8")
        self.assertIn("3 card(s)", board)
        self.assertIn("2 older finished card(s) are counted here and not listed", board)
        self.assertIn("**done-2**", board)
        self.assertNotIn("**done-0**", board)

    def test_99_finished_cards_past_the_declared_age_leave_for_the_archive_unless_working_cards_name_them(self):
        host = self.installed()
        cards = host / install_target("delivery", reads_as="cards")
        cards.mkdir(parents=True, exist_ok=True)

        def card(identity, state, created, **fields):
            (cards / f"{identity}.json").write_text(json.dumps(
                {"schema_version": 1, "id": identity, "title": identity, "state": state, "created_at": created,
                 **fields}, indent=2) + "\n", encoding="utf-8", newline="\n")

        card("old-done", "landed", "2026-01-01T00:00:00+00:00")
        card("old-needed", "landed", "2026-01-01T00:00:00+00:00")
        card("new-done", "landed", "2099-01-01T00:00:00+00:00")
        card("next", "shaped", "2026-10-17T00:00:00+00:00", after=["old-needed"])
        nothing = self.run_kit(KIT, host, "archive", "--by", "dev")
        self.assertIn("declares no archive_after_days", nothing.stdout)
        policy = host / install_target("delivery", reads_as="policy")
        body = json.loads(policy.read_text(encoding="utf-8"))
        policy.write_text(json.dumps({**body, "archive_after_days": 30}, indent=2) + "\n", encoding="utf-8", newline="\n")
        planned = self.run_kit(KIT, host, "archive", "--by", "dev", "--plan")
        self.assertEqual(0, planned.returncode, planned.stderr)
        self.assertTrue((cards / "old-done.json").exists(), "--plan moved a card")
        moved = self.run_kit(KIT, host, "archive", "--by", "dev")
        self.assertEqual(0, moved.returncode, moved.stdout + moved.stderr)
        self.assertFalse((cards / "old-done.json").exists())
        self.assertTrue((host / "docs" / "work" / "archive" / "old-done.json").exists())
        self.assertTrue((cards / "old-needed.json").exists(), "a card a working card names was archived")
        self.assertTrue((cards / "new-done.json").exists())
        self.assertIn("PASS  FF-WORK-ORDER", self._failed(host))

    def test_a0_lowering_a_card_is_the_owners_door_and_raising_it_is_anyones(self):
        host = self.installed()
        cards = host / install_target("delivery", reads_as="cards")
        cards.mkdir(parents=True, exist_ok=True)
        (cards / "orders.json").write_text(json.dumps(
            {"schema_version": 1, "id": "orders", "title": "orders", "state": "shaped", "class": "normal",
             "created_at": "2026-10-17T00:00:00+00:00"}, indent=2) + "\n", encoding="utf-8", newline="\n")
        raised = self.run_kit(KIT, host, "reshape", "--card", "orders", "--class", "major", "--by", "dev")
        self.assertEqual(0, raised.returncode, raised.stdout + raised.stderr)
        waiting = self.run_kit(KIT, host, "reshape", "--card", "orders", "--class", "normal", "--by", "dev")
        self.assertEqual(3, waiting.returncode, waiting.stdout + waiting.stderr)
        self.assertEqual("major", json.loads((cards / "orders.json").read_text(encoding="utf-8"))["class"])
        lowered = self.run_kit(KIT, host, "reshape", "--card", "orders", "--class", "normal", "--approve", "owner")
        self.assertEqual(0, lowered.returncode, lowered.stdout + lowered.stderr)
        card = json.loads((cards / "orders.json").read_text(encoding="utf-8"))
        self.assertEqual({"from": "major", "to": "normal", "approved_by": "owner"},
                         {k: card["reshaped"][-1][k] for k in ("from", "to", "approved_by")})

    def test_a1_ci_holds_every_pushed_commit_to_the_floor_a_skipped_hook_did_not(self):
        host = self.installed()
        self.declare(host, ("migrations", r"^db/migrations/", "irreversible"))
        env = dict(os.environ, GIT_AUTHOR_NAME="f", GIT_AUTHOR_EMAIL="f@example.invalid",
                   GIT_COMMITTER_NAME="f", GIT_COMMITTER_EMAIL="f@example.invalid")
        git = lambda *a: subprocess.run(["git", "-C", str(host), *a], check=True, capture_output=True, text=True, env=env)
        git("add", "-A"); git("commit", "-q", "--no-verify", "-m", "chore: the installed host")
        base = git("rev-parse", "HEAD").stdout.strip()
        (host / "db" / "migrations").mkdir(parents=True)
        (host / "db" / "migrations" / "0001.sql").write_text("drop table t;\n", encoding="utf-8")
        git("add", "-A"); git("commit", "-q", "--no-verify", "-m", "feat: quietly")
        caught = self.run_kit(KIT, host, "weigh", "--base", base, "--head", "HEAD", "--each")
        self.assertEqual(1, caught.returncode, caught.stdout + caught.stderr)
        self.assertIn("owes a card", caught.stdout)
        self.assertIn("1 commit(s) held to the floor, 1 refused", caught.stdout)

    def test_a2_weighing_names_the_downstream_and_the_lessons_of_what_it_touches(self):
        host = self.installed()
        body = {"schema_version": 1, "default_undo": "reversible", "max_areas": {},
                "areas": [{"id": "contracts", "paths": "^api/contracts/", "undo": "costly", "because": "a fixture",
                           "owner": "api-team", "feeds": ["web"]},
                          {"id": "web", "paths": "^web/", "undo": "reversible", "because": "a fixture",
                           "owner": "web-team", "feeds": ["e2e"]},
                          {"id": "e2e", "paths": "^e2e/", "undo": "reversible", "because": "a fixture"}]}
        (host / AREAS).write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8", newline="\n")
        cards = host / install_target("delivery", reads_as="cards")
        cards.mkdir(parents=True, exist_ok=True)
        (cards / "renamed-field.json").write_text(json.dumps(
            {"schema_version": 1, "id": "renamed-field", "title": "a renamed field", "state": "landed",
             "created_at": "2026-10-17T00:00:00+00:00",
             "lesson": {"subject": "contracts", "extent": "local", "statement": "a renamed field breaks the web client"}},
            indent=2) + "\n", encoding="utf-8", newline="\n")
        said = self.run_kit(KIT, host, "weigh", "--path", "api/contracts/orders.json")
        self.assertEqual(0, said.returncode, said.stdout + said.stderr)
        self.assertIn("owner api-team", said.stdout)
        self.assertIn("feeds web (owner web-team)", said.stdout)
        self.assertIn("feeds e2e", said.stdout)
        self.assertIn("lesson (renamed-field, contracts): a renamed field breaks the web client", said.stdout)

    def test_a3_a_card_proved_by_the_gate_that_reads_it_does_not_evaluate_itself_forever(self):
        """Met adopting this kit on a real host: a finished card whose criterion is FF-WORK-ORDER -- the
        gate that re-reads finished cards' criteria -- made check and the board recurse without end."""
        host = self.installed()
        cards = host / install_target("delivery", reads_as="cards")
        cards.mkdir(parents=True, exist_ok=True)
        (cards / "adopted.json").write_text(json.dumps(
            {"schema_version": 1, "id": "adopted", "title": "adopted", "state": "landed",
             "created_at": "2026-10-17T00:00:00+00:00",
             "criteria": [{"id": "order", "statement": "the order holds",
                           "proof": {"kind": "declared-rule-holds", "ref": "FF-WORK-ORDER"}}]},
            indent=2) + "\n", encoding="utf-8", newline="\n")
        rendered = self.run_kit(KIT, host, "render")
        self.assertEqual(0, rendered.returncode, rendered.stdout + rendered.stderr)
        said = self._failed(host)
        self.assertIn("PASS  FF-WORK-ORDER", said)
        self.assertNotIn("RecursionError", said)

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
