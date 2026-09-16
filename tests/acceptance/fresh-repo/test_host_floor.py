"""Acceptance: the host tree meets the drawn floor (ADR-015 amendment 1, link L3a).

The drawing places the pinned copy AT `.agents/kit/` and the lock the host was given at
`.agents/project/kit.lock.json`. Before this link a host carried the copy one level down, beside a
second copy of every doctrine page and of the host drawing itself, and ten drawn host paths were
declared `pending: L3`. These tests hold the destination, each against a real host:

  1. a fresh approved host meets its floor, the declaration carries no `pending: L3` row, and an
     empty declared collection is present as the empty directory it honestly is;
  2. an install that would write inside the pinned tree -- the old vendored page, exactly -- is
     refused as a shadowed path, by code, before a byte moves;
  3. a runtime adapter contributes its own floor row, which bites only where it is enabled and is
     printed with the link that will give it content;
  4. a host carrying the OLD shape (the real 0.1.5 release, read at its revision) upgrades to the
     flat shape as one planned act that `--plan` shows, and runs from the flat copy afterwards.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest

from harness import KIT, LOCK, Fixtures, planned  # noqa: I001 -- sets the interpreter's path

import pin  # noqa: E402
import resolver  # noqa: E402
from manifest import Manifest  # noqa: E402

PINNED, SEAT = pin.seats(Manifest(KIT))
GOVERNANCE = next(c for c in Manifest(KIT).capabilities
                  if any(i["mode"] == pin.MODE for i in c.installs))
LAYOUT = next(doc for doc in GOVERNANCE.documents.values() if doc.get("side") == "host")
#: One path, one owner: a writer inside the pinned tree is the composition's own shadowing
#: refusal, never a second rule for the same fact.
CODE = resolver.CompositionError.code

#: The last release carrying the OLD shape (`.agents/kit/pinned/` + vendored pages): 0.1.5 at the
#: commit that closed link L2. A revision, never a working tree -- the same form a host is given.
OLD_SHAPE_REVISION = "ad73054"


def said(result) -> str:
    return result.stdout + result.stderr


def pinned_cli(host, verb, *flags):
    result = subprocess.run(
        [sys.executable, str(host / PINNED / "interpreters" / "cli.py"), verb, "--root", str(host),
         *flags], capture_output=True, text=True, encoding="utf-8", cwd=str(host))
    print(f"\n$ <pinned> {verb} {' '.join(flags)}\n[exit {result.returncode}]\n{said(result)}")
    return result


class HostFloor(Fixtures, unittest.TestCase):

    def test_281_a_fresh_host_meets_its_floor_and_no_row_waits_on_l3(self):
        self.assertEqual([], [e["path"] for e in LAYOUT["entries"] if e.get("pending") == "L3"],
                         "a drawn host path still waits on link L3")
        host = self.installed()
        ran = pinned_cli(host, "check")
        self.assertEqual(0, ran.returncode, said(ran))
        self.assertIn("PASS  FF-HOST-FLOOR", ran.stdout)
        # Declared collections this host has put nothing into: present, and empty -- never absent
        # and never filled with a placeholder.
        for entry in LAYOUT["entries"]:
            if entry.get("capability") in ("roles", "runtimes") and entry["path"].startswith(".agents/generated/"):
                self.assertTrue((host / entry["path"]).is_dir(), entry["path"])
                self.assertEqual([], list((host / entry["path"]).iterdir()), entry["path"])

    def test_282_a_writer_inside_the_pinned_tree_is_refused_in_the_plan(self):
        page = GOVERNANCE.raw["doctrine"]

        def vendor_the_page_again(kit):
            self.edit_json(kit, Manifest(KIT).declaration_of(GOVERNANCE.id), lambda doc: doc[
                "installs"].append({"mode": "vendor", "class": "vendor",
                                    "target": f"{PINNED}doctrine/{page.rsplit('/', 1)[1]}",
                                    "source": page}))

        kit = self.fixture_kit("second-writer", patch=vendor_the_page_again)
        host = self.host()
        refused = self.run_kit(kit, host, "init")
        self.assertNotEqual(0, refused.returncode)
        self.assertIn(f"[{CODE}]", refused.stderr)
        self.assertIn(f"{PINNED}doctrine/", refused.stderr)
        self.assertFalse((host / ".agents").exists(), "a refused composition writes nothing")

    def test_283_an_adapter_brings_its_own_floor_row_and_it_is_named_with_its_link(self):
        from test_adapters import adapted_kit  # noqa: E402 -- the one way a host takes adapters

        kit = adapted_kit()
        host = self.installed(kit)
        ran = pinned_cli(host, "check")
        self.assertIn("PASS  FF-HOST-FLOOR", ran.stdout)
        issued = {c.id for c in Manifest(KIT).capabilities}
        brought = {row["path"]: (row, c.id) for c in Manifest(kit).capabilities
                   if c.id not in issued for row in c.raw.get("floor", [])}
        self.assertTrue(brought, "no taken adapter declared a floor row")
        for path, (row, owner) in brought.items():
            self.assertIn(f"PENDING  {path}  (link {row['pending']}, {owner})", ran.stdout)
        in_kit = {e["path"] for e in LAYOUT["entries"]} | {
            row["path"] for c in Manifest(KIT).capabilities for row in c.raw.get("floor", [])}
        self.assertEqual(set(), in_kit & set(brought),
                         "kit/ itself names a runtime product's directory")

    def test_284_an_old_shape_host_upgrades_to_the_flat_shape_as_one_planned_act(self):
        known = subprocess.run(["git", "-C", str(KIT.parent), "cat-file", "-e",
                                f"{OLD_SHAPE_REVISION}^{{commit}}"], capture_output=True)
        if known.returncode != 0:
            self.skipTest(f"revision {OLD_SHAPE_REVISION} is not in this clone's history")
        # The OLD release is run by its OWN interpreter, as a host given 0.1.5 ran it: its
        # declarations read by today's code would be a shape no release ever had.
        old, scratch = pin.fetched(f"git+{KIT.parent.as_posix()}@{OLD_SHAPE_REVISION}"
                                   f"#subdirectory=kit")
        self._trash.append(scratch)
        host = self.host()
        for flags in ((), ("--approve", "acceptance-suite")):
            result = subprocess.run([sys.executable, str(old / "interpreters" / "cli.py"), "init",
                                     "--root", str(host), "--kit", str(old), *flags],
                                    capture_output=True, text=True, encoding="utf-8")
            print(f"\n$ <0.1.5> init {' '.join(flags)}\n[exit {result.returncode}]\n"
                  f"{said(result)}")
        old_tree = host / PINNED / "pinned"
        self.assertTrue(old_tree.is_dir(), "the 0.1.5 release did not leave the old shape")
        old_pages = [p for p in (host / PINNED).iterdir() if p.name != "pinned"]
        self.assertTrue(old_pages, "the 0.1.5 release vendored nothing beside its pinned copy")

        plan = self.run_kit(KIT, host, "upgrade", "--plan")
        self.assertEqual(0, plan.returncode, said(plan))
        foreseen = dict((path, disposition) for disposition, path in planned(plan.stdout))
        self.assertEqual("replaced", foreseen.get(PINNED), "the plan does not show the move")
        self.assertEqual("created", foreseen.get(SEAT), "the plan does not seat the lock")
        self.assertIn(f"inside {PINNED}", plan.stdout,
                      "the old paths are not named as absorbed by the flat tree")

        done = self.run_kit(KIT, host, "upgrade")
        self.assertEqual(0, done.returncode, said(done))
        self.assertFalse(old_tree.exists(), "the old pinned copy survived the move")
        for page in old_pages:
            self.assertFalse(page.exists(), f"{page.name}: a second copy survived the move")
        self.assertEqual((KIT / LOCK).read_bytes(), (host / SEAT).read_bytes())
        on_disk = {p.relative_to(host / PINNED).as_posix()
                   for p in (host / PINNED).rglob("*") if p.is_file()}
        self.assertEqual({e["path"] for e in json.loads((KIT / LOCK).read_text(encoding="utf-8"))["files"]},
                         on_disk)
        ran = pinned_cli(host, "check")
        self.assertEqual(0, ran.returncode, said(ran))
        self.assertIn("PASS  FF-KIT-PINNED", ran.stdout)
        self.assertIn("PASS  FF-HOST-FLOOR", ran.stdout)


if __name__ == "__main__":
    unittest.main()
