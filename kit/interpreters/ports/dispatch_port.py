"""Dispatch port -- the ONE place a worker is started, and the gate that stands there.

ADR-017 decision 1, made structural. Every refusal a dispatch can earn is taken HERE, in the port,
and not in any runtime's hook: a hook may CALL this, it may never replace it. That is the whole
reason the port exists. The packet gate that fires in one runtime because that runtime happens to
have a pre-spawn hook, and does not fire in another because it has none, is not a gate -- it is a
property of whoever happened to be driving, and the two runtimes would each be locally correct while
one of them silently let a malformed task through (Cardinal III, VIII).

So the order is fixed and every step of it is this module's:

  1. REFUSE, on pure reads, before a byte is written -- an unreadable packet, an incomplete one, a
     DISPATCH-ID that no enabled capability's adapter will answer to, a host that declares no way
     to isolate a worker at all, an id already used. Nothing has been leased, made or started, so a
     refused dispatch leaves the host exactly as it found it.
  2. LEASE the path the worker will write in -- the same hold mechanism, the same document, the
     same break-by-name door as the hold a run takes on a host. One writer per path (ADR-007,
     ADR-017 decision 6). A second lease implementation would be a second answer to 'is anyone
     already in there', and the two would agree until one of them was fixed.
  3. OPEN the task record, at `submitted`, BEFORE anything is started. A record written only at the
     end proves nothing about a dispatch that never reached the end -- and a worker started by a
     process that then died leaves a tree full of changes that reads exactly like finished work.
  4. ISOLATE: make the worker's own tree through the declared provider's argv.
  5. START the adapter's argv in that tree, with the record at `working`.
  6. CLOSE the record exactly once, with the state the ADAPTER's declaration says that ending
     meant, the artifacts read from the channels it declared, and the exit code recorded BESIDE the
     state, never in place of it.

What this module holds no opinion about: which intelligences exist, what any of them is called,
what a task should say, or which one a task should go to. The adapters are found by the CONTRACT
their document keeps and never by a list of publishers; the placeholders and channels an adapter
may name are the ones this port PROVIDES, and one it does not provide is refused BY NAME rather
than substituted with an empty string -- a worker started with a silently blank instruction is the
most expensive silence there is (Cardinal V).
"""

from __future__ import annotations

import json
import re
import subprocess
import uuid
from pathlib import Path

import admission
import declared
import ephemeral
import hostlock
from errors import KitError

#: The contracts this port selects on -- schema names, which are this kit's own vocabulary and
#: nobody's product. The SET of publishers stays open: every enabled capability that keeps the
#: contract is found, and a new intelligence is a new adapter directory (ADR-014, ADR-017 d.2).
ADAPTERS = {"validates": "dispatch-adapter"}
ADAPTER_LIST = "adapters"
PROVIDERS = {"validates": "workspace-provider"}
PROVIDER_LIST = "providers"

#: The two shapes this port reads and writes, by the name of the schema that is their one home.
PACKET = "dispatch-packet"
TASK = "task"

#: The A2A task states this port can put a record into. The vocabulary's one home is the `task`
#: schema; these are the names the interpreter uses to reach it, and `vocabulary` below refuses at
#: the first write if the two have parted -- so the pair cannot drift silently the way a constant
#: quietly restating an enum always eventually does. `input-required` is deliberately absent: no
#: adapter can produce it until the round-trip exists (C4), and an interpreter naming a state it
#: never writes would read as a capability this kit has.
SUBMITTED, WORKING, COMPLETED, FAILED = "submitted", "working", "completed", "failed"

#: Where a dispatch's records live, in the kit's own vocabulary. The PLACE they resolve to is the
#: manifest's ephemeral plane declaration and is never written here (Cardinal III).
HOME = "dispatch"
#: The name of the tree inside a task's own directory, so that the record, the lease and the tree
#: of one dispatch sit together under its id and a reader never has to correlate three places.
TREE = "tree"

#: What this port PROVIDES to a declaration. A placeholder or a channel outside these sets is
#: refused by name; widening either is this interpreter providing one more, never an enum edited
#: in a schema (Cardinal II).
PROVIDED = ("id", "instruction", "branch", "role", "workspace", "task", "artifact")
CHANNELS = ("stdout", "stderr", "file")

