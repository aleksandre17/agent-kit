"""Acceptance: the DISPATCH PORT -- one place a worker is started (ADR-017 link C, slice C2).

The claim under test is not that a dispatch works. It is that the GATE HAS ONE HOME. A packet gate
living in a runtime's spawn hook fires where that runtime has such a hook and is silently absent
where it does not, and the two orchestrators are each locally correct while one of them lets a
malformed task through. So:

  1. a malformed dispatch is refused BY THE PORT whatever the caller -- through the served CLI verb
     and through a direct in-process call that bypasses every verb, hook and runtime, with the same
     code and the same refusal. Nothing is leased, nothing is made, nothing is started;
  2. a well-formed one is leased, isolated, started and RECORDED: the task record exists before the
     worker does, moves through A2A's states, and closes once carrying the artifact the adapter
     declared -- read from the channel it named, never from a guess.

No product is named here. The adapter the walked path runs through is a FIXTURE published the way
any adapter is published -- a directory, a capability declaration and a document keeping the
dispatch contract -- which is the property itself: the port serves an intelligence nobody shipped.
The real `claude-subagent` adapter is a declaration about somebody else's software and is NOT
exercised: it has never been observed running, and a suite that pretended otherwise would be the
one lie this design exists to prevent.
"""

from __future__ import annotations

import atexit
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from harness import Fixtures

import dispatch_port
import ephemeral
import hostlock
from context import Context

from test_adapters import ADAPTERS, adapted_kit

#: The fixture worker: it writes inside the tree it was given and prints one JSON document. Held
#: free of braces on purpose -- a declaration's placeholders are written in braces, and a program
#: carrying its own would be a fixture arguing with the grammar it is being run through.
WORKER = (
    "import json, pathlib, sys" "\n"
    "pathlib.Path('worker-was-here.txt').write_text(sys.argv[1], encoding='utf-8')" "\n"
    "print(json.dumps(dict(said=sys.argv[1], role=sys.argv[2])))" "\n"
    "sys.stderr.write('the worker spoke here')" "\n"
)

ARTIFACT, DIAGNOSTIC = "result", "diagnostics"


def fixture_adapter() -> Path:
    """An adapter for an intelligence nobody shipped, published exactly as a real one is."""
    home = Path(tempfile.mkdtemp(prefix="dispatch-adapter-")).resolve() / "an-intelligence"
    atexit.register(shutil.rmtree, home.parent, True)
    home.mkdir(parents=True)
    seat = f"capabilities/{home.name}"
    (home / "capability.json").write_text(json.dumps({
        "schema_version": 1, "id": home.name, "version": "1.0.0",
        "summary": "A fixture dispatch adapter: an intelligence this kit never shipped, taken by a "
                   "host exactly as any adapter is, so that the port is measured on a declaration "
                   "it has no knowledge of.",
        "requires": [], "provides": [], "conflicts": [], "declares": {},
        "documents": [{"id": "fixture_dispatch", "source": f"{seat}/dispatch.json",
                       "validates": dispatch_port.ADAPTERS["validates"]}],
        "floor": [], "installs": [], "gates": [],
    }, indent=2) + "\n", encoding="utf-8", newline="\n")
    (home / "dispatch.json").write_text(json.dumps({
        "schema_version": 1,
        dispatch_port.ADAPTER_LIST: [{
            "id": home.name,
            "says": "A fixture. It is this repository's own interpreter, run on a program written "
                    "here, so nothing in this row is a claim about anybody else's software.",
            "starts": {"argv": [sys.executable, "-c", WORKER, "{instruction}", "{role}"]},
            "returns": [{"name": ARTIFACT, "from": "stdout", "media_type": "application/json"},
                        {"name": DIAGNOSTIC, "from": "stderr"}],
            "completed_on": {"exit": 0},
        }],
    }, indent=2) + "\n", encoding="utf-8", newline="\n")
    return home


ADAPTER = fixture_adapter()


def packet(identity: str, **fields) -> dict:
    return dict({"schema_version": 1, "id": identity, "route": ADAPTER.name,
                 "instruction": "write the file you were asked for", "branch": f"dispatch/{identity}",
                 "role": "a-worker"}, **fields)


