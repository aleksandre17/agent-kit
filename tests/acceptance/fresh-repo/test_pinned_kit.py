"""Acceptance: the host carries its kit (ADR-016, link B of the whole line).

The blueprint's arrow ① says the payload crosses into a host as vendor + lock, and that a host's
kit plane is a PINNED COPY of the kit. Measured before this slice, a clean host held nine doctrine
pages and no interpreter: it could run nothing by itself. These tests hold the opposite, and each
one is a mutation against a real fixture kit or a real host:

  1. an approved host holds the WHOLE kit, verbatim, at its tree target, and the lock it is judged
     against at the declared seat -- and a release pins its own lock byte for byte;
  2. a verb runs from that copy with the kit that installed it GONE, and says which kit spoke;
  3. a working tree pins honestly, as `+unreleased`, never as the release it is not;
  4. a changed pinned file fails its gate by name, and the pinned copy refuses to re-stamp itself;
  5. the same release is kept, not rewritten; a stray file is removed by the next delivery;
  6. `release` states identity and says authenticity is NOT ESTABLISHED -- and refuses a working
     tree;
  7. a release SOURCE is read at a revision, and a revision that is not a release is refused.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from harness import CLI, KIT, LOCK, Fixtures, applied, ship  # noqa: I001 -- sets the interpreter's path

import pin  # noqa: E402
from manifest import Manifest  # noqa: E402

#: Where the pinned kit lands, and where the lock the host was given sits -- asked of the
#: declarations, never spelled here.
PINNED, SEAT = pin.seats(Manifest(KIT))
CODE = pin.ReleaseError.code


def said(result) -> str:
    return result.stdout + result.stderr


def pinned_cli(host: Path, verb: str, *flags):
    result = subprocess.run(
        [sys.executable, str(host / PINNED / "interpreters" / "cli.py"), verb, "--root", str(host),
         *flags], capture_output=True, text=True, encoding="utf-8", cwd=str(host))
    print(f"\n$ <pinned> {verb} {' '.join(flags)}\n[exit {result.returncode}]\n{said(result)}")
    return result


def from_source(source: str, host: Path, verb: str, *flags):
    """A run whose `--kit` is given as TEXT -- a directory, or a release source (a revision)."""
    result = subprocess.run([sys.executable, str(CLI), verb, "--root", str(host), "--kit", source,
                             *flags], capture_output=True, text=True, encoding="utf-8")
    print(f"\n$ {verb} {' '.join(flags)} --kit {source}\n[exit {result.returncode}]\n{said(result)}")
    return result


class PinnedKit(Fixtures, unittest.TestCase):

    def test_273_an_approved_host_carries_the_whole_kit_and_the_lock_at_its_seat(self):
        host = self.installed()
        lock = json.loads((KIT / LOCK).read_text(encoding="utf-8"))
        for entry in lock["files"]:
            self.assertEqual((KIT / entry["path"]).read_bytes(),
                             (host / PINNED / entry["path"]).read_bytes(), entry["path"])
        self.assertEqual((KIT / LOCK).read_bytes(), (host / SEAT).read_bytes(),
                         "a release pins its OWN lock, verbatim, at the declared seat")
        on_disk = {p.relative_to(host / PINNED).as_posix()
                   for p in (host / PINNED).rglob("*") if p.is_file()}
        self.assertEqual({e["path"] for e in lock["files"]}, on_disk,
                         "the pinned tree is exactly the release: nothing missing, nothing extra "
                         "-- and no second copy of any page beside it")

    def test_274_a_verb_runs_from_the_pinned_copy_with_the_installing_kit_gone(self):
        kit = self.fixture_kit("gone")
        host = self.installed(kit)
        shutil.rmtree(kit.parent)
        self.assertFalse(kit.exists())
        ran = pinned_cli(host, "check")
        self.assertEqual(0, ran.returncode, said(ran))
        first = ran.stdout.splitlines()[0]
        self.assertIn(f"kit at {(host / PINNED).resolve().as_posix().rstrip('/')}", first,
                      "the first line of every run names the kit that spoke")
        self.assertIn("PASS  FF-KIT-PINNED", ran.stdout)

    def test_275_a_working_tree_pins_as_unreleased_and_never_as_the_release(self):
        kit = self.fixture_kit("tree", patch=lambda k: (k / "README.md").write_text(
            (k / "README.md").read_text(encoding="utf-8") + "\nan uncommitted line\n",
            encoding="utf-8", newline="\n"))
        host = self.installed(kit)
        held = json.loads((host / SEAT).read_text(encoding="utf-8"))
        version = Manifest(kit).version
        self.assertEqual(f"{version}+{pin.UNRELEASED}", held["kit_version"])
        self.assertIn("an uncommitted line", (host / PINNED / "README.md").read_text(encoding="utf-8"))
        self.assertEqual(0, pinned_cli(host, "check").returncode)
        refused = pinned_cli(host, "release")
        self.assertNotEqual(0, refused.returncode)
        self.assertIn(f"[{CODE}]", refused.stderr)

    def test_276_a_changed_pinned_file_fails_its_gate_and_the_copy_refuses_to_restamp_itself(self):
        host = self.installed()
        target = host / PINNED / "README.md"
        target.write_text(target.read_text(encoding="utf-8") + "tampered\n",
                          encoding="utf-8", newline="\n")
        ran = pinned_cli(host, "check")
        self.assertNotEqual(0, ran.returncode)
        self.assertIn("FAIL  FF-KIT-PINNED", ran.stdout)
        self.assertIn(f"{PINNED}README.md: {pinned_lockfile_state('stale')}", ran.stdout)
        again = pinned_cli(host, "init")
        self.assertIn(f"[{CODE}]", again.stderr)
        self.assertIn("delivering ITSELF", again.stderr)
        self.assertIn("tampered", target.read_text(encoding="utf-8"),
                      "a refusal writes nothing -- the host's bytes are still what it had")

    def test_277_the_same_release_is_kept_and_a_stray_file_is_removed_by_the_next_delivery(self):
        host = self.installed()
        again = self.run_kit(KIT, host, "init")
        self.assertEqual(0, again.returncode, said(again))
        self.assertIn(("kept", PINNED), applied(again.stdout))
        stray = host / PINNED / "interpreters" / "stray.py"
        stray.write_text("# nobody shipped this\n", encoding="utf-8")
        failed = pinned_cli(host, "check")
        self.assertIn(f"{PINNED}interpreters/stray.py", failed.stdout)
        healed = self.run_kit(KIT, host, "init")
        self.assertIn(("replaced", PINNED), applied(healed.stdout))
        self.assertFalse(stray.exists(), "the tree is the release; a stray is not carried")
        self.assertEqual(0, pinned_cli(host, "check").returncode)

    def test_278_release_states_identity_and_never_implies_authenticity(self):
        host = self.host()
        ran = from_source(str(KIT), host, "release")
        self.assertEqual(0, ran.returncode, said(ran))
        digest = pin.digest_of((KIT / LOCK).read_text(encoding="utf-8"))
        self.assertIn(f"release {Manifest(KIT).version} · lock sha256:{digest}", ran.stdout)
        self.assertIn(pin.UNSIGNED, ran.stdout)
        self.assertFalse((host / ".agents").exists(), "release writes nothing into the host")
        tree = self.fixture_kit("unlocked", patch=lambda k: (k / "README.md").write_text(
            "changed\n", encoding="utf-8", newline="\n"))
        refused = from_source(str(tree), host, "release")
        self.assertIn(f"[{CODE}]", refused.stderr)
        self.assertIn("README.md", refused.stderr)

    def test_279_a_release_source_is_read_at_a_revision_and_a_non_release_revision_is_refused(self):
        repo = self._temp("kit-upstream-")
        subprocess.run(["git", "init", "--quiet", str(repo)], check=True)
        shutil.copyfile(KIT.parent / ".gitattributes", repo / ".gitattributes")
        ship(repo / "kit")
        git = ["git", "-C", str(repo), "-c", "user.name=suite", "-c", "user.email=suite@invalid"]
        subprocess.run([*git, "add", "."], check=True, capture_output=True)
        subprocess.run([*git, "commit", "--quiet", "-m", "a release"], check=True)
        source = f"git+{repo.as_posix()}@HEAD#subdirectory=kit"
        host = self.host()
        drafted = from_source(source, host, "init")
        self.assertEqual(3, drafted.returncode, said(drafted))
        done = from_source(source, host, "init", "--approve", "acceptance-suite")
        self.assertEqual(0, done.returncode, said(done))
        self.assertEqual((KIT / LOCK).read_bytes(), (host / SEAT).read_bytes())
        self.assertEqual([], list(Path(tempfile.gettempdir()).glob("kit-release-*")),
                         "the fetched release is removed after the run")
        (repo / "kit" / "README.md").write_text("not the release\n", encoding="utf-8")
        subprocess.run([*git, "commit", "--quiet", "-am", "a drifted tree"], check=True)
        refused = from_source(source, self.host(), "init")
        self.assertIn(f"[{CODE}]", refused.stderr)
        self.assertIn("is not a release", refused.stderr)
        # The working tree of that repository is not what was read: HEAD is.
        self.assertIn("README.md", refused.stderr)


class PinnedComposition(Fixtures, unittest.TestCase):

    def test_280_a_capability_the_host_took_is_still_taken_when_the_pinned_copy_speaks(self):
        """Found on the live walk of host #2, not foreseen: the first pinned lock was a fresh
        reading of EVERYTHING, so provenance run from the pinned copy saw the taken adapters as
        issued by the kit and reported every pin WITHDRAWN -- while they were in force."""
        from test_adapters import adapted_kit  # noqa: E402 -- the one way a host takes adapters
        import lockfile  # noqa: E402
        import provenance  # noqa: E402

        kit = adapted_kit()
        host = self.installed(kit)
        held = json.loads((host / SEAT).read_text(encoding="utf-8"))
        not_issued = {e["path"] for e in held["files"] if e["accounted_by"] == lockfile.NOT_ISSUED}
        self.assertTrue(not_issued, "the taken adapters were absorbed into what the kit issued")
        self.assertEqual(set(), not_issued & lockfile.issued(json.loads(
            (KIT / LOCK).read_text(encoding="utf-8"))), "a path the kit issued was marked not issued")
        shutil.rmtree(kit.parent)
        ran = pinned_cli(host, "check")
        self.assertIn(f"integrity {provenance.PINNED.upper()}", ran.stdout)
        self.assertNotIn(provenance.WITHDRAWN.upper(), ran.stdout)
        self.assertIn("PASS  FF-PROVENANCE-PINNED", ran.stdout)
        self.assertIn("PASS  FF-KIT-PINNED", ran.stdout)


def pinned_lockfile_state(word: str) -> str:
    """The state word as the lock survey owns it -- imported, never restated."""
    import lockfile  # noqa: E402
    return {"stale": lockfile.STALE}[word]


if __name__ == "__main__":
    unittest.main()
