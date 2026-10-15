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

A worker that cannot proceed has a sixth ending, and it is the whole of slice C4: it ASKS. An
adapter may declare `asks` -- the ending its product uses when it needs input, and the DECLARED
artifact its question comes back in -- and then the record is not closed at all. It is moved to
`input-required`, holding the question, the token that re-enters that same worker, and, when the
adapter declares no way back in, the sentence saying so at the moment it was asked. A question is
READ FROM A CHANNEL THE ADAPTER DECLARED and is never sniffed out of a worker's prose: a port that
recognised a question by its shape would be deciding, on a product's behalf, what one looks like.

So this port serves TWO acts through one door, and which act a document is, the DOCUMENT says:

  7. RESUME: an act naming a task that stands at `input-required` and carrying an operator's
     answer. The same lease, the same record, the same tree, and the adapter's own `resumes` argv
     with `{answer}` and `{reentry}` in it -- the same worker re-entered, never a second one
     started on a longer instruction. An adapter that declares no `resumes` makes this refuse BY
     NAME, saying which adapter lacks it, because a task nobody can answer must say so rather than
     look like one nobody has answered yet.
  8. JUDGE AGAIN, whatever the ending: a worker that asked a question also WROTE, and a resumed one
     wrote twice. Admission is a reading of one RETURN and never a verdict a task keeps, so every
     return is judged -- including the one that only asked.

What this module holds no opinion about: which intelligences exist, what any of them is called,
what a task should say, which one a task should go to, how one signals that it needs input, or how
one is re-entered. The adapters are found by the CONTRACT their document keeps and never by a list
of publishers; the placeholders and channels an adapter may name are the ones this port PROVIDES,
and one it does not provide is refused BY NAME rather than substituted with an empty string -- a
worker started with a silently blank instruction is the most expensive silence there is
(Cardinal V).
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
import readings
from errors import KitError

#: The contracts this port selects on -- schema names, which are this kit's own vocabulary and
#: nobody's product. The SET of publishers stays open: every enabled capability that keeps the
#: contract is found, and a new intelligence is a new adapter directory (ADR-014, ADR-017 d.2).
ADAPTERS = {"validates": "dispatch-adapter"}
ADAPTER_LIST = "adapters"
PROVIDERS = {"validates": "workspace-provider"}
PROVIDER_LIST = "providers"
#: The host's route table (ADR-022 decision 3): its cells and its verification profiles, found by the
#: contract their document keeps -- shipped or authored, never by a path spelled here.
ROUTES = {"validates": "route-table"}
CELL_LIST, PROFILE_LIST = "cells", "profiles"
#: The kind a returned artifact may declare it CARRIES: the worker's structured return.
RETURN = "dispatch-return"

#: The two shapes this port reads and writes, by the name of the schema that is their one home.
PACKET = "dispatch-packet"
TASK = "task"

#: The A2A task states this port can put a record into. The vocabulary's one home is the `task`
#: schema; these are the names the interpreter uses to reach it, and `vocabulary` below refuses at
#: the first write if the two have parted -- so the pair cannot drift silently the way a constant
#: quietly restating an enum always eventually does.
SUBMITTED, WORKING, INPUT_REQUIRED = "submitted", "working", "input-required"
COMPLETED, FAILED = "completed", "failed"

#: What this port EXITS with when a dispatch ends at `input-required`. Not 0 and not 1: the task did
#: not complete and nothing about it failed, and a caller that could only tell those two
#: apart would either report a waiting worker as done or raise an incident about a question. It is
#: 3 is the code this kit already gives a DECLARED STATE that is not a failure (a stalled install
#: exits with it), and a waiting worker is exactly that kind of ending.
WAITING = 3

#: The blocks an adapter may declare for the round-trip, by the names its schema gives them. Both
#: are OPTIONAL and independent: an intelligence that never asks declares neither and nothing about
#: it changes, and an adapter that can ask but not be re-entered declares only `asks` -- which is a
#: real and honest state, recorded on the task as unresumable at the moment the question was read,
#: rather than a task that merely looks unanswered.
ASKS, RESUMES = "asks", "resumes"

