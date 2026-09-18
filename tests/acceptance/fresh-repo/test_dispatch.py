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
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from harness import Fixtures

import admission
import dispatch_port
import ephemeral
import hostlock
from context import Context

from test_adapters import ADAPTERS, adapted_kit
from test_enforcement import GATES_FILE

#: The fixture worker: it writes inside the tree it was given and prints one JSON document. Held
#: free of braces on purpose -- a declaration's placeholders are written in braces, and a program
#: carrying its own would be a fixture arguing with the grammar it is being run through.
WROTE = "worker-was-here.txt"
WORKER = (
    "import json, pathlib, sys" "\n"
    f"pathlib.Path({WROTE!r}).write_text(sys.argv[1], encoding='utf-8')" "\n"
    "print(json.dumps(dict(said=sys.argv[1], role=sys.argv[2])))" "\n"
    "sys.stderr.write('the worker spoke here')" "\n"
)

ARTIFACT, DIAGNOSTIC = "result", "diagnostics"

#: The one text this host refuses, and the gate that refuses it -- calibrated on the very file the
#: fixture worker writes, so that the two dispatches below differ in the TEXT and in nothing else.
REFUSED = "a word this host has declared it refuses"
GATE = {
    "id": "a-word-this-host-refuses",
    "paths": f"^{re.escape(WROTE)}$",
    "forbids": re.escape(REFUSED),
    "because": "this host declares that word unwelcome.",
    "instead": "any other word.",
    "proves": {"path": WROTE, "text": REFUSED},
    "admits": {"path": WROTE, "text": "a word this host has declared nothing about"},
}


def _declares_provider(path: Path) -> bool:
    """Whether this file is the document declaring that workspace provider -- read by the CONTRACT
    it keeps, exactly as the port finds it, and never by a path spelled here."""
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return False
    return isinstance(document, dict) and bool(document.get(dispatch_port.PROVIDER_LIST))


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

    def repository(self, kit: Path = None) -> Path:
        """An installed host that is a real repository with a commit: a worker's isolated tree is
        checked out of one, and a repository with no commit has no state to branch from."""
        host = self.installed(kit or self.kit)
        env = dict(os.environ, GIT_AUTHOR_NAME="fixture", GIT_AUTHOR_EMAIL="f@example.invalid",
                   GIT_COMMITTER_NAME="fixture", GIT_COMMITTER_EMAIL="f@example.invalid")
        for argv in (["add", "-A"], ["commit", "-q", "--no-verify", "-m", "the installed host"]):
            ran = subprocess.run(["git", *argv], cwd=host, capture_output=True, text=True, env=env)
            self.assertEqual(0, ran.returncode, ran.stderr)
        return host

    def through_the_verb(self, host: Path, handed: str, kit: Path = None):
        result = subprocess.run(
            [sys.executable, str(Path(dispatch_port.__file__).parent.parent / "cli.py"),
             self.verb, "--root", str(host), "--kit", str(kit or self.kit)],
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


    # == 3. admission on return =================================================================
    def test_315_what_a_worker_left_in_its_tree_is_refused_by_this_hosts_own_gates_on_return(self):
        """The other half of the isolation (ADR-017 decision 5), walked.

        A worker is not prevented from writing -- it cannot be, which is the whole reason it was
        given a tree of its own. So the question is what happens when it writes something this host
        refuses: the change must not enter, the refusal must be this host's OWN declared gate
        speaking in its own words, and the account of it must survive the process that found it.

        Two dispatches, one gate, one difference: the text the worker was told to write. Nothing
        else changes -- not the adapter, not the provider, not the host -- so what the assertion
        measures is the judgement on return and nothing beside it.
        """
        host = self.repository()
        (host / GATES_FILE).write_text(json.dumps({"schema_version": 1, "gates": [GATE]}) + "\n",
                                       encoding="utf-8")

        admitted = "text this host has nothing to say about"
        walked = self.through_the_verb(host, json.dumps(packet("c3-admitted", instruction=admitted)))
        self.assertEqual(0, walked.returncode, walked.stdout + walked.stderr)
        self.assertEqual(admission.ADMITTED, self.record(host, "c3-admitted")["admission"]["verdict"])

        refused = self.through_the_verb(host, json.dumps(packet("c3-refused", instruction=REFUSED)))
        self.assertEqual(1, refused.returncode, refused.stdout + refused.stderr)
        self.assertIn(f"[{admission.NotAdmitted.code}]", refused.stderr)
        self.assertIn(GATE["id"], refused.stdout)

        # The worker FINISHED and what it wrote is NOT ADMITTED -- two propositions, two fields.
        # A single word doing both jobs would have had to hide one of them.
        task = self.record(host, "c3-refused")
        self.assertEqual(dispatch_port.COMPLETED, task["state"])
        self.assertEqual(0, task["exit_code"])
        verdict = task["admission"]
        self.assertEqual(admission.REFUSED, verdict["verdict"])
        self.assertEqual([WROTE], verdict["judged"])
        self.assertEqual([{"path": WROTE, "gate": GATE["id"], "because": GATE["because"],
                           "instead": GATE["instead"]}], verdict["refusals"])
        self.assertTrue(verdict["at"])

        # The evidence for the refusal outlives it: the tree still holds what was refused, and the
        # host never received it. A refusal that destroyed what it refused could not be checked.
        self.assertTrue((host / task["workspace"] / WROTE).is_file())
        self.assertFalse((host / WROTE).exists())

    def test_316_a_host_whose_provider_cannot_report_a_return_starts_no_worker_at_all(self):
        """Refused at the DOOR, before anything is leased: a worker whose change could never be
        judged is not a worker this port starts and reports on afterwards."""
        self.assertTrue(admission.declares(dispatch_port.provider(self.context(self.repository()))),
                        "the taken provider cannot report a return, so the refusal below would "
                        "pass on nothing")
        blinded = []

        def blind(kit: Path) -> None:
            """The provider's own document -- found by the CONTRACT it keeps, exactly as the port
            finds it -- with its way of reporting a return taken out. A host that declares
            isolation and no way to judge what came back out of it."""
            for document in [p for p in kit.rglob("*.json") if _declares_provider(p)]:
                declaration = json.loads(document.read_text(encoding="utf-8"))
                for row in declaration[dispatch_port.PROVIDER_LIST]:
                    blinded.append(row.pop(admission.RETURNED, None) and row["id"])
                document.write_text(json.dumps(declaration, indent=2) + "\n", encoding="utf-8",
                                    newline="\n")

        kit = adapted_kit(patch=blind, adapters=[*ADAPTERS, ADAPTER])
        self.assertTrue([row for row in blinded if row], "no provider was blinded")
        host = self.repository(kit)
        said = self.through_the_verb(host, json.dumps(packet("c3-unjudgeable")), kit=kit)
        self.assertEqual(1, said.returncode, said.stdout + said.stderr)
        self.assertIn(f"[{dispatch_port.DispatchUnserved.code}]", said.stderr)
        # Nothing was leased, made or started: the refusal is at the door, before the writing.
        home = Path(ephemeral.root(self.context(host))) / dispatch_port.HOME
        self.assertFalse((host / home / "c3-unjudgeable").exists())


if __name__ == "__main__":
    unittest.main()
