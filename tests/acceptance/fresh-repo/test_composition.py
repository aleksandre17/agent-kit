"""Acceptance: composition -- what a SET of declarations does, and what it refuses."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from harness import FIXTURES, KIT, Fixtures, install_order
from manifest import Manifest  # noqa: E402  -- the path is prepared by importing harness first


# ------------------------------------------------------------------------------------------
# The ordering RULE, transcribed -- not imported, and not copied from an output.
#
# A literal list of paths is a SECOND HOME for the manifest: it goes red every time a capability
# is added, for a reason that has nothing to do with ordering, and what it finally agrees with is
# yesterday's output rather than the rule. So the rule is stated here in its own words and the
# expected sequence is DERIVED from the same declarations the interpreter reads.
#
# It is a transcription and never a call: nothing below imports `resolver`. If the two ever
# disagree, one of them is wrong and the suite says so -- which is the whole point of writing the
# rule twice in two languages rather than once and quoting its answer.
# ------------------------------------------------------------------------------------------

def dependency_levels(capabilities) -> list:
    """The rule: **dependencies first, ties broken by id** -- read level by level.

    A capability is READY when every capability providing something it requires is already
    placed. All capabilities ready at once form one LEVEL, and inside a level the order is by id.
    The level is the part a literal list can never show: it is why `observability` precedes
    `hygiene` although `h` sorts first -- they are not tied, they are on different levels.
    """
    provided: dict = {}
    for capability in capabilities:
        for name in capability.raw.get("provides", []):
            provided.setdefault(name, set()).add(capability.id)
    depends = {
        capability.id: {
            provider
            for need in capability.requires if need["kind"] == "capability"
            for provider in provided.get(need["id"], set()) if provider != capability.id
        }
        for capability in capabilities
    }
    placed, levels = set(), []
    while len(placed) < len(capabilities):
        ready = sorted(c.id for c in capabilities if c.id not in placed and depends[c.id] <= placed)
        if not ready:
            raise AssertionError(f"no order satisfies {sorted(set(depends) - placed)}")
        levels.append(ready)
        placed |= set(ready)
    return levels


def expected_install_order(kit_root) -> list:
    """The path sequence the ordering rule implies for a kit, derived from its declarations.

    Three rules compose, and all three are read from the declarations rather than remembered:
      * capabilities run in dependency order (above);
      * inside a capability, installs happen in the order they are DECLARED -- except that the
        PROJECTION class is a later phase, so every projection of the whole set follows every
        install of the whole set;
      * and the ESTATE is later still -- last of everything, because it is a MEASUREMENT of what
        the run gave this host. A record taken before the writes it records would state a moment
        that described nothing, so its position is not a preference and is asserted as a rule.

    A PLURAL projection -- one whose declared target names a collection, because it writes one
    file per record rather than one file about a set -- is deliberately not derived here. Its
    paths are a function of the host's own content, so a derivation from declarations alone
    cannot state them and must not pretend to. What it contributes is asserted separately, at
    the one place that can know: against a host that has been measured.
    """
    capabilities = Manifest(kit_root).capabilities
    by_id = {c.id: c for c in capabilities}
    ordered = [by_id[cid] for level in dependency_levels(capabilities) for cid in level]
    singular = [item for item in
                (i for c in ordered for i in c.installs if i["class"] == "projection")
                if not item["target"].endswith("/")]
    estate = [item for c in ordered for item in c.installs if item["mode"] == "estate"]
    return (
        [item["target"] for c in ordered for item in c.installs
         if item["class"] != "projection" and item["mode"] != "estate"]
        + [item["target"] for item in singular]
        + [item["target"] for item in estate]
    )


def plural_projections(kit_root) -> list:
    """Every declared projection whose target names a COLLECTION -- the ones whose write set only
    a host can answer for."""
    return [item for c in Manifest(kit_root).capabilities for item in c.installs
            if item["class"] == "projection" and item["target"].endswith("/")]


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
        """Assert the RULE, not a remembered sequence: dependencies first, ties by id, level by
        level -- derived from the same declarations the run reads. And assert it does not move
        when the manifest lists the same capabilities the other way round.

        What this used to assert was a literal list of paths, which is a second home for the
        manifest: it agreed with yesterday's output and went red whenever a capability arrived,
        for a reason that was never about ordering. The bite is unchanged and now has to be
        argued for rather than remembered, so the guards below are the price of the derivation:
        an expectation computed from the same file the run reads could otherwise be satisfied by
        an empty list, by a set that lost a capability, or by a rule that placed a requirer
        before its provider -- and each of those is asserted against explicitly.
        """
        host = self.host()
        straight = self.run_kit(KIT, host, "init", "--approve", "acceptance-suite")
        self.assertEqual(0, straight.returncode, straight.stderr)
        walked = install_order(straight.stdout)
        expected = expected_install_order(KIT)

        # The plural projections, at the one place that can answer for them. This host authored
        # nothing, so each writes NOTHING -- and that zero is asserted rather than assumed: a
        # projection that quietly wrote a file here would otherwise slip past the set comparison
        # below as an unexplained extra, and one that wrote its own target as a FILE would be a
        # directory-shaped declaration landing as a document.
        for item in plural_projections(KIT):
            self.assertNotIn(item["target"], walked,
                             "a collection-shaped projection wrote its own target as a file")
            self.assertEqual([], sorted(
                path for path in walked if path.startswith(item["target"])),
                f"{item['target']} projected files for a host that declared no records")
            self.assertTrue((host / item["target"]).is_dir()
                            or not (host / item["target"]).exists(),
                            "a plural projection's plane is a directory or is honestly absent")

        # An expectation derived from a declaration can be vacuous. These four say it is not:
        # it is non-empty, it is not one capability's worth, every declared capability put at
        # least one path into it, and no capability's paths are interleaved with another's.
        capabilities = Manifest(KIT).capabilities
        self.assertGreater(len(expected), len(capabilities), "a derived expectation that small "
                           "would be satisfied by almost any order")
        self.assertEqual(sorted(expected), sorted(walked),
                         "the run touched a different SET of paths than the declarations imply")
        for capability in capabilities:
            self.assertTrue(set(capability.targets()) & set(walked),
                            f"{capability.id} declares installs and touched no path")

        # ... and the rule itself: a capability that REQUIRES a provision may never be reached
        # before the capability offering it. Asserted over the walked order directly, so it holds
        # even if the derivation above were wrong in the same direction.
        first_touch = {c.id: min(walked.index(t) for t in c.targets() if t in walked)
                       for c in capabilities}
        provides = {p: c.id for c in capabilities for p in c.raw.get("provides", [])}
        for capability in capabilities:
            for need in capability.requires:
                provider = provides.get(need["id"]) if need["kind"] == "capability" else None
                if provider and provider != capability.id:
                    self.assertLess(first_touch[provider], first_touch[capability.id],
                                    f"{capability.id} was reached before {provider}, which it requires")

        self.assertEqual(expected, walked, "the walked order is not the order the rule implies")

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