#: The two acts this port serves through one door, and the field that tells them apart. A packet
#: STARTS a worker; a resume act names the task it answers and carries the operator's answer back
#: into the worker already standing at it. The discriminant is a field of the DOCUMENT -- the
#: caller declares which act it is handing over and this port reads that declaration. A mouth that
#: decided it from a flag of its own would put the distinction in whoever happened to be driving,
#: and the act would then mean something different through a hook than through the verb.
RESUME, ANSWER, ANSWERED_BY = "resume", "answer", "by"
#: What a resumed record keeps of the exchange, in A2A's own vocabulary: `agent` is the worker's
#: question, `user` the operator's answer. Adopted whole rather than renamed -- a private word for
#: a solved concept is a second home (ADR-017 decision 3).
HISTORY, AGENT, OPERATOR = "history", "agent", "user"
#: The two things an `asks` block names a carrier for: the worker's QUESTION, and the token that
#: re-enters that same worker. The second is optional -- an intelligence resumed by where its work
#: stands rather than by a name for its session declares no carrier and names no `{reentry}`.
QUESTION, REENTRY = "question", "reentry"

#: Where a dispatch's records live, in the kit's own vocabulary. The PLACE they resolve to is the
#: manifest's ephemeral plane declaration and is never written here (Cardinal III).
HOME = "dispatch"
#: The name of the tree inside a task's own directory, so that the record, the lease and the tree
#: of one dispatch sit together under its id and a reader never has to correlate three places.
TREE = "tree"

#: What this port PROVIDES to a declaration. A placeholder or a channel outside these sets is
#: refused by name; widening either is this interpreter providing one more, never an enum edited
#: in a schema (Cardinal II).
PROVIDED = ("id", "instruction", "branch", "role", "workspace", "task", "artifact",
            "deliverable", ANSWER, REENTRY)
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
    mine = {SUBMITTED, WORKING, INPUT_REQUIRED, COMPLETED, FAILED}
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


def coherent(adapter: dict) -> dict:
    """One adapter, held to what this port provides -- every block of it, before anything is
    leased. A declaration is read WHOLE at the door: an adapter whose resume argv names a
    placeholder nobody provides would be found out only at the moment an operator answered, which
    is the worst moment in the round-trip to discover it."""
    where = f"adapter {adapter['id']!r}"
    blank = {name: "" for name in PROVIDED}
    _argv(adapter["starts"]["argv"], blank, where=where)
    returns = {part["name"]: part for part in adapter["returns"]}
    for part in adapter["returns"]:
        if part["from"] not in CHANNELS:
            raise DispatchUnserved(
                f"{where} returns its artifact {part['name']!r} from "
                f"{part['from']!r}, a channel this port does not provide (it provides "
                f"{list(CHANNELS)}); an artifact read from nowhere would be a fabricated one")
    if RESUMES in adapter:
        _argv(adapter[RESUMES]["argv"], blank, where=f"{where} ({RESUMES})")
    asks = adapter.get(ASKS)
    if asks is None:
        return adapter
    if asks["exit"] == adapter["completed_on"]["exit"]:
        raise DispatchUnserved(
            f"{where} says its worker both FINISHED and NEEDS INPUT on exit {asks['exit']}. One "
            f"ending cannot mean two states: whichever this port then wrote would be right half "
            f"the time and unfalsifiable the rest")
    for role in (QUESTION, REENTRY):
        named = asks.get(role)
        if named is not None and named not in returns:
            raise DispatchUnserved(
                f"{where} says its worker's {role} comes back as the artifact {named!r}, which it "
                f"does not declare in `returns` (it declares {sorted(returns)}). A question read "
                f"from a channel nobody declared would be a question this port invented")
    if asks.get(REENTRY) is not None and asks[REENTRY] == asks[QUESTION]:
        raise DispatchUnserved(
            f"{where} reads both its worker's question and the token that re-enters that worker "
            f"out of the one artifact {asks[QUESTION]!r}. One text cannot be both without this "
            f"port parsing it, and a port that parsed a product's answer would hold that product's "
            f"grammar")
    return adapter


