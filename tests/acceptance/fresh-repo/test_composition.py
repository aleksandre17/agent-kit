"""Acceptance: composition -- what a SET of declarations does, and what it refuses."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from harness import FIXTURES, KIT, Fixtures, install_order


# ==========================================================================================
# Composition. One capability can prove none of this: `requires`, `provides`, `conflicts`,
# ordering and shadowing are claims ABOUT A SET. Every negative case below is built as a
# FIXTURE KIT -- a throwaway copy of the real kit with its declarations patched, or with an
# extra declaration dropped in -- so that no real capability is deformed to manufacture a
# failure, and so that a fixture cannot drift from the truth it was copied out of.
# ==========================================================================================

class Composition(Fixtures, unittest.TestCase):

    # -- requires ---------------------------------------------------------------------------
    def test_20_a_required_capability_that_is_disabled_is_a_named_refusal(self):
        """`knowledge` requires `governance`. Disabled, the resolver must REFUSE and name the
        unmet requirement -- not enable governance on the host's behalf, and not proceed."""
        def disable_governance(kit: Path):
            self.edit_json(kit, "MANIFEST.json", lambda m: m.__setitem__(
                "capabilities", [c for c in m["capabilities"] if c["id"] != "governance"]))
        host = self.host()
        result = self.run_kit(self.fixture_kit("no-governance", disable_governance), host)
        self.assertNotEqual(0, result.returncode)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("unmet requirement", result.stderr)
        self.assertIn("capability:governance", result.stderr)
        self.assertIn("nothing was enabled on its behalf", result.stderr)
        self.assertFalse((host / ".agents").exists(), "a refused set must not have written anything")
        self.assertFalse((host / "docs").exists(), "a refused set must not have written anything")

    # -- provides ---------------------------------------------------------------------------
    def test_21_a_requirement_is_matched_by_provision_not_by_id(self):
        """Renaming what governance PROVIDES breaks the requirement even though its id is
        unchanged -- so the match is against the contract, not the name."""
        def rename_provision(kit: Path):
            self.edit_json(kit, "capabilities/governance/capability.json",
                           lambda c: c.__setitem__("provides", ["authority"]))
        result = self.run_kit(self.fixture_kit("provision-renamed", rename_provision), self.host())
        self.assertNotEqual(0, result.returncode)
        self.assertIn("capability:governance", result.stderr)
        self.assertIn("no enabled capability provides it", result.stderr)

    def test_22_any_capability_offering_the_provision_satisfies_the_requirer(self):
        """The same rename on BOTH sides installs cleanly: the requirer never learns which
        capability satisfied it, which is the whole point of a provision."""
        def alias_both(kit: Path):
            self.edit_json(kit, "capabilities/governance/capability.json",
                           lambda c: c.__setitem__("provides", ["authority"]))
            # Every requirer is re-pointed, and WHICH capabilities those are is asked of the
            # declarations. A test that named one requirer would stop measuring the kit the day a
            # second capability required the same provision -- it would still pass, and it would
            # be agreeing with a snapshot rather than reading the set in front of it.
            for entry in json.loads((kit / "MANIFEST.json").read_text(encoding="utf-8"))["capabilities"]:
                self.edit_json(kit, entry["declaration"], lambda c: c.__setitem__(
                    "requires", [
                        {"kind": "capability", "id": "authority"}
                        if requirement["kind"] == "capability" and requirement["id"] == "governance"
                        else requirement
                        for requirement in c["requires"]
                    ]))
        result = self.run_kit(self.fixture_kit("provision-aliased", alias_both), self.host(),
                              "init", "--approve", "acceptance-suite")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("check: 0 gate(s) failed", result.stdout)

    # -- conflicts --------------------------------------------------------------------------
    def test_23_a_declared_conflict_is_refused(self):
        def declare_conflict(kit: Path):
            self.edit_json(kit, "capabilities/knowledge/capability.json",
                           lambda c: c.__setitem__("conflicts", ["governance"]))
        result = self.run_kit(self.fixture_kit("conflicting", declare_conflict), self.host())
        self.assertNotEqual(0, result.returncode)
        self.assertIn("declared conflict", result.stderr)
        self.assertIn("'governance'", result.stderr)

    # -- ordering ---------------------------------------------------------------------------
    def test_24_the_install_order_is_declared_not_incidental(self):
        """Assert the ORDER, not the set: dependencies first, ties by id. And assert it does not
        move when the manifest lists the same capabilities the other way round."""
        straight = self.run_kit(KIT, self.host(), "init", "--approve", "acceptance-suite")
        self.assertEqual(0, straight.returncode, straight.stderr)
        self.assertEqual([
            # `delivery` requires no provision, so it ties with `governance` and the tie is broken
            # by id -- which is why it goes first. `knowledge` requires governance and can never
            # precede it, whatever order the manifest happens to list them in.
            ".agents/project/delivery/policy.json",
            ".agents/project/delivery/cards/",
            ".agents/kit/doctrine/delivery.md",
            # `evaluation` requires no provision either, so it is in the same tie and its id
            # places it second. Nothing about JUDGING makes it late: it lays a blank declaration
            # and an empty space, and both are as early as anything else that depends on nothing.
            ".agents/project/evaluation/evaluation.json",
            ".agents/project/evaluation/readings.json",
            ".agents/runtime/evaluation/judgements/",
            ".agents/kit/doctrine/evaluation.md",
            ".agents/project/profile.json",
            ".agents/project/project.json",
            ".agents/project/laws.md",
            ".agents/.gitignore",
            ".agents/kit/doctrine/governance.md",
            # `observability` requires no provision either, so it is in the same tie as the two
            # above and its id places it third -- after `governance`, before anything that
            # depends on governance. Nothing about WATCHING a run makes it late.
            ".agents/project/observability/observation.json",
            ".agents/runtime/observability/runs/",
            ".agents/kit/doctrine/observability.md",
            # `hygiene` and `knowledge` both require what governance provides, so neither may
            # precede it; the tie between the two is broken by id, and hygiene lands first.
            ".agents/project/hygiene/residence.json",
            ".agents/kit/doctrine/hygiene.md",
            ".agents/kit/doctrine/knowledge.md",
            "docs/decisions/ADR-0001-a-documents-kind-decides-its-authority.md",
            "docs/reference/README.md",
            ".agents/generated/delivery/BOARD.md",
            ".agents/generated/evaluation/QUALITY.md",
            ".agents/generated/governance/INDEX.md",
            ".agents/generated/observability/RUNS.md",
            ".agents/generated/hygiene/RESIDENCE.md",
        ], install_order(straight.stdout))

        def reverse_manifest(kit: Path):
            self.edit_json(kit, "MANIFEST.json",
                           lambda m: m.__setitem__("capabilities", list(reversed(m["capabilities"]))))
        reversed_run = self.run_kit(self.fixture_kit("reversed", reverse_manifest), self.host(),
                                    "init", "--approve", "acceptance-suite")
        self.assertEqual(0, reversed_run.returncode, reversed_run.stderr)
        self.assertEqual(install_order(straight.stdout), install_order(reversed_run.stdout),
                         "declaration order leaked into install order")

    # -- shadowing --------------------------------------------------------------------------
    def test_25_two_capabilities_installing_to_one_path_is_refused(self):
        """Not ordered, not last-writer-wins: refused, naming both owners and the path."""
        def add_collider(kit: Path):
            self.edit_json(kit, "MANIFEST.json", lambda m: m["capabilities"].append(
                {"id": "collider", "declaration": "capabilities/collider/capability.json"}))
        host = self.host()
        result = self.run_kit(
            self.fixture_kit("collider", add_collider,
                             add=[(FIXTURES / "collider/capability.json", "capabilities/collider/capability.json")]),
            host)
        self.assertNotEqual(0, result.returncode)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("shadowed path", result.stderr)
        self.assertIn("'collider'", result.stderr)
        self.assertIn("'governance'", result.stderr)
        self.assertIn(".agents/project/laws.md", result.stderr)
        self.assertFalse((host / ".agents").exists(), "the refusal must precede the first byte")

    # -- the Kind Law gate ------------------------------------------------------------------
    def test_26_the_kind_law_gate_passes_where_the_location_grants_the_claim(self):
        """The green half. A name that claims declaring authority, in the one kind that grants
        it, must PASS -- a gate that only ever fails is not a gate."""
        host = self.installed()
        adr = host / "docs/decisions/ADR-0001-a-documents-kind-decides-its-authority.md"
        self.assertTrue(adr.is_file(), "the seeded decision is the passing case")
        first = self.run_kit(KIT, host, "check")
        self.assertIn("PASS  FF-KIND-AUTHORITY", first.stdout)

        # the red half: the SAME name, moved to a kind that cannot declare.
        smuggled = host / "docs/reference/CANON-what-we-do-here.md"
        smuggled.write_text("Every agent must do as this page says.\n", encoding="utf-8")
        failed = self.run_kit(KIT, host, "check")
        self.assertEqual(1, failed.returncode)
        self.assertIn("FAIL  FF-KIND-AUTHORITY", failed.stdout)
        self.assertIn("claims DECLARING authority", failed.stdout)
        self.assertIn("'docs/reference', which cannot declare", failed.stdout)

        # ... and a claim in no declared kind at all is caught too, with a different reason.
        smuggled.unlink()
        stray = host / "docs/DESIGN-the-shape-of-things.md"
        stray.write_text("This is how it shall be built.\n", encoding="utf-8")
        astray = self.run_kit(KIT, host, "check")
        self.assertEqual(1, astray.returncode)
        self.assertIn("no declared kind", astray.stdout)

        # a page that claims nothing is never judged, whatever it says.
        stray.unlink()
        (host / "docs/guides").mkdir(parents=True, exist_ok=True)
        (host / "docs/guides/how-to-run-the-kit.md").write_text("Run `init`.\n", encoding="utf-8")
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode)

    # -- one declaration, every surface ------------------------------------------------------
    def test_27_the_new_capability_reaches_the_projection_with_no_template_edit(self):
        """The governance INDEX iterates whatever is enabled. Adding a second capability had to
        change it -- and did, without a line of template or renderer changing. A model that
        reaches only one surface is incomplete, not done."""
        host = self.installed()
        index = (host / ".agents/generated/governance/INDEX.md").read_text(encoding="utf-8")
        self.assertIn("### knowledge 0.1.0", index)
        self.assertIn("FF-KIND-AUTHORITY", index)
        self.assertIn("docs/decisions/ADR-0001-a-documents-kind-decides-its-authority.md", index)
        self.assertLess(index.index("### governance"), index.index("### knowledge"),
                        "the projection must follow the resolved order, not the manifest's")


