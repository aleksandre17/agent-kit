"""Acceptance: install the kit into a repository that has never seen it.

This is the only test that measures the framework's central claim. A kit exercised only inside the
repository that grew it cannot tell UNIVERSAL from FAMILIAR: everything works there, and nothing
was measured. So the host here is an empty scratch git repository, created fresh, and the kit is
reached ONLY through `kit/` -- never through the framework's own tree.

Run:  python tests/acceptance/fresh-repo/test_fresh_repo.py
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
KIT = REPO / "kit"
CLI = KIT / "interpreters" / "cli.py"

for extra in (KIT / "interpreters", KIT / "interpreters" / "ports", KIT / "interpreters" / "verbs"):
    sys.path.insert(0, str(extra))

from manifest import Manifest  # noqa: E402
from workspace import Workspace, WriteScopeError  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(root: Path, rel: str) -> dict:
    base = root / rel
    out = {}
    for dirpath, _dirs, files in os.walk(base):
        for name in files:
            whole = Path(dirpath) / name
            out[whole.relative_to(root).as_posix()] = sha(whole)
    return out


class FreshRepo(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="kit-fresh-")).resolve()
        subprocess.run(["git", "init", "--quiet", str(cls.tmp)], check=True,
                       capture_output=True, text=True)
        cls.manifest = Manifest(KIT)
        cls.first = cls.run_verb("init")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    @classmethod
    def run_verb(cls, verb: str):
        result = subprocess.run(
            [sys.executable, str(CLI), verb, "--root", str(cls.tmp), "--kit", str(KIT)],
            capture_output=True, text=True,
        )
        print(f"\n$ python kit/interpreters/cli.py {verb} --root <scratch>\n"
              f"[exit {result.returncode}]\n{result.stdout}{result.stderr}")
        return result

    # -- the install ------------------------------------------------------------------------
    def test_01_init_succeeds_into_an_empty_git_repo(self):
        self.assertEqual(0, self.first.returncode, self.first.stderr)

    def test_02_bindings_exist_and_honour_their_schemas(self):
        for rel, schema in ((".agents/project/project.json", "project"),
                            (".agents/project/profile.json", "profile")):
            target = self.tmp / rel
            self.assertTrue(target.is_file(), f"{rel} was not created")
            errors = self.manifest.validate(json.loads(target.read_text(encoding="utf-8")), schema)
            self.assertEqual([], errors, f"{rel}: {errors}")

    def test_03_the_reading_states_when_it_was_taken(self):
        profile = json.loads((self.tmp / ".agents/project/profile.json").read_text(encoding="utf-8"))
        self.assertTrue(profile["taken_at"], "a reading with no moment cannot be contradicted")
        self.assertIn("+00:00", profile["taken_at"])
        self.assertTrue(profile["facts"].get("vcs.git"), "the host is a git repository and was measured as one")
        self.assertEqual(profile["boundary"]["path_separator"], "/")

    def test_04_every_produced_path_resolves_to_exactly_one_class(self):
        declared = [(p["root"].rstrip("/") + "/", p["class"]) for p in self.manifest.planes]
        for capability in self.manifest.capabilities:
            for item in capability.installs:
                declared.append((item["target"], item["class"]))
        produced = digest(self.tmp, ".agents")
        self.assertTrue(produced, "the kit produced nothing at all")
        for rel in produced:
            classes = {k for prefix, k in declared if rel == prefix or rel.startswith(prefix)}
            self.assertEqual(1, len(classes), f"{rel} resolves to {sorted(classes)}")

    def test_05_check_exits_zero(self):
        self.assertEqual(0, self.run_verb("check").returncode)

    # -- re-running -------------------------------------------------------------------------
    def test_06_second_init_mutates_no_binding_file(self):
        before = digest(self.tmp, ".agents/project")
        before[".agents/.gitignore"] = sha(self.tmp / ".agents/.gitignore")
        second = self.run_verb("init")
        self.assertEqual(0, second.returncode)
        after = digest(self.tmp, ".agents/project")
        after[".agents/.gitignore"] = sha(self.tmp / ".agents/.gitignore")
        self.assertEqual(before, after, "a second init rewrote host truth")
        self.assertIn("kept", second.stdout, "a second init should keep bindings, not create them")

    def test_07_render_is_byte_reproducible(self):
        before = digest(self.tmp, ".agents/generated")
        self.assertTrue(before, "nothing was projected")
        shutil.rmtree(self.tmp / ".agents/generated")
        self.assertEqual(0, self.run_verb("render").returncode)
        self.assertEqual(before, digest(self.tmp, ".agents/generated"),
                         "a deleted projection did not come back byte-identical")

    # -- the port that bounds every write ---------------------------------------------------
    def test_08_workspace_refuses_a_write_outside_declared_installs(self):
        capability = self.manifest.capabilities[0]
        scoped = Workspace(self.tmp).scoped(capability.targets())
        rogue = ".agents/project/rogue.md"
        self.assertNotIn(rogue, capability.targets())
        with self.assertRaises(WriteScopeError) as refusal:
            scoped.write_text(rogue, "a capability writing where nothing declared it may")
        print(f"\n[refusal] {refusal.exception}")
        self.assertFalse((self.tmp / rogue).exists(), "the refusal must precede the byte")
        # and the same port, scoped as the capability declared it, does write:
        declared = capability.targets()[0]
        scoped.write_text(declared, (self.tmp / declared).read_text(encoding="utf-8"))

    def test_09_escaping_the_root_is_refused_too(self):
        with self.assertRaises(Exception):
            Workspace(self.tmp).write_text("../outside.md", "x")

    # -- what the kit does where its requirements are NOT met --------------------------------
    def test_10_a_host_that_fails_a_requirement_is_told_so(self):
        plain = Path(tempfile.mkdtemp(prefix="kit-nogit-")).resolve()
        try:
            result = subprocess.run(
                [sys.executable, str(CLI), "init", "--root", str(plain), "--kit", str(KIT)],
                capture_output=True, text=True,
            )
            print(f"\n$ init into a directory that is not a repository\n"
                  f"[exit {result.returncode}]\n{result.stdout}{result.stderr}")
            self.assertNotEqual(0, result.returncode)
            self.assertIn("unavailable", result.stdout)
            self.assertNotIn("Traceback", result.stderr, "a known situation must not arrive as a stack trace")
        finally:
            shutil.rmtree(plain, ignore_errors=True)

    def test_11_a_malformed_binding_is_a_named_refusal_not_a_traceback(self):
        (self.tmp / ".agents/project/project.json").write_text('{"schema_version": 1}', encoding="utf-8")
        result = self.run_verb("check")
        self.assertEqual(1, result.returncode)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("does not honour schema", result.stderr)


# ==========================================================================================
# Composition. One capability can prove none of this: `requires`, `provides`, `conflicts`,
# ordering and shadowing are claims ABOUT A SET. Every negative case below is built as a
# FIXTURE KIT -- a throwaway copy of the real kit with its declarations patched, or with an
# extra declaration dropped in -- so that no real capability is deformed to manufacture a
# failure, and so that a fixture cannot drift from the truth it was copied out of.
# ==========================================================================================

FIXTURES = Path(__file__).resolve().parent / "fixtures"
INSTALL_WORDS = ("created", "kept", "vendored", "projected")


def install_order(stdout: str) -> list:
    """The sequence of paths the run actually touched -- the ORDER, not merely the set."""
    order = []
    for line in stdout.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0] in INSTALL_WORDS:
            order.append(parts[1])
    return order


class Composition(unittest.TestCase):
    maxDiff = None
    _trash: list = []

    @classmethod
    def tearDownClass(cls):
        for path in cls._trash:
            shutil.rmtree(path, ignore_errors=True)

    # -- fixtures ---------------------------------------------------------------------------
    @classmethod
    def _temp(cls, prefix: str) -> Path:
        made = Path(tempfile.mkdtemp(prefix=prefix)).resolve()
        cls._trash.append(made)
        return made

    @classmethod
    def host(cls) -> Path:
        made = cls._temp("kit-host-")
        subprocess.run(["git", "init", "--quiet", str(made)], check=True, capture_output=True, text=True)
        return made

    @classmethod
    def fixture_kit(cls, name: str, patch=None, add=()) -> Path:
        """A copy of the REAL kit with declarations patched in place. Copied, never re-authored:
        a hand-written fixture of a declaration is a second home for it, and would go on passing
        after the original changed."""
        base = cls._temp(f"kit-fix-{name}-") / "kit"
        shutil.copytree(KIT, base)
        for src, rel in add:
            dest = base / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest)
        if patch:
            patch(base)
        return base

    @staticmethod
    def edit_json(kit: Path, rel: str, mutate) -> None:
        target = kit / rel
        value = json.loads(target.read_text(encoding="utf-8"))
        mutate(value)
        target.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def run_kit(cls, kit: Path, host: Path, verb: str = "init"):
        result = subprocess.run(
            [sys.executable, str(CLI), verb, "--root", str(host), "--kit", str(kit)],
            capture_output=True, text=True,
        )
        print(f"\n$ {verb} --kit <{kit.parent.name}> --root <host>\n"
              f"[exit {result.returncode}]\n{result.stdout}{result.stderr}")
        return result

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
            self.edit_json(kit, "capabilities/knowledge/capability.json",
                           lambda c: c.__setitem__("requires", [{"kind": "capability", "id": "authority"}]))
        result = self.run_kit(self.fixture_kit("provision-aliased", alias_both), self.host())
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
        straight = self.run_kit(KIT, self.host())
        self.assertEqual(0, straight.returncode, straight.stderr)
        self.assertEqual([
            ".agents/project/profile.json",
            ".agents/project/project.json",
            ".agents/project/laws.md",
            ".agents/.gitignore",
            ".agents/kit/doctrine/governance.md",
            ".agents/kit/doctrine/knowledge.md",
            "docs/decisions/ADR-0001-a-documents-kind-decides-its-authority.md",
            "docs/reference/README.md",
            ".agents/generated/governance/INDEX.md",
        ], install_order(straight.stdout))

        def reverse_manifest(kit: Path):
            self.edit_json(kit, "MANIFEST.json",
                           lambda m: m.__setitem__("capabilities", list(reversed(m["capabilities"]))))
        reversed_run = self.run_kit(self.fixture_kit("reversed", reverse_manifest), self.host())
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
        host = self.host()
        self.assertEqual(0, self.run_kit(KIT, host).returncode)
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
        host = self.host()
        self.assertEqual(0, self.run_kit(KIT, host).returncode)
        index = (host / ".agents/generated/governance/INDEX.md").read_text(encoding="utf-8")
        self.assertIn("### knowledge 0.1.0", index)
        self.assertIn("FF-KIND-AUTHORITY", index)
        self.assertIn("docs/decisions/ADR-0001-a-documents-kind-decides-its-authority.md", index)
        self.assertLess(index.index("### governance"), index.index("### knowledge"),
                        "the projection must follow the resolved order, not the manifest's")


if __name__ == "__main__":
    unittest.main(verbosity=2)