def judgeable(isolation: dict) -> dict:
    """The provider, held to the one thing every return of a worker's tree needs: a way for the
    tree to say what changed in it. Asked before a worker is started AND before a standing one is
    re-entered, because a resumed worker writes too and a return nobody could judge is the same
    silence whichever turn produced it."""
    if not admission.declares(isolation):
        raise DispatchUnserved(
            f"the workspace provider {isolation['id']!r} states how a worker's tree is MADE and not "
            f"how it says what changed in it, so nothing could judge what this worker returned. "
            f"A runtime that cannot be stopped mid-write is admitted on RETURN or not at all "
            f"(ADR-017 decision 5); no worker is started where that reading is impossible")
    return isolation


def route(ctx, packet: dict) -> dict:
    """The packet judged against the host's route table (ADR-022 decision 3) -- the cell it falls in,
    or the statement that the host declares none. Every mismatch is named at once: the cell a task
    belongs to is the host's declaration, and a packet that disagrees with it is not routed by the
    port choosing one side.

    With no cell declared the port carries the packet and judges nothing by its routing facts, and
    the record SAYS so: a route nobody declared is not a route that was checked."""
    cells = declared.rules(ctx, ROUTES, CELL_LIST)
    profiles = {row["id"]: row for row in declared.rules(ctx, ROUTES, PROFILE_LIST)}
    named = packet.get("profile")
    if named is not None and named not in profiles:
        raise DispatchRefused(
            f"dispatch {packet['id']!r} names the verification profile {named!r}, which this host's "
            f"route table does not declare (declared: {sorted(profiles)}). A profile is the only thing "
            f"this port runs on a task's behalf, and it runs only one the host named")
    if not cells:
        return {"cell": None, "says": "this host declares no route table cell, so no routing fact of "
                                      "this packet was judged"}
    cell = next((c for c in cells if c["decision_density"] == packet["decision_density"]
                 and c["reversibility"] == packet["reversibility"]), None)
    if cell is None:
        raise DispatchRefused(
            f"dispatch {packet['id']!r} states decision_density={packet['decision_density']!r} and "
            f"reversibility={packet['reversibility']!r}, and no cell of this host's route table holds "
            f"that pair (cells: {[(c['decision_density'], c['reversibility']) for c in cells]})")
    wrong = []
    if cell.get("role") and packet.get("role") != cell["role"]:
        wrong.append(f"the cell routes to the role {cell['role']!r} and the packet names "
                     f"{packet.get('role')!r}")
    if cell.get("adapter") and packet["route"] != cell["adapter"]:
        wrong.append(f"the cell routes to the adapter {cell['adapter']!r} and the packet to "
                     f"{packet['route']!r}")
    if cell.get("requires_profile") and named is None:
        wrong.append("the cell requires a verification profile and the packet names none")
    for limit, given in (cell.get("budget") or {}).items():
        stated = (packet.get("budget") or {}).get(limit)
        if stated is None or stated > given:
            wrong.append(f"the cell caps {limit} at {given} and the packet states {stated!r}")
    if cell.get("ceiling_chars") and len(packet["instruction"]) > cell["ceiling_chars"]:
        wrong.append(f"the instruction is {len(packet['instruction'])} characters and the cell's "
                     f"ceiling is {cell['ceiling_chars']} -- an inlined wall is re-billed on every call")
    if wrong:
        raise DispatchRefused(
            f"dispatch {packet['id']!r} falls in the cell {cell['id']!r} of this host's route table, "
            f"and does not honour it:\n  " + "\n  ".join(wrong))
    return {"cell": cell["id"], "says": cell.get("says", "")}