#: The name of the file this port PROVIDES for a worker that answers in a file rather than on a
#: stream. It sits in the task's own directory and NOT in the worker's tree, deliberately: an
#: answer is not a change to the repository, so it must not be judged as one on return, and it must
#: outlive a tree that is withdrawn. The port never writes it and never invents its content -- a
#: declared file channel that the worker left unwritten is recorded as a DECLARED ABSENCE and never
#: as an empty artifact, because an empty answer and an answer never given read identically.
ARTIFACT = "artifact"
FILE = "file"

_PLACEHOLDER = re.compile(r"\{([a-z_]+)\}")


class DispatchRefused(KitError):
    """A task was handed to the port that it will not start: unreadable, incomplete, routed to an
    adapter nobody declares, or already dispatched. Refused before anything is leased, made or
    started -- a gate that let the malformed through and reported it afterwards would be a report,
    not a gate."""

    code = "KIT0049"


class DispatchUnserved(KitError):
    """This host declares no way to carry a dispatch out -- no isolation for a worker, or more than
    one. Refused rather than defaulted: a worker with nowhere of its own to write would write into
    the host, which is the one thing the isolation exists to prevent."""

    code = "KIT0050"


class VocabularyDrift(KitError):
    """This interpreter names a task state the task schema does not declare, or the schema declares
    one this interpreter cannot name. A defect in the kit, refused at the first write rather than
    discovered later as a record nobody's reader recognises."""

    code = "KIT0051"


# -- what the host declares ---------------------------------------------------------------------
def vocabulary(ctx) -> list:
    """The task states, read from their ONE home. Called before the first write, so a schema and an
    interpreter that have parted are named as that, at the door, and never half-written."""
    states = list(ctx.manifest.schema(TASK)["properties"]["state"]["enum"])
    mine = {SUBMITTED, WORKING, COMPLETED, FAILED}
    unknown = sorted(mine - set(states))
    if unknown:
        raise VocabularyDrift(
            f"this port writes task state(s) {unknown}, which the {TASK!r} schema does not declare "
            f"(it declares {states}); one vocabulary has two homes and they have parted")
    return states


def adapters(ctx) -> dict:
    """Every dispatch adapter any enabled capability declares, by id. Found by the contract its
    document keeps -- so a third intelligence is a third adapter directory and nothing here moves.
    An id declared twice is refused by `declared`, which is where that refusal belongs."""
    return {row["id"]: row for row in declared.rules(ctx, ADAPTERS, ADAPTER_LIST)}


def provider(ctx) -> dict:
    """The one way this host isolates a worker. Zero and two are both refused, and for the same
    reason: 'the worker's own tree' must name exactly one place."""
    found = declared.rules(ctx, PROVIDERS, PROVIDER_LIST)
    if len(found) != 1:
        raise DispatchUnserved(
            f"this host has {len(found)} enabled declaration(s) of how a worker's isolated "
            f"workspace is made; exactly one is required. A dispatch with nowhere isolated to run "
            f"is not carried out in the host's own tree instead"
            + (f" (declared: {sorted(p['id'] for p in found)})" if found else ""))
    return found[0]


# -- the refusals -------------------------------------------------------------------------------
def packet_from(raw) -> dict:
    """A packet out of whatever a caller handed over. The parse lives HERE, not in the verb, so a
    hook that reads its own stdin and a caller that already holds a dict are refused by the same
    words: the gate is independent of who calls it."""
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        raise DispatchRefused(
            f"a dispatch packet is a JSON object; this caller handed over a "
            f"{type(raw).__name__}, which states no task at all")
    try:
        value = json.loads(raw) if raw.strip() else None
    except ValueError as exc:
        raise DispatchRefused(f"what was handed over is not readable as a dispatch packet -- {exc}; "
                              f"nothing states what task this is, so nothing can be started") from exc
    if not isinstance(value, dict):
        raise DispatchRefused(
            "what was handed over is not a dispatch packet: a task is an object stating its id, "
            "its route, its instruction and its branch, and no dispatch is started on less")
    return value


def complete(ctx, packet: dict) -> dict:
    """The packet, held to the shape that declares what a complete one is. Every missing part is
    named at once: a caller told about one absence at a time learns the contract by repetition."""
    errors = ctx.manifest.validate(packet, PACKET)
    if errors:
        raise DispatchRefused(
            "this dispatch packet is INCOMPLETE and no worker is started on it:\n  "
            + "\n  ".join(errors))
    return packet


