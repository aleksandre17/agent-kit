"""Acceptance: two principals on one tree, arbitrated by a claim that BITES (ADR-022 decision 7, S5).

Held here, with two runtimes served through two surfaces of one host:

  1. a write under ANOTHER principal's standing claim is refused by the one judge, naming who holds it,
     since when and why; the claimant's own write passes; once released, the other may write;
  2. a claim is broken only BY NAME, and the break is recorded on it;
  3. with a window declared, a peer's admitted write refuses mine to the same path -- unless my claim
     on it postdates the peer's write, which supersedes that history; with the seeded window of 0,
     a recent write refuses nothing;
  4. a claim with no reason is refused, and nothing is kept.

Every place and code is read from the declaration or module that owns it.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from harness import KIT, Fixtures
from manifest import Manifest

import claims

from test_adapters import A_CLASS, DESCRIPTORS, ENABLING_FIELD, adapted_kit, surface_documents
from test_enforcement import VENDOR, _event

CORE = Manifest(KIT)
ARBITRATION = next(i["target"] for c in CORE.capabilities for i in c.installs
                   if i.get("validates") == claims.ARBITRATION)
PATH = "src/shared.ts"


class Claims(Fixtures, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.kit = adapted_kit()
        _rel, surfaces = surface_documents(cls.kit)
        cls.one, cls.two = [s for s in surfaces if "hands" in s][:2]

    def two_principals(self, window: int = 0) -> Path:
        host = self.installed(self.kit)
        for surface in (self.one, self.two):
            path = host / DESCRIPTORS / f"{surface['id']}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"schema_version": 1, "id": surface["id"], "class": A_CLASS["id"],
                                        ENABLING_FIELD: surface["id"]}) + "\n", encoding="utf-8")
        (host / ARBITRATION).write_text(json.dumps({"schema_version": 1, "window_minutes": window}) + "\n",
                                        encoding="utf-8", newline="\n")
        self.assertEqual(0, self.run_kit(self.kit, host, "render").returncode)
        return host

    def writes(self, host: Path, surface: dict, text: str = "export const x = 1"):
        pinned = host / VENDOR / "interpreters" / "cli.py"
        event = _event(surface["hands"], PATH, text)
        return subprocess.run([sys.executable, str(pinned), "judge", "--root", str(host), "--surface", surface["id"]],
                              input=event if isinstance(event, str) else json.dumps(event),
                              capture_output=True, text=True)

    def claim(self, host: Path, *flags):
        return self.run_kit(self.kit, host, "claim", *flags)

    def refused(self, ran, surface) -> bool:
        return ran.returncode == surface["hands"]["refusal"]["exit"]

    def test_390_a_write_under_another_principals_claim_is_refused_until_it_is_released(self):
        host = self.two_principals()
        taken = self.claim(host, "--by", self.one["id"], "--path", PATH, "--reason", "refactoring the module")
        self.assertEqual(0, taken.returncode, taken.stderr)
        blocked = self.writes(host, self.two)
        self.assertTrue(self.refused(blocked, self.two), blocked.stdout + blocked.stderr)
        self.assertIn(self.one["id"], blocked.stderr)
        self.assertIn("refactoring the module", blocked.stderr)
        self.assertEqual(0, self.writes(host, self.one).returncode, "the claimant's own write was refused")
        self.assertEqual(0, self.claim(host, "--by", self.one["id"], "--relinquish").returncode)
        self.assertEqual(0, self.writes(host, self.two).returncode, "a released claim still blocked")

    def test_391_a_claim_is_broken_only_by_name_and_the_break_is_recorded(self):
        host = self.two_principals()
        self.claim(host, "--by", self.one["id"], "--path", PATH, "--reason", "left standing")
        broken = self.claim(host, "--by", self.one["id"], "--relinquish", "--break-lock", "the-owner")
        self.assertEqual(0, broken.returncode, broken.stderr)
        self.assertIn("BROKEN by the-owner", broken.stdout)
        place = next(i["target"] for c in CORE.capabilities for i in c.installs if i.get("validates") == claims.CLAIM)
        record = json.loads((host / place / f"{self.one['id']}.json").read_text(encoding="utf-8"))
        self.assertEqual("the-owner", record["broken_by"])

    def test_392_a_peer_write_inside_the_window_refuses_mine_unless_my_later_claim_supersedes_it(self):
        host = self.two_principals(window=60)
        self.assertEqual(0, self.writes(host, self.one).returncode)
        contested = self.writes(host, self.two)
        self.assertTrue(self.refused(contested, self.two), contested.stdout + contested.stderr)
        self.assertIn(self.one["id"], contested.stderr)
        self.claim(host, "--by", self.two["id"], "--path", PATH, "--reason", "read what the peer wrote; taking it")
        self.assertEqual(0, self.writes(host, self.two).returncode, "a later claim did not supersede older history")

    def test_393_with_the_seeded_window_a_recent_write_refuses_nothing(self):
        host = self.two_principals(window=0)
        self.assertEqual(0, self.writes(host, self.one).returncode)
        self.assertEqual(0, self.writes(host, self.two).returncode)

    def test_394_a_claim_without_a_reason_is_refused_and_nothing_is_kept(self):
        host = self.two_principals()
        said = self.claim(host, "--by", self.one["id"], "--path", PATH)
        self.assertNotEqual(0, said.returncode)
        self.assertIn(f"[{claims.ClaimRefused.code}]", said.stderr)
        self.assertIn("no claim stands", self.claim(host).stdout)


if __name__ == "__main__":
    unittest.main()