def grounded(ctx, packet: dict) -> None:
    """Every ground the packet cites BY KEY, read back from the ledger before a worker starts. A ground
    that no longer holds refuses the dispatch: a brief built on a stale premise burns the whole run,
    and the worker that would correctly refuse it has already been paid for (ADR-022 decision 4)."""
    stale = []
    for row in packet.get("ground", []):
        if "key" in row:
            try:
                readings.get(ctx, row["key"])
            except readings.GroundMiss as miss:
                stale.append(str(miss))
    if stale:
        raise DispatchRefused(f"dispatch {packet['id']!r} cites ground that does not hold:\n  "
                              + "\n  ".join(stale))


def accepted(ctx, raw) -> tuple:
    """Every refusal, taken together, on pure reads. Returns (packet, adapter, provider). A caller
    that wants to know whether a dispatch WOULD be accepted asks this and writes nothing."""
    vocabulary(ctx)
    packet = complete(ctx, packet_from(raw))
    grounded(ctx, packet)
    route(ctx, packet)
    return packet, coherent(routed(ctx, packet)), judgeable(provider(ctx))


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


def _provides(**given) -> dict:
    """Every value this port provides, with the ones this act carries filled in and every other one
    DECLARED ABSENT rather than left out. `_argv` refuses a placeholder whose value is None by name
    and refuses a missing one by the same words, so the two readings must not be allowed to part:
    an absence stated here is the same absence a declaration meets."""
    return dict({name: None for name in PROVIDED}, **given)


# -- the acts -----------------------------------------------------------------------------------
def dispatch(ctx, args, raw, *, run=None) -> int:
    """The one door, and the two acts behind it: STARTING a worker, and RESUMING one that asked.

    Which act this is, the DOCUMENT says -- a packet states a route and an instruction, a resume
    act names the task it answers. The distinction is read here and never taken from a flag: a
    mouth that decided it would make the act mean one thing through a hook and another through the
    verb, and the gate would again be a property of whoever was driving.

    `run` is the process runner, injected so that either act can be exercised without the port
    reaching for a boundary of its own; it defaults to the real one. Nothing else about this
    function is substitutable, deliberately: the gate is not a policy a caller may bring.
    """
    handed = packet_from(raw)
    if RESUME in handed:
        return _resumed(ctx, args, handed, run or _ran)
    return _started(ctx, args, handed, run or _ran)


def _started(ctx, args, handed, run) -> int:
    """Refuse, lease, open, isolate, start, close -- or park at `input-required`, if the worker
    ended by asking. The whole of a first dispatch, in one place."""
    packet, adapter, workspaces = accepted(ctx, handed)
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
    record.value["route"] = route(ctx, packet)
    return _held(lease, record, lambda: _isolated_then_started(
        ctx, packet, adapter, workspaces, record, tree_rel, run))