def routed(ctx, packet: dict) -> dict:
    """The adapter this task's DISPATCH-ID was routed to -- or the refusal that it was not routed
    at all. A route naming an adapter nobody declares is a NAME WITH NO REFERENT (Cardinal VII):
    the dispatching side and this host agree perfectly on the word and disagree completely on what it
    points to, and the port chooses none on its behalf."""
    known = adapters(ctx)
    if not known:
        raise DispatchUnserved(
            "this host has taken no dispatch adapter, so there is no intelligence to route "
            f"{packet['id']!r} to. An adapter is a declaration a host takes; none was.")
    adapter = known.get(packet["route"])
    if adapter is None:
        raise DispatchRefused(
            f"dispatch {packet['id']!r} is routed to {packet['route']!r}, which no capability this "
            f"host has enabled declares (declared: {sorted(known)}). An unrouted id is not a task "
            f"this port guesses a destination for")
    return adapter


def accepted(ctx, raw) -> tuple:
    """Every refusal, taken together, on pure reads. Returns (packet, adapter, provider). A caller
    that wants to know whether a dispatch WOULD be accepted asks this and writes nothing."""
    vocabulary(ctx)
    packet = complete(ctx, packet_from(raw))
    adapter = routed(ctx, packet)
    _argv(adapter["starts"]["argv"], {name: "" for name in PROVIDED}, where=f"adapter {adapter['id']!r}")
    for part in adapter["returns"]:
        if part["from"] not in CHANNELS:
            raise DispatchUnserved(
                f"adapter {adapter['id']!r} returns its artifact {part['name']!r} from "
                f"{part['from']!r}, a channel this port does not provide (it provides "
                f"{list(CHANNELS)}); an artifact read from nowhere would be a fabricated one")
    isolation = provider(ctx)
    if not admission.declares(isolation):
        raise DispatchUnserved(
            f"the workspace provider {isolation['id']!r} states how a worker's tree is MADE and not "
            f"how it says what changed in it, so nothing could judge what this worker returned. "
            f"A runtime that cannot be stopped mid-write is admitted on RETURN or not at all "
            f"(ADR-017 decision 5); no worker is started where that reading is impossible")
    return packet, adapter, isolation


# -- the places ---------------------------------------------------------------------------------
def home(ctx, dispatch_id: str, leaf: str) -> str:
    return ephemeral.place(ctx, f"{HOME}/{dispatch_id}/{leaf}")


def _argv(parts, values: dict, where: str) -> list:
    """A declared argv with this port's values in it. A placeholder the port does not provide is
    refused BY NAME; one whose value this task does not carry is refused as that -- never filled
    with an empty string, which is how a worker comes to be started with no instruction at all."""
    filled = []
    for part in parts:
        for name in _PLACEHOLDER.findall(part):
            if name not in PROVIDED:
                raise DispatchUnserved(
                    f"{where} names the placeholder {{{name}}}, which this port does not provide "
                    f"(it provides {[f'{{{p}}}' for p in PROVIDED]})")
            if values.get(name) is None:
                raise DispatchRefused(
                    f"{where} is started with {{{name}}}, and this packet states no {name}. A "
                    f"worker is not started with that word left blank")
            part = part.replace("{" + name + "}", str(values[name]))
        filled.append(part)
    return filled


