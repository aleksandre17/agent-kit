"""Acceptance: a reading is replaced only through a door (ADR-021 amendment 2).

The reading is taken once, by `init`, and `reading-current` compares a fresh one against it. A host
whose tree moved on purpose is held to:

  1. a reading that still holds is not retaken -- nothing is written;
  2. the gate that fails names its remedy; `retake --plan` names every fact that moved and writes
     nothing; an unapproved retake is a door and writes nothing;
  3. an approved retake writes the fresh reading with who replaced which reading, and the gate
     passes again;
  4. a take from inside the host is recorded where every clone can read it -- relative to the host.

The moved fact is a nested file: what a `**/` glob declares is evidence wherever the repository
carries it, never only at the root. Every path, mode, detector and id is read from its declaration.
"""

from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path

from harness import Fixtures

import manifest as manifest_port
from errors import PendingApproval
from manifest import Manifest
from test_adapters import ADAPTERS, UNACTIVATED, adapted_kit, documents_of as _documents
from test_detectors import concrete
from test_pinned_kit import pinned_cli, said


def _nested(detector) -> bool:
    return any(e["kind"] == "glob_any" and e.get("pattern", "").startswith("**/") and not e.get("optional")
               for e in detector["evidence"])


#: The core reads no ecosystem (ADR-023 amendment 5): a detector that reads at ANY depth is brought by
#: a published adapter, so the kit these tests install is the real kit with the first such adapter
#: taken -- chosen by what its detector declares, never by a name.
KIT = adapted_kit(adapters=[next(a for a in ADAPTERS for d in _documents(a, "detector") if _nested(d))])
CORE = Manifest(KIT)
_INSTALLS = {i["mode"]: i for c in CORE.capabilities for i in c.installs}
READING = _INSTALLS["reading"]["target"]
STATEMENT = _INSTALLS[manifest_port.TAKEN_DECLARATION_MODE]["target"]
GATE = next(g["id"] for c in CORE.capabilities for g in c.gates if g["kind"] == "reading-current")


def _required(detector) -> list:
    return [e for e in detector["evidence"] if not e.get("optional")]


#: A detector that reads its evidence at ANY depth: its one required item is a `**/` glob. Chosen
#: from the declarations, never by a name -- the fact it emits is what a nested file moves.
NESTED = next(d for d in sorted(CORE.detectors, key=lambda d: d["id"])
              if len(_required(d)) == 1 and _required(d)[0].get("pattern", "").startswith("**/"))
FACT = next(k for k, v in NESTED["emits"].items() if v is True)
FILE = concrete(_required(NESTED)[0]["pattern"])


def _reading(host) -> dict:
    return json.loads((host / READING).read_text(encoding="utf-8"))


class Retake(Fixtures, unittest.TestCase):

    def test_404_a_reading_that_still_holds_is_not_retaken_and_nothing_is_written(self):
        host = self.installed(KIT)
        before = (host / READING).read_bytes()
        ran = pinned_cli(host, "retake", "--approve", "acceptance-suite")
        self.assertEqual(0, ran.returncode, said(ran))
        self.assertIn("holds", ran.stdout)
        self.assertEqual(before, (host / READING).read_bytes())

    def test_405_a_moved_host_names_the_door_and_only_an_approved_retake_replaces_its_reading(self):
        host = self.installed(KIT)
        recorded = _reading(host)
        self.assertNotIn(FACT, recorded["facts"])
        nested = host / "apps" / FILE
        nested.parent.mkdir(parents=True)
        nested.write_text("{}\n", encoding="utf-8")
        before = (host / READING).read_bytes()

        checked = pinned_cli(host, "check")
        self.assertIn(f"FAIL  {GATE}", checked.stdout, said(checked))
        self.assertIn("retake --approve", checked.stdout)

        planned = pinned_cli(host, "retake", "--plan")
        self.assertEqual(0, planned.returncode, said(planned))
        self.assertIn(f"+ {FACT} = True", planned.stdout)
        self.assertEqual(before, (host / READING).read_bytes(), "a plan wrote the reading")

        refused = pinned_cli(host, "retake")
        self.assertEqual(PendingApproval.exit_code, refused.returncode, said(refused))
        self.assertEqual(before, (host / READING).read_bytes(), "an unapproved retake wrote")

        approved = pinned_cli(host, "retake", "--approve", "acceptance-suite")
        self.assertEqual(0, approved.returncode, said(approved))
        fresh = _reading(host)
        self.assertIs(True, fresh["facts"][FACT])
        self.assertEqual("acceptance-suite", fresh["retaken"]["signed_by"])
        self.assertEqual(recorded["taken_at"], fresh["retaken"]["replaces"])
        self.assertIn(f"PASS  {GATE}", pinned_cli(host, "check").stdout)


class TakeSource(Fixtures, unittest.TestCase):

    def test_406_a_take_is_recorded_relative_to_the_host_inside_it_and_absolute_outside(self):
        adapter = UNACTIVATED[0]
        host = self.installed(KIT)
        inside = host / "vendor" / adapter.name
        shutil.copytree(adapter, inside)
        for given in (inside, adapter):
            took = pinned_cli(host, "take", "--path", str(given), "--approve", "acceptance-suite")
            self.assertEqual(0, took.returncode, said(took))
            row = json.loads((host / STATEMENT).read_text(encoding="utf-8"))["takes"][0]
            if given is inside:
                self.assertEqual(f"vendor/{adapter.name}", row["source"])
            else:
                self.assertTrue(Path(row["source"]).is_absolute(), row)