def _resumed(ctx, args, act, run) -> int:
    """An operator's answer, carried back into the worker that asked for it.

    The SAME worker: the same record, the same lease path, the same tree, re-entered through the
    adapter's own declared way in. Nothing here re-states the task -- a resume that started a
    second worker on a longer instruction would be a different worker agreeing with the first one's
    name, which is the whole of Cardinal VII in one act.
    """
    vocabulary(ctx)
    identity = act.get(RESUME)
    if not isinstance(identity, str) or not identity.strip():
        raise DispatchRefused(
            f"this act carries {RESUME!r} and names no task with it: an answer with no question "
            f"named is not carried anywhere, and no worker is re-entered on a guess")
    answer = act.get(ANSWER)
    if not isinstance(answer, str) or not answer.strip():
        raise DispatchRefused(
            f"resuming {identity!r} states no {ANSWER!r}. A worker that asked is re-entered with an "
            f"operator's answer, never with that word left blank -- a blank answer and no answer "
            f"read identically to whatever is waiting on it")
    task_rel = home(ctx, identity, "task.json")
    if not ctx.workspace.exists(task_rel):
        raise DispatchRefused(
            f"this host holds no dispatch called {identity!r}: nothing stands at {task_rel}. A task "
            f"is resumed where it was left, and a record that is not here was not left here")
    record = _Record.reopened(ctx, task_rel)
    standing = record.value["state"]
    if standing != INPUT_REQUIRED:
        raise DispatchRefused(
            f"dispatch {identity!r} stands at {standing!r} as of {record.moment()}, and only a task "
            f"at {INPUT_REQUIRED!r} has a worker waiting on an answer. Nothing was re-entered, and "
            f"the record at {task_rel} is untouched")
    known = adapters(ctx)
    adapter = known.get(record.value["adapter"])
    if adapter is None:
        raise DispatchRefused(
            f"dispatch {identity!r} was started through the adapter {record.value['adapter']!r}, "
            f"which no capability this host has enabled declares any more (declared: "
            f"{sorted(known)}). A worker is re-entered through the declaration it was started "
            f"through, and that declaration is no longer on this host")
    if RESUMES not in adapter:
        raise DispatchUnserved(
            f"the adapter {adapter['id']!r} declares {ASKS!r} and no {RESUMES!r}: it states how its "
            f"worker asks a question and not how one is re-entered, so this host has no way to "
            f"carry an answer back into it. The question stands at {task_rel} and is unanswerable "
            f"until that adapter declares one -- which is a declaration, not an edit to this port")
    coherent(adapter)
    workspaces = judgeable(provider(ctx))
    tree_rel = record.value["workspace"]
    if not ctx.workspace.exists(tree_rel):
        raise DispatchRefused(
            f"the tree dispatch {identity!r} was given at {tree_rel} is no longer here, and a "
            f"worker is re-entered where it was left. What it had done stood in that tree; an "
            f"answer carried into a tree made afresh would be answering a question nobody asked")

    now = ctx.clock.now()
    if getattr(args, "plan", False):
        print(f"resume: {identity} would be leased again at {record.value['lease']}, its answer "
              f"recorded at {task_rel}, and the worker standing in {tree_rel} re-entered through "
              f"the adapter {adapter['id']} -- nothing was written")
        return 0

    lease = hostlock.take(ctx, record.value["lease"], run_id=uuid.uuid4().hex,
                          verb=getattr(args, "verb", HOME), now=now,
                          break_by=getattr(args, "break_lock", None), registers=False)
    # The answer is written into the record BEFORE the worker is re-entered, for the reason the
    # record itself is opened before the worker is started: an answer recorded only once the worker
    # came back says nothing about a resume that never got there, and the one question a reader of
    # a half-finished task must be able to settle is what this worker was told.
    record.answered(now, answer, by=act.get(ANSWERED_BY))
    packet = record.value["packet"]
    values = _values(ctx, packet, record, tree_rel, answer=answer, reentry=record.reentry())
    return _held(lease, record, lambda: _turn(
        ctx, packet, adapter, workspaces, record, tree_rel, RESUMES, values, run,
        moment="resumed_at"))


def _held(lease, record, work) -> int:
    """One act, under one lease, with one record. The endings are the same for both acts, so they
    are stated once: a lease is released with what happened, and a record is closed FAILED only
    where nothing else has closed it."""
    code, message = 1, None
    try:
        code, message = work()
        return code
    except admission.NotAdmitted as refused:
        # The record already carries the worker's own ending and the verdict on what it wrote.
        # Re-closing it here would overwrite both with this refusal, and the account of what the
        # worker actually did would be replaced by the account of what the host did about it.
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


def _values(ctx, packet, record, tree_rel, **carried) -> dict:
    """What this port provides to a declaration for one turn of one worker. The task's own words
    are the same on every turn -- it is the same task -- and what a resume adds is exactly the
    answer and the way back in."""
    return _provides(
        id=packet["id"], branch=packet["branch"], instruction=packet["instruction"],
        role=packet.get("role"), deliverable=packet.get("deliverable"),
        workspace=ctx.workspace.path(tree_rel).as_posix(),
        task=ctx.workspace.path(record.rel).as_posix(),
        artifact=ctx.workspace.path(home(ctx, packet["id"], ARTIFACT)).as_posix(), **carried)


