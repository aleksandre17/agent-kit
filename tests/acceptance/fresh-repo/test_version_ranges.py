"""Acceptance: version ranges on `requires` -- a requirement may name the versions it accepts.

ADR-001 point 1 accepts `requires` as a capability or fact PLUS a semver range. Every case below
is a FIXTURE KIT patched from the real one, and every name and version it uses is READ from the
declarations -- a requirer that already requires a capability, the capability providing it, and
the version that capability declares -- so nothing here goes on passing after the kit changes.
The ranges themselves are node-semver's own notation (version_range.py names the dialect).
"""

from __future__ import annotations

import unittest
from pathlib import Path

from harness import KIT, Fixtures
from manifest import Manifest  # noqa: E402  -- the path is prepared by importing harness first

import version_range  # noqa: E402

CAPABILITIES = sorted(Manifest(KIT).capabilities, key=lambda c: c.id)
PROVIDER_OF = {name: c for c in CAPABILITIES for name in c.raw.get("provides", [])}

#: The first capability, by id, that requires another capability -- and the requirement itself.
REQUIRER, NEED = next((c, n) for c in CAPABILITIES for n in c.requires if n["kind"] == "capability")
PROVIDER = PROVIDER_OF[NEED["id"]]
VERSION = PROVIDER.version

#: The first capability, by id, that requires a FACT about the host.
FACT_HOLDER, FACT = next((c, n) for c in CAPABILITIES for n in c.requires if n["kind"] == "fact")


def declaration(capability) -> str:
    return f"capabilities/{capability.id}/capability.json"


class VersionRanges(Fixtures, unittest.TestCase):

    def ranged(self, name: str, wanted: str, provider_version: str | None = None) -> Path:
        """A fixture kit where REQUIRER states `wanted` on its requirement, and optionally the
        provider declares a different version."""
        def patch(kit: Path):
            def narrow(c):
                for need in c["requires"]:
                    if need["kind"] == NEED["kind"] and need["id"] == NEED["id"]:
                        need["version"] = wanted
            self.edit_json(kit, declaration(REQUIRER), narrow)
            if provider_version is not None:
                self.edit_json(kit, declaration(PROVIDER),
                               lambda c: c.__setitem__("version", provider_version))
        return self.fixture_kit(name, patch)

    def walked(self, kit: Path) -> Path:
        """Draft, then approve: a set is only proven to compose once the whole door is walked."""
        host = self.host()
        self.run_kit(kit, host)
        result = self.run_kit(kit, host, "init", "--approve", "a-named-person")
        self.assertEqual(0, result.returncode, result.stderr)
        return host

    def assertRefusedUntouched(self, result, host: Path):
        self.assertNotEqual(0, result.returncode)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse((host / ".agents").exists(), "a refused set must not have written anything")

    def test_171_a_requirement_at_a_range_its_provider_satisfies_installs_like_any_other(self):
        host = self.walked(self.ranged("range-met", f"^{VERSION}"))
        self.assertTrue((host / ".agents").exists(), "a satisfied range installed nothing")

    def test_172_a_provider_outside_the_range_is_a_named_refusal_stating_what_was_wanted_and_found(self):
        host = self.host()
        result = self.run_kit(self.ranged("range-unmet", f">{VERSION}"), host)
        self.assertRefusedUntouched(result, host)
        self.assertIn("unsatisfied version range", result.stderr)
        self.assertIn(f"{REQUIRER.id!r} requires capability:{NEED['id']} at '>{VERSION}'",
                      result.stderr)
        self.assertIn(f"found {PROVIDER.id} {VERSION}", result.stderr)
        self.assertIn("nothing was enabled on its behalf", result.stderr)

    def test_173_a_caret_on_a_zero_major_version_stops_before_the_next_minor_as_node_semver_declares(self):
        """`^0.1.0` means `>=0.1.0 <0.2.0`, not `<1.0.0`. The kit ships 0.x throughout, so this
        is the reading every range written against it will actually get."""
        host = self.host()
        result = self.run_kit(self.ranged("caret-zero", "^0.1.0", provider_version="0.2.0"), host)
        self.assertRefusedUntouched(result, host)
        self.assertIn("found " + PROVIDER.id + " 0.2.0", result.stderr)

    def test_174_a_requirement_with_no_range_is_satisfied_by_any_version_of_its_provider(self):
        """Every requirement declared before ranges existed states none, and must mean what it
        always meant: any version at all."""
        def far_away(kit: Path):
            self.edit_json(kit, declaration(PROVIDER), lambda c: c.__setitem__("version", "999.0.0"))
        self.walked(self.fixture_kit("no-range", far_away))

    def test_175_an_operator_outside_the_implemented_subset_is_refused_by_name_and_never_ignored(self):
        host = self.host()
        result = self.run_kit(self.ranged("unknown-operator", f"!={VERSION}"), host)
        self.assertRefusedUntouched(result, host)
        self.assertIn("unreadable version range", result.stderr)
        self.assertIn("operator '!='", result.stderr)

    def test_176_a_range_on_a_fact_requirement_is_refused_because_a_fact_declares_no_version(self):
        def ranged_fact(kit: Path):
            def narrow(c):
                for need in c["requires"]:
                    if need["kind"] == "fact" and need["id"] == FACT["id"]:
                        need["version"] = f"^{VERSION}"
            self.edit_json(kit, declaration(FACT_HOLDER), narrow)
        host = self.host()
        result = self.run_kit(self.fixture_kit("ranged-fact", ranged_fact), host)
        self.assertRefusedUntouched(result, host)
        self.assertIn(f"requires fact:{FACT['id']}", result.stderr)
        self.assertIn("has none", result.stderr)

    def test_177_every_operator_desugars_exactly_as_node_semver_documents_it(self):
        """The dialect's own documented examples, held against the grammar table directly."""
        documented = {
            "^1.2.3": [(">=", (1, 2, 3)), ("<", (2, 0, 0))],
            "^0.2.3": [(">=", (0, 2, 3)), ("<", (0, 3, 0))],
            "^0.0.3": [(">=", (0, 0, 3)), ("<", (0, 0, 4))],
            "~1.2.3": [(">=", (1, 2, 3)), ("<", (1, 3, 0))],
            "1.2.3": [("=", (1, 2, 3))],
        }
        for text, bounds in documented.items():
            self.assertEqual([bounds], version_range.parse(text), text)
        self.assertTrue(version_range.satisfies("1.5.0", ">=1.2.3 <2.0.0 || 3.0.0"))
        self.assertTrue(version_range.satisfies("3.0.0", ">=1.2.3 <2.0.0 || 3.0.0"))
        self.assertFalse(version_range.satisfies("2.0.0", ">=1.2.3 <2.0.0 || 3.0.0"))


if __name__ == "__main__":
    unittest.main()
