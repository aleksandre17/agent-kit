"""Acceptance: a continuity capsule is written by compare-and-swap, so two writers never lose an update.

Ported invariants (the predecessor's capsule tests), on a host that takes the shared-tree bundle:

  1. a write over the revision on disk lands as the next revision and leaves one journal line;
  2. a write that read an OLDER revision is refused by its code, and the capsule is unchanged -- the
     lost update that two runtimes on one tree produced, made impossible;
  3. a capsule holding two things in progress, or not keeping its contract, is refused.

Every path and code is read from the bundle and the verb that own them.
"""

from __future__ import annotations

import json
import unittest

from harness import KIT, REPO, Fixtures

from test_pinned_kit import said
from verbs import capsule

STARTER = REPO / "starters" / "standard.json"
BUNDLE = REPO / "bundles" / "shared-tree"
SEAT = next(i["target"] for i in json.loads((BUNDLE / "capability.json").read_text(encoding="utf-8"))["installs"]
            if i.get("validates") == capsule.CONTRACT)


class Capsule(Fixtures, unittest.TestCase):

    def started(self):
        host = self.host()
        starter = json.loads(STARTER.read_text(encoding="utf-8"))
        starter["takes"] = [str((STARTER.parent / t).resolve()) for t in starter["takes"]] + [str(BUNDLE)]
        written = self._temp("starter-") / "starter.json"
        written.write_text(json.dumps(starter), encoding="utf-8")
        ran = self.run_kit(KIT, host, "start", "--path", str(written), "--approve", "acceptance-suite")
        self.assertEqual(0, ran.returncode, said(ran))
        return host

    def next_capsule(self, host, rev, **fields):
        value = json.loads((host / SEAT).read_text(encoding="utf-8"))
        value.update({capsule.REV: rev, "intent": "finish the fixture", "updated_by": "a runtime", **fields})
        path = self._temp("capsule-") / "next.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def test_530_a_write_over_the_revision_on_disk_lands_and_a_stale_one_is_refused(self):
        host = self.started()
        first = self.run_kit(KIT, host, "capsule", "--write", str(self.next_capsule(host, 1)), "--rev", "0")
        self.assertEqual(0, first.returncode, said(first))
        # A second runtime read revision 0 too, and writes over it: refused, nothing lost.
        stale = self.run_kit(KIT, host, "capsule", "--write", str(self.next_capsule(host, 1, intent="theirs")), "--rev", "0")
        self.assertIn(f"[{capsule.CapsuleRefused.code}]", said(stale))
        self.assertEqual("finish the fixture", json.loads((host / SEAT).read_text(encoding="utf-8"))["intent"])
        journal = list(host.glob(f"**/{capsule.SUBJECT}.journal.jsonl"))
        self.assertEqual(1, len(journal[0].read_text(encoding="utf-8").splitlines()))

    def test_531_two_things_in_progress_are_refused(self):
        host = self.started()
        ran = self.run_kit(KIT, host, "capsule", "--write", str(self.next_capsule(host, 1, wip=["a", "b"])), "--rev", "0")
        self.assertIn(f"[{capsule.CapsuleRefused.code}]", said(ran))


if __name__ == "__main__":
    unittest.main()
