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
     declared -- read from the channel it named, never from a guess;
  3. a worker that cannot proceed ASKS instead of guessing, and the SAME worker is re-entered with
     an operator's answer through the argv its adapter declared (C4). The record never closes while
     it stands, the question and the way back in are read from declared channels, and what the
     resumed worker left in its tree is admitted or refused exactly as C3 judges any return;
  4. a worker whose adapter declares no way back in parks a task that SAYS SO, and the resume act
     refuses by that adapter's name -- the difference between a question nobody can answer and one
     nobody has answered yet is the whole of Cardinal V here.

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

ARTIFACT, DIAGNOSTIC, SESSION = "result", "diagnostics", "session"

#: The round-trip's fixture worker (C4). It writes in the tree it was given exactly as the first
#: one does, puts its QUESTION in the file the port provided for its artifact, says on its own
#: stdout what would re-enter it, and ends with the code its adapter declares for 'I need input'.
#: Held free of braces for the same reason as the worker above.
ASKS_ON = 7
QUESTION = "which of the two shapes did you mean"
REENTRY = "a-session-no-other-task-has"
ASKER = (
    "import pathlib, sys" "\n"
    f"pathlib.Path({WROTE!r}).write_text(sys.argv[1], encoding='utf-8')" "\n"
    f"pathlib.Path(sys.argv[2]).write_text({QUESTION!r}, encoding='utf-8')" "\n"
    f"sys.stdout.write({REENTRY!r} + chr(10))" "\n"
    "sys.stderr.write('the worker asked here')" "\n"
    f"sys.exit({ASKS_ON})" "\n"
)
#: The same worker, re-entered. It is handed the operator's answer and the way back in, and it
#: writes BOTH into its artifact -- so what the record holds at the end proves which answer reached
#: which worker, rather than merely that something ran a second time.
RESUMER = (
    "import pathlib, sys" "\n"
    f"pathlib.Path({WROTE!r}).write_text(sys.argv[1], encoding='utf-8')" "\n"
    "pathlib.Path(sys.argv[3]).write_text('answered ' + sys.argv[1] + ' in ' + sys.argv[2], "
    "encoding='utf-8')" "\n"
    "sys.stderr.write('the worker resumed here')" "\n"
)

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


def fixture_adapter(name: str = "an-intelligence", **declared) -> Path:
    """An adapter for an intelligence nobody shipped, published exactly as a real one is.

    `declared` is whatever this one says beyond the two blocks every adapter has -- an `asks`, a
    `resumes`, or neither. One publisher, several intelligences: which blocks a row carries is a
    DECLARATION, and the suite reaches the port's new behaviour without the port learning a name.
    """
    home = Path(tempfile.mkdtemp(prefix="dispatch-adapter-")).resolve() / name
    atexit.register(shutil.rmtree, home.parent, True)
    home.mkdir(parents=True)
    seat = f"capabilities/{home.name}"
    (home / "capability.json").write_text(json.dumps({
        "schema_version": 1, "id": home.name, "version": "1.0.0",
        "summary": "A fixture dispatch adapter: an intelligence this kit never shipped, taken by a "
                   "host exactly as any adapter is, so that the port is measured on a declaration "
                   "it has no knowledge of.",
        "requires": [], "provides": [], "conflicts": [], "declares": {},
        # One readable, one name: two fixture adapters installed side by side are two capabilities,
        # and a document id they shared would resolve to two things.
        "documents": [{"id": f"{home.name.replace('-', '_')}_dispatch",
                       "source": f"{seat}/dispatch.json",
                       "validates": dispatch_port.ADAPTERS["validates"]}],
        "floor": [], "installs": [], "gates": [],
    }, indent=2) + "\n", encoding="utf-8", newline="\n")
    (home / "dispatch.json").write_text(json.dumps({
        "schema_version": 1,
        dispatch_port.ADAPTER_LIST: [dict({
            "id": home.name,
            "says": "A fixture. It is this repository's own interpreter, run on a program written "
                    "here, so nothing in this row is a claim about anybody else's software.",
            "starts": {"argv": [sys.executable, "-c", WORKER, "{instruction}", "{role}"]},
            "returns": [{"name": ARTIFACT, "from": "stdout", "media_type": "application/json"},
                        {"name": DIAGNOSTIC, "from": "stderr"}],
            "completed_on": {"exit": 0},
        }, **declared)],
    }, indent=2) + "\n", encoding="utf-8", newline="\n")
    return home


