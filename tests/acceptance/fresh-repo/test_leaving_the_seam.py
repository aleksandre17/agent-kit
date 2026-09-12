"""Acceptance: leaving the seam -- a host taking over what the kit vendored into it (ADR-010).

The kit's answer is not an `eject`. It is a door, one PATH at a time: a named person signs it, the
estate row records who, when and what the host held, the row's class becomes the class the
steward declares its paths transfer to, and from then on no writer of this kit touches the path
and every reading names it. Each test below is an attack on one of those promises:

  1. nothing changes hands without a name -- a cede with no approver stalls at the door, and a
     plan writes nothing;
  2. what changed hands is on the row: who, when, what the host held, and the one class it now
     holds -- while the moment the host RECEIVED its bytes does not move;
  3. no writer takes it back: not `upgrade` when upstream moved, not `init` run again, not a
     restore after the host deleted it;
  4. the surface never lies: the path is named as taken over on every reading, including the
     unremarkable ones, and upstream bytes it no longer receives are said to exist;
  5. the declaration decides: a steward that offers no transfer cannot be ceded from, a transfer
     to a class the kit does not declare is refused, and a record claiming a transfer no
     declaration offers is refused rather than read;
  6. a request is whole or nothing: one path that cannot change hands stops all of them.
"""

from __future__ import annotations

import hashlib
import json
import unittest

from harness import KIT, Fixtures, states  # noqa: I001 -- sets the path

import estate  # noqa: E402

MANIFEST = json.loads((KIT / "MANIFEST.json").read_text(encoding="utf-8"))
STEWARDSHIP_SOURCE = "capabilities/governance/stewardship.json"
STEWARDSHIP = json.loads((KIT / STEWARDSHIP_SOURCE).read_text(encoding="utf-8"))
GOVERNANCE = json.loads(
    (KIT / "capabilities" / "governance" / "capability.json").read_text(encoding="utf-8"))

#: Everything below is READ from the declarations. A test holding its own copy of a path, a
#: steward or a class would go on passing after the declaration moved.
ESTATE = next(i["target"] for i in GOVERNANCE["installs"] if i["mode"] == estate.MODE)
A_VENDORED_FILE = next(i for i in GOVERNANCE["installs"] if i["mode"] == "vendor")
A_SEEDED_FILE = next(i for i in GOVERNANCE["installs"] if i["mode"] == "seed")
_STEWARD_OF = {row["mode"]: row["steward"] for row in STEWARDSHIP["modes"]}
_BY_ID = {s["id"]: s for s in STEWARDSHIP["stewards"]}
TRANSFER = _BY_ID[_STEWARD_OF[A_VENDORED_FILE["mode"]]]["transfers_to"]
RECEIVING = _BY_ID[TRANSFER["steward"]]
#: The words the receiving steward prints, by cell -- the surface's vocabulary, from its one home.
SAYS = {row["cell"]: row["state"] for row in RECEIVING["cells"]}

UPSTREAM_NOW = "what upstream says now\n"
REFUSED = "[KIT0035]"


def _payload(rel: str, text: str):
    def patch(kit):
        (kit / rel).write_text(text, encoding="utf-8", newline="\n")
    return patch


def _row(host, path):
    record = json.loads((host / ESTATE).read_text(encoding="utf-8"))
    return next(r for r in record["files"] if r["path"] == path), record


