"""Acceptance: the hooks a product runs -- posture, receipts, recovery points, packets, the push gate.

Held here, on a started host, through each hook as its product's command runs it (the host's pinned
kit, the product's event on stdin, read through the surface's declared hands):

  1. a destructive command gets a recovery point under the declared refs and is let through (advisory);
  2. a brief missing the declared packet fields is refused in one line naming them, a compliant one is
     silent, an oversized one is refused (blocking);
  3. a blocking hook that cannot decide -- a surface nobody declares -- FAILS CLOSED, and every
     invocation leaves one receipt;
  4. the push gate is served beside the commit gate;
  5. a session starts with one context line, in the form the surface declares;
  6. the stop gate is served only where the host takes a continuity capsule, and there refuses a stop
     over a capsule that breaks its contract;
  7. a product's own sub-agent leaves a ledger row -- requested vs verified model, tokens -- read
     through the surface's declared `hands.ledger`, a mismatch named;
  8. a host that takes a message policy records a change only with a message of the declared form --
     through git itself -- and a rule that does not bite its own specimen is failed by `check` and
     never applied; a host that takes none is held to nothing.

Every key, label, ref and code is read from the declarations and the module that owns it.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import unittest

from harness import KIT, REPO, Fixtures

import hooks
from context import Context
from test_adapters import ADAPTERS, documents_of, surfaces_of
from test_pinned_kit import said
import messages
from verbs import capsule, guard, ledger, message, session, spawn, stop

STARTER = REPO / "starters" / "standard.json"
TAKEN = [(STARTER.parent / rel).resolve() for rel in json.loads(STARTER.read_text(encoding="utf-8"))["takes"]]
SURFACE = next(s for a in ADAPTERS if a.resolve() in TAKEN for s in surfaces_of(a)
               if s.get("hands", {}).get("commands") and s["hands"].get("prompts"))
COMMAND = next(r for d in TAKEN for doc in documents_of(d, guard.PATTERNS[0]["validates"]) for r in doc["commands"])
CAPSULE = REPO / "bundles" / "shared-tree"
SEAT = next(i["target"] for i in json.loads((CAPSULE / "capability.json").read_text(encoding="utf-8"))["installs"]
            if i.get("validates") == capsule.CONTRACT)
SETTINGS = next(r["target"] for r in SURFACE["renders"] if r["view"] == "enforcement")
MESSAGES = REPO / "policies" / "conventional-commits"
RULE = next(r for d in [MESSAGES] for doc in documents_of(d, message.SOURCES[0]["validates"]) for r in doc[messages.RULES])
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

    def started_with_capsule(self):
        return self.started_taking(CAPSULE)

    def started_taking(self, *extra, green=True):
        host = self.host()
        starter = json.loads(STARTER.read_text(encoding="utf-8"))
        starter["takes"] = [str((STARTER.parent / t).resolve()) for t in starter["takes"]] + [str(e) for e in extra]
        written = self._temp("starter-") / "starter.json"
        written.write_text(json.dumps(starter), encoding="utf-8")
        ran = self.run_kit(KIT, host, "start", "--path", str(written), "--approve", "acceptance-suite")
        if not green:
            return host, ran
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

    def test_485_a_session_starts_with_one_context_line_in_the_declared_form(self):
        host = self.started()
        served = (host / SETTINGS).read_text(encoding="utf-8")
        json.loads(served)
        for module in (session, ledger):
            self.assertIn(f" {module.__name__.rpartition('.')[2]} --root ", served)
        ran = self.hook(host, session.__name__.rpartition(".")[2], SURFACE["id"], "{}")
        self.assertEqual(0, ran.returncode, said(ran))
        shape = SURFACE["hands"]["context"]["stdout"]
        head, _, tail = shape.partition("{context}")
        out = ran.stdout.strip()
        self.assertTrue(out.startswith(head) and out.endswith(tail), out)
        self.assertIn(Context(kit_root=KIT, host_root=host).manifest.version, out)
        self.assertEqual(1, out.count("\n") + 1)

    def test_486_the_stop_gate_is_served_with_the_capsule_and_refuses_a_broken_one(self):
        name = stop.__name__.rpartition(".")[2]
        plain = self.started()
        self.assertNotIn(f" {name} --root ", (plain / SETTINGS).read_text(encoding="utf-8"))
        self.assertEqual(0, self.hook(plain, name, SURFACE["id"], "{}").returncode)
        host = self.started_with_capsule()
        self.assertIn(f" {name} --root ", json.dumps(json.loads((host / SETTINGS).read_text(encoding="utf-8"))))
        kept = self.hook(host, name, SURFACE["id"], "{}")
        self.assertEqual(0, kept.returncode, said(kept))
        value = json.loads((host / SEAT).read_text(encoding="utf-8"))
        (host / SEAT).write_text(json.dumps({**value, "wip": ["one", "two"]}), encoding="utf-8")
        broken = self.hook(host, name, SURFACE["id"], "{}")
        self.assertEqual(SURFACE["hands"]["refusal"]["exit"], broken.returncode, said(broken))
        self.assertIn(capsule.CapsuleRefused.code, broken.stderr)
        (host / SEAT).unlink()
        self.assertEqual(SURFACE["hands"]["refusal"]["exit"], self.hook(host, name, SURFACE["id"], "{}").returncode)

    def test_487_a_products_own_sub_agent_leaves_a_ledger_row_and_a_mismatch_is_named(self):
        host = self.started()
        spec = SURFACE["hands"]["ledger"]
        fields = spec["entries"]["fields"]

        def line(key, asked, ran, spent):
            row = dict(spec["entries"].get("where") or {})
            for name, value in ((spec["entries"]["key"], key), (fields[ledger.REQUESTED], asked),
                                (fields[ledger.RESPONDED], ran), (fields["gen_ai.usage.output_tokens"], spent)):
                here, parts = row, name.split(".")
                for part in parts[:-1]:
                    here = here.setdefault(part, {})
                here[parts[-1]] = value
            return json.dumps(row)

        transcript = self._temp("transcript-") / "agent.jsonl"
        transcript.write_text("\n".join([line("t1", "model-a", "model-a", 3), line("t1", "model-a", "model-a", 7),
                                         line("t2", "model-a", "model-b", 5)]) + "\n", encoding="utf-8")
        event = json.loads(_event(spec["transcript"], str(transcript)))
        event.update(json.loads(_event(spec["agent"], "agent-1")))
        name = ledger.__name__.rpartition(".")[2]
        ran = self.hook(host, name, SURFACE["id"], json.dumps(event))
        self.assertEqual(0, ran.returncode, said(ran))
        self.assertIn("model-b", ran.stderr)
        rows = [json.loads(r) for p in host.glob(f"**/{ledger.LEDGER}/{SURFACE['id']}.jsonl")
                for r in p.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(1, len(rows))
        self.assertEqual((2, 12, True), (rows[0]["turns"], rows[0]["gen_ai.usage.output_tokens"], rows[0]["mismatch"]))
        summary = self.run_kit(KIT, host, name)
        self.assertEqual(0, summary.returncode, said(summary))
        self.assertIn("1 run(s), 1 on a model other than the one requested", summary.stdout)

    def commit(self, host, name, text):
        env = {**os.environ, "GIT_AUTHOR_NAME": "suite", "GIT_AUTHOR_EMAIL": "s@invalid",
               "GIT_COMMITTER_NAME": "suite", "GIT_COMMITTER_EMAIL": "s@invalid"}
        (host / name).write_text(name + "\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(host), "add", name], capture_output=True, env=env)
        # A message as an editor leaves it: git's own comment lines below the text the author wrote.
        draft = self._temp("message-") / "MSG"
        draft.write_text(text + "\n\n# Please enter the commit message for your changes.\n", encoding="utf-8")
        return subprocess.run(["git", "-C", str(host), "commit", "-q", "--cleanup=strip", "-F", str(draft)],
                              capture_output=True, text=True, env=env)

    def test_488_a_message_policy_holds_every_commit_through_git_and_an_uncalibrated_rule_is_never_applied(self):
        plain = self.started()
        self.assertEqual(0, self.commit(plain, "one.txt", RULE["proves"]).returncode, "a host that took no policy was held")
        host = self.started_taking(MESSAGES)
        refused = self.commit(host, "two.txt", RULE["proves"])
        self.assertNotEqual(0, refused.returncode, said(refused))
        self.assertIn(f"[{message.MessageRefused.code}] {RULE['id']}", refused.stderr)
        admitted = self.commit(host, "three.txt", RULE["admits"])
        self.assertEqual(0, admitted.returncode, said(admitted))
        # A policy nobody ships, whose rule admits the very message it claims to refuse.
        fixture = self._temp("policy-") / "a-fixture-message-policy"
        shutil.copytree(MESSAGES, fixture)
        declaration = json.loads((fixture / "capability.json").read_text(encoding="utf-8"))
        seat = f"capabilities/{declaration['id']}/"
        document = declaration["documents"][0]
        rel = document["source"][len(seat):]
        declaration["id"] = fixture.name
        document["source"] = f"capabilities/{fixture.name}/{rel}"
        (fixture / "capability.json").write_text(json.dumps(declaration), encoding="utf-8")
        value = json.loads((fixture / rel).read_text(encoding="utf-8"))
        value[messages.RULES] = [{**RULE, "id": "a-rule-that-does-not-bite", "proves": RULE["admits"]}]
        (fixture / rel).write_text(json.dumps(value), encoding="utf-8")
        # `start` ends with `check`: everything is served and activated, and the check is red on the rule.
        loose, started = self.started_taking(fixture, green=False)
        self.assertNotEqual(0, started.returncode)
        self.assertIn("a-rule-that-does-not-bite: UNCALIBRATED", said(started))
        unjudged = self.commit(loose, "four.txt", RULE["proves"])
        self.assertEqual(0, unjudged.returncode, said(unjudged))
        self.assertIn("a-rule-that-does-not-bite", unjudged.stderr)


if __name__ == "__main__":
    unittest.main()