ADAPTER = fixture_adapter()
#: An intelligence that can ask AND be re-entered, and one that can only ask. The second is not a
#: broken adapter: a product with no way back in is a real one, and what the port must never do is
#: let its task read like a question somebody merely has not answered yet.
ASKING = fixture_adapter(
    "an-intelligence-that-asks",
    starts={"argv": [sys.executable, "-c", ASKER, "{instruction}", "{artifact}"]},
    returns=[{"name": ARTIFACT, "from": "file", "media_type": "text/plain"},
             {"name": SESSION, "from": "stdout"},
             {"name": DIAGNOSTIC, "from": "stderr"}],
    asks={"exit": ASKS_ON, "question": ARTIFACT, "reentry": SESSION},
    resumes={"argv": [sys.executable, "-c", RESUMER, "{answer}", "{reentry}", "{artifact}"]},
)
UNANSWERABLE = fixture_adapter(
    "an-intelligence-that-cannot-be-re-entered",
    starts={"argv": [sys.executable, "-c", ASKER, "{instruction}", "{artifact}"]},
    returns=[{"name": ARTIFACT, "from": "file", "media_type": "text/plain"},
             {"name": DIAGNOSTIC, "from": "stderr"}],
    asks={"exit": ASKS_ON, "question": ARTIFACT},
)


def answer(identity: str, said: str, **fields) -> str:
    """The other act this port serves, as an operator hands it over: the task it answers, and the
    answer. No flag says which act this is -- the document does."""
    return json.dumps(dict({"schema_version": 1, dispatch_port.RESUME: identity,
                            dispatch_port.ANSWER: said}, **fields))


def packet(identity: str, **fields) -> dict:
    return dict({"schema_version": 1, "id": identity, "route": ADAPTER.name,
                 "instruction": "write the file you were asked for", "branch": f"dispatch/{identity}",
                 "role": "a-worker"}, **fields)


