"""Acceptance: the upgrade -- the first time this kit meets a tree it did not create.

Everything the kit had proved before this was proved on a repository it made itself, where
nothing had moved because nothing was ever supposed to have. Here a human has been living in the
host, and one distinction decides everything: *the host edited this* against *upstream changed
this*. It is invisible in the bytes on disk, so the kit records what it GAVE, and every test
below is an attack on that record or on what is done with it.

What these must show, and each one by MUTATION rather than by assertion of the happy path:

  1. a host with no record is REFUSED, by name. Not upgraded conservatively, not assumed
     pristine -- a tree states what it IS and never what it RECEIVED, and bridging that gap
     would make every reading below a fiction dressed as a measurement;
  2. a file the host legitimately changed is not silently overwritten AND not silently kept: it
     is named at every run, and where upstream changed it too, the whole upgrade stops;
  3. that stop is answerable by a NAMED HUMAN and by nothing else -- and what they accepted is
     on the row afterwards, with the digest it superseded;
  4. a refusal that no name resolves stays refused however it is asked;
  5. what the reconciliation SAID would happen is what the installer does. Two decisions would
     be a plan that can drift, and a plan that can drift is believed exactly once;
  6. the declaration is what decides. Remove a cell, remove a mode's steward, and the run
     refuses rather than defaulting -- because a reconciliation that always finds a safe answer
     certifies rather than measures.
"""

from __future__ import annotations

import hashlib
import json
import unittest

from harness import KIT, Fixtures, applied, planned  # noqa: I001 -- sets the interpreter's path

import estate  # noqa: E402
import reconcile  # noqa: E402
from plan import DISPOSITIONS  # noqa: E402

MANIFEST = json.loads((KIT / "MANIFEST.json").read_text(encoding="utf-8"))
STEWARDSHIP = json.loads(
    (KIT / "capabilities" / "governance" / "stewardship.json").read_text(encoding="utf-8"))
SCHEMA = json.loads((KIT / "schemas" / "stewardship.schema.json").read_text(encoding="utf-8"))

#: Where the record lives and which install writes it -- read from the declarations, never spelled
#: here. A test that keeps its own copy of a path goes on passing after the declaration moves it.
GOVERNANCE = json.loads(
    (KIT / "capabilities" / "governance" / "capability.json").read_text(encoding="utf-8"))
ESTATE = next(i["target"] for i in GOVERNANCE["installs"] if i["mode"] == estate.MODE)
A_VENDORED_FILE = next(i for i in GOVERNANCE["installs"] if i["mode"] == "vendor")
A_SEEDED_FILE = next(i for i in GOVERNANCE["installs"] if i["mode"] == "seed")

#: What an upstream release says at a source that used to say something else. One string, used
#: by every fixture below: a digest is what these tests measure, and two spellings of the same
#: bytes would be two homes for the one value they all compare against.
UPSTREAM_NOW = "what upstream says now\n"

#: A plane the kit governs entirely, taken from the manifest rather than named.
VENDOR_PLANE = next(p["root"] for p in MANIFEST["planes"] if p["class"] == "vendor")


def _payload(rel: str, text: str):
    """A fixture kit whose PAYLOAD has moved -- an upstream release, in the only way that
    matters to a reconciliation: the bytes at a declared source are not the bytes that were
    shipped. Written with an explicit LF, because a carriage return crossing a boundary would
    change a digest invisibly and this whole slice is digests."""
    def patch(kit):
        target = kit / rel
        target.write_text(text, encoding="utf-8", newline="\n")
    return patch


def states(stdout: str) -> dict:
    """path -> the state the reconciliation printed for it."""
    words = {row["state"] for s in STEWARDSHIP["stewards"] for row in s["cells"]}
    words |= {reconcile.UNACCOUNTED, reconcile.RE_STEWARDED}
    found = {}
    for line in stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] in words and "/" in parts[1]:
            found[parts[1]] = parts[0]
    return found