def _isolated_then_started(ctx, packet, adapter, workspaces, record, tree_rel, run) -> tuple:
    root = ctx.workspace.path(".")
    made = _argv(workspaces["isolate"]["argv"],
                 _provides(id=packet["id"], branch=packet["branch"], workspace=tree_rel),
                 where=f"workspace provider {workspaces['id']!r}")
    isolated = run(made, cwd=root, stdin=None)
    if isolated.returncode != 0:
        why = (isolated.stderr or isolated.stdout or "").strip() or f"exit {isolated.returncode}"
        record.close(FAILED, isolated.returncode,
                     f"the worker's isolated workspace could not be made -- {why}")
        print(f"dispatch: {packet['id']} FAILED before it started -- {why}")
        return 1, why
    return _turn(ctx, packet, adapter, workspaces, record, tree_rel, "starts",
                 _values(ctx, packet, record, tree_rel), run, moment="started_at")


def _turn(ctx, packet, adapter, workspaces, record, tree_rel, block, values, run, *, moment) -> tuple:
    """ONE turn of one worker -- its first, or a resumed one. The two differ in exactly two things:
    the declared argv that enters the worker, and the moment that is recorded. Everything after the
    process returns is identical and deliberately so -- the artifacts are read from the same
    declared channels, what the tree came back with meets the same admission, and the ending is
    read from the same declaration. A second path for the second turn would be a second answer to
    what this worker produced, and the two would agree until one of them was fixed."""
    tree = ctx.workspace.path(tree_rel)
    where = f"adapter {adapter['id']!r} ({block})"
    declaration = adapter[block]
    argv = _argv(declaration["argv"], values, where=where)
    stdin = _argv([declaration["stdin"]], values, where=where)[0] \
        if "stdin" in declaration else None
    record.move(WORKING, **{moment: ctx.clock.now()})
    worker = run(argv, cwd=tree, stdin=stdin)

    artifacts = [_artifact(part, worker, ctx.workspace.path(home(ctx, packet["id"], ARTIFACT)))
                 for part in adapter["returns"]]

    # The other half of the isolation (ADR-017 decision 5). It is read whatever the worker's own
    # ending was: a worker that failed still wrote, one that only asked a question still wrote, and
    # a tree nobody judged because its process returned non-zero is exactly the unverified change
    # the isolation exists to catch.
    verdict = admission.of(ctx, workspaces, tree,
                           _argv(workspaces[admission.RETURNED][admission.ARGV],
                                 _provides(id=packet["id"], branch=packet["branch"],
                                           workspace=tree.as_posix()),
                                 where=f"workspace provider {workspaces['id']!r}"),
                           run)

    asks = adapter.get(ASKS)
    if asks is not None and worker.returncode == asks["exit"]:
        turn = _question(adapter, asks, artifacts, ctx.clock.now())
        record.asked(worker.returncode, turn, artifacts=artifacts, admission=verdict)
        ended, code, message = INPUT_REQUIRED, WAITING, "waiting on an answer"
        print(f"dispatch: {packet['id']} {INPUT_REQUIRED} through {adapter['id']} in {tree_rel} "
              f"(exit {worker.returncode}); the worker is standing, its question and everything "
              f"needed to re-enter it are at {record.rel}")
        print(_asked(turn))
    else:
        ended = COMPLETED if worker.returncode == adapter["completed_on"]["exit"] else FAILED
        message = None if ended == COMPLETED else f"worker exit {worker.returncode}"
        stated = None
        returned, why = _returned(ctx, packet, adapter, artifacts)
        if returned is not None:
            record.value["return"] = returned
        if why and ended == COMPLETED:
            ended, message, stated = FAILED, why, why
        if ended == COMPLETED and packet.get("profile"):
            checked = _verified(ctx, packet, tree, run)
            record.value["verification"] = checked
            if not checked["passed"]:
                stated = (f"the deliverable did not pass the verification profile "
                          f"{packet['profile']!r} (exit {checked['exit']})")
                ended, message = FAILED, stated
        record.close(ended, worker.returncode, stated, artifacts=artifacts, admission=verdict)
        code = 0 if ended == COMPLETED else 1
        print(f"dispatch: {packet['id']} {ended} through {adapter['id']} in {tree_rel} "
              f"(exit {worker.returncode}); {len(artifacts)} artifact(s) recorded at {record.rel}")
    print(admission.said(verdict))
    if verdict["verdict"] != admission.ADMITTED:
        raise admission.NotAdmitted(
            f"dispatch {packet['id']!r} ended {ended}, and what its worker left in {tree_rel} is "
            f"NOT ADMITTED to this host. The verdict, every path it judged and every refusal stand "
            f"at {record.rel}")
    return code, message