class Dispatch(Fixtures, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.kit = adapted_kit(adapters=[*ADAPTERS, ADAPTER])
        #: The verb, read from the file that declares it -- never a word spelled here.
        cls.verb = Path(dispatch_port.__file__).parent.parent.joinpath("verbs")
        cls.verb = next(p.stem for p in cls.verb.glob("*.py")
                        if p.stem != "__init__" and "dispatch" in p.stem)

    def repository(self) -> Path:
        """An installed host that is a real repository with a commit: a worker's isolated tree is
        checked out of one, and a repository with no commit has no state to branch from."""
        host = self.installed(self.kit)
        env = dict(os.environ, GIT_AUTHOR_NAME="fixture", GIT_AUTHOR_EMAIL="f@example.invalid",
                   GIT_COMMITTER_NAME="fixture", GIT_COMMITTER_EMAIL="f@example.invalid")
        for argv in (["add", "-A"], ["commit", "-q", "--no-verify", "-m", "the installed host"]):
            ran = subprocess.run(["git", *argv], cwd=host, capture_output=True, text=True, env=env)
            self.assertEqual(0, ran.returncode, ran.stderr)
        return host

    def through_the_verb(self, host: Path, handed: str):
        result = subprocess.run(
            [sys.executable, str(Path(dispatch_port.__file__).parent.parent / "cli.py"),
             self.verb, "--root", str(host), "--kit", str(self.kit)],
            input=handed, capture_output=True, text=True)
        print(f"\n$ {self.verb} --root <host>  <<< {handed[:80]}\n"
              f"[exit {result.returncode}]\n{result.stdout}{result.stderr}")
        return result

    def context(self, host: Path) -> Context:
        return Context(kit_root=self.kit, host_root=host)

    def record(self, host: Path, identity: str) -> dict:
        ctx = self.context(host)
        return json.loads((host / dispatch_port.home(ctx, identity, "task.json")).read_text(encoding="utf-8"))

    # == 1. refused by the port, whatever the caller ============================================
    def test_313_a_malformed_dispatch_is_refused_by_the_port_through_every_caller(self):
        host = self.repository()
        ctx = self.context(host)
        home = Path(ephemeral.root(ctx)) / dispatch_port.HOME
        malformed = {
            "unreadable": "this is not a packet at all",
            "incomplete": json.dumps({k: v for k, v in packet("incomplete-task").items()
                                      if k != "instruction"}),
            "unrouted": json.dumps(packet("unrouted-task", route="an-intelligence-nobody-declares")),
        }
        for why, handed in malformed.items():
            with self.subTest(refusal=why):
                # (a) the caller every runtime is served: the verb, through the entry point.
                said = self.through_the_verb(host, handed)
                self.assertEqual(1, said.returncode, said.stdout + said.stderr)
                self.assertIn(f"[{dispatch_port.DispatchRefused.code}]", said.stderr)
                # (b) the caller that bypasses every verb, hook and runtime -- the same gate.
                with self.assertRaises(dispatch_port.DispatchRefused) as direct:
                    dispatch_port.accepted(ctx, handed)
                self.assertTrue(str(direct.exception))
                # Nothing was leased, made or started by either caller.
                self.assertFalse((host / home).exists(), f"a refused dispatch wrote into {home}")

    # == 2. the walked path ======================================================================
    def test_314_a_good_dispatch_is_leased_isolated_started_and_recorded_once(self):
        host = self.repository()
        ctx = self.context(host)
        identity = "c2-walked-path"
        handed = json.dumps(packet(identity))

        walked = self.through_the_verb(host, handed)
        self.assertEqual(0, walked.returncode, walked.stdout + walked.stderr)
        self.assertIn(identity, walked.stdout)

        # A DISPATCH-ID names ONE task: the second dispatch under the same name is refused rather
        # than overwriting the only account of what the first worker did.
        again = self.through_the_verb(host, handed)
        self.assertEqual(1, again.returncode, again.stdout + again.stderr)
        self.assertIn(f"[{dispatch_port.DispatchRefused.code}]", again.stderr)

        task = self.record(host, identity)
        self.assertEqual(dispatch_port.COMPLETED, task["state"], task.get("status_message"))
        self.assertEqual(identity, task["id"])
        self.assertEqual(ADAPTER.name, task["adapter"])
        self.assertEqual(0, task["exit_code"])
        self.assertTrue(task["opened_at"] and task["started_at"] and task["ended_at"])
        self.assertEqual(json.loads(handed), task["packet"])

        # The artifact came back through the channel the adapter declared, and carries what the
        # worker actually printed -- never a status message doing an answer's job.
        artifacts = {part["name"]: part for part in task["artifacts"]}
        self.assertEqual({ARTIFACT, DIAGNOSTIC}, set(artifacts))
        spoke = json.loads(artifacts[ARTIFACT]["text"])
        self.assertEqual(json.loads(handed)["instruction"], spoke["said"])
        self.assertEqual(json.loads(handed)["role"], spoke["role"])
        self.assertIn("worker spoke", artifacts[DIAGNOSTIC]["text"])

        # The worker wrote INSIDE the tree it was leased, and nowhere else.
        tree = host / task["workspace"]
        self.assertTrue((tree / "worker-was-here.txt").is_file(), "the worker's tree holds nothing")
        self.assertFalse((host / "worker-was-here.txt").exists(),
                         "the worker wrote into the host's own tree")
        branched = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=tree,
                                  capture_output=True, text=True)
        self.assertEqual(json.loads(handed)["branch"], branched.stdout.strip())

        # The lease is the kit's ONE hold mechanism: it stands where the task ran, and it was
        # CLOSED with an ending rather than deleted -- a hold that vanished leaves a host unable
        # to say it was ever held.
        lease = json.loads((host / task["lease"]).read_text(encoding="utf-8"))
        self.assertFalse(hostlock.standing(lease), "the lease outlived the task it held")
        self.assertEqual(0, lease["exit_code"])


if __name__ == "__main__":
    unittest.main()