class Upgrade(Fixtures, unittest.TestCase):

    # -- 1. the record, or nothing --------------------------------------------------------
    def test_119_a_host_with_no_record_of_what_it_received_is_refused_by_name(self):
        """The cell most likely to be quietly bridged. A tree that LOOKS untouched is not a tree
        that was measured, and treating it as one would make every other reading here a fiction."""
        host = self.installed()
        (host / ESTATE).unlink()
        refused = self.run_kit(KIT, host, "upgrade")
        self.assertNotEqual(0, refused.returncode, "an unreadable host was upgraded anyway")
        self.assertIn(ESTATE, refused.stderr)
        self.assertIn("never what it RECEIVED", refused.stderr)

    def test_120_a_clean_upgrade_states_every_state_including_the_ones_with_none(self):
        """A surface that lists only what it found reads identically to a survey that found
        nothing. Every word any steward can produce is printed with its count, zeros included."""
        host = self.installed()
        clean = self.run_kit(KIT, host, "upgrade")
        self.assertEqual(0, clean.returncode, clean.stderr)
        printed = {line.split()[1] for line in clean.stdout.splitlines()
                   if len(line.split()) == 2 and line.split()[0].isdigit()}
        declared = {row["state"] for s in STEWARDSHIP["stewards"] for row in s["cells"]}
        self.assertTrue(declared <= printed,
                        f"states with no rows went unprinted: {sorted(declared - printed)}")
        self.assertIn("  0 ", clean.stdout, "no zero was declared, so none can be believed")

    # -- 2. the file the host legitimately changed -----------------------------------------
    def test_121_a_host_edit_upstream_did_not_touch_is_kept_and_named_every_run(self):
        """Silently keeping is also a decision, and it leaves no trace: the host then believes it
        is on this version while carrying its own bytes at that path. So it is KEPT and SAID."""
        host = self.installed()
        target = host / A_VENDORED_FILE["target"]
        mine = target.read_text(encoding="utf-8") + "a line this host added\n"
        target.write_text(mine, encoding="utf-8", newline="\n")

        for run in range(2):
            done = self.run_kit(KIT, host, "upgrade")
            self.assertEqual(0, done.returncode, done.stderr)
            self.assertEqual(reconcile.DIVERGED_KEPT,
                             states(done.stdout).get(A_VENDORED_FILE["target"]),
                             f"run {run}: the divergence stopped being reported")
            self.assertEqual(mine, target.read_text(encoding="utf-8"),
                             f"run {run}: the host's own bytes were overwritten")

    def test_122_a_host_edit_upstream_also_changed_stops_the_whole_upgrade(self):
        """The cell this slice exists for. Not the path skipped and the rest applied -- a partial
        upgrade leaves a host in a state no version describes."""
        host = self.installed()
        target = host / A_VENDORED_FILE["target"]
        mine = target.read_text(encoding="utf-8") + "a line this host added\n"
        target.write_text(mine, encoding="utf-8", newline="\n")
        moved = self.fixture_kit("moved", _payload(A_VENDORED_FILE["source"],
                                                   UPSTREAM_NOW))

        refused = self.run_kit(moved, host, "upgrade")
        self.assertEqual(3, refused.returncode, "a conflict did not stall at a door")
        whole = refused.stdout + refused.stderr
        self.assertIn(A_VENDORED_FILE["target"], whole)
        self.assertIn("this reading says", whole, "a refusal that states only one moment")
        self.assertIn("DOOR", whole)
        self.assertEqual(mine, target.read_text(encoding="utf-8"),
                         "a refused upgrade wrote to the path it refused")
        self.assertNotIn(UPSTREAM_NOW.strip(), target.read_text(encoding="utf-8"))

    def test_123_a_named_human_may_accept_it_and_what_they_accepted_is_on_the_row(self):
        """A decision whose only record is a terminal session answers differently on Tuesday."""
        host = self.installed()
        target = host / A_VENDORED_FILE["target"]
        target.write_text(target.read_text(encoding="utf-8") + "mine\n",
                          encoding="utf-8", newline="\n")
        was = estate.__dict__["hashlib"].sha256(target.read_bytes()).hexdigest()
        moved = self.fixture_kit("adopted", _payload(A_VENDORED_FILE["source"],
                                                     UPSTREAM_NOW))

        walked = self.run_kit(moved, host, "upgrade", "--approve", "the-owner")
        self.assertEqual(0, walked.returncode, walked.stderr)
        self.assertEqual(UPSTREAM_NOW, target.read_text(encoding="utf-8"))

        row = next(r for r in json.loads((host / ESTATE).read_text(encoding="utf-8"))["files"]
                   if r["path"] == A_VENDORED_FILE["target"])
        self.assertEqual("the-owner", row["signed_by"], "nobody's name is on the overwrite")
        self.assertTrue(row["signed_at"], "an acceptance with no moment cannot be placed")
        self.assertEqual(was, row["superseded"],
                         "the record does not say what these bytes replaced")

    # -- 3. the refusals no name resolves ---------------------------------------------------
    def test_124_a_path_the_host_authored_where_this_kit_now_ships_one_is_refused(self):
        """No class permits overwriting bytes the kit never wrote -- and no approver either: a
        structural contradiction is not a thing anyone has the standing to wave through."""
        host = self.installed()
        arriving = f"{VENDOR_PLANE}/doctrine/a-file-this-host-wrote-first.md"

        def bring(kit):
            self.edit_json(kit, "capabilities/governance/capability.json",
                           lambda c: c["installs"].append(
                               {"mode": "vendor", "class": "vendor", "target": arriving,
                                "source": A_VENDORED_FILE["source"]}))
        (host / arriving).parent.mkdir(parents=True, exist_ok=True)
        (host / arriving).write_text("mine, and here first\n", encoding="utf-8", newline="\n")

        for flags in ([], ["--approve", "the-owner"]):
            refused = self.run_kit(self.fixture_kit("collides", bring), host, "upgrade", *flags)
            self.assertNotEqual(0, refused.returncode, f"a collision was resolved by {flags}")
            self.assertIn(arriving, refused.stdout + refused.stderr)
            self.assertEqual("mine, and here first\n",
                             (host / arriving).read_text(encoding="utf-8"))

    def test_125_a_file_nothing_explains_is_refused_and_is_not_taken_away(self):
        """An unexplained path in a plane whose whole premise is that every path resolves to a
        declared class. The kit did not put it there and will not remove it."""
        host = self.installed()
        stray = host / VENDOR_PLANE / "a-file-nothing-declares.md"
        stray.write_text("who put me here\n", encoding="utf-8", newline="\n")

        refused = self.run_kit(KIT, host, "upgrade")
        self.assertNotEqual(0, refused.returncode, "an unaccounted path was upgraded past")
        self.assertIn("a-file-nothing-declares.md", refused.stdout + refused.stderr)
        self.assertTrue(stray.exists(), "the kit deleted a file it never wrote")

    # -- 4. what the kit owns, and what the host owns ---------------------------------------
    def test_126_an_untouched_kit_owned_file_takes_the_new_bytes_and_the_record_advances(self):
        """The ordinary upgrade, and the one doctrine self-versioning rides on: the change is
        listed path by path before it happens, and the record afterwards says which version."""
        host = self.installed()
        moved = self.fixture_kit("advances", _payload(A_VENDORED_FILE["source"],
                                                      UPSTREAM_NOW))
        before = json.loads((host / ESTATE).read_text(encoding="utf-8"))

        done = self.run_kit(moved, host, "upgrade")
        self.assertEqual(0, done.returncode, done.stderr)
        self.assertEqual(reconcile.ADVANCED, states(done.stdout).get(A_VENDORED_FILE["target"]))
        self.assertEqual(UPSTREAM_NOW,
                         (host / A_VENDORED_FILE["target"]).read_text(encoding="utf-8"))

        after = json.loads((host / ESTATE).read_text(encoding="utf-8"))
        self.assertNotEqual(before["files"], after["files"], "the record did not move with it")
        row = next(r for r in after["files"] if r["path"] == A_VENDORED_FILE["target"])
        self.assertEqual(
            hashlib.sha256(UPSTREAM_NOW.encode("utf-8")).hexdigest(), row["digest"],
            "the record still says this host holds the bytes it was given last time")

    def test_127_a_seed_the_host_owns_is_offered_and_never_rewritten(self):
        """Create-once is not suspended by an upgrade. A kit that 'just updates' a seed is a kit
        editing the host's own words, and the host would have no way to know it had happened."""
        host = self.installed()
        target = host / A_SEEDED_FILE["target"]
        mine = target.read_text(encoding="utf-8")
        moved = self.fixture_kit("offered", _payload(A_SEEDED_FILE["source"],
                                                     "a seed upstream rewrote\n"))

        done = self.run_kit(moved, host, "upgrade")
        self.assertEqual(0, done.returncode, done.stderr)
        self.assertEqual(mine, target.read_text(encoding="utf-8"), "a seed was rewritten")
        said = states(done.stdout).get(A_SEEDED_FILE["target"])
        self.assertIsNotNone(said, "an upgrade that had new bytes for a seed said nothing")
        self.assertNotEqual(reconcile.UNCHANGED, said,
                            "new content for a seed was not even reported as available")

    # -- 5. one decision, not two -----------------------------------------------------------
    def test_128_what_the_reconciliation_foresaw_is_what_the_installer_carried_out(self):
        """A plan that can drift from its apply is worse than no plan: it is a promise the
        operator believes exactly once. The two are the same value, so they are compared."""
        host = self.installed()
        moved = self.fixture_kit("foreseen", _payload(A_VENDORED_FILE["source"],
                                                      UPSTREAM_NOW))
        foreseen = self.run_kit(moved, host, "upgrade", "--plan")
        self.assertEqual(0, foreseen.returncode, foreseen.stderr)
        carried = self.run_kit(moved, host, "upgrade")
        self.assertEqual(0, carried.returncode, carried.stderr)
        self.assertEqual(planned(foreseen.stdout), applied(carried.stdout),
                         "the upgrade did not do what it said it would do")
        self.assertIn((DISPOSITIONS["replace"], A_VENDORED_FILE["target"]),
                      applied(carried.stdout),
                      "a derivation this test would pass on an empty plan")

    # -- 6. the declaration decides, and its silence is a refusal ---------------------------
    def test_129_a_cell_no_steward_answers_is_refused_rather_than_defaulted(self):
        """A reconciliation that always finds a safe answer certifies rather than measures."""
        host = self.installed()

        def forget(kit):
            self.edit_json(kit, "capabilities/governance/stewardship.json",
                           lambda d: [s.__setitem__("cells", [c for c in s["cells"]
                                                              if c["cell"] != reconcile.UNCHANGED])
                                      for s in d["stewards"]])
        refused = self.run_kit(self.fixture_kit("silent-cell", forget), host, "upgrade")
        self.assertNotEqual(0, refused.returncode, "a cell nothing answers was answered anyway")
        self.assertIn(reconcile.UNCHANGED, refused.stderr)

    def test_130_an_install_mode_with_no_steward_is_refused(self):
        """Nothing states who owns the bytes it writes, so no reconciliation may be attempted
        over it. Declared, not defaulted -- a default is a rule arriving with a new mode."""
        host = self.installed()

        def unown(kit):
            self.edit_json(kit, "capabilities/governance/stewardship.json",
                           lambda d: d.__setitem__(
                               "modes", [m for m in d["modes"] if m["mode"] != "vendor"]))
        refused = self.run_kit(self.fixture_kit("unowned-mode", unown), host, "upgrade")
        self.assertNotEqual(0, refused.returncode, "a path with no declared owner was upgraded")
        self.assertIn("vendor", refused.stderr)

    def test_131_the_dispositions_a_steward_may_name_are_the_plans_own_vocabulary(self):
        """One home for the words. The schema states the contract between the declaration and its
        reader; if it drifted from the plan, a steward could name an effect nothing can carry out
        and the file would read perfectly."""
        column = SCHEMA["properties"]["stewards"]["items"]["properties"]["cells"]["items"]
        self.assertEqual(sorted(DISPOSITIONS), sorted(column["properties"]["file"]["enum"]),
                         "the schema and the plan disagree about what may happen to a file")
        named = {row["file"] for s in STEWARDSHIP["stewards"] for row in s["cells"]}
        self.assertTrue(named <= set(DISPOSITIONS),
                        f"a steward names an effect no plan can carry out: {named}")