def _returned(ctx, packet, adapter, artifacts) -> tuple:
    """(the worker's structured return, why it is not acceptable) -- read from the artifact the
    ADAPTER declared carries it, and from nothing else. An adapter that declares no carrier returns no
    structure, and that is printed rather than read as an empty return. A declared carrier that is
    absent, unreadable or does not honour the return schema closes the task as failed, by name: a
    worker that promised to say what it cost and said nothing has not finished."""
    carried = [part for part in adapter["returns"] if part.get("carries") == RETURN]
    if not carried:
        print(f"dispatch: {packet['id']} -- the adapter {adapter['id']!r} declares no artifact that "
              f"carries a {RETURN!r}, so no economy, finding or brief grade comes back from it")
        return None, None
    read = next(a for a in artifacts if a["name"] == carried[0]["name"])
    if read.get("absent"):
        return None, f"the declared {RETURN!r} is absent -- {read['absent']}"
    try:
        value = json.loads(read.get("text") or "")
    except ValueError as exc:
        return None, f"the declared {RETURN!r} is not readable -- {exc}"
    errors = ctx.manifest.validate(value, RETURN)
    if errors:
        return value, f"the declared {RETURN!r} does not honour its schema: " + "; ".join(errors)
    if value.get("id") != packet["id"]:
        return value, f"the {RETURN!r} answers {value.get('id')!r}, not this dispatch {packet['id']!r}"
    return value, None


def _verified(ctx, packet, tree, run) -> dict:
    """The host's NAMED verification profile, run in the worker's tree on return. Its argv is the
    host's declaration -- never text from the packet -- and its result is recorded whatever it was."""
    profile = {row["id"]: row for row in declared.rules(ctx, ROUTES, PROFILE_LIST)}[packet["profile"]]
    done = run(profile["argv"], cwd=tree, stdin=None, timeout=profile["timeout_s"])
    said = ((done.stdout or "") + (done.stderr or "")).strip().splitlines()
    return {"profile": profile["id"], "exit": done.returncode, "passed": done.returncode == 0,
            "tail": said[-20:]}


def _question(adapter: dict, asks: dict, artifacts: list, at: str) -> dict:
    """The worker's turn of the exchange, built from the channels the ADAPTER declared and from
    nothing else. What is not there is DECLARED absent in the place it would have been: an empty
    question is not a short one, a missing re-entry token is not an empty string, and an adapter
    with no way back in is said so HERE, at the moment the question was read, rather than left to
    be discovered by an operator whose answer is then refused."""
    read = {part["name"]: part for part in artifacts}
    asked = read[asks[QUESTION]]
    turn = {"role": AGENT, "at": at}
    if (asked.get("text") or "").strip():
        turn["text"] = asked["text"]
    else:
        turn["absent"] = asked.get("absent") or (
            f"this worker signalled that it needs input and the artifact {asks[QUESTION]!r} it "
            f"declares its question in came back empty; an empty question and a question never "
            f"asked read identically, and neither one can be answered")
    if REENTRY in asks:
        token = read[asks[REENTRY]]
        if (token.get("text") or "").strip():
            # Carried WITHOUT the newline the stream it came on adds: this value crosses into an
            # argv, where two sides agree on the name of a session and disagree on its bytes
            # (Cardinal VII). The artifact itself is kept verbatim -- the record is never edited to
            # make a later act convenient.
            turn[REENTRY] = token["text"].strip()
        else:
            turn["reentry_absent"] = token.get("absent") or (
                f"this adapter says the token that re-enters its worker comes back as the artifact "
                f"{asks[REENTRY]!r}, and that artifact came back empty")
    if RESUMES not in adapter:
        turn["unresumable"] = (
            f"the adapter {adapter['id']!r} declares no {RESUMES!r}: this host can read this "
            f"question and has no declared way to carry an answer back into the worker that asked "
            f"it. The worker is standing and nothing on this host will re-enter it")
    return turn


