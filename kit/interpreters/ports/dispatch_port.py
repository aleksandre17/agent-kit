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
import subprocess
import uuid

import admission
import declared
import dispatching
import hostlock
import taskrecord
from errors import KitError

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
    handed = dispatching.packet_from(raw)
    if dispatching.RESUME in handed:
        return _resumed(ctx, args, handed, run or _ran)
    return _started(ctx, args, handed, run or _ran)


def _started(ctx, args, handed, run) -> int:
    """Refuse, lease, open, isolate, start, close -- or park at `input-required`, if the worker
    ended by asking. The whole of a first dispatch, in one place."""
    packet, adapter, workspaces = dispatching.accepted(ctx, handed)
    identity = packet["id"]
    lease_rel = dispatching.home(ctx, identity, "lease")
    task_rel = dispatching.home(ctx, identity, "task.json")
    tree_rel = dispatching.home(ctx, identity, dispatching.TREE)
    if ctx.workspace.exists(task_rel):
        raise dispatching.DispatchRefused(
            f"dispatch {identity!r} has already been dispatched on this host: its record stands at "
            f"{task_rel}. A DISPATCH-ID names one task, and a second dispatch under the same name "
            f"would overwrite the only account of what the first one did")
    if ctx.workspace.exists(tree_rel):
        raise dispatching.DispatchRefused(
            f"{tree_rel} already exists, and a worker is given a tree that was MADE for it, never "
            f"one that was found: a found tree is somebody else's work with nobody leasing it")

    now = ctx.clock.now()
    if getattr(args, "plan", False):
        print(f"dispatch: {identity} would be leased at {lease_rel}, recorded at {task_rel}, "
              f"isolated at {tree_rel} on branch {packet['branch']}, and started through the "
              f"adapter {adapter['id']} -- nothing was written")
        return 0

    lease = hostlock.take(ctx, lease_rel, run_id=uuid.uuid4().hex, verb=getattr(args, "verb", dispatching.HOME),
                          now=now, break_by=getattr(args, "break_lock", None), registers=False)
    record = taskrecord.Record.opened(ctx, task_rel, packet=packet, adapter=adapter["id"],
                            workspace=tree_rel, lease=lease_rel, now=now)
    record.value["route"] = dispatching.route(ctx, packet)
    return _held(lease, record, lambda: _isolated_then_started(
        ctx, packet, adapter, workspaces, record, tree_rel, run))


