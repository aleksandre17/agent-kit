"""Acceptance: a capability is believed once a record of something that happened proves it (ADR-022 S4).

A runtime descriptor CLAIMS what its runtime can do, and until now every page said so honestly:
nothing in this kit could prove one. The prior system measured why that matters -- a runtime declared
a capability while its receipt directory held zero proofs of it, and was already being offered work
on it. Held here:

  1. a claim stays CLAIMED until an event the kit provides is observed through that runtime;
  2. a write the judge REFUSES through a runtime's surface is that event for the capability whose
     `observed_on` names it -- the runtime's page then reads PROVEN, with the record beside it;
  3. a write the judge admits proves nothing, and leaves nothing;
  4. the capability is never spelled by the interpreter: it is found by the event it is observed on.

Every name is read from the declarations that own it.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from harness import KIT, Fixtures
from manifest import Manifest

import attestation

from test_adapters import A_CLASS, DESCRIPTORS, ENABLING_FIELD, adapted_kit, surface_documents
from test_enforcement import GATES_FILE, HOST_GATE, VENDOR, _event

CORE = Manifest(KIT)
CLASSES = json.loads((KIT / "runtimes/classes.json").read_text(encoding="utf-8"))
OBSERVED = next(c["id"] for c in CLASSES["capabilities"] if c.get("observed_on") == attestation.REFUSED_WRITE)
OBSERVATIONS = next(i["target"] for c in CORE.capabilities for i in c.installs
                    if i.get("validates") == attestation.OBSERVATIONS)
PAGES = next(i["target"] for c in CORE.capabilities for i in c.installs
             if i.get("class") == "projection" and "each" in i and i["target"].endswith("runtimes/"))


class Attestation(Fixtures, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.kit = adapted_kit()
        _rel, surfaces = surface_documents(cls.kit)
        cls.surface = next(s for s in surfaces if "hands" in s and not s["hands"].get("carries"))

    def claiming_host(self) -> Path:
        host = self.installed(self.kit)
        path = host / DESCRIPTORS / f"{self.surface['id']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"schema_version": 1, "id": self.surface["id"], "class": A_CLASS["id"],
                                    ENABLING_FIELD: self.surface["id"],
                                    "claims": [{"capability": OBSERVED, "says": "its edits pass through the judge"}]})
                        + "\n", encoding="utf-8")
        (host / GATES_FILE).write_text(json.dumps({"schema_version": 1, "gates": [HOST_GATE]}) + "\n",
                                       encoding="utf-8")
        self.assertEqual(0, self.run_kit(self.kit, host, "render").returncode)
        return host

    def judge(self, host: Path, text: str):
        pinned = host / VENDOR / "interpreters" / "cli.py"
        event = _event(self.surface["hands"], HOST_GATE["proves"]["path"], text)
        return subprocess.run([sys.executable, str(pinned), "judge", "--root", str(host),
                               "--surface", self.surface["id"]],
                              input=json.dumps(event), capture_output=True, text=True)

    def page(self, host: Path) -> str:
        self.assertEqual(0, self.run_kit(self.kit, host, "render").returncode)
        return (host / PAGES / f"{self.surface['id']}.md").read_text(encoding="utf-8")

    def proven_section(self, page: str) -> str:
        return page.split("### Proven", 1)[1].split("### Claimed", 1)[0]

    def test_380_a_claim_stays_claimed_until_a_refusal_through_that_runtime_proves_it(self):
        host = self.claiming_host()
        self.assertNotIn(OBSERVED, self.proven_section(self.page(host)))
        refused = self.judge(host, HOST_GATE["proves"]["text"])
        self.assertEqual(self.surface["hands"]["refusal"]["exit"], refused.returncode, refused.stderr)
        records = list((host / OBSERVATIONS).glob("*.json"))
        self.assertEqual(1, len(records), "the refusal left no record, or more than one")
        record = json.loads(records[0].read_text(encoding="utf-8"))
        self.assertEqual((self.surface["id"], OBSERVED, attestation.REFUSED_WRITE),
                         (record["runtime"], record["capability"], record["event"]))
        self.assertIn(OBSERVED, self.proven_section(self.page(host)))

    def test_381_an_admitted_write_proves_nothing_and_leaves_nothing(self):
        host = self.claiming_host()
        admitted = self.judge(host, HOST_GATE["admits"]["text"])
        self.assertEqual(0, admitted.returncode, admitted.stderr)
        self.assertEqual([], list((host / OBSERVATIONS).glob("*.json")) if (host / OBSERVATIONS).exists() else [])
        self.assertNotIn(OBSERVED, self.proven_section(self.page(host)))

    def test_382_the_capability_an_event_observes_is_found_by_the_event_and_never_spelled(self):
        """The general rule -- no instance vocabulary inside the machinery -- is the boundary suite's;
        this holds the one promise this slice made: the capability is reached through `observed_on`."""
        for module in ("attestation.py", "verbs/judge.py"):
            text = (KIT / "interpreters" / module).read_text(encoding="utf-8")
            self.assertNotIn(OBSERVED, text, f"{module} spells the capability it observes")


if __name__ == "__main__":
    unittest.main()
