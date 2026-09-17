"""Acceptance: taken capabilities live BESIDE the pinned kit, never inside it (ADR-018, slice C1b).

A fresh host pinned from the release takes both published runtime adapters and is then held to:

  1. the take is a DOOR: unapproved, it names what it would take and writes nothing;
  2. approved, each adapter lands verbatim in its take plane with a row in the take declaration --
     and the pinned kit stays byte-equal to its lock (`FF-KIT-PINNED` passes);
  3. the manifest COMPOSES release + takes: the host enables them, pins their provenance, renders
     each product's served settings, and `check` reports 0 failed, the composition stated as
     `release <v> + taken: <ids>`;
  4. `taken-intact` judges each take against its row: a changed byte and a directory nobody
     declared taken each fail by name; a vanished plane is refused at every load;
  5. a take never shadows the release: an issued id is refused at the take AND at every load.

Every path, mode, field and code is read from the declaration or module that owns it.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from harness import KIT, LOCK, Fixtures

import ephemeral
import hostlock
import manifest as manifest_port
import provenance
from errors import PendingApproval
from manifest import Manifest
import declared
from test_adapters import A_CLASS, ADAPTERS, DESCRIPTORS, ENABLING_FIELD, LIST, SELECTOR
from test_pinned_kit import PINNED, SEAT, pinned_cli, said
from verbs.take import TakeError

CORE = Manifest(KIT)
_INSTALLS = {i["mode"]: i for c in CORE.capabilities for i in c.installs}
PLANE = _INSTALLS[manifest_port.TAKEN_MODE]
STATEMENT = _INSTALLS[manifest_port.TAKEN_DECLARATION_MODE]
ANSWERS = _INSTALLS["declaration"]["target"]
GATE = next(g["id"] for c in CORE.capabilities for g in c.gates if g["kind"] == "taken-intact")
HOLD = (f"{[p['root'].rstrip('/') for p in CORE.planes if p['class'] == ephemeral.OBSERVED][0]}"
        f"/{hostlock.NAME}")
PIN_GATE = next(g["id"] for c in CORE.capabilities for g in c.gates if g["kind"] == "pinned-kit-intact")


def _id(adapter: Path) -> str:
    return json.loads((adapter / PLANE["declaration"]).read_text(encoding="utf-8"))["id"]


class Taken(Fixtures, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ids = sorted(_id(a) for a in ADAPTERS)
        cls.paths = ",".join(str(a) for a in ADAPTERS)

    def taken_host(self, kit: Path = KIT) -> Path:
        host = self.installed(kit)
        took = pinned_cli(host, "take", "--path", self.paths, "--approve", "acceptance-suite")
        self.assertEqual(0, took.returncode, said(took))
        return host

    def composed_host(self, kit: Path = KIT) -> Path:
        """Taken, enabled by the owner's declaration, pinned at the provenance door, served."""
        host = self.taken_host(kit)
        answers = json.loads((host / ANSWERS).read_text(encoding="utf-8"))
        answers["capabilities"] = sorted(set(answers["capabilities"]) | set(self.ids))
        (host / ANSWERS).write_text(json.dumps(answers, indent=2) + "\n", encoding="utf-8", newline="\n")
        _rel, surfaces = surface_documents_of(host)
        for surface in surfaces:
            path = host / DESCRIPTORS / f"{surface['id']}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"schema_version": 1, "id": surface["id"], "class": A_CLASS["id"],
                                        ENABLING_FIELD: surface["id"]}) + "\n", encoding="utf-8", newline="\n")
        pinned = pinned_cli(host, "init", "--approve", "acceptance-suite")
        self.assertEqual(0, pinned.returncode, said(pinned))
        self.assertEqual(0, pinned_cli(host, "render").returncode)
        return host

    # == 1. the door ============================================================================
    def test_300_an_unapproved_take_names_what_it_would_take_and_writes_nothing(self):
        host = self.installed(KIT)
        before = (host / STATEMENT["target"]).read_bytes()
        ran = pinned_cli(host, "take", "--path", self.paths)
        self.assertEqual(PendingApproval.exit_code, ran.returncode, said(ran))
        self.assertIn(f"[{PendingApproval.code}]", ran.stderr)
        for identity in self.ids:
            self.assertIn(identity, ran.stdout)
            self.assertFalse((host / PLANE["target"] / identity).exists())
        self.assertEqual(before, (host / STATEMENT["target"]).read_bytes())

    # == 2. beside, never inside ================================================================
    def test_301_a_take_lands_in_its_plane_with_a_row_and_the_pinned_kit_stays_its_lock(self):
        host = self.taken_host()
        rows = {r["id"]: r for r in json.loads((host / STATEMENT["target"]).read_text(encoding="utf-8"))["takes"]}
        self.assertEqual(self.ids, sorted(rows))
        for adapter in ADAPTERS:
            identity = _id(adapter)
            with self.subTest(take=identity):
                for source in (p for p in adapter.rglob("*") if p.is_file()):
                    copy = host / PLANE["target"] / identity / source.relative_to(adapter)
                    self.assertEqual(source.read_bytes(), copy.read_bytes())
                self.assertFalse((host / PINNED / "capabilities" / identity).exists())
                self.assertEqual("acceptance-suite", rows[identity]["taken_by"])
                self.assertNotIn("digest", rows[identity], "a reading written on a declaration has two homes")
        self.assertEqual((KIT / LOCK).read_bytes(), (host / SEAT).read_bytes())
        ran = pinned_cli(host, "check")
        self.assertIn(f"PASS  {PIN_GATE}", ran.stdout)
        self.assertIn(f"PASS  {GATE}", ran.stdout)

    # == 3. the composition, walked to a served runtime =========================================
    def test_302_a_host_that_took_both_adapters_serves_them_and_checks_green_as_release_plus_taken(self):
        host = self.composed_host()
        _rel, surfaces = surface_documents_of(host)
        served = [r["target"] for s in surfaces for r in s["renders"] if r["view"] == "enforcement"]
        self.assertEqual(len(self.ids), len(served), "each taken adapter serves its enforcement setting")
        for target in served:
            self.assertTrue((host / target).is_file(), target)
            json.loads((host / target).read_text(encoding="utf-8"))
        ran = pinned_cli(host, "check")
        self.assertEqual(0, ran.returncode, said(ran))
        self.assertIn("check: 0 gate(s) failed", ran.stdout)
        self.assertIn(f"release {CORE.version} + taken: {', '.join(self.ids)}", ran.stdout)
        self.assertIn(f"PASS  {PIN_GATE}", ran.stdout)
        self.assertIn(f"PASS  {GATE}", ran.stdout)
        self.assertIn("PASS  FF-PROVENANCE-PINNED", ran.stdout)
        self.assertEqual((KIT / LOCK).read_bytes(), (host / SEAT).read_bytes())

    # == 4. each take judged against its row ====================================================
    def test_303_a_changed_take_and_an_undeclared_directory_fail_the_gate_and_a_vanished_plane_fails_every_load(self):
        host = self.composed_host()
        plane = host / PLANE["target"]
        first, second = self.ids
        changed = next(p for p in (plane / first).rglob("*") if p.is_file())
        changed.write_bytes(changed.read_bytes() + b"\n")
        shutil.copytree(ADAPTERS[0], plane / "nobody-took-this")
        ran = pinned_cli(host, "check")
        self.assertIn(f"FAIL  {GATE}", ran.stdout)
        self.assertIn(f"{PLANE['target']}{first}/: measures", ran.stdout)
        self.assertIn("its pin holds h1:", ran.stdout)
        self.assertIn(f"{PLANE['target']}nobody-took-this/: present in the take plane", ran.stdout)
        self.assertNotEqual(0, ran.returncode)
        # A row whose plane is gone cannot even be COMPOSED: every load refuses it by name, before
        # any verb could speak with a manifest that silently lacks a capability the host declared.
        shutil.rmtree(plane / second)
        gone = pinned_cli(host, "check")
        self.assertIn(f"[{manifest_port.ManifestError.code}]", gone.stderr)
        self.assertIn(f"{second}/{PLANE['declaration']}", gone.stderr)

    def test_303b_the_digest_is_read_from_the_pin_and_never_from_a_row(self):
        host = self.composed_host()
        statement = json.loads((host / STATEMENT["target"]).read_text(encoding="utf-8"))
        # A pre-amendment row carrying a WRONG digest is not read: the pin is the one home.
        statement["takes"][0]["digest"] = "h1:AAAA"
        (host / STATEMENT["target"]).write_text(json.dumps(statement) + "\n", encoding="utf-8", newline="\n")
        ran = pinned_cli(host, "check")
        self.assertIn(f"PASS  {GATE}", ran.stdout, said(ran))
        # Retaking sheds a carried digest from every row.
        took = pinned_cli(host, "take", "--path", self.paths, "--approve", "acceptance-suite")
        self.assertEqual(0, took.returncode, said(took))
        rows = json.loads((host / STATEMENT["target"]).read_text(encoding="utf-8"))["takes"]
        self.assertFalse([r for r in rows if "digest" in r])

    # == 4b. the pin is written when the bytes arrive (amendment 2) =============================
    def pins(self, host: Path) -> dict:
        estate = json.loads((host / _INSTALLS["estate"]["target"]).read_text(encoding="utf-8"))
        return {p["capability"]: p for p in estate.get("taken", [])}

    def test_305_an_approved_take_pins_at_arrival_trust_on_first_use_and_init_attests_it(self):
        host = self.taken_host()
        pins = self.pins(host)
        self.assertEqual(self.ids, sorted(pins))
        for identity in self.ids:
            self.assertEqual({"basis": "trust-on-first-use"}, pins[identity]["trust"])
            self.assertEqual(provenance.NOT_YET_READ, pins[identity]["authenticity"]["state"])
        green = pinned_cli(host, "check")
        self.assertIn(f"PASS  {GATE}", green.stdout, said(green))
        self.assertIn("trust-on-first-use", green.stdout)
        attested = self.pins(self.composed_host())
        for identity in self.ids:
            self.assertEqual("attested", attested[identity]["trust"]["basis"])
            self.assertEqual("acceptance-suite", attested[identity]["trust"]["attested_by"])

    def test_305b_a_trust_basis_the_declaration_does_not_name_is_refused(self):
        host = self.taken_host()
        path = host / _INSTALLS["estate"]["target"]
        estate = json.loads(path.read_text(encoding="utf-8"))
        estate["taken"][0]["trust"] = {"basis": "vouched-for"}
        path.write_text(json.dumps(estate, indent=2) + "\n", encoding="utf-8", newline="\n")
        ran = pinned_cli(host, "check")
        self.assertNotIn(f"PASS  {GATE}", ran.stdout, said(ran))
        self.assertIn("vouched-for", ran.stdout + ran.stderr)

    def test_306_bytes_changed_between_take_and_init_are_refused_by_init_and_fail_check(self):
        host = self.taken_host()
        answers = json.loads((host / ANSWERS).read_text(encoding="utf-8"))
        answers["capabilities"] = sorted(set(answers["capabilities"]) | set(self.ids))
        (host / ANSWERS).write_text(json.dumps(answers, indent=2) + "\n", encoding="utf-8", newline="\n")
        changed = next(p for p in (host / PLANE["target"] / self.ids[0]).rglob("*") if p.is_file())
        changed.write_bytes(changed.read_bytes() + b"\n")
        before = self.pins(host)
        init = pinned_cli(host, "init", "--approve", "acceptance-suite")
        self.assertNotEqual(0, init.returncode, said(init))
        self.assertIn("drifted", init.stdout + init.stderr)
        self.assertEqual(before, self.pins(host), "a refused attestation re-pinned the drift")
        ran = pinned_cli(host, "check")
        self.assertIn(f"FAIL  {GATE}", ran.stdout, said(ran))
        self.assertIn("its pin holds h1:", ran.stdout)

    def test_307_a_take_with_no_pin_fails_the_gate(self):
        host = self.taken_host()
        at = host / _INSTALLS["estate"]["target"]
        estate = json.loads(at.read_text(encoding="utf-8"))
        estate["taken"] = []
        at.write_text(json.dumps(estate, indent=2) + "\n", encoding="utf-8", newline="\n")
        ran = pinned_cli(host, "check")
        self.assertIn(f"FAIL  {GATE}", ran.stdout, said(ran))
        self.assertIn("no provenance pin holds it", ran.stdout)
        self.assertNotIn("NOT YET PINNED", ran.stdout)

    def test_308_a_take_holds_the_host_as_its_one_writer(self):
        host = self.taken_host()
        hold = json.loads((host / HOLD).read_text(encoding="utf-8"))
        self.assertEqual("take", hold["verb"], "take wrote the host without holding it")
        self.assertFalse(hostlock.standing(hold), "take walked away still holding the host")
        # A second writer meeting a standing hold is refused at the door, and writes nothing.
        hold.pop(hostlock.RELEASED_AT, None)
        (host / HOLD).write_text(json.dumps(hold) + "\n", encoding="utf-8", newline="\n")
        before = self.pins(host)
        again = pinned_cli(host, "take", "--path", self.paths, "--approve", "acceptance-suite")
        self.assertEqual(3, again.returncode, said(again))
        self.assertEqual(before, self.pins(host))

    # == 5. a take never shadows the release ====================================================
    def test_304_an_id_the_release_issued_is_refused_at_the_take_and_at_every_load(self):
        host = self.installed(KIT)
        issued = CORE.capabilities[0].id
        impostor = Path(tempfile.mkdtemp(prefix="kit-impostor-")).resolve()
        self.addCleanup(shutil.rmtree, impostor, True)
        shutil.copytree(ADAPTERS[0], impostor / issued)
        declaration = impostor / issued / PLANE["declaration"]
        raw = json.loads(declaration.read_text(encoding="utf-8"))
        declaration.write_text(json.dumps(raw | {"id": issued}) + "\n", encoding="utf-8", newline="\n")
        refused = pinned_cli(host, "take", "--path", str(impostor / issued), "--approve", "suite")
        self.assertIn(f"[{manifest_port.TakeShadows.code}]", refused.stderr)
        self.assertFalse((host / PLANE["target"] / issued).exists())

        statement = json.loads((host / STATEMENT["target"]).read_text(encoding="utf-8"))
        statement["takes"] = [{"id": issued, "source": "planted", "digest": "h1:AAAA",
                               "taken_by": "nobody", "at": "2026-09-17T00:00:00+00:00"}]
        (host / STATEMENT["target"]).write_text(json.dumps(statement) + "\n", encoding="utf-8", newline="\n")
        loaded = pinned_cli(host, "check")
        self.assertIn(f"[{manifest_port.TakeShadows.code}]", loaded.stderr)
        self.assertNotEqual(TakeError.code, manifest_port.TakeShadows.code)


def surface_documents_of(host: Path) -> tuple:
    """The surfaces a HOST composes -- read through the composed manifest, exactly as it speaks."""
    composed = manifest_port.composed(host / PINNED, host)
    names = declared.named(composed.capabilities, SELECTOR)
    surfaces = [row for c in composed.capabilities for name in names if name in c.documents
                for row in c.documents[name][LIST]]
    return None, surfaces


if __name__ == "__main__":
    unittest.main()