def _resumed(ctx, args, act, run) -> int:
    """An operator's answer, carried back into the worker that asked for it.

    The SAME worker: the same record, the same lease path, the same tree, re-entered through the
    adapter's own declared way in. Nothing here re-states the task -- a resume that started a
    second worker on a longer instruction would be a different worker agreeing with the first one's
    name, which is the whole of Cardinal VII in one act.
    """
    dispatching.vocabulary(ctx)
    identity = act.get(dispatching.RESUME)
    if not isinstance(identity, str) or not identity.strip():
        raise dispatching.DispatchRefused(
            f"this act carries {dispatching.RESUME!r} and names no task with it: an answer with no question "
            f"named is not carried anywhere, and no worker is re-entered on a guess")
    answer = act.get(dispatching.ANSWER)
    if not isinstance(answer, str) or not answer.strip():
        raise dispatching.DispatchRefused(
            f"resuming {identity!r} states no {dispatching.ANSWER!r}. A worker that asked is re-entered with an "
            f"operator's answer, never with that word left blank -- a blank answer and no answer "
            f"read identically to whatever is waiting on it")
    task_rel = dispatching.home(ctx, identity, "task.json")
    if not ctx.workspace.exists(task_rel):
        raise dispatching.DispatchRefused(
            f"this host holds no dispatch called {identity!r}: nothing stands at {task_rel}. A task "
            f"is resumed where it was left, and a record that is not here was not left here")
    record = taskrecord.Record.reopened(ctx, task_rel)
    standing = record.value["state"]
    if standing != dispatching.INPUT_REQUIRED:
        raise dispatching.DispatchRefused(
            f"dispatch {identity!r} stands at {standing!r} as of {record.moment()}, and only a task "
            f"at {dispatching.INPUT_REQUIRED!r} has a worker waiting on an answer. Nothing was re-entered, and "
            f"the record at {task_rel} is untouched")
    known = dispatching.adapters(ctx)
    adapter = known.get(record.value["adapter"])
    if adapter is None:
        raise dispatching.DispatchRefused(
            f"dispatch {identity!r} was started through the adapter {record.value['adapter']!r}, "
            f"which no capability this host has enabled declares any more (declared: "
            f"{sorted(known)}). A worker is re-entered through the declaration it was started "
            f"through, and that declaration is no longer on this host")
    if dispatching.RESUMES not in adapter:
        raise dispatching.DispatchUnserved(
            f"the adapter {adapter['id']!r} declares {dispatching.ASKS!r} and no {dispatching.RESUMES!r}: it states how its "
            f"worker asks a question and not how one is re-entered, so this host has no way to "
            f"carry an answer back into it. The question stands at {task_rel} and is unanswerable "
            f"until that adapter declares one -- which is a declaration, not an edit to this port")
    dispatching.coherent(adapter)
    workspaces = dispatching.judgeable(dispatching.provider(ctx))
    tree_rel = record.value["workspace"]
    if not ctx.workspace.exists(tree_rel):
        raise dispatching.DispatchRefused(
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
                          verb=getattr(args, "verb", dispatching.HOME), now=now,
                          break_by=getattr(args, "break_lock", None), registers=False)
    # The answer is written into the record BEFORE the worker is re-entered, for the reason the
    # record itself is opened before the worker is started: an answer recorded only once the worker
    # came back says nothing about a resume that never got there, and the one question a reader of
    # a half-finished task must be able to settle is what this worker was told.
    record.answered(now, answer, by=act.get(dispatching.ANSWERED_BY))
    packet = record.value["packet"]
    values = _values(ctx, packet, record, tree_rel, answer=answer, reentry=record.reentry())
    return _held(lease, record, lambda: _turn(
        ctx, packet, adapter, workspaces, record, tree_rel, dispatching.RESUMES, values, run,
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
        record.close(dispatching.FAILED, code, message)
        raise
    except BaseException as unforeseen:  # noqa: BLE001 -- re-raised; only the record is added
        record.close(dispatching.FAILED, 1, f"{type(unforeseen).__name__}: {unforeseen}")
        raise
    finally:
        lease.release(code, message)


def _values(ctx, packet, record, tree_rel, **carried) -> dict:
    """What this port provides to a declaration for one turn of one worker. The task's own words
    are the same on every turn -- it is the same task -- and what a resume adds is exactly the
    answer and the way back in."""
    routed = record.value.get("route") or {}
    return dispatching.provides(
        **{k: routed[k] for k in ("model", "effort", "budget_usd", "max_turns") if k in routed},
        id=packet["id"], branch=packet["branch"], instruction=packet["instruction"],
        role=packet.get("role"), deliverable=packet.get("deliverable"),
        workspace=ctx.workspace.path(tree_rel).as_posix(),
        task=ctx.workspace.path(record.rel).as_posix(),
        artifact=ctx.workspace.path(dispatching.home(ctx, packet["id"], dispatching.ARTIFACT)).as_posix(), **carried)


def _isolated_then_started(ctx, packet, adapter, workspaces, record, tree_rel, run) -> tuple:
    root = ctx.workspace.path(".")
    made = dispatching.argv(workspaces["isolate"]["argv"],
                 dispatching.provides(id=packet["id"], branch=packet["branch"], workspace=tree_rel),
                 where=f"workspace provider {workspaces['id']!r}")
    isolated = run(made, cwd=root, stdin=None)
    if isolated.returncode != 0:
        why = (isolated.stderr or isolated.stdout or "").strip() or f"exit {isolated.returncode}"
        record.close(dispatching.FAILED, isolated.returncode,
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
    # An option enters the argv only when the route gave its value: the route decides the model, the
    # effort and the caps, the adapter says how its product is told (ADR-024).
    parts = declaration["argv"] + [p for option in declaration.get("options", [])
                                   if values.get(option["when"]) is not None for p in option["argv"]]
    argv = dispatching.argv(parts, values, where=where)
    stdin = dispatching.argv([declaration["stdin"]], values, where=where)[0] \
        if "stdin" in declaration else None
    record.move(dispatching.WORKING, **{moment: ctx.clock.now()})
    # The STOP CONDITION every product honours: a run past its declared wall time ends as a recorded
    # failure (exit 124), never a silent retry.
    stop = (record.value.get("route") or {}).get("timeout_s")
    worker = run(argv, cwd=tree, stdin=stdin, **({"timeout": stop} if stop else {}))

    artifacts = [_artifact(part, worker, ctx.workspace.path(dispatching.home(ctx, packet["id"], dispatching.ARTIFACT)))
                 for part in adapter["returns"]]

    # The other half of the isolation (ADR-017 decision 5). It is read whatever the worker's own
    # ending was: a worker that failed still wrote, one that only asked a question still wrote, and
    # a tree nobody judged because its process returned non-zero is exactly the unverified change
    # the isolation exists to catch.
    verdict = admission.of(ctx, workspaces, tree,
                           dispatching.argv(workspaces[admission.RETURNED][admission.ARGV],
                                 dispatching.provides(id=packet["id"], branch=packet["branch"],
                                           workspace=tree.as_posix()),
                                 where=f"workspace provider {workspaces['id']!r}"),
                           run)

    asks = adapter.get(dispatching.ASKS)
    if asks is not None and worker.returncode == asks["exit"]:
        turn = _question(adapter, asks, artifacts, ctx.clock.now())
        record.asked(worker.returncode, turn, artifacts=artifacts, admission=verdict)
        ended, code, message = dispatching.INPUT_REQUIRED, dispatching.WAITING, "waiting on an answer"
        print(f"dispatch: {packet['id']} {dispatching.INPUT_REQUIRED} through {adapter['id']} in {tree_rel} "
              f"(exit {worker.returncode}); the worker is standing, its question and everything "
              f"needed to re-enter it are at {record.rel}")
        print(_asked(turn))
    else:
        ended = dispatching.COMPLETED if worker.returncode == adapter["completed_on"]["exit"] else dispatching.FAILED
        message = None if ended == dispatching.COMPLETED else f"worker exit {worker.returncode}"
        stated = None
        returned, why = _returned(ctx, packet, adapter, artifacts)
        if returned is not None:
            record.value["return"] = returned
        if why and ended == dispatching.COMPLETED:
            ended, message, stated = dispatching.FAILED, why, why
        if ended == dispatching.COMPLETED and packet.get("profile"):
            checked = _verified(ctx, packet, tree, run)
            record.value["verification"] = checked
            if not checked["passed"]:
                stated = (f"the deliverable did not pass the verification profile "
                          f"{packet['profile']!r} (exit {checked['exit']})")
                ended, message = dispatching.FAILED, stated
        escalates = (record.value.get("route") or {}).get("escalates_to")
        if escalates and (ended != dispatching.COMPLETED or verdict["verdict"] != admission.ADMITTED):
            # A declared signal fired: the record names where the next run belongs. Nothing is started
            # here -- an escalation is a new decision, never a silent retry on a stronger mind.
            record.value["escalate"] = {"to": escalates, "because": message or "its return was not admitted"}
            print(f"dispatch: {packet['id']} escalates to the route cell {escalates!r} -- run it there")
        record.close(ended, worker.returncode, stated, artifacts=artifacts, admission=verdict)
        code = 0 if ended == dispatching.COMPLETED else 1
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
    carried = [part for part in adapter["returns"] if part.get("carries") == dispatching.RETURN]
    if not carried:
        print(f"dispatch: {packet['id']} -- the adapter {adapter['id']!r} declares no artifact that "
              f"carries a {dispatching.RETURN!r}, so no economy, finding or brief grade comes back from it")
        return None, None
    read = next(a for a in artifacts if a["name"] == carried[0]["name"])
    if read.get("absent"):
        return None, f"the declared {dispatching.RETURN!r} is absent -- {read['absent']}"
    try:
        value = json.loads(read.get("text") or "")
    except ValueError as exc:
        return None, f"the declared {dispatching.RETURN!r} is not readable -- {exc}"
    errors = ctx.manifest.validate(value, dispatching.RETURN)
    if errors:
        return value, f"the declared {dispatching.RETURN!r} does not honour its schema: " + "; ".join(errors)
    if value.get("id") != packet["id"]:
        return value, f"the {dispatching.RETURN!r} answers {value.get('id')!r}, not this dispatch {packet['id']!r}"
    return value, None


def _verified(ctx, packet, tree, run) -> dict:
    """The host's NAMED verification profile, run in the worker's tree on return. Its argv is the
    host's declaration -- never text from the packet -- and its result is recorded whatever it was."""
    profile = {row["id"]: row for row in declared.rules(ctx, dispatching.ROUTES, dispatching.PROFILE_LIST)}[packet["profile"]]
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
    asked = read[asks[dispatching.QUESTION]]
    turn = {"role": dispatching.AGENT, "at": at}
    if (asked.get("text") or "").strip():
        turn["text"] = asked["text"]
    else:
        turn["absent"] = asked.get("absent") or (
            f"this worker signalled that it needs input and the artifact {asks[dispatching.QUESTION]!r} it "
            f"declares its question in came back empty; an empty question and a question never "
            f"asked read identically, and neither one can be answered")
    if dispatching.REENTRY in asks:
        token = read[asks[dispatching.REENTRY]]
        if (token.get("text") or "").strip():
            # Carried WITHOUT the newline the stream it came on adds: this value crosses into an
            # argv, where two sides agree on the name of a session and disagree on its bytes
            # (Cardinal VII). The artifact itself is kept verbatim -- the record is never edited to
            # make a later act convenient.
            turn[dispatching.REENTRY] = token["text"].strip()
        else:
            turn["reentry_absent"] = token.get("absent") or (
                f"this adapter says the token that re-enters its worker comes back as the artifact "
                f"{asks[dispatching.REENTRY]!r}, and that artifact came back empty")
    if dispatching.RESUMES not in adapter:
        turn["unresumable"] = (
            f"the adapter {adapter['id']!r} declares no {dispatching.RESUMES!r}: this host can read this "
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
    if part["from"] == dispatching.FILE:
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
        raise dispatching.DispatchUnserved(
            f"{argv[0]!r} could not be run on this machine -- {exc}. What a declaration names is a "
            f"claim about somebody else's software until it is measured; this is that measurement, "
            f"and it says the program is not here") from exc