class Dispatch(Fixtures, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.kit = adapted_kit(adapters=[*ADAPTERS, ADAPTER, ASKING, UNANSWERABLE])
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


    # == 4. the round-trip ======================================================================
    def test_317_a_worker_that_cannot_proceed_asks_and_the_same_one_is_re_entered(self):
        """ADR-017 slice C4, walked end to end.

        The claim is not that a second process ran. It is that the SAME worker was re-entered with
        an operator's answer: the record never closed, it held the question and the way back in,
        the answer went into the adapter's own declared resume argv, and what came back names both.
        A resume that quietly started a fresh worker on a longer instruction would satisfy every
        weaker assertion, which is why the artifact must carry the session the FIRST turn issued.
        """
        host = self.repository()
        identity = "c4-round-trip"

        asked = self.through_the_verb(host, json.dumps(packet(identity, route=ASKING.name)))
        self.assertEqual(dispatch_port.WAITING, asked.returncode, asked.stdout + asked.stderr)
        self.assertIn(QUESTION, asked.stdout)

        standing = self.record(host, identity)
        self.assertEqual(dispatch_port.INPUT_REQUIRED, standing["state"])
        self.assertNotIn("ended_at", standing, "a worker that is standing was recorded as ended")
        self.assertEqual(ASKS_ON, standing["exit_code"])
        turn = standing[dispatch_port.HISTORY][-1]
        self.assertEqual(dispatch_port.AGENT, turn["role"])
        self.assertEqual(QUESTION, turn["text"])
        self.assertEqual(REENTRY, turn[dispatch_port.REENTRY])
        self.assertTrue(turn["at"])
        self.assertNotIn("unresumable", turn)
        # It asked, and it also WROTE: the return is judged whatever the ending was.
        self.assertEqual(admission.ADMITTED, standing["admission"]["verdict"])
        self.assertIn(WROTE, standing["admission"]["judged"])

        said = "the second shape, and only that one"
        walked = self.through_the_verb(host, answer(identity, said, by="an-operator"))
        self.assertEqual(0, walked.returncode, walked.stdout + walked.stderr)

        closed = self.record(host, identity)
        self.assertEqual(dispatch_port.COMPLETED, closed["state"])
        self.assertEqual([dispatch_port.AGENT, dispatch_port.OPERATOR],
                         [t["role"] for t in closed[dispatch_port.HISTORY]])
        answered = closed[dispatch_port.HISTORY][-1]
        self.assertEqual(said, answered["text"])
        self.assertEqual("an-operator", answered["by"])
        self.assertTrue(closed["resumed_at"] and closed["ended_at"])
        self.assertEqual(standing["workspace"], closed["workspace"], "a second tree was made")

        # The SAME worker: what came back names the operator's answer AND the session the first
        # turn issued -- so the answer reached the declared resume argv and nothing else did.
        produced = {part["name"]: part for part in closed["artifacts"]}[ARTIFACT]["text"]
        self.assertIn(said, produced)
        self.assertIn(REENTRY, produced)
        # The resumed worker wrote too, and what it left was judged exactly as C3 judges a return.
        self.assertEqual(admission.ADMITTED, closed["admission"]["verdict"])
        self.assertEqual(said, (host / closed["workspace"] / WROTE).read_text(encoding="utf-8"))

        # A task that is no longer waiting is not resumed again: the refusal names the state it
        # stands in and the moment that reading was taken.
        over = self.through_the_verb(host, answer(identity, said))
        self.assertEqual(1, over.returncode, over.stdout + over.stderr)
        self.assertIn(f"[{dispatch_port.DispatchRefused.code}]", over.stderr)
        self.assertIn(dispatch_port.COMPLETED, over.stderr)

    def test_318_a_question_no_adapter_can_answer_says_so_and_the_resume_refuses_by_name(self):
        """An adapter that declares how its worker asks and not how one is re-entered.

        The task is REAL and the question is real; what is absent is the way back in. So the record
        must say that at the moment the question was read -- not leave a task that reads exactly
        like one nobody has got around to answering -- and the resume act must refuse BY NAME,
        saying which adapter lacks the declaration, because 'this cannot be resumed' with no name
        in it is a sentence an operator can do nothing with.
        """
        host = self.repository()
        identity = "c4-unanswerable"

        asked = self.through_the_verb(host, json.dumps(packet(identity, route=UNANSWERABLE.name)))
        self.assertEqual(dispatch_port.WAITING, asked.returncode, asked.stdout + asked.stderr)
        turn = self.record(host, identity)[dispatch_port.HISTORY][-1]
        self.assertEqual(QUESTION, turn["text"])
        self.assertIn(UNANSWERABLE.name, turn["unresumable"])
        self.assertIn(UNANSWERABLE.name, asked.stdout)

        refused = self.through_the_verb(host, answer(identity, "an answer nobody can deliver"))
        self.assertEqual(1, refused.returncode, refused.stdout + refused.stderr)
        self.assertIn(f"[{dispatch_port.DispatchUnserved.code}]", refused.stderr)
        self.assertIn(UNANSWERABLE.name, refused.stderr)

        # Nothing was re-entered and nothing was rewritten: the task stands where it was, with the
        # one account of what its worker asked.
        stands = self.record(host, identity)
        self.assertEqual(dispatch_port.INPUT_REQUIRED, stands["state"])
        self.assertEqual(1, len(stands[dispatch_port.HISTORY]))

    def test_319_an_answer_to_a_task_this_host_never_dispatched_is_refused_before_any_write(self):
        """The resume act's own refusals, which are the port's like every other: an act naming no
        task, an act carrying no answer, and an answer to an id this host has never seen."""
        host = self.repository()
        for why, handed in {
            "no task named": json.dumps({"schema_version": 1, dispatch_port.RESUME: "",
                                         dispatch_port.ANSWER: "an answer"}),
            "no answer carried": json.dumps({"schema_version": 1,
                                             dispatch_port.RESUME: "c4-round-trip"}),
            "a task nobody dispatched": answer("c4-a-task-nobody-dispatched", "an answer"),
        }.items():
            with self.subTest(refusal=why):
                said = self.through_the_verb(host, handed)
                self.assertEqual(1, said.returncode, said.stdout + said.stderr)
                self.assertIn(f"[{dispatch_port.DispatchRefused.code}]", said.stderr)


if __name__ == "__main__":
    unittest.main()