class LeavingTheSeam(Fixtures, unittest.TestCase):

    def _ceded(self, kit=KIT):
        host = self.installed(kit)
        done = self.run_kit(kit, host, "cede", "--path", A_VENDORED_FILE["target"],
                            "--approve", "the-owner")
        self.assertEqual(0, done.returncode, done.stderr)
        return host

    def _edit(self, host, line="a line this host owns now\n"):
        target = host / A_VENDORED_FILE["target"]
        mine = target.read_text(encoding="utf-8") + line
        target.write_text(mine, encoding="utf-8", newline="\n")
        return target, mine

    # -- 1. nothing changes hands without a name ----------------------------------------------
    def test_219_a_cede_with_no_approver_stalls_at_the_door_and_a_plan_writes_nothing(self):
        """A one-way door for a host is a HUMAN door. Neither asking nor planning opens it."""
        host = self.installed()
        before = (host / ESTATE).read_bytes()

        planned = self.run_kit(KIT, host, "cede", "--path", A_VENDORED_FILE["target"], "--plan")
        self.assertEqual(0, planned.returncode, planned.stderr)
        self.assertIn(A_VENDORED_FILE["target"], planned.stdout)
        self.assertIn(RECEIVING["summary"], planned.stdout,
                      "the plan did not state what the host loses, in the declaration's words")

        stalled = self.run_kit(KIT, host, "cede", "--path", A_VENDORED_FILE["target"])
        self.assertEqual(3, stalled.returncode, "a transfer with nobody's name on it went through")
        self.assertIn("DOOR", stalled.stderr)
        self.assertEqual(before, (host / ESTATE).read_bytes(),
                         "the record changed before anyone signed for it")

    # -- 2. what changed hands is on the row --------------------------------------------------
    def test_220_the_row_records_who_when_what_was_held_and_the_one_class_it_holds_now(self):
        host = self.installed()
        held = hashlib.sha256((host / A_VENDORED_FILE["target"]).read_bytes()).hexdigest()
        _, before = _row(host, A_VENDORED_FILE["target"])
        self._ceded_on(host)

        row, after = _row(host, A_VENDORED_FILE["target"])
        signed = row[estate.CEDED]
        self.assertEqual("the-owner", signed["signed_by"])
        self.assertTrue(signed["signed_at"], "a transfer with no moment cannot be placed")
        self.assertEqual(held, signed["held"], "the row does not say what the host took over")
        self.assertEqual(TRANSFER["class"], row["class"],
                         "the path does not hold the class its steward transfers it to")
        self.assertEqual(A_VENDORED_FILE["mode"], row["mode"],
                         "history changed hands too: the mode that wrote the bytes was rewritten")
        self.assertEqual((before["taken_at"], before["signed_by"]),
                         (after["taken_at"], after["signed_by"]),
                         "the moment this host RECEIVED its bytes moved over a delivery that "
                         "never happened")

    def _ceded_on(self, host):
        done = self.run_kit(KIT, host, "cede", "--path", A_VENDORED_FILE["target"],
                            "--approve", "the-owner")
        self.assertEqual(0, done.returncode, done.stderr)

    # -- 3. no writer takes it back -------------------------------------------------------------
    def test_221_after_a_cede_an_upstream_change_to_an_edited_file_neither_refuses_nor_writes(self):
        """Without the cede this exact tree is a conflict that stops the upgrade (test_122). With
        it, the path is the host's: the upgrade goes through, keeps the host's bytes, and SAYS
        that upstream has bytes this host will not receive."""
        host = self._ceded()
        target, mine = self._edit(host)
        moved = self.fixture_kit("ceded-moved", _payload(A_VENDORED_FILE["source"], UPSTREAM_NOW))

        done = self.run_kit(moved, host, "upgrade")
        self.assertEqual(0, done.returncode, done.stderr)
        self.assertEqual(mine, target.read_text(encoding="utf-8"),
                         "an upgrade wrote to a path the host had taken over")
        self.assertEqual(SAYS["conflicted"], states(done.stdout).get(A_VENDORED_FILE["target"]),
                         "the upgrade did not say what this host no longer receives")
        self.assertIn("taken over by the-owner", done.stdout)
        self.assertIn(estate.CEDED, _row(host, A_VENDORED_FILE["target"])[0],
                      "the upgrade's record dropped the signature")

    def test_222_init_run_again_does_not_replace_a_file_the_host_took_over(self):
        """A vendor mode replaces because it cannot tell whether the host touched a file. The
        record says so, with a name on it, and a second `init` is not a way around a door."""
        host = self._ceded()
        target, mine = self._edit(host)
        again = self.run_kit(KIT, host, "init")
        self.assertEqual(0, again.returncode, again.stderr)
        self.assertEqual(mine, target.read_text(encoding="utf-8"),
                         "init replaced a file the host had taken over")
        self.assertIn(estate.CEDED, _row(host, A_VENDORED_FILE["target"])[0])

    def test_223_a_file_the_host_took_over_and_then_deleted_is_not_restored(self):
        host = self._ceded()
        (host / A_VENDORED_FILE["target"]).unlink()
        done = self.run_kit(KIT, host, "upgrade")
        self.assertEqual(0, done.returncode, done.stderr)
        self.assertFalse((host / A_VENDORED_FILE["target"]).exists(),
                         "the kit restored a file the host had taken over and removed")
        self.assertEqual(SAYS["restored"], states(done.stdout).get(A_VENDORED_FILE["target"]))

    # -- 4. the surface never lies ----------------------------------------------------------
    def test_224_a_taken_over_path_is_named_on_every_reading_even_when_nothing_moved(self):
        """`unchanged` is the ordinary cell and is not printed per path. For a path the kit no
        longer vouches for, silence would read as the kit still standing behind it."""
        host = self._ceded()
        for run in range(2):
            done = self.run_kit(KIT, host, "upgrade")
            self.assertEqual(0, done.returncode, done.stderr)
            self.assertEqual(SAYS["unchanged"], states(done.stdout).get(A_VENDORED_FILE["target"]),
                             f"run {run}: a taken-over path went unnamed")

    # -- 5. the declaration decides ----------------------------------------------------------
    def test_225_a_path_whose_steward_offers_no_transfer_cannot_be_ceded(self):
        """A seed is already the host's; there is nothing to take over and no door to sign."""
        self.assertIsNone(_BY_ID[_STEWARD_OF[A_SEEDED_FILE["mode"]]].get("transfers_to"),
                          "precondition: the seed's steward is declared to offer no transfer")
        host = self.installed()
        before = (host / ESTATE).read_bytes()
        refused = self.run_kit(KIT, host, "cede", "--path", A_SEEDED_FILE["target"],
                               "--approve", "the-owner")
        self.assertNotEqual(0, refused.returncode)
        self.assertIn(REFUSED, refused.stderr)
        self.assertIn(A_SEEDED_FILE["target"], refused.stderr)
        self.assertEqual(before, (host / ESTATE).read_bytes())

    def test_226_withdrawing_the_transfer_from_the_declaration_withdraws_the_door(self):
        """The interpreter privileges no steward: remove `transfers_to` and the same request is
        refused, with no line of code changed."""
        def withdraw(kit):
            self.edit_json(kit, STEWARDSHIP_SOURCE, lambda d: [
                s.pop("transfers_to", None) for s in d["stewards"]])
        closed = self.fixture_kit("no-transfer", withdraw)
        host = self.installed(closed)
        refused = self.run_kit(closed, host, "cede", "--path", A_VENDORED_FILE["target"],
                               "--approve", "the-owner")
        self.assertNotEqual(0, refused.returncode)
        self.assertIn(REFUSED, refused.stderr)

    def test_227_a_transfer_to_a_class_the_kit_does_not_declare_is_refused(self):
        """The four-class seam is a floor: every path holds exactly one DECLARED class, before a
        transfer and after it."""
        classes = {p["class"] for p in MANIFEST["planes"]}
        nowhere = "a-class-nothing-declares"
        self.assertNotIn(nowhere, classes)

        def misdeclare(kit):
            def patch(d):
                for s in d["stewards"]:
                    if s.get("transfers_to"):
                        s["transfers_to"]["class"] = nowhere
            self.edit_json(kit, STEWARDSHIP_SOURCE, patch)
        bad = self.fixture_kit("no-class", misdeclare)
        host = self.installed(bad)
        before = (host / ESTATE).read_bytes()
        refused = self.run_kit(bad, host, "cede", "--path", A_VENDORED_FILE["target"],
                               "--approve", "the-owner")
        self.assertNotEqual(0, refused.returncode)
        self.assertIn(REFUSED, refused.stderr)
        self.assertIn(nowhere, refused.stderr)
        self.assertEqual(before, (host / ESTATE).read_bytes())

    def test_228_a_record_claiming_a_transfer_no_declaration_offers_is_refused_not_read(self):
        """Hand-writing a signature onto a row is not a door. Where the steward offers no
        transfer, the record states an ownership nothing could have granted."""
        host = self.installed()
        target = host / ESTATE
        record = json.loads(target.read_text(encoding="utf-8"))
        for row in record["files"]:
            if row["path"] == A_SEEDED_FILE["target"]:
                row[estate.CEDED] = {"signed_by": "nobody", "signed_at": "never", "held": None}
        target.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
        refused = self.run_kit(KIT, host, "upgrade")
        self.assertNotEqual(0, refused.returncode, "a forged transfer was read as ownership")
        self.assertIn(A_SEEDED_FILE["target"], refused.stderr)

    # -- 6. whole or nothing ----------------------------------------------------------------
    def test_229_one_path_that_cannot_change_hands_stops_the_whole_request(self):
        host = self.installed()
        before = (host / ESTATE).read_bytes()
        asked = f"{A_VENDORED_FILE['target']},{A_SEEDED_FILE['target']}"
        refused = self.run_kit(KIT, host, "cede", "--path", asked, "--approve", "the-owner")
        self.assertNotEqual(0, refused.returncode)
        self.assertIn(REFUSED, refused.stderr)
        self.assertEqual(before, (host / ESTATE).read_bytes(),
                         "half a request was carried out")

    def test_230_a_path_already_taken_over_is_not_signed_for_twice(self):
        host = self._ceded()
        row, _ = _row(host, A_VENDORED_FILE["target"])
        again = self.run_kit(KIT, host, "cede", "--path", A_VENDORED_FILE["target"],
                             "--approve", "someone-else")
        self.assertNotEqual(0, again.returncode)
        self.assertIn(REFUSED, again.stderr)
        self.assertIn(row[estate.CEDED]["signed_by"], again.stderr,
                      "the refusal did not name who already signed")
        self.assertEqual(row, _row(host, A_VENDORED_FILE["target"])[0])


if __name__ == "__main__":
    unittest.main()
