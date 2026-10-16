"""Acceptance: a product's persistent memory points, never copies (ADR-024).

The memory policy reads each served product's memory home -- declared on its surface, never in the
kit -- and refuses a note holding a secret or copying a line the repository holds. Held here, on a
started host whose home directory is a fixture:

  1. a note that copies a repository line, and one holding a secret a host gate refuses, are refused;
     a note that only points is admitted;
  2. a home that does not exist is NOT MEASURED, and passes.

Every path and rule is read from the surface, the policy and the module that owns them.
"""

from __future__ import annotations

import json
import os
import unittest
from unittest import mock

from harness import KIT, REPO, Fixtures

import memory as memory_gate
from context import Context
from test_adapters import ADAPTERS, documents_of, surfaces_of
from test_pinned_kit import said

STARTER = REPO / "starters" / "standard.json"
TAKEN = [(STARTER.parent / rel).resolve() for rel in json.loads(STARTER.read_text(encoding="utf-8"))["takes"]]
SURFACE = next(s for a in ADAPTERS if a.resolve() in TAKEN for s in surfaces_of(a) if s.get("memory"))
POLICY = next(p for p in TAKEN if any(g["kind"] == memory_gate.KIND
                                      for g in json.loads((p / "capability.json").read_text(encoding="utf-8"))["gates"]))
PARAMS = next(g["params"] for g in json.loads((POLICY / "capability.json").read_text(encoding="utf-8"))["gates"]
              if g["kind"] == memory_gate.KIND)
SECRET = next(g["proves"]["text"] for d in TAKEN for doc in documents_of(d, "edit-gate") for g in doc["gates"]
              if g["paths"] == ".*")


class Memory(Fixtures, unittest.TestCase):

    def test_450_a_copying_or_secret_note_is_refused_and_a_pointer_admitted(self):
        host = self.host()
        ran = self.run_kit(KIT, host, "start", "--path", str(STARTER), "--approve", "acceptance-suite")
        self.assertEqual(0, ran.returncode, said(ran))
        fact = "A fixture fact this repository holds in exactly one file, at full length, for the test."
        (host / "docs").mkdir(exist_ok=True)
        (host / "docs" / "fact.md").write_text(fact + "\n", encoding="utf-8")
        fake_home = self._temp("memory-home-")
        with mock.patch.dict(os.environ, {"HOME": str(fake_home), "USERPROFILE": str(fake_home)}):
            ctx = Context(kit_root=KIT, host_root=host)
            home = memory_gate.home_of(ctx, SURFACE["memory"])
            self.assertEqual([], memory_gate.KINDS[memory_gate.KIND](ctx, PARAMS))  # absent: NOT MEASURED
            home.mkdir(parents=True)
            (home / "pointer.md").write_text("The fixture fact: see docs/fact.md.\n", encoding="utf-8")
            self.assertEqual([], memory_gate.KINDS[memory_gate.KIND](ctx, PARAMS))
            (home / "copy.md").write_text(fact + "\n", encoding="utf-8")
            (home / "secret.md").write_text(SECRET + "\n", encoding="utf-8")
            refused = memory_gate.KINDS[memory_gate.KIND](ctx, PARAMS)
        self.assertTrue(any("copy.md" in r and "docs/fact.md" in r for r in refused), refused)
        self.assertTrue(any("secret.md" in r for r in refused), refused)
        self.assertFalse(any("pointer.md" in r for r in refused), refused)


if __name__ == "__main__":
    unittest.main()
