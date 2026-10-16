"""Acceptance: the hooks a product runs -- posture, receipts, recovery points, packets, the push gate.

Held here, on a started host, through each hook as its product's command runs it (the host's pinned
kit, the product's event on stdin, read through the surface's declared hands):

  1. a destructive command gets a recovery point under the declared refs and is let through (advisory);
  2. a brief missing the declared packet fields is refused in one line naming them, a compliant one is
     silent, an oversized one is refused (blocking);
  3. a blocking hook that cannot decide -- a surface nobody declares -- FAILS CLOSED, and every
     invocation leaves one receipt;
  4. the push gate is served beside the commit gate.

Every key, label, ref and code is read from the declarations and the module that owns it.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest

from harness import KIT, REPO, Fixtures

import hooks
from context import Context
from test_adapters import ADAPTERS, documents_of, surfaces_of
from test_pinned_kit import said
from verbs import guard, spawn

STARTER = REPO / "starters" / "standard.json"
TAKEN = [(STARTER.parent / rel).resolve() for rel in json.loads(STARTER.read_text(encoding="utf-8"))["takes"]]
SURFACE = next(s for a in ADAPTERS if a.resolve() in TAKEN for s in surfaces_of(a)
               if s.get("hands", {}).get("commands") and s["hands"].get("prompts"))
COMMAND = next(r for d in TAKEN for doc in documents_of(d, guard.PATTERNS[0]["validates"]) for r in doc["commands"])
PACKET = next(p for d in TAKEN for doc in documents_of(d, spawn.PACKETS[0]["validates"]) for p in doc["packets"])


def _event(keys, value):
    """An event a product would write, holding `value` at the first declared dotted key."""
    event: dict = {}
    here = event
    parts = keys[0].split(".")
    for part in parts[:-1]:
        here = here.setdefault(part, {})
    here[parts[-1]] = value
    return json.dumps(event)


class Hooks(Fixtures, unittest.TestCase):

    def started(self):
        host = self.host()
        ran = self.run_kit(KIT, host, "start", "--path", str(STARTER), "--approve", "acceptance-suite")
        self.assertEqual(0, ran.returncode, said(ran))
        return host

    def hook(self, host, verb, surface, stdin):
        pinned = host / Context(kit_root=KIT, host_root=host).manifest.plane("vendor") / "interpreters" / "cli.py"
        return subprocess.run([sys.executable, "-I", "-B", str(pinned), verb, "--root", str(host), "--surface", surface],
                              input=stdin, capture_output=True, text=True, cwd=host)

    def test_480_a_destructive_command_gets_a_recovery_point_and_runs(self):
        host = self.started()
        git = ["git", "-C", str(host), "-c", "user.email=s@invalid", "-c", "user.name=suite"]
        (host / "kept.txt").write_text("one\n", encoding="utf-8")
        subprocess.run([*git, "add", "kept.txt"], capture_output=True)
        subprocess.run([*git, "commit", "-q", "--no-verify", "-m", "kept"], capture_output=True)
        (host / "kept.txt").write_text("two\n", encoding="utf-8")
        ran = self.hook(host, "guard", SURFACE["id"], _event(SURFACE["hands"]["commands"], "git reset --hard"))
        self.assertEqual(0, ran.returncode, said(ran))
        refs = subprocess.run([*git, "for-each-ref", guard.REFS], capture_output=True, text=True).stdout
        self.assertIn(guard.REFS, refs)

    def test_481_a_brief_is_a_packet_under_its_ceiling_or_it_is_not_sent(self):
        host = self.started()
        refusal = SURFACE["hands"]["refusal"]["exit"]
        keys = SURFACE["hands"]["prompts"]
        lacking = self.hook(host, "spawn", SURFACE["id"], _event(keys, "do the thing"))
        self.assertEqual(refusal, lacking.returncode)
        self.assertTrue(all(f["label"] in lacking.stderr for f in PACKET["fields"]))
        whole = " ".join(f"{f['label']}: x." for f in PACKET["fields"])
        self.assertEqual(0, self.hook(host, "spawn", SURFACE["id"], _event(keys, whole)).returncode)
        wall = whole + " y" * (PACKET["ceiling_tokens"] * PACKET["bytes_per_token"])
        self.assertEqual(refusal, self.hook(host, "spawn", SURFACE["id"], _event(keys, wall)).returncode)

    def test_482_a_blocking_hook_that_cannot_decide_fails_closed_and_every_run_leaves_a_receipt(self):
        host = self.started()
        ran = self.hook(host, "spawn", "a-surface-nobody-declares", "{}")
        self.assertEqual(hooks.CLOSED, ran.returncode, said(ran))
        ctx = Context(kit_root=KIT, host_root=host)
        self.assertEqual(1, len(hooks.receipts(ctx, "a-surface-nobody-declares")))
        self.hook(host, "guard", SURFACE["id"], "{}")
        self.assertEqual(1, len(hooks.receipts(ctx, SURFACE["id"])))

    def test_484_the_doctor_proves_every_served_hook_fires_and_names_a_dead_one(self):
        host = self.started()
        ran = self.run_kit(KIT, host, "doctor")
        self.assertEqual(0, ran.returncode, said(ran))
        self.assertNotIn("DEAD", ran.stdout)
        self.assertIn("LIVE", ran.stdout)
        # A judge the pinned kit cannot run is a dead chain on a surface whose refusal is not the
        # entry point's own usage error -- named, and the doctor fails.
        pinned = host / Context(kit_root=KIT, host_root=host).manifest.plane("vendor") / "interpreters" / "verbs" / "judge.py"
        pinned.unlink()
        broken = self.run_kit(KIT, host, "doctor")
        self.assertEqual(1, broken.returncode, said(broken))
        self.assertIn("DEAD", broken.stdout)

    def test_483_the_push_gate_is_served_beside_the_commit_gate(self):
        host = self.started()
        commit = next(r for a in ADAPTERS if a.resolve() in TAKEN for s in surfaces_of(a)
                      for r in s["renders"] if r["target"].endswith("pre-commit"))
        self.assertTrue((host / commit["target"].replace("pre-commit", "pre-push")).is_file())


if __name__ == "__main__":
    unittest.main()
