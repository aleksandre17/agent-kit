"""Acceptance: the ENFORCEMENT LINE -- served runtime settings -> a hook vendored in the pinned kit
-> the HOST-DECLARED edit gates (ADR-017 link C, slice C1a).

  1. every taken adapter that declares a `hands` block is served a setting whose hook runs the
     `judge` verb from the host's PINNED kit, through that adapter's own surface;
  2. a violating edit handed over in each product's own event shape is refused with the product's
     declared refusal code, naming the host's gate; a clean one passes; an event naming no path is
     refused as unjudged;
  3. `check` fails an uncalibrated host gate;
  4. the hook carries no policy and no product: the kit ships zero edit gates, and the judge's
     interpreter files contain no surface id, no product event key and no gate id.

Product names and event keys arrive only from the adapters' own declarations.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from harness import KIT, Fixtures
from manifest import Manifest

import activated
import activation
import judge as judge_verb

from test_adapters import A_CLASS, DESCRIPTORS, ENABLING_FIELD, RECORD, adapted_kit, surface_documents

CORE = Manifest(KIT)
ENFORCEMENT = next(c for c in CORE.capabilities if any(g["kind"] == "edit-gates-calibrated" for g in c.gates))
GATES_FILE = next(i["target"] for i in ENFORCEMENT.installs if i.get("validates") == "edit-gate")
GATE_ID = next(g["id"] for g in ENFORCEMENT.gates)
VENDOR = next(p["root"] for p in CORE.planes if p["class"] == "vendor")
HOST_GATE = {
    "id": "no-privileged-dimension",
    "paths": r"^src/",
    "forbids": r"ctx\.year",
    "because": "a privileged dimension.",
    "instead": "ctx.dims['time'].",
    "proves": {"path": "src/a.ts", "text": "const y = ctx.year"},
    "admits": {"path": "src/a.ts", "text": "const y = ctx.dims['time']"},
}


def _event(hands: dict, path: str, text: str) -> dict:
    """An event in the product's OWN shape, built from its declared keys -- first key of each."""
    def put(event, dotted, value):
        parts = dotted.split(".")
        for part in parts[:-1]:
            event = event.setdefault(part, {})
        event[parts[-1]] = value
    if hands.get("carries") == judge_verb.CARRIES_PATCH:  # the event IS a patch, in the hand's own two patterns
        return f"+++ b/{path}" + chr(10) + f"+{text}" + chr(10) if path else f"+{text}" + chr(10)
    event: dict = {}
    if hands.get("patch"):
        put(event, hands["patch"]["from"][0], f"*** Begin Patch\n*** Add File: {path}\n+{text}\n*** End Patch\n")
    else:
        put(event, hands["paths"][0], path)
        put(event, next(k for k in hands["texts"] if "*" not in k), text)
    return event


