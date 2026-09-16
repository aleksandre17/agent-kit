"""Acceptance: HOST CHOICE and the plan -- P3, the one door where a human stands."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from harness import KIT, Fixtures, Manifest, applied, host_digest, planned


# ==========================================================================================
# Selection and the plan. Everything above proves what a set of DECLARATIONS does. Nothing
# above proves what a HOST CHOSE, and that is where the interesting failures live: a host
# leaving out something another capability needs, a host leaving out what the kit cannot
# stand without, a host asked to approve before a single byte moves.
# ==========================================================================================

class Selection(Fixtures, unittest.TestCase):

    def answers(self, host: Path) -> dict:
        return json.loads((host / ".agents/project/project.json").read_text(encoding="utf-8"))

    def targets_of(self, capability_id: str) -> list:
        manifest = Manifest(KIT)
        found = [c for c in manifest.capabilities if c.id == capability_id]
        self.assertEqual(1, len(found))
        return list(found[0].targets())

    # -- the host chooses ---------------------------------------------------------------------
    def test_30_a_host_that_enables_a_subset_gets_exactly_that_subset(self):
        """The path set is asserted BOTH ways: what the chosen capability declared is present,
        and every path the excluded one declared is absent. A subset proved only by what exists
        is not proved at all -- the interesting half is what did not get written."""
        host = self.installed(KIT, "--enable", "governance")
        self.assertEqual(["governance"], self.answers(host)["capabilities"])
        present = set(host_digest(host))
        for target in self.targets_of("governance"):
            # A target ending in '/' names a TREE (the kit's one '/' rule): it is present when
            # something was written under it, never as a file of that name.
            written = ([p for p in present if p.startswith(target)] if target.endswith("/")
                       else [target] if target in present else [])
            self.assertTrue(written, f"{target} was chosen and is missing")
        for target in self.targets_of("knowledge"):
            self.assertNotIn(target, present, f"{target} belongs to a capability nobody enabled")
        self.assertFalse((host / "docs").exists(),
                         "the excluded capability's whole plane must be absent, not merely empty")
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode,
                         "a subset host must be as checkable as a whole one")

    def test_31_disabling_a_capability_another_requires_is_refused_and_mutates_nothing(self):
        """The case a kit-only composition test could never reach. `knowledge` requires what
        `governance` provides; a host that leaves governance out is refused, told which choice
        caused it, and left untouched -- the kit does not helpfully re-enable it."""
        def let_governance_be_disabled(kit: Path):
            self.edit_json(kit, "MANIFEST.json", lambda m: [
                entry.pop("never_disabled", None) for entry in m["capabilities"]])
        host = self.host()
        kit = self.fixture_kit("disablable-governance", let_governance_be_disabled)
        result = self.run_kit(kit, host, "init", "--disable", "governance")
        self.assertNotEqual(0, result.returncode)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("unmet requirement", result.stderr)
        self.assertIn("capability:governance", result.stderr)
        self.assertIn("which this host chose to disable", result.stderr)
        self.assertIn("nothing was enabled on its behalf", result.stderr)
        self.assertEqual({}, host_digest(host), "a refused selection wrote to the host")

    def test_32_never_disabled_is_read_and_is_what_refuses(self):
        """The flag stops being a declaration nobody consults. Proved by DIFFERENCE: the same
        command against two kits differing only in that one field is refused for two different
        reasons -- so it is the field that fired, not something else."""
        host = self.host()
        flagged = self.run_kit(KIT, host, "init", "--disable", "governance")
        self.assertNotEqual(0, flagged.returncode)
        self.assertIn("never_disabled", flagged.stderr)
        self.assertEqual({}, host_digest(host))

        def drop_the_flag(kit: Path):
            self.edit_json(kit, "MANIFEST.json", lambda m: [
                entry.pop("never_disabled", None) for entry in m["capabilities"]])
        unflagged = self.run_kit(self.fixture_kit("unflagged", drop_the_flag), self.host(),
                                 "init", "--disable", "governance")
        self.assertNotIn("never_disabled", unflagged.stderr,
                         "removing the declaration must remove the refusal it causes")

    def test_33_a_selection_naming_a_capability_nobody_declares_is_refused(self):
        """A typo must be SEEN. Silently honouring it would install a set the operator never
        asked for while the command line went on reading as obeyed."""
        result = self.run_kit(KIT, self.host(), "init", "--enable", "governance,knowlege")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("'knowlege'", result.stderr)
        self.assertIn("no capability in this kit declares", result.stderr)

    def test_34_a_selection_may_not_contradict_a_host_that_has_already_answered(self):
        host = self.installed()
        answered = self.answers(host)["capabilities"]
        result = self.run_kit(KIT, host, "init", "--disable", "knowledge")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("already declared its set", result.stderr)
        # What the host answered is READ, never restated here: a test carrying its own copy of the
        # kit's default set is a second home for it, and would have to be edited every time a
        # capability is declared -- which is the moment a test stops measuring and starts agreeing.
        self.assertIn("knowledge", answered, "the flag named a capability the host had chosen")
        self.assertEqual(answered, self.answers(host)["capabilities"],
                         "the answers file is the host's, and a flag may not rewrite it")

    # -- the plan -----------------------------------------------------------------------------
    def test_35_the_plan_touches_nothing(self):
        host = self.host()
        before = host_digest(host)
        self.run_kit(KIT, host, "init", "--plan", "--approve", "acceptance-suite")
        self.assertEqual(before, host_digest(host), "a plan wrote to the host")
        self.assertEqual({}, host_digest(host))

    def test_36_the_planned_write_set_equals_the_applied_write_set(self):
        """Asserted by comparison, never by eye. The plan and the apply are the same value: the
        verb decides once, `--plan` prints the decision and the apply consumes it."""
        host = self.host()
        plan_run = self.run_kit(KIT, host, "init", "--plan", "--approve", "acceptance-suite")
        self.assertEqual(0, plan_run.returncode, plan_run.stderr)
        foreseen = planned(plan_run.stdout)
        self.assertTrue(foreseen, "the plan listed nothing at all")

        apply_run = self.run_kit(KIT, host, "init", "--approve", "acceptance-suite")
        self.assertEqual(0, apply_run.returncode, apply_run.stderr)
        self.assertEqual(foreseen, applied(apply_run.stdout),
                         "what the plan promised is not what the apply did")

    def test_37_a_plan_on_an_installed_host_foresees_what_is_kept(self):
        """The second-run plan is the honest one: a plan that can only say `create` tells an
        operator nothing about a host that already has files in it."""
        host = self.installed()
        second = self.run_kit(KIT, host, "init", "--plan")
        self.assertEqual(0, second.returncode, second.stderr)
        foreseen = dict((path, word) for word, path in planned(second.stdout))
        self.assertEqual("kept", foreseen[".agents/project/project.json"])
        self.assertEqual("kept", foreseen[".agents/project/laws.md"])
        # The kit a host was given is KEPT when the same release is delivered again -- the tree and
        # the lock at its seat, one act (the shipped kit vendors no page to replace since L3a).
        import pin  # noqa: E402
        from manifest import Manifest  # noqa: E402
        for seat in pin.seats(Manifest(KIT)):
            self.assertEqual("kept", foreseen[seat])
        self.assertEqual(applied(self.run_kit(KIT, host, "init").stdout), planned(second.stdout))

    def test_38_check_writes_nothing_so_it_cannot_be_asked_for_a_plan(self):
        result = self.run_kit(KIT, self.installed(), "check", "--plan")
        self.assertEqual(2, result.returncode)
        self.assertIn("nothing to plan", result.stderr)

    # -- the draft blocks ---------------------------------------------------------------------
    def test_39_every_later_verb_refuses_while_an_unapproved_draft_stands(self):
        host = self.host()
        self.assertEqual(3, self.run_kit(KIT, host, "init").returncode)
        for verb in ("check", "render"):
            result = self.run_kit(KIT, host, verb)
            self.assertEqual(3, result.returncode, f"{verb} ran on an unapproved host")
            self.assertNotIn("Traceback", result.stderr)
            self.assertIn("status 'draft'", result.stderr)
            self.assertIn("never approved", result.stderr)
        self.assertEqual([".agents/project/project.json"], sorted(host_digest(host)),
                         "a stalled install left more behind than the draft it declared")

    def test_40_approval_is_recorded_with_a_name_and_a_moment(self):
        host = self.installed()
        answers = self.answers(host)
        self.assertEqual("accepted", answers["status"])
        self.assertEqual("acceptance-suite", answers["signed_by"])
        self.assertTrue(answers["signed_at"])
        self.assertTrue(answers["drafted_at"])
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode)


