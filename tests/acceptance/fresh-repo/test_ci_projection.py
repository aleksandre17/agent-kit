"""Acceptance: the CI PROJECTION -- the return point nobody skips (ADR-017 link C, slice C1c part 4).

`git commit --no-verify` skips every local hook by git's design. A surface whose product runs on
every push and pull request, in a clone made for that one run, is served a pipeline definition that
runs the kit THIS HOST CARRIES -- `check` over the tree and the one `judge` over the pushed change --
so the same host gates stand where no local flag reaches. So:

  1. the served definition names the pinned kit's own interpreter for both steps, through its surface,
     and fetches no kit; the record names it as the kit's, and it is no evidence about the host;
  2. a check run THROUGH a surface that declares its clone ephemeral names a working clone's setting
     NOT MEASURED and fails nothing on it -- a check through no surface still reads it -- and a check
     through a surface nobody declares is refused;
  3. a definition the host already holds at the served path is never written over, and a definition
     of the host's own beside it is never touched;
  4. the served step commands, run exactly as written by `sh -e` against a fixture event and a
     fixture repository, refuse a change a host gate forbids and admit a clean one -- for a proposed
     change, a pushed one, and a push with no earlier commit.

Selected by declaration (the surface's `clone` field, the schema's word read from the gate that
honours it), never by a product's id. What only a real push proves is not proven here.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

import test_commit_gate as commit_gate  # first: it brings the harness, which places the kit's modules

import activated  # noqa: E402
import activation  # noqa: E402
import check as check_verb  # noqa: E402
import judge  # noqa: E402
import rows  # noqa: E402
import serving  # noqa: E402
from manifest import Manifest  # noqa: E402

enforcement = commit_gate.enforcement
HOST_GATE = enforcement.HOST_GATE
VENDOR = enforcement.VENDOR
_git = commit_gate._git
#: A `run: |` block scalar -- the one YAML form the served steps are written in, read as text.
RUN_BLOCK = re.compile(r"^(?P<indent>\s*)run: \|\s*$")
ZERO = "0" * 40


def run_blocks(text: str) -> list:
    """Every `run: |` block, dedented: the exact commands the product hands its shell."""
    lines, blocks = text.split("\n"), []
    for index, line in enumerate(lines):
        opened = RUN_BLOCK.match(line)
        if not opened:
            continue
        body, depth = [], len(opened.group("indent"))
        for following in lines[index + 1:]:
            if following.strip() and len(following) - len(following.lstrip()) <= depth:
                break
            body.append(following)
        margin = min(len(b) - len(b.lstrip()) for b in body if b.strip())
        blocks.append("\n".join(b[margin:] for b in body).rstrip("\n") + "\n")
    return blocks


class CiProjection(enforcement.Enforcement):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ephemeral = [s for s in cls.surfaces
                         if s.get(activated.CLONE) == activated.EPHEMERAL and s["hands"].get("carries") == judge.CARRIES_PATCH]
        if not cls.ephemeral:
            raise AssertionError("no taken adapter declares an ephemeral patch-carrying surface -- "
                                 "this suite would pass on nothing")
        cls.activating = [s for s in cls.surfaces if activation.FIELD in s]

    locals().update({name: None for name in dir(enforcement.Enforcement) if name.startswith("test_")})

    @staticmethod
    def target(surface) -> str:
        return next(r["target"] for r in surface["renders"])

    def repository(self) -> Path:
        return commit_gate.CommitGate.repository(self)

    def test_296_the_served_pipeline_runs_the_pinned_check_and_judge_and_is_no_evidence_about_the_host(self):
        host = self.served_host([HOST_GATE])
        served = {row["path"]: row for row in json.loads((host / enforcement.RECORD).read_text(encoding="utf-8"))["served"]}
        for surface in self.ephemeral:
            with self.subTest(surface=surface["id"]):
                target = self.target(surface)
                self.assertEqual(surface["id"], served[target]["surface"])
                text = (host / target).read_text(encoding="utf-8")
                self.assertNotIn("\r", text)
                steps = run_blocks(text)
                self.assertTrue(any(f'"{VENDOR}/interpreters/cli.py" check --root . --surface {surface["id"]}' in s for s in steps))
                self.assertTrue(any(f'"{VENDOR}/interpreters/cli.py" judge --root . --surface {surface["id"]}' in s for s in steps))
                self.assertNotIn("--kit", text, "a served pipeline that names a kit runs one this host did not pin")
                self.assertNotIn("git+", text)

                through = self.run_kit(self.kit, host, "check", "--surface", surface["id"])
                self.assertEqual(0, through.returncode, through.stdout + through.stderr)
                self.assertNotIn("  FAIL", through.stdout, "the served file changed a reading of the host")
                for other in self.activating:
                    self.assertIn(f"{other['id']}: NOT MEASURED", through.stdout)
        plain = self.run_kit(self.kit, host, "check")
        for other in self.activating:
            self.assertIn(f"{other['id']}: {activation.INACTIVE}", plain.stdout)
        unknown = self.run_kit(self.kit, host, "check", "--surface", "no-such-surface")
        self.assertNotEqual(0, unknown.returncode)
        self.assertIn(f"[{check_verb.ThroughUnknown.code}]", unknown.stderr)

    def test_297_a_host_definition_at_the_served_path_is_refused_and_one_beside_it_is_left_alone(self):
        for surface in self.ephemeral:
            with self.subTest(surface=surface["id"]):
                host = self.installed(self.kit)
                target = host / self.target(surface)
                target.parent.mkdir(parents=True, exist_ok=True)
                theirs = b"name: the owner's own\n"
                target.write_bytes(theirs)
                beside = target.parent / f"owner-{target.name}"
                beside.write_bytes(theirs)
                refused = self.served_host_on(host)
                self.assertNotEqual(0, refused.returncode)
                self.assertIn(f"[{serving.ServeCollision.code}]", refused.stderr)
                self.assertEqual(theirs, target.read_bytes())
                target.unlink()
                admitted = self.served_host_on(host)
                self.assertEqual(0, admitted.returncode, admitted.stdout + admitted.stderr)
                self.assertEqual(theirs, beside.read_bytes(), "the kit touched a definition it does not own")

    def test_298_declared_owners_are_served_into_a_span_of_the_hosts_file_and_branch_protection_is_named_not_set(self):
        core = Manifest(self.kit)
        # The view that lays out a host's declared rows, found by the resolver that answers for it.
        view = next(v for c in core.capabilities for i in c.installs for v in i.get("serves", {}).get("views", [])
                    if any(k["kind"] in rows.RESOLVES for k in v.get("carries", [])))
        contract = next(k["params"]["validates"] for k in view["carries"] if k["kind"] in rows.RESOLVES)
        seat = next(i["target"] for c in core.capabilities for i in c.installs if i.get("validates") == contract)
        owning = [(s, r) for s in self.surfaces for r in s["renders"] if r["view"] == view["id"]]
        if not owning:
            raise AssertionError("no taken adapter serves the owners view -- this test would pass on nothing")
        host = self.installed(self.kit)
        value = json.loads((host / seat).read_text(encoding="utf-8"))
        value["rules"] = [{"id": "kit-planes", "pattern": "/.agents/", "owners": ["@an-org/maintainers", "a@b.example"]}]
        (host / seat).write_text(json.dumps(value) + "\n", encoding="utf-8")
        ran = self.served_host_on(host)
        self.assertEqual(0, ran.returncode, ran.stdout + ran.stderr)
        for _surface, render in owning:
            path = host / render["target"]
            self.assertIn("/.agents/ @an-org/maintainers a@b.example\n", path.read_text(encoding="utf-8"))
            # The file is the host's: a line of its own outside the span survives every render.
            path.write_text("* @the-owner\n" + path.read_text(encoding="utf-8"), encoding="utf-8")
            again = self.served_host_on(host)
            self.assertEqual(0, again.returncode, again.stdout + again.stderr)
            self.assertTrue(path.read_text(encoding="utf-8").startswith("* @the-owner\n"))
        doctor = self.run_kit(self.kit, host, "doctor")
        controls = [c for s in self.surfaces for c in s.get("controls", [])]
        self.assertTrue(controls, "no taken adapter names a control only a person sets")
        for control in controls:
            self.assertIn("NOT ASSERTED", doctor.stdout)
            self.assertIn(control["command"], doctor.stdout)

    def served_host_on(self, host: Path) -> subprocess.CompletedProcess:
        for surface in self.surfaces:
            path = host / enforcement.DESCRIPTORS / f"{surface['id']}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"schema_version": 1, "id": surface["id"], "class": enforcement.A_CLASS["id"],
                                        enforcement.ENABLING_FIELD: surface["id"]}) + "\n", encoding="utf-8")
        return self.run_kit(self.kit, host, "render")

    def steps(self, host: Path, surface, event: dict) -> list:
        """Run every served step exactly as written, by `sh -e`, as the product documents it."""
        results = []
        with tempfile.TemporaryDirectory() as scratch:
            event_path = Path(scratch) / "event.json"
            event_path.write_text(json.dumps(event), encoding="utf-8", newline="\n")
            env = dict(os.environ, GITHUB_EVENT_PATH=str(event_path))
            for index, step in enumerate(run_blocks((host / self.target(surface)).read_text(encoding="utf-8"))):
                script = Path(scratch) / f"step-{index}.sh"
                script.write_text(step, encoding="utf-8", newline="\n")
                results.append(subprocess.run(["sh", "-e", str(script)], cwd=host, capture_output=True, text=True, env=env))
        return results

    def test_298_the_served_steps_run_as_written_refuse_a_violating_change_and_admit_a_clean_one(self):
        for surface in self.ephemeral:
            with self.subTest(surface=surface["id"]):
                host = self.repository()
                base = _git(host, "rev-parse", "HEAD").stdout.strip()
                (host / "src").mkdir(exist_ok=True)
                (host / "src" / "a.ts").write_text(f"let y = {HOST_GATE['proves']['text']};\n", encoding="utf-8", newline="\n")
                _git(host, "add", "src/a.ts")
                _git(host, "commit", "-q", "--no-verify", "-m", "a violation the local hook never saw")
                for event in ({"pull_request": {"base": {"sha": base}}}, {"before": base}, {"before": ZERO}):
                    with self.subTest(event=event):
                        check_step, prove_step, judge_step = self.steps(host, surface, event)
                        self.assertEqual(0, check_step.returncode, check_step.stdout + check_step.stderr)
                        self.assertEqual(0, prove_step.returncode, prove_step.stdout + prove_step.stderr)
                        self.assertEqual(surface["hands"]["refusal"]["exit"], judge_step.returncode, judge_step.stdout)
                        self.assertIn(HOST_GATE["id"], judge_step.stderr)

                (host / "src" / "a.ts").write_text(f"let y = {HOST_GATE['admits']['text']};\n", encoding="utf-8", newline="\n")
                _git(host, "commit", "-q", "--no-verify", "-am", "clean")
                clean = _git(host, "rev-parse", "HEAD~1").stdout.strip()
                _check, _prove, judged = self.steps(host, surface, {"before": clean})
                self.assertEqual(0, judged.returncode, judged.stdout + judged.stderr)
                _check, _prove, unreadable = self.steps(host, surface, {"before": "f" * 40})
                self.assertEqual(surface["hands"]["refusal"]["exit"], unreadable.returncode, "an unreadable base was waved through")


if __name__ == "__main__":
    unittest.main()
