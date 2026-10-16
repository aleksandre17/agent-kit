"""Dispatching -- what a dispatch IS, read without starting anything (ADR-017).

The dispatch port (`ports/dispatch_port.py`) is the ONE place a worker is started. Everything a
dispatch is made of that can be known WITHOUT starting one lives here, in the core, where more than
one reader may reach it: the vocabulary of task states (whose one home is the `task` schema), the
contracts an adapter and an isolation provider keep, the refusals a packet earns on pure reads
before a byte is written, and the places a dispatch's records occupy. The port composes these into
the acts; `returns` reads the records they leave; a verb hands a packet in. None of them reaches
the port to learn what a dispatch is.

What this module holds no opinion about: which intelligences exist, what any of them is called,
what a task should say, which one a task should go to, how one signals that it needs input, or how
one is re-entered. Adapters are found by the CONTRACT their document keeps, never by a list of
publishers; a placeholder or a channel an adapter names that this kit does not PROVIDE is refused
BY NAME rather than substituted with an empty string (Cardinal V).
"""


from __future__ import annotations

import json
import re

import admission
import declared
import ephemeral
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
            "deliverable", ANSWER, REENTRY, "model", "effort", "budget_usd", "max_turns")
#: What a route cell decides for the worker it routes (ADR-024): the model, effort and caps an adapter's
#: `options` tell its product, the stop condition the port enforces, and where a failure escalates.
ROUTED = ("task_class", "actor", "model", "effort", "budget_usd", "max_turns", "timeout_s", "escalates_to")
#: The actor a route dispatches. `script` work is a verb, `human` work a door: neither starts a worker.
DISPATCHED = "model"
CLASSES = ({"validates": "task-classes"}, "classes")
CHANNELS = ("stdout", "stderr", "file")

#: The name of the file this port PROVIDES for a worker that answers in a file rather than on a
#: stream. It sits in the task's own directory and NOT in the worker's tree, deliberately: an
#: answer is not a change to the repository, so it must not be judged as one on return, and it must
#: outlive a tree that is withdrawn. The port never writes it and never invents its content -- a
#: declared file channel that the worker left unwritten is recorded as a DECLARED ABSENCE and never
#: as an empty artifact, because an empty answer and an answer never given read identically.
ARTIFACT = "artifact"
FILE = "file"

PLACEHOLDER = re.compile(r"\{([a-z_]+)\}")


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
    argv(adapter["starts"]["argv"], blank, where=where)
    for option in adapter["starts"].get("options", []) + (adapter.get(RESUMES) or {}).get("options", []):
        if option["when"] not in PROVIDED:
            raise DispatchUnserved(f"{where} declares an option for {option['when']!r}, which this port "
                                   f"does not provide (it provides {list(PROVIDED)})")
        argv(option["argv"], blank, where=f"{where} (option {option['when']})")
    returns = {part["name"]: part for part in adapter["returns"]}
    for part in adapter["returns"]:
        if part["from"] not in CHANNELS:
            raise DispatchUnserved(
                f"{where} returns its artifact {part['name']!r} from "
                f"{part['from']!r}, a channel this port does not provide (it provides "
                f"{list(CHANNELS)}); an artifact read from nowhere would be a fabricated one")
    if RESUMES in adapter:
        argv(adapter[RESUMES]["argv"], blank, where=f"{where} ({RESUMES})")
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
                 and c["reversibility"] == packet["reversibility"]
                 and (not packet.get("task_class") or c.get("task_class") in (None, packet["task_class"]))), None)
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
    classes = {row["id"]: row for row in declared.rules(ctx, *CLASSES)}
    named_class = cell.get("task_class") or packet.get("task_class")
    if named_class and named_class not in classes:
        wrong.append(f"the task class {named_class!r} is declared by no task-class vocabulary "
                     f"(declared: {sorted(classes)})")
    actor = cell.get("actor") or (classes.get(named_class) or {}).get("actor", DISPATCHED)
    if actor != DISPATCHED:
        wrong.append(f"the cell's work is carried out by a {actor}, never a dispatched model: run the "
                     f"verb or script, or walk the owner's door -- a token spent on it buys nothing")
    if wrong:
        raise DispatchRefused(
            f"dispatch {packet['id']!r} falls in the cell {cell['id']!r} of this host's route table, "
            f"and does not honour it:\n  " + "\n  ".join(wrong))
    return {"cell": cell["id"], "says": cell.get("says", ""),
            **{k: cell[k] for k in ROUTED if k in cell}, "actor": actor}


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


def argv(parts, values: dict, where: str) -> list:
    """A declared argv with this port's values in it. A placeholder the port does not provide is
    refused BY NAME; one whose value this task does not carry is refused as that -- never filled
    with an empty string, which is how a worker comes to be started with no instruction at all."""
    filled = []
    for part in parts:
        for name in PLACEHOLDER.findall(part):
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


#: The OpenTelemetry GenAI semantic-convention attributes a run record carries (names only; the
#: conventions are their one home). The operation is this port's: it invokes an agent.
OPERATION, PROVIDER, REQUEST_MODEL = "gen_ai.operation.name", "gen_ai.provider.name", "gen_ai.request.model"
INVOKE_AGENT = "invoke_agent"


def _dotted(value, key: str):
    for part in key.split("."):
        if part == "@keys":
            value = next(iter(value), None) if isinstance(value, dict) else None
        elif isinstance(value, dict):
            value = value.get(part)
        else:
            return None
    return value


def telemetry(adapter: dict, artifacts: list, route: dict) -> dict:
    """The run's cost and identity, read from what the adapter DECLARES its product reports -- never
    sniffed out of prose, never estimated. Absent where the product reports nothing."""
    found = {OPERATION: INVOKE_AGENT}
    if route.get("model"):
        found[REQUEST_MODEL] = route["model"]
    usage = adapter.get("usage")
    if usage is None:
        return {**found, "reported": False}
    found[PROVIDER] = usage["provider"]
    text = next((a.get("text") for a in artifacts if a["name"] == usage["from"]), None)
    document = None
    try:
        if text and usage.get("jsonl"):
            lines = [json.loads(line) for line in text.splitlines() if line.strip().startswith("{")]
            document = next((row for row in reversed(lines)
                             if all(row.get(k) == v for k, v in (usage.get("where") or {}).items())), None)
        elif text:
            document = json.loads(text)
    except ValueError:
        document = None
    if document is None:
        return {**found, "reported": False}
    found.update({name: _dotted(document, key) for name, key in usage["fields"].items()
                  if _dotted(document, key) is not None})
    return {**found, "reported": True}


def provides(**given) -> dict:
    """Every value this port provides, with the ones this act carries filled in and every other one
    DECLARED ABSENT rather than left out. `_argv` refuses a placeholder whose value is None by name
    and refuses a missing one by the same words, so the two readings must not be allowed to part:
    an absence stated here is the same absence a declaration meets."""
    return dict({name: None for name in PROVIDED}, **given)


