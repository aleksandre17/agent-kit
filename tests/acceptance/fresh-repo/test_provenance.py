"""Acceptance: PROVENANCE of what a host takes that the kit did not issue (ADR-008).

A doctrine bundle is the first case: bytes a third party published, placed in a kit by a human.
The decision separates two propositions and every test here holds one of them to its word:

  * INTEGRITY -- the host pins a content digest at FIRST CONTACT, at a door, with a name and a
    moment. Bytes that later differ at the same version are refused and never re-pinned; a version
    OLDER than the pin is refused whoever signed it; a NEWER one is a door again.
  * AUTHENTICITY -- delegated to a verifier the kit declares as data. Where it did not run, the pin
    says so in a declared word and the surface prints NOT ESTABLISHED. It is never printed as
    verified, and a signature the verifier REJECTS is a refusal, not an absence.

Every word, path and code is read from the declaration that owns it: the provenance document, the
governance capability that ships it, the refusal class that carries the code.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

from harness import KIT, Fixtures
from test_doctrine import BUNDLE, bundle_kit

import provenance

GOVERNANCE = next(
    json.loads((KIT / entry["declaration"]).read_text(encoding="utf-8"))
    for entry in json.loads((KIT / "MANIFEST.json").read_text(encoding="utf-8"))["capabilities"]
    if provenance.DOCUMENT in {d["id"] for d in json.loads(
        (KIT / entry["declaration"]).read_text(encoding="utf-8")).get("documents", [])})
DOCUMENT = json.loads((KIT / next(d["source"] for d in GOVERNANCE["documents"]
                                  if d["id"] == provenance.DOCUMENT)).read_text(encoding="utf-8"))
ESTATE = next(item["target"] for item in GOVERNANCE["installs"] if item["mode"] == "estate")
GATE = next(gate["id"] for gate in GOVERNANCE["gates"] if gate["kind"] == "provenance-pinned")
REFUSED = provenance.ProvenanceRefused.code
VERIFIER = DOCUMENT["verifiers"][0]
STANDING = {row["state"]: row["standing"] for row in DOCUMENT["authenticity"]}
DISPOSITION = {row["state"]: row["disposition"] for row in DOCUMENT["states"]}
H1 = re.compile(r"h1:[A-Za-z0-9+/]{43}=")
SIGNATURE = f"capabilities/{BUNDLE['id']}/capability.sig"
SIGNER = "publisher@example.test"


def versioned(version: str):
    return lambda value: value.update({"version": version})


def claimed(value: dict) -> None:
    value["provenance"] = {"verifier": VERIFIER["id"], "signer": SIGNER, "signature": SIGNATURE}


def pins(host: Path) -> list:
    return json.loads((host / ESTATE).read_text(encoding="utf-8")).get("taken")


def said(result) -> str:
    return result.stdout + result.stderr


class Provenance(Fixtures, unittest.TestCase):

    def test_202_first_contact_with_a_bundle_is_pinned_at_the_door_with_a_name_a_moment_and_a_digest(self):
        """Trust on first use, made a recorded act. The draft names the stranger before anybody
        accepts it; the approval pins exactly one digest under the approver's name, dated to the
        reading. A pin with no name is a pin nobody can be held to."""
        kit, host = bundle_kit(), self.host()
        drafted = self.run_kit(kit, host, "init")
        self.assertEqual(3, drafted.returncode)
        self.assertIn("FIRST-CONTACT", drafted.stdout, "the draft did not name what it would take")
        self.assertEqual(0, self.run_kit(kit, host, "init", "--approve", "the-owner").returncode)
        [pin] = pins(host)
        self.assertEqual((BUNDLE["id"], BUNDLE["version"], "the-owner"),
                         (pin["capability"], pin["version"], pin["pinned_by"]))
        self.assertRegex(pin["digest"], H1)
        self.assertTrue(pin["pinned_at"], "a pin without a moment cannot be placed against anything")

    def test_203_an_unsigned_bundle_is_pinned_and_its_authenticity_is_declared_not_established(self):
        """The surface never lies. An unsigned bundle is not `trusted` and is not silently green:
        the pin carries the declared word and every check prints the standing in capitals."""
        kit = bundle_kit()
        host = self.installed(kit)
        self.assertEqual(provenance.UNSIGNED, pins(host)[0]["authenticity"]["state"])
        read = self.run_kit(kit, host, "check")
        self.assertEqual(0, read.returncode)
        self.assertIn(f"authenticity {STANDING[provenance.UNSIGNED].upper()}", read.stdout)
        self.assertNotIn(f"authenticity {STANDING[provenance.VERIFIED].upper()}", read.stdout,
                         "a verification that never ran was printed as established")

    def test_204_bytes_that_drift_under_a_pinned_version_are_refused_and_never_re_pinned(self):
        """go.sum's one rule. The same version with different bytes is the attack a pin exists to
        catch: check fails on it, init refuses before any write, and an approval does NOT open it
        -- a door that could re-pin a drift would make every pin a formality."""
        kit = bundle_kit()
        host = self.installed(kit)
        before = pins(host)
        payload = next(kit / item["source"] for item in BUNDLE["installs"] if item.get("source"))
        payload.write_text(payload.read_text(encoding="utf-8") + "\nA line nobody released.\n",
                           encoding="utf-8", newline="\n")
        read = self.run_kit(kit, host, "check")
        self.assertEqual(1, read.returncode, "check was green over bytes that are not the pin")
        self.assertIn(f"FAIL  {GATE}", read.stdout)
        self.assertIn(provenance.DRIFTED, read.stdout)
        forced = self.run_kit(kit, host, "init", "--approve", "the-owner")
        self.assertNotEqual(0, forced.returncode)
        self.assertIn(REFUSED, said(forced), "a drift was not refused under its own code")
        self.assertEqual(before, pins(host), "a drifted capability was re-pinned")

    def test_205_a_bundle_older_than_the_version_pinned_is_refused_whoever_approves_it(self):
        """The rollback defence (TUF's). A publisher's older, once-legitimate release is exactly
        what an attacker who cannot forge a new one replays; the pin is the high-water mark and no
        door lowers it."""
        host = self.installed(bundle_kit(versioned("1.1.0")))
        older = bundle_kit()
        forced = self.run_kit(older, host, "init", "--approve", "the-owner")
        self.assertNotEqual(0, forced.returncode)
        self.assertIn(REFUSED, said(forced))
        self.assertIn(provenance.ROLLED_BACK, said(forced))
        self.assertEqual("1.1.0", pins(host)[0]["version"])

    def test_206_a_newer_bundle_is_a_door_and_walking_it_records_what_the_pin_supersedes(self):
        """A new version is new bytes from a publisher and is met as first contact is: named, and
        stopped until a person takes it -- and then the pin says what it replaced."""
        host = self.installed(bundle_kit())
        first = pins(host)[0]
        newer = bundle_kit(versioned("1.1.0"))
        waiting = self.run_kit(newer, host, "init")
        self.assertEqual(3, waiting.returncode, "a new version was taken on nobody's word")
        self.assertIn(provenance.ADVANCED.upper(), waiting.stdout)
        self.assertEqual(0, self.run_kit(newer, host, "init", "--approve", "the-owner").returncode)
        [pin] = pins(host)
        self.assertEqual(("1.1.0", {"version": first["version"], "digest": first["digest"]}),
                         (pin["version"], pin["supersedes"]))

    def test_207_capabilities_this_kit_issued_are_never_taken_and_the_zero_is_printed(self):
        """What the kit issued is pinned by the kit's own lock; the estate's list of what was
        taken from elsewhere is then a DECLARED zero, and the surface says none in words."""
        host = self.installed()
        self.assertEqual([], pins(host))
        read = self.run_kit(KIT, host, "check")
        self.assertIn("TAKEN  none", read.stdout)

    def test_208_a_record_that_predates_pins_holds_no_pin_and_check_says_so_rather_than_passing(self):
        """Ambiguity resolves to nothing. An estate written before pins existed carries no `taken`;
        that is read as NO pin, the taken bundle is a stranger again, and check fails on it."""
        kit = bundle_kit()
        host = self.installed(kit)
        record = json.loads((host / ESTATE).read_text(encoding="utf-8"))
        del record["taken"]
        (host / ESTATE).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        read = self.run_kit(kit, host, "check")
        self.assertEqual(1, read.returncode)
        self.assertIn(provenance.FIRST_CONTACT, read.stdout)
        self.assertEqual(DISPOSITION[provenance.FIRST_CONTACT], "door")

    def test_209_a_claimed_signature_with_no_trust_root_on_the_host_is_a_named_absence(self):
        """A claim establishes nothing. A bundle that says it was signed, on a host that has said
        whom it trusts to nobody, is pinned with the word for that -- never verified."""
        kit = bundle_kit(claimed)
        (kit / SIGNATURE).write_text("not a signature anybody checked\n", encoding="utf-8", newline="\n")
        host = self.installed(kit)
        self.assertEqual(provenance.NO_TRUST_ROOT, pins(host)[0]["authenticity"]["state"])


def _ssh_keygen():
    """The delegated verifier, MEASURED on this machine: present, and able to sign and verify.
    Anything less is a declared skip with its reason, never a quiet pass."""
    program = shutil.which(VERIFIER["argv"][0])
    if program is None:
        return None, f"{VERIFIER['argv'][0]} is not on PATH"
    probe = subprocess.run([program, "-Y", "verify"], capture_output=True, text=True)
    if "unknown option" in (probe.stderr or "").lower() or "illegal option" in (probe.stderr or "").lower():
        return None, f"{program} predates `-Y verify` ({probe.stderr.strip()[:120]})"
    return program, ""


PROGRAM, WHY_NOT = _ssh_keygen()


@unittest.skipIf(PROGRAM is None, f"no usable delegated verifier on this machine: {WHY_NOT}")
class DelegatedVerifier(Fixtures, unittest.TestCase):

    def _key(self, where: Path, name: str) -> Path:
        key = where / name
        made = subprocess.run([PROGRAM, "-q", "-t", "ed25519", "-N", "", "-C", name, "-f", str(key)],
                              capture_output=True, text=True)
        if made.returncode:
            self.skipTest(f"{PROGRAM} could not make a key here: {made.stderr.strip()[:200]}")
        return key

    def _signed(self, key: Path, kit: Path, digest: str) -> None:
        statement = (DOCUMENT["statement"].replace("{capability}", BUNDLE["id"])
                     .replace("{version}", BUNDLE["version"]).replace("{digest}", digest))
        message = key.parent / "statement"
        message.write_bytes(statement.encode("utf-8"))
        signed = subprocess.run([PROGRAM, "-Y", "sign", "-f", str(key), "-n", VERIFIER["namespace"],
                                 str(message)], capture_output=True, text=True)
        if signed.returncode:
            self.skipTest(f"{PROGRAM} could not sign here: {signed.stderr.strip()[:200]}")
        shutil.copyfile(message.with_name("statement.sig"), kit / SIGNATURE)

    def _drafted(self):
        kit, host = bundle_kit(claimed), self.host()
        (kit / SIGNATURE).write_text("placeholder\n", encoding="utf-8", newline="\n")
        drafted = self.run_kit(kit, host, "init")
        return kit, host, H1.search(drafted.stdout).group(0)

    def _trust(self, host: Path, key: Path) -> None:
        root = host / VERIFIER["trust_root"]
        root.parent.mkdir(parents=True, exist_ok=True)
        public = key.with_name(key.name + ".pub").read_text(encoding="utf-8").split()
        root.write_text(f"{SIGNER} {public[0]} {public[1]}\n", encoding="utf-8")

    def test_210_a_signature_the_real_verifier_accepts_against_the_hosts_trust_root_is_recorded_verified(self):
        """Asymmetric verification, delegated to the tool git itself uses, against a key the HOST
        chose to trust. The pin records the verifier, the signer and the digest of the trust root
        it was checked against, and the moment."""
        kit, host, digest = self._drafted()
        keys = self._temp("kit-keys-")
        key = self._key(keys, "publisher")
        self._signed(key, kit, digest)
        self._trust(host, key)
        approved = self.run_kit(kit, host, "init", "--approve", "the-owner")
        self.assertEqual(0, approved.returncode, said(approved))
        found = pins(host)[0]["authenticity"]
        self.assertEqual((provenance.VERIFIED, SIGNER), (found["state"], found["signer"]))
        self.assertIn(f"authenticity {STANDING[provenance.VERIFIED].upper()}",
                      self.run_kit(kit, host, "check").stdout)

    def test_211_a_signature_by_a_key_the_host_does_not_trust_is_refused_and_nothing_is_pinned(self):
        """Evidence against is not an absence. A signature the verifier rejects stops the door:
        nothing is pinned, and the refusal carries its code."""
        kit, host, digest = self._drafted()
        keys = self._temp("kit-keys-")
        self._signed(self._key(keys, "impostor"), kit, digest)
        self._trust(host, self._key(keys, "publisher"))
        refused = self.run_kit(kit, host, "init", "--approve", "the-owner")
        self.assertNotEqual(0, refused.returncode)
        self.assertIn(REFUSED, said(refused))
        self.assertIn(provenance.REFUTED, said(refused))
        self.assertFalse((host / ESTATE).exists() and pins(host), "a refuted bundle was pinned")


if __name__ == "__main__":
    unittest.main()
