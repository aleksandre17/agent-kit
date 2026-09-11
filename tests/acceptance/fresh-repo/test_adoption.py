"""Acceptance: ADOPTION -- the kit entering a tree it NEVER CREATED.

`upgrade` met a tree the kit had made and a human had since edited. Here the kit meets a
repository written by people and tools that never heard of it: paths whose provenance is unknown
and unknowable from inside the tree, some of them sitting exactly where this kit installs.

The decision under test is ADR-003: `foreign` is NOT a fifth class. A class in this kit is a
WRITE PERMISSION conferred by a declaration, so a class conferred by the ABSENCE of a declaration
would be a permission over bytes nobody declared -- and it would make `path-class-total`
unfalsifiable, because every unexplained path would then resolve to exactly one class forever.
A foreign path therefore has NO class, and it HALTS.

What these must show, each by attacking the thing rather than asserting the happy path:

  1. a path the host authored where this kit installs stops the WHOLE operation, and not one byte
     of the host moves -- for a kit-owned path and for a host-owned one alike;
  2. a path is found because a DECLARATION accounts for the plane it sits in, never because its
     name looked like something. The pair matters more than either half: an unrecognisable name
     inside a governed plane HALTS, and a name copied verbatim from the kit's own payload, sitting
     outside every plane, does NOT. A heuristic over filenames would get exactly one of those
     right, and it is the precise lie this whole system exists to prevent;
  3. the roster is produced by the machine: every row traceable to an install statement or a plane
     root, every state printed with a count, and the zeros printed as zeros;
  4. adoption cannot be bypassed. Typing the installer's name instead, or walking the human door,
     reaches the same refusal;
  5. it introduces NO cell of its own -- every word it prints is one some steward already
     declared, which is the evidence that the four-class seam was complete all along;
  6. the gate that holds the seam can still go RED. A decision that makes a fitness function
     unfalsifiable is not a decision, it is a retirement;
  7. a host inside a host is refused BY NAME, at the boundary, before anything is read;
  8. and the half of that rule which ADR-003 Section 6 had to amend after HOST #2: whether an
     unaccounted path REFUSES is the PLANE's own declaration. A plane the kit disclaims reports
     and does not obstruct; a plane the kit owns still halts the whole operation. The pair is the
     test -- a change that only relaxed would have retired the gate rather than corrected it.
"""

from __future__ import annotations

import json
import unittest

from harness import (  # noqa: I001 -- sets the interpreter's path before the imports below
    KIT,
    Fixtures,
    census,
    host_digest,
    reconciliation_words,
    states,
)

import adoption  # noqa: E402
import reconcile  # noqa: E402

MANIFEST = json.loads((KIT / "MANIFEST.json").read_text(encoding="utf-8"))
GOVERNANCE = json.loads(
    (KIT / "capabilities" / "governance" / "capability.json").read_text(encoding="utf-8"))

#: Two paths this kit installs, under two different stewards -- read from the declarations, never
#: spelled here. A collision is a refusal for both, and for different reasons: the kit may not
#: overwrite bytes it never wrote, and it may not create-once over a file already authored.
A_KIT_OWNED_PATH = next(i["target"] for i in GOVERNANCE["installs"] if i["mode"] == "vendor")
A_HOST_OWNED_PATH = next(i["target"] for i in GOVERNANCE["installs"] if i["mode"] == "seed")

#: A plane this kit governs entirely, taken from the manifest.
VENDOR_PLANE = next(p["root"] for p in MANIFEST["planes"] if p["class"] == "vendor")
#: Asked of the DECLARATION, never named here: which plane reports what it does not account for,
#: and which refuse. A test that hardcoded `ephemeral` would pass a manifest that had changed its
#: mind, and would be measuring this file's memory instead of the kit's statement (ADR-003 Section 6).
REPORTING_PLANES = [p for p in MANIFEST["planes"] if p["unaccounted"] == "report"]
REFUSING_PLANES = [p for p in MANIFEST["planes"] if p["unaccounted"] == "refuse"]

#: A name lifted VERBATIM from the kit's own payload, to be planted where no plane reaches. If
#: anything here classed by resemblance, this is the file it would seize.
A_NAME_THE_KIT_ALSO_USES = A_KIT_OWNED_PATH.split("/")[-1]