def _asked(turn: dict) -> str:
    """The question in one line, for whoever is watching the dispatch rather than reading records."""
    parts = [f"question: {turn['text']}"] if "text" in turn else [
        f"question: NOT READ -- {turn['absent']}"]
    if turn.get("reentry_absent"):
        parts.append(f"  re-entry: NOT READ -- {turn['reentry_absent']}")
    if turn.get("unresumable"):
        parts.append(f"  UNRESUMABLE -- {turn['unresumable']}")
    return "\n".join(parts)


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


def _ran(argv, cwd, stdin, timeout=None):
    """The one boundary this port crosses to start anything. No shell: the declaration is a fixed
    argv and stays one. A program that is absent is a REFUSAL, never a worker that quietly did
    nothing -- what is not observed is declared, never fabricated."""
    try:
        return subprocess.run([str(part) for part in argv], cwd=str(cwd), input=stdin,
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        # A declared bound that passed is an ending, stated: never a hang, never a silent success.
        return subprocess.CompletedProcess(exc.cmd, 124, exc.stdout or "", f"timed out after {timeout}s")
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

    @staticmethod
    def reopened(ctx, rel: str) -> "_Record":
        """A record that is already standing, read back so the SAME document goes on being
        rewritten. A resume that opened a second record would leave two accounts of one task, and
        each would be internally correct."""
        try:
            value = json.loads(ctx.workspace.path(rel).read_text(encoding="utf-8"))
        except (OSError, ValueError, UnicodeDecodeError) as exc:
            raise DispatchRefused(
                f"the task record at {rel} cannot be read back -- {exc}. What a worker was told and "
                f"what state it is in are that document's to say; nothing is re-entered on a "
                f"record this host cannot read") from exc
        return _Record(ctx, ephemeral.scope(ctx), rel, value)

    def moment(self) -> str:
        """WHEN this record last said anything -- so a state is never reported without the moment
        it was taken at. A state with no moment goes on certifying for as long as it sits there."""
        turns = self.value.get(HISTORY) or []
        return (self.value.get("ended_at") or (turns[-1]["at"] if turns else None)
                or self.value.get("started_at") or self.value["opened_at"])

    def reentry(self):
        """The way back into the worker standing at this record: the token of the LAST question it
        asked, or None. A worker resumed twice hands back a new one each time, and the earliest
        token would re-enter a turn that is already over."""
        for turn in reversed(self.value.get(HISTORY) or []):
            if turn["role"] == AGENT and turn.get(REENTRY):
                return turn[REENTRY]
        return None

    def asked(self, code: int, turn: dict, artifacts, admission) -> None:
        """The worker stopped and asked. NOT an ending: no `ended_at` is written, because the task
        has not ended and a moment written here would say it had. What the worker produced on the
        way to asking, and the verdict on what it left in its tree, are recorded exactly as they
        are at any other return."""
        self.value.update(state=INPUT_REQUIRED, exit_code=code, artifacts=artifacts,
                          admission=admission)
        self.value.setdefault(HISTORY, []).append(turn)
        self._flush("as this worker asks for input")

    def answered(self, at: str, text: str, by: str = None) -> None:
        """The operator's turn, written before the worker is re-entered with it."""
        self.value.setdefault(HISTORY, []).append(
            dict({"role": OPERATOR, "at": at, "text": text}, **({"by": by} if by else {})))
        self._flush("as an answer is carried back into it")

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