class Enforcement(Fixtures, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.kit = adapted_kit()
        _rel, surfaces = surface_documents(cls.kit)
        cls.surfaces = [s for s in surfaces if "hands" in s]

    def served_host(self, gates=()) -> Path:
        host = self.installed(self.kit)
        for surface in self.surfaces:
            path = host / DESCRIPTORS / f"{surface['id']}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"schema_version": 1, "id": surface["id"], "class": A_CLASS["id"],
                                        ENABLING_FIELD: surface["id"]}) + "\n", encoding="utf-8")
        (host / GATES_FILE).write_text(json.dumps({"schema_version": 1, "gates": list(gates)}) + "\n",
                                       encoding="utf-8")
        self.assertEqual(0, self.run_kit(self.kit, host, "render").returncode)
        return host

    def judge(self, host: Path, surface: dict, event) -> subprocess.CompletedProcess:
        pinned = host / VENDOR / "interpreters" / "cli.py"
        return subprocess.run([sys.executable, str(pinned), "judge", "--root", str(host),
                               "--surface", surface["id"]],
                              input=event if isinstance(event, str) else json.dumps(event),
                              capture_output=True, text=True)

    def test_288_every_hand_declaring_surface_is_served_a_setting_that_runs_the_pinned_judge(self):
        self.assertTrue(self.surfaces, "no taken adapter declares a hand -- this would pass on nothing")
        host = self.served_host()
        served = json.loads((host / RECORD).read_text(encoding="utf-8"))["served"]
        for surface in self.surfaces:
            with self.subTest(surface=surface["id"]):
                target = next(r["target"] for r in surface["renders"] if r["view"] == "enforcement")
                self.assertIn(target, {row["path"] for row in served})
                text = (host / target).read_text(encoding="utf-8")
                if target.endswith(".json"):
                    json.loads(text)
                self.assertIn(f"{VENDOR}/interpreters/cli.py", text)
                self.assertIn(f"judge --root", text)
                self.assertIn(f"--surface {surface['id']}", text)
                self.assertTrue((host / VENDOR / "interpreters" / "verbs" / "judge.py").is_file(),
                                "the served hook names a judge the pinned kit does not carry")
        checked = self.run_kit(self.kit, host, "check")
        activating = [s["id"] for s in self.surfaces if activation.FIELD in s]
        failed = [line.split()[1] for line in checked.stdout.splitlines() if line.startswith("  FAIL")]
        # A served surface whose product runs nothing until a setting names it is NOT yet a guard,
        # and check says so in those words -- never a green that no commit ever passed through.
        gate = next(g["id"] for c in CORE.capabilities for g in c.gates if g["kind"] == activated.KIND)
        self.assertEqual([gate] if activating else [], failed, checked.stdout)
        for surface in activating:
            self.assertIn(f"{surface}: {activation.INACTIVE}", checked.stdout)

    def test_289_a_violating_edit_is_refused_through_the_host_gate_and_a_clean_one_passes(self):
        host = self.served_host([HOST_GATE])
        for surface in self.surfaces:
            hands = surface["hands"]
            with self.subTest(surface=surface["id"]):
                absolute = str(host / "src" / "a.ts")
                refused = self.judge(host, surface, _event(hands, absolute, "let y = ctx.year;"))
                self.assertEqual(hands["refusal"]["exit"], refused.returncode, refused.stdout + refused.stderr)
                self.assertIn(HOST_GATE["id"], refused.stderr)
                clean = self.judge(host, surface, _event(hands, "src/a.ts", "let y = ctx.dims['time'];"))
                self.assertEqual(0, clean.returncode, clean.stdout + clean.stderr)
                elsewhere = self.judge(host, surface, _event(hands, "docs/a.md", "ctx.year"))
                self.assertEqual(0, elsewhere.returncode, elsewhere.stdout + elsewhere.stderr)
                nameless = self.judge(host, surface, _event(hands, "", "ctx.year"))
                unjudged = self.judge(host, surface, {"unrelated": True})
                if hands.get("nothing") == judge_verb.NOTHING_ADMITTED:
                    # DECLARED complete grammar: naming no file introduces no text in any path.
                    self.assertEqual(0, nameless.returncode, nameless.stdout + nameless.stderr)
                    self.assertNotIn(HOST_GATE["id"], nameless.stderr)
                else:
                    self.assertEqual(hands["refusal"]["exit"], nameless.returncode, "an empty path was judged as the host root")
                    self.assertEqual(hands["refusal"]["exit"], unjudged.returncode)

    def test_289b_a_drive_spelled_as_a_posix_mount_is_placed_and_a_driveless_rooted_path_is_refused(self):
        host = self.served_host([HOST_GATE])
        target = (host / "src" / "a.ts").resolve()
        drive = target.drive
        if not drive:
            self.skipTest("this filesystem has no drives: a rooted path is exactly what it names")
        mounted = f"/{drive[0].lower()}{target.as_posix()[len(drive):]}"
        for surface in self.surfaces:
            hands = surface["hands"]
            with self.subTest(surface=surface["id"]):
                for spelled in (mounted, "/cygdrive" + mounted):
                    refused = self.judge(host, surface, _event(hands, spelled, "let y = ctx.year;"))
                    self.assertEqual(hands["refusal"]["exit"], refused.returncode, refused.stdout + refused.stderr)
                    self.assertIn(HOST_GATE["id"], refused.stderr)
                driveless = self.judge(host, surface, _event(hands, "/nowhere/src/a.ts", "let y = ctx.year;"))
                self.assertEqual(hands["refusal"]["exit"], driveless.returncode, driveless.stdout + driveless.stderr)
                self.assertNotIn("lies outside this host", driveless.stdout)

    def test_290_check_fails_an_uncalibrated_host_gate(self):
        host = self.served_host([{**HOST_GATE, "admits": HOST_GATE["proves"]}])
        checked = self.run_kit(self.kit, host, "check")
        self.assertEqual(1, checked.returncode)
        self.assertIn(f"FAIL  {GATE_ID}", checked.stdout)

    def test_291_the_hook_carries_no_policy_and_names_no_product(self):
        seed = next(i["source"] for i in ENFORCEMENT.installs if i.get("validates") == "edit-gate")
        self.assertEqual([], json.loads((KIT / seed).read_text(encoding="utf-8"))["gates"])
        interpreters = [KIT / "interpreters" / "verbs" / "judge.py", KIT / "interpreters" / "gates" / "edits.py"]
        forbidden = {HOST_GATE["id"]}
        for surface in self.surfaces:
            forbidden.add(surface["id"])
            hands = surface["hands"]
            forbidden |= {key.split(".")[0] for key in hands["paths"] + hands["texts"]}
        for path in interpreters:
            text = path.read_text(encoding="utf-8")
            for word in sorted(forbidden):
                with self.subTest(file=path.name, word=word):
                    self.assertNotIn(word, text)


if __name__ == "__main__":
    unittest.main()
