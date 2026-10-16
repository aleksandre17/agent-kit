"""Acceptance: a policy published beside the kit holds every host that takes it (ADR-023 amendment 3).

A rule true of every repository -- no private key, no access token -- is written once, as edit gates
in a published capability, and taken by each host instead of copied into it. Each policy is held to:

  1. it declares only documents that keep an enforced contract, and every gate and message rule is
     calibrated: it refuses what it says it refuses and admits the lookalike it says is legitimate;
  2. a host started by a starter that takes it can COMMIT the install itself -- the policy's own
     calibration text lands in the take plane, which is the publisher's bytes and judged by digest --
     and is refused, at the commit, an edit that introduces what a gate forbids.

Every path, id and contract is read from the policy, the starter or the module that owns it.
"""

from __future__ import annotations

import json
import subprocess
import unittest

from harness import KIT, REPO, Fixtures

import edits
import manifest as manifest_port
import messages
from manifest import Manifest
from test_pinned_kit import said
from verbs import guard, message, spawn

CORE = Manifest(KIT)
DECLARATION = next(i for c in CORE.capabilities for i in c.installs
                   if i["mode"] == manifest_port.TAKEN_MODE)["declaration"]
EDIT_GATE = "edit-gate"
#: The contracts something ENFORCES: the edit judge's, and each contract a hook verb reads.
MESSAGE_RULES = message.SOURCES[0]["validates"]
ENFORCED = {EDIT_GATE, guard.PATTERNS[0]["validates"], spawn.PACKETS[0]["validates"], MESSAGE_RULES}
POLICIES = sorted(p.parent for p in (REPO / "policies").glob(f"*/{DECLARATION}"))
STARTERS = sorted((REPO / "starters").glob("*.json"))


def _gates(policy, contract=EDIT_GATE, rows=edits.RULES) -> list:
    value = json.loads((policy / DECLARATION).read_text(encoding="utf-8"))
    seat = f"capabilities/{value['id']}/"
    return [gate for document in value.get("documents", []) if document["validates"] == contract
            for gate in json.loads((policy / document["source"][len(seat):]).read_text(encoding="utf-8"))
            [rows]]


def _git(host, *argv):
    return subprocess.run(["git", "-C", str(host), "-c", "user.name=suite", "-c", "user.email=suite@invalid",
                           *argv], capture_output=True, text=True)


class Policies(Fixtures, unittest.TestCase):

    def test_413_every_policy_keeps_the_edit_gate_contract_and_every_gate_is_calibrated(self):
        self.assertTrue(POLICIES, "ADR-023 amendment 3 publishes at least one policy")
        for policy in POLICIES:
            value = json.loads((policy / DECLARATION).read_text(encoding="utf-8"))
            # A policy is ENFORCED: it ships an edit-gate document or declares a gate `check` runs,
            # and may tell every runtime its rule (a briefing section) -- every document keeps a
            # contract the kit declares.
            self.assertTrue(any(d["validates"] in ENFORCED for d in value["documents"]) or value["gates"])
            for document in value["documents"]:
                self.assertTrue(CORE.schema(document["validates"]))
            for gate in _gates(policy):
                with self.subTest(policy=policy.name, gate=gate["id"]):
                    self.assertEqual([], edits.calibration(gate))
            for rule in _gates(policy, MESSAGE_RULES, messages.RULES):
                with self.subTest(policy=policy.name, rule=rule["id"]):
                    self.assertEqual([], messages.calibration(rule))

    def test_414_a_started_host_commits_its_install_and_refuses_what_a_policy_forbids(self):
        starter = next(s for s in STARTERS
                       if any((s.parent / rel).resolve() in {p.resolve() for p in POLICIES}
                              for rel in json.loads(s.read_text(encoding="utf-8"))["takes"]))
        taken = [p for p in POLICIES if any((starter.parent / rel).resolve() == p.resolve()
                                            for rel in json.loads(starter.read_text(encoding="utf-8"))["takes"])]
        host = self.host()
        ran = self.run_kit(KIT, host, "start", "--path", str(starter), "--approve", "acceptance-suite")
        self.assertEqual(0, ran.returncode, said(ran))
        _git(host, "add", "-A")
        installed = _git(host, "commit", "-m", "the install")
        self.assertEqual(0, installed.returncode, installed.stdout + installed.stderr)
        for policy in taken:
            for gate in _gates(policy):
                with self.subTest(gate=gate["id"]):
                    # At the gate's own specimen path, under a directory of the host's own -- a gate
                    # may reach only the files its `paths` names.
                    target = host / "src" / gate["proves"]["path"]
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(gate["proves"]["text"] + "\n", encoding="utf-8")
                    _git(host, "add", "-A")
                    refused = _git(host, "commit", "-m", "a secret")
                    self.assertNotEqual(0, refused.returncode, refused.stdout + refused.stderr)
                    self.assertIn(gate["id"], refused.stdout + refused.stderr)
                    _git(host, "reset", "--quiet")
                    target.unlink()


if __name__ == "__main__":
    unittest.main()