# -- the act ------------------------------------------------------------------------------------
def dispatch(ctx, args, raw, *, run=None) -> int:
    """Refuse, lease, open, isolate, start, close. The whole of a dispatch, in one place.

    `run` is the process runner, injected so that the act can be exercised without the port
    reaching for a boundary of its own; it defaults to the real one. Nothing else about this
    function is substitutable, deliberately: the gate is not a policy a caller may bring.
    """
    packet, adapter, workspaces = accepted(ctx, raw)
    identity = packet["id"]
    lease_rel = home(ctx, identity, "lease")
    task_rel = home(ctx, identity, "task.json")
    tree_rel = home(ctx, identity, TREE)
    if ctx.workspace.exists(task_rel):
        raise DispatchRefused(
            f"dispatch {identity!r} has already been dispatched on this host: its record stands at "
            f"{task_rel}. A DISPATCH-ID names one task, and a second dispatch under the same name "
            f"would overwrite the only account of what the first one did")
    if ctx.workspace.exists(tree_rel):
        raise DispatchRefused(
            f"{tree_rel} already exists, and a worker is given a tree that was MADE for it, never "
            f"one that was found: a found tree is somebody else's work with nobody leasing it")

    now = ctx.clock.now()
    if getattr(args, "plan", False):
        print(f"dispatch: {identity} would be leased at {lease_rel}, recorded at {task_rel}, "
              f"isolated at {tree_rel} on branch {packet['branch']}, and started through the "
              f"adapter {adapter['id']} -- nothing was written")
        return 0

    lease = hostlock.take(ctx, lease_rel, run_id=uuid.uuid4().hex, verb=getattr(args, "verb", HOME),
                          now=now, break_by=getattr(args, "break_lock", None), registers=False)
    record = _Record.opened(ctx, task_rel, packet=packet, adapter=adapter["id"],
                            workspace=tree_rel, lease=lease_rel, now=now)
    code, message = 1, None
    try:
        code, message = _carried_out(ctx, packet, adapter, workspaces, record,
                                     tree_rel, run or _ran)
        return code
    except admission.NotAdmitted as refused:
        # The record is already CLOSED, carrying the worker's own ending and the verdict on what it
        # wrote. Re-closing it here would overwrite both with this refusal, and the account of what
        # the worker actually did would be replaced by the account of what the host did about it.
        code, message = refused.exit_code, str(refused)
        raise
    except KitError as refusal:
        code, message = refusal.exit_code, str(refusal)
        record.close(FAILED, code, message)
        raise
    except BaseException as unforeseen:  # noqa: BLE001 -- re-raised; only the record is added
        record.close(FAILED, 1, f"{type(unforeseen).__name__}: {unforeseen}")
        raise
    finally:
        lease.release(code, message)


def _carried_out(ctx, packet, adapter, workspaces, record, tree_rel, run) -> tuple:
    root = ctx.workspace.path(".")
    tree = ctx.workspace.path(tree_rel)
    provider_where = f"workspace provider {workspaces['id']!r}"
    made = _argv(workspaces["isolate"]["argv"],
                 {"id": packet["id"], "branch": packet["branch"], "workspace": tree_rel,
                  "instruction": None, "role": None, "task": None, ARTIFACT: None},
                 where=provider_where)
    isolated = run(made, cwd=root, stdin=None)
    if isolated.returncode != 0:
        why = (isolated.stderr or isolated.stdout or "").strip() or f"exit {isolated.returncode}"
        record.close(FAILED, isolated.returncode,
                     f"the worker's isolated workspace could not be made -- {why}")
        print(f"dispatch: {packet['id']} FAILED before it started -- {why}")
        return 1, why

    answer = ctx.workspace.path(home(ctx, packet["id"], ARTIFACT))
    values = {"id": packet["id"], "branch": packet["branch"], "instruction": packet["instruction"],
              "role": packet.get("role"), "workspace": tree.as_posix(),
              "task": ctx.workspace.path(record.rel).as_posix(), ARTIFACT: answer.as_posix()}
    where = f"adapter {adapter['id']!r}"
    argv = _argv(adapter["starts"]["argv"], values, where=where)
    stdin = _argv([adapter["starts"]["stdin"]], values, where=where)[0] \
        if "stdin" in adapter["starts"] else None
    record.move(WORKING, started_at=ctx.clock.now())
    worker = run(argv, cwd=tree, stdin=stdin)

    artifacts = [_artifact(part, worker, answer) for part in adapter["returns"]]
    ended = COMPLETED if worker.returncode == adapter["completed_on"]["exit"] else FAILED

    # The other half of the isolation (ADR-017 decision 5). It is read whatever the worker's own
    # ending was: a worker that failed still wrote, and a tree nobody judged because its process
    # returned non-zero is exactly the unverified change the isolation exists to catch.
    verdict = admission.of(ctx, workspaces, tree,
                           _argv(workspaces[admission.RETURNED][admission.ARGV],
                                 {"id": packet["id"], "branch": packet["branch"],
                                  "workspace": tree.as_posix(), "instruction": None, "role": None,
                                  "task": None, ARTIFACT: None},
                                 where=provider_where),
                           run)
    record.close(ended, worker.returncode, artifacts=artifacts, admission=verdict)
    print(f"dispatch: {packet['id']} {ended} through {adapter['id']} in {tree_rel} "
          f"(exit {worker.returncode}); {len(artifacts)} artifact(s) recorded at {record.rel}")
    print(admission.said(verdict))
    if verdict["verdict"] != admission.ADMITTED:
        raise admission.NotAdmitted(
            f"dispatch {packet['id']!r} ended {ended}, and what its worker left in {tree_rel} is "
            f"NOT ADMITTED to this host. The verdict, every path it judged and every refusal stand "
            f"at {record.rel}")
    return (0 if ended == COMPLETED else 1), (None if ended == COMPLETED else f"worker exit {worker.returncode}")