#: The root the class-total gate is DECLARED to hold, read from the declaration that holds it. It
#: is the parent of the planes: a path directly beneath it resolves to no class at all, which is
#: the reading that must still be able to fail.
GOVERNED_ROOT = next(g["params"]["root"] for g in GOVERNANCE["gates"]
                     if g["kind"] == "path-class-total")

#: A name that resembles nothing this kit ships, to be planted inside a governed plane. If
#: anything here classed by resemblance, this is the file it would miss.
A_NAME_NOTHING_RESEMBLES = "zqx-notes-from-2019.tmp"


def _plant(host, rel: str, text: str = "bytes this kit never wrote\n"):
    """A path written by somebody who never heard of this kit. Explicit LF: a carriage return
    crossing a boundary changes a digest invisibly, and this whole slice is digests."""
    target = host / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")
    return target


class Adoption(Fixtures, unittest.TestCase):

    # -- 1. the foreign path halts, and the host does not move ----------------------------
    def test_132_a_path_the_host_authored_where_this_kit_installs_halts_the_whole_install(self):
        """Two stewards, one answer. The kit may not overwrite bytes it never wrote, and it may
        not create-once over a file that is already there -- neither is a permission any
        declaration grants, so neither is taken."""
        for target in (A_KIT_OWNED_PATH, A_HOST_OWNED_PATH):
            with self.subTest(target=target):
                host = self.host()
                _plant(host, target)
                before = host_digest(host)
                refused = self.run_kit(KIT, host, "init")
                self.assertNotEqual(0, refused.returncode, f"{target} was installed over")
                self.assertIn(target, refused.stderr)
                self.assertIn("no permission", refused.stderr)
                self.assertEqual(before, host_digest(host),
                                 "a refused adoption still moved bytes in the host")

    def test_133_the_refusal_is_whole_and_names_every_foreign_path_at_once(self):
        """Not this path skipped and the rest installed. A partial adoption leaves a tree in a
        state no version describes, and nothing afterwards can say what it is."""
        host = self.host()
        planted = [A_KIT_OWNED_PATH, A_HOST_OWNED_PATH,
                   f"{VENDOR_PLANE}/{A_NAME_NOTHING_RESEMBLES}"]
        for rel in planted:
            _plant(host, rel)
        before = host_digest(host)
        refused = self.run_kit(KIT, host, "init")
        self.assertNotEqual(0, refused.returncode)
        for rel in planted:
            self.assertIn(rel, refused.stderr, f"{rel} was left out of the roster")
        self.assertIn("3 path(s)", refused.stderr, "the refusal did not count what it refused")
        self.assertEqual(before, host_digest(host))

    # -- 2. found by DECLARATION, never by resemblance -------------------------------------
    def test_134_a_path_is_foreign_because_a_declaration_accounts_for_its_plane_not_its_name(self):
        """The pair is the test. A name resembling nothing, inside a plane a declaration governs,
        HALTS; the kit's own filename, planted where no plane reaches, does NOT. A heuristic over
        filenames gets exactly one of these right -- and it is the lie this system exists against.
        """
        unrecognisable_but_governed = f"{VENDOR_PLANE}/{A_NAME_NOTHING_RESEMBLES}"
        host = self.host()
        _plant(host, unrecognisable_but_governed)
        halted = self.run_kit(KIT, host, "adopt")
        self.assertNotEqual(0, halted.returncode, "a governed plane admitted an unexplained path")
        self.assertIn(unrecognisable_but_governed, halted.stderr)
        self.assertEqual(reconcile.UNACCOUNTED,
                         states(halted.stdout).get(unrecognisable_but_governed))

        familiar_but_ungoverned = f"somebody-elses/{A_NAME_THE_KIT_ALSO_USES}"
        clean = self.host()
        _plant(clean, familiar_but_ungoverned)
        adopted = self.run_kit(KIT, clean, "adopt")
        self.assertEqual(0, adopted.returncode,
                         f"{familiar_but_ungoverned} was seized because its NAME looked familiar")
        self.assertNotIn(familiar_but_ungoverned, adopted.stdout)

    # -- 3. the roster is the machine's, and its zeros are declared ------------------------
    def test_135_the_roster_states_every_state_including_the_ones_with_none(self):
        """A surface that lists only what it found reads identically to a survey that found
        nothing. Every word any steward can produce is printed with its count."""
        host = self.host()
        _plant(host, f"{VENDOR_PLANE}/{A_NAME_NOTHING_RESEMBLES}")
        read = self.run_kit(KIT, host, "adopt")
        counted = census(read.stdout)
        self.assertEqual(reconciliation_words(), set(counted),
                         "a state the reconciliation can produce went unprinted")
        self.assertEqual(1, counted[reconcile.UNACCOUNTED])
        self.assertEqual(0, counted[reconcile.COLLISION], "an uncounted zero cannot be believed")

    def test_136_adoption_introduces_no_state_of_its_own(self):
        """Adoption is the SAME reconciliation with one reading empty. If it had needed a word of
        its own, the four-class seam would have had a hole in it -- and it did not."""
        host = self.host()
        _plant(host, A_KIT_OWNED_PATH)
        _plant(host, f"{VENDOR_PLANE}/{A_NAME_NOTHING_RESEMBLES}")
        read = self.run_kit(KIT, host, "adopt")
        printed = set(states(read.stdout).values()) | set(census(read.stdout))
        self.assertTrue(printed <= reconciliation_words(),
                        f"adoption invented {sorted(printed - reconciliation_words())}")
        self.assertNotIn("foreign", MANIFEST["classes"],
                         "`foreign` became a class, and a class is a write permission")

    def test_137_adopt_reads_and_writes_nothing_at_all(self):
        """A verb whose whole subject is paths this kit has no permission to touch may not begin
        by writing into the host it is surveying -- not a plane, not a record, not a marker."""
        host = self.host()
        before = host_digest(host)
        read = self.run_kit(KIT, host, "adopt")
        self.assertEqual(0, read.returncode, read.stderr)
        self.assertEqual(before, host_digest(host), "the reading half wrote into the host")
        self.assertIn("no path in this host stands foreign", read.stdout)

    # -- 4. it cannot be bypassed -----------------------------------------------------------
    def test_138_neither_the_installer_nor_the_human_door_can_walk_past_a_foreign_path(self):
        """`adopt` would be advisory decoration if typing the installer's name got past it, and
        the door is for accepting a REPLACEMENT the kit is entitled to make -- never for granting
        a permission no declaration confers."""
        for flags in ((), ("--approve", "somebody"), ("--plan",)):
            with self.subTest(flags=flags):
                host = self.host()
                _plant(host, A_KIT_OWNED_PATH)
                before = host_digest(host)
                refused = self.run_kit(KIT, host, "init", *flags)
                self.assertNotEqual(0, refused.returncode,
                                    f"adoption was walked past with {flags}")
                self.assertIn(A_KIT_OWNED_PATH, refused.stderr)
                self.assertEqual(before, host_digest(host))

    def test_139_a_host_that_has_already_answered_is_carried_forward_and_never_re_adopted(self):
        """Adopting an installed host would take a reading saying it was given nothing, over a
        host that was given something -- and every reading built on that is a fiction."""
        host = self.installed()
        refused = self.run_kit(KIT, host, "adopt")
        self.assertNotEqual(0, refused.returncode, "an installed host was adopted a second time")
        self.assertIn("already ANSWERED", refused.stderr)
        self.assertIn("upgrade", refused.stderr)

    def test_140_the_roster_is_re_taken_and_never_edited(self):
        """A human resolves a row by changing what a fresh reading MEASURES -- moving the path --
        and never by classing it. So the same command, run again, says something different."""
        host = self.host()
        planted = _plant(host, f"{VENDOR_PLANE}/{A_NAME_NOTHING_RESEMBLES}")
        self.assertNotEqual(0, self.run_kit(KIT, host, "adopt").returncode)
        moved = host / A_NAME_NOTHING_RESEMBLES
        planted.rename(moved)
        self.assertEqual(0, self.run_kit(KIT, host, "adopt").returncode,
                         "a resolved roster still refused")
        moved.rename(planted)
        self.assertNotEqual(0, self.run_kit(KIT, host, "adopt").returncode,
                            "the reading did not change back, so it was not a reading")

    # -- 6. the seam's own gate must still be able to fail -----------------------------------
    def test_141_the_gate_that_holds_the_four_class_seam_can_still_go_red(self):
        """The whole argument against a fifth class. Had `foreign` become one, every unexplained
        path would resolve to exactly one class and this gate could never fail again -- an
        attribution that cannot fail certifies rather than measures."""
        host = self.installed()
        clean = self.run_kit(KIT, host, "check")
        self.assertEqual(0, clean.returncode, clean.stderr)
        _plant(host, f"{GOVERNED_ROOT}/{A_NAME_NOTHING_RESEMBLES}")
        red = self.run_kit(KIT, host, "check")
        self.assertNotEqual(0, red.returncode, "an unclassed path passed the class-total gate")
        self.assertIn("no class", red.stdout)

    # -- 7. the host inside a host ----------------------------------------------------------
    def test_142_a_host_inside_a_host_is_refused_by_name_before_anything_is_read(self):
        """Every verb takes one --root and installs one surface, and nothing states what a nested
        host inherits or may contradict. Two hosts, each internally right, is the failure no
        participant can detect from where it stands -- so it is refused rather than survived."""
        outer = self.installed()
        inner = outer / "packages" / "core"
        inner.mkdir(parents=True)
        #: The path that made the outer directory a HOST -- asked of the declarations, so the
        #: refusal is shown to name the thing it actually measured.
        identifying = next(i["target"] for i in GOVERNANCE["installs"]
                           if i["mode"] in adoption.IDENTIFYING)
        for verb in ("adopt", "init"):
            with self.subTest(verb=verb):
                before = host_digest(outer)
                refused = self.run_kit(KIT, inner, verb)
                self.assertNotEqual(0, refused.returncode, f"{verb} nested one host inside another")
                self.assertIn("INSIDE a host this kit already holds", refused.stderr)
                self.assertIn(identifying, refused.stderr,
                              "the refusal did not name what made the outer root a host")
                self.assertIn("GAP-NESTED-HOST-GRAMMAR", refused.stderr)
                self.assertEqual(before, host_digest(outer),
                                 "a refused nested install still moved bytes")

    # -- 8. the stance toward the unaccounted belongs to the PLANE (ADR-003 Section 6) ------
    def test_143_a_plane_the_kit_disclaims_reports_what_it_does_not_account_for_and_never_refuses(self):
        """Measured on HOST #2, the first tree this kit ever met that it did not create: 81 session
        receipts in the ephemeral plane made a real repository unadoptable. The surface said `the
        kit did not put it here and will not take it away` and in the same breath demanded it be
        removed. Nothing in a region the kit owns nothing in can obstruct a write it was never
        going to make -- and the path is still PRINTED, because not refusing is not the same as
        not seeing."""
        self.assertTrue(REPORTING_PLANES, "no plane declares that it reports; Section 6 is unreachable")
        for plane in REPORTING_PLANES:
            with self.subTest(plane=plane["class"]):
                dropping = f"{plane['root']}/{A_NAME_NOTHING_RESEMBLES}"
                host = self.host()
                _plant(host, dropping)
                read = self.run_kit(KIT, host, "adopt")
                self.assertEqual(0, read.returncode,
                                 f"{plane['class']!r} obstructed an install over a path it disclaims")
                self.assertIn(dropping, read.stdout, "a reported path was not printed at all")
                self.assertEqual(reconcile.UNACCOUNTED, states(read.stdout).get(dropping),
                                 "a reported path lost the state that names what it is")
                self.assertNotIn(dropping, read.stderr,
                                 "a path that does not refuse was still named in the refusal")

    def test_144_a_plane_the_kit_owns_still_halts_the_whole_operation_over_one_unaccounted_path(self):
        """The other half, and the reason this is a correction rather than a retirement. A relaxation
        that also stopped the owned planes from biting would have deleted the rule while appearing
        to refine it -- and a gate earns its keep only by DENYING."""
        self.assertTrue(REFUSING_PLANES, "no plane refuses; the seam has stopped holding anything")
        for plane in REFUSING_PLANES:
            with self.subTest(plane=plane["class"]):
                intruder = f"{plane['root']}/{A_NAME_NOTHING_RESEMBLES}"
                host = self.host()
                _plant(host, intruder)
                before = host_digest(host)
                refused = self.run_kit(KIT, host, "init")
                self.assertNotEqual(0, refused.returncode,
                                    f"{plane['class']!r} admitted an unexplained path")
                self.assertIn(intruder, refused.stderr)
                self.assertEqual(before, host_digest(host),
                                 "a refused install still moved bytes in the host")


if __name__ == "__main__":
    unittest.main()