def _artifact(part: dict, worker, answer) -> dict:
    """One declared artifact, read from the channel the adapter named -- or a DECLARED ABSENCE in
    the place its text would have been. A worker that promised a file and wrote none has produced
    nothing, and nothing is what is recorded."""
    found = {"name": part["name"], "from": part["from"],
             **({"media_type": part["media_type"]} if "media_type" in part else {})}
    if part["from"] == FILE:
        if not answer.is_file():
            return dict(found, absent=f"this adapter returns {part['name']!r} in the file this port "
                                      f"provided at {answer.as_posix()}, and the worker wrote none")
        try:
            return dict(found, text=answer.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError) as exc:
            return dict(found, absent=f"the file this port provided for {part['name']!r} could not "
                                      f"be read back -- {exc}")
    return dict(found, text=(worker.stdout if part["from"] == "stdout" else worker.stderr) or "")


def _ran(argv, cwd, stdin):
    """The one boundary this port crosses to start anything. No shell: the declaration is a fixed
    argv and stays one. A program that is absent is a REFUSAL, never a worker that quietly did
    nothing -- what is not observed is declared, never fabricated."""
    try:
        return subprocess.run([str(part) for part in argv], cwd=str(cwd), input=stdin,
                              capture_output=True, text=True)
    except OSError as exc:
        raise DispatchUnserved(
            f"{argv[0]!r} could not be run on this machine -- {exc}. What a declaration names is a "
            f"claim about somebody else's software until it is measured; this is that measurement, "
            f"and it says the program is not here") from exc


class _Record:
    """One task record, held open and rewritten at every transition -- the same life a run receipt
    and an install journal have, for the same reason. Every transition is FLUSHED: batching the
    writes for the end would make this document exactly the thing it exists to refute."""

    __slots__ = ("ctx", "workspace", "rel", "value")

    def __init__(self, ctx, workspace, rel: str, value: dict) -> None:
        self.ctx, self.workspace, self.rel, self.value = ctx, workspace, rel, value

    @staticmethod
    def opened(ctx, rel: str, *, packet, adapter, workspace, lease, now) -> "_Record":
        value = {
            "schema_version": ctx.manifest.version_of(TASK),
            "id": packet["id"],
            "state": SUBMITTED,
            "packet": packet,
            "adapter": adapter,
            "workspace": workspace,
            "branch": packet["branch"],
            "lease": lease,
            "opened_at": now,
            "kit_version": ctx.manifest.version,
            "boundary": ctx.boundary(),
        }
        record = _Record(ctx, ephemeral.scope(ctx), rel, value)
        record._flush("as this dispatch opens it")
        return record

    def _flush(self, moment: str) -> None:
        errors = self.ctx.manifest.validate(self.value, TASK)
        if errors:
            raise VocabularyDrift(f"{self.rel} {moment} does not honour the kit schema {TASK!r}, "
                                  f"and a task record that is not one is not written:\n  "
                                  + "\n  ".join(errors))
        self.workspace.write_json(self.rel, self.value)

    def move(self, state: str, **fields) -> None:
        self.value.update(state=state, **fields)
        self._flush(f"as it moves to {state}")

    def close(self, state: str, code: int, message: str = None, artifacts=None,
              admission=None) -> None:
        """The end, stated in the same act as its moment. A state without a moment goes on
        certifying for as long as it sits there and cannot be contradicted."""
        self.value.update(state=state, ended_at=self.ctx.clock.now(), exit_code=code)
        if artifacts is not None:
            self.value["artifacts"] = artifacts
        if admission is not None:
            self.value["admission"] = admission
        if message:
            self.value["status_message"] = message
        self._flush("as this dispatch closes it")
