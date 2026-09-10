"""init -- measure the host, resolve what it CHOSE, draft the answer, and only then mutate.

This verb holds the one door in the whole design where a human stands. It measures, classifies,
composes and DRAFTS an answer; the owner approves; only an approved answer is installed against.
An init whose approval never came leaves a declared, dated state on disk and exits with its own
code -- a stalled install is a state, never a hung process and never a silent proceed.

Two things are separated here on purpose:

  * WHAT IS TRUE of the host -- measured, and never argued with.
  * WHAT THIS HOST CHOSE -- the answers file, in the host's own plane. Once it exists it is the
    source of truth for the set and the kit never overwrites it. The one exception is the
    approval itself, which is the OWNER writing through the kit, and is recorded with a name.

Everything written was declared by a capability, and it is written through a workspace scoped to
exactly that capability's declared targets. Re-running is not a re-generation -- BINDING is
created only if absent -- so a second `init` on an approved host is, by construction, render+check.

Install modes are an OPEN registry keyed by the mode a declaration states, and each mode has TWO
halves: FORESEE, which says what would happen, and APPLY, which does it. The apply never decides;
it is handed the foreseen disposition. That is what makes a plan incapable of drifting from its
own application -- not care and not review, but the fact that there is only one decision.
"""

from __future__ import annotations

import adoption
import check as check_verb
import collection
import doors
import estate as estate_module
import plan as plan_module
import render as render_verb
from context import SCHEMA_VERSION
from errors import KitError, PendingApproval

SUMMARY = "measure, choose, draft the answer, seed, vendor, render, check"
MUTATES = True
REQUIRES_APPROVED_HOST = False


class InstallError(KitError):
    """A declaration named an install mode this interpreter does not know, a selection that
    contradicts host truth, or a written file that does not honour its own schema."""


# -- foresee: what WOULD happen, decided exactly once -----------------------------------------
def _once(ws, item, state):
    """Created if absent, never re-applied. The host owns it from then on."""
    return "keep" if ws.exists(item["target"]) else "create"


def _always(ws, item, state):
    """Framework payload: replaced wholesale, never edited downstream."""
    return "replace" if ws.exists(item["target"]) else "create"


def _answer(ws, item, state):
    """The answers file is create-once like any host truth -- except for the approval, which is
    the owner's own act passing through the kit, and is therefore a PLANNED replace rather than
    an edit nobody saw coming."""
    if not ws.exists(item["target"]):
        return "create"
    return "replace" if state["approving_draft"] else "keep"


# -- apply: the foreseen disposition, carried out ---------------------------------------------
def _mode_reading(ctx, ws, item, state):
    """The measured environment. Written once; a later reading is compared, never imposed."""
    ws.write_json(item["target"], state["reading"])


def _mode_declaration(ctx, ws, item, state):
    """What this host has decided: its set, its status, and who accepted it. A prior answer is
    carried forward field by field -- approving a draft must not silently re-answer it."""
    prior = state["existing"] or {}
    answer = {
        "schema_version": SCHEMA_VERSION,
        "status": "accepted" if state["approver"] else "draft",
        "kit_version": ctx.manifest.version,
        "capabilities": prior.get("capabilities") or sorted(c.id for c in state["enabled"]),
        "unavailable": prior.get("unavailable", state["unavailable"]),
        "drafted_at": prior.get("drafted_at", state["reading"]["taken_at"]),
    }
    if state["approver"]:
        answer["signed_by"] = state["approver"]
        answer["signed_at"] = state["reading"]["taken_at"]
    ws.write_json(item["target"], answer)


def _mode_seed(ctx, ws, item, state):
    """Created once if absent, never re-applied, never diffed."""
    ws.write_text(item["target"], ctx.manifest.payload_text(item["source"]))


def _mode_vendor(ctx, ws, item, state):
    ws.write_text(item["target"], ctx.manifest.payload_text(item["source"]))


def _mode_space(ctx, ws, item, state):
    """A place the HOST authors into, owned by the capability that declared it. The kit creates
    it and puts nothing in it: seeding an example would be the kit authoring the host's content,
    and an empty space is an honest declared state, not a missing one."""
    ws.make_dir(item["target"])


#: mode -> (phase, foresee, apply). The `answer` phase is the ONLY thing an unapproved host may
#: write: it is the draft the owner is being asked to accept, and nothing moves until they do.
INSTALL_MODES = {
    "reading": ("install", _once, _mode_reading),
    "declaration": ("answer", _answer, _mode_declaration),
    "seed": ("install", _once, _mode_seed),
    "vendor": ("install", _always, _mode_vendor),
    "space": ("install", _once, _mode_space),
    "projection": ("render", None, None),
    "estate": ("record", None, None),
}

#: The phases the install loop itself carries out. A phase named here and nowhere else belongs to
#: a LATER step of the run: `render` recomputes the projections, `record` measures what this host
#: was given once everything else has landed. A record taken in the middle of the writes would be
#: a reading of a half-installed host, stating a moment that described nothing.
INSTALLED_PHASES = ("answer", "install")


def _mode_of(capability, item):
    mode = item["mode"]
    if mode not in INSTALL_MODES:
        raise InstallError(
            f"capability {capability.id!r} declares install mode {mode!r}; "
            f"registered modes are {sorted(INSTALL_MODES)}"
        )
    return INSTALL_MODES[mode]


def _install_plan(ctx, enabled, state) -> list:
    """The write set an install would produce, as data. While the host is unapproved this is
    exactly the ANSWER -- the draft the owner is asked to accept -- and nothing else."""
    writes = []
    for capability in enabled:
        scoped = state["scopes"][capability.id]
        for item in capability.installs:
            phase, foresee, _apply_fn = _mode_of(capability, item)
            if phase not in INSTALLED_PHASES or (phase != "answer" and not state["approved"]):
                continue
            # A disposition this run has ALREADY DECIDED outranks the mode's own foresight, and
            # this is not a precedence ladder: the mode's rule is what a foresight can say with no
            # record to read -- `vendor` replaces because nothing could tell it whether the host
            # had touched the file. Where a reconciliation HAS read the record, it has answered
            # the same question with more evidence, and the answer arrives here as data so that
            # foresee and apply remain ONE decision across both verbs.
            writes.append(plan_module.Write(
                (ctx.decided.get(item["target"]) or {}).get("file")
                or foresee(scoped, item, state),
                item["class"], item["mode"], capability.id, item["target"], item))
    return writes


def _record_plan(ctx, enabled, signed_by, writes=()) -> list:
    """The estate write, foreseen -- and foreseen by MEASURING, not by assuming a run writes.

    Empty where this kit declares no estate at all: a kit that records nothing says so by planning
    nothing, rather than leaving an operator to notice an absence. Where a record already stands
    and this run gives nothing, the disposition is `keep`, because the moment that document states
    is the moment this host received those bytes and no run may move it over a delivery that did
    not happen.

    Whether this run gives anything is read from the OTHER writes it has already foreseen, and
    never from the disk in front of it. A record planned by measuring what is there NOW would
    foresee `keep` and then find itself replaced by the very writes it was planned beside -- the
    plan and the apply disagreeing about the one file whose job is to say what happened.
    """
    item = ctx.install_of_mode("estate", required=False)
    if item is None:
        return []
    owner = next(c for c in enabled for i in c.installs if i["target"] == item["target"])
    recorded = estate_module.read(ctx)
    entries = estate_module.rows(ctx, enabled, estate_module.stewardship(ctx),
                                 recorded, ctx.decided, writes)
    if not ctx.workspace.exists(item["target"]):
        disposition = "create"
    elif estate_module.restates(recorded, ctx, entries, signed_by):
        disposition = "keep"
    else:
        disposition = "replace"
    return [plan_module.Write(disposition, item["class"], item["mode"],
                              owner.id, item["target"], item)]


def _signed(args, existing):
    """Whose name is on the writes: the approver walking the door now, or the one already
    recorded. Never nobody -- a record of what a machine did to a host, with no name on it,
    cannot be contradicted by anyone."""
    return args.approve or (existing or {}).get(doors.SIGNED_BY)


def _apply(ctx, state, writes) -> None:
    """Carry out a plan. It decides nothing: the disposition arrived with the entry."""
    for write in writes:
        scoped = state["scopes"][write.capability]
        if write.disposition != "keep":
            _mode_of(state["by_id"][write.capability], write.item)[2](ctx, scoped, write.item, state)
        print(f"  {write.accomplished:<9}  {write.target}")
        _validate(ctx, write.item)


def _validate(ctx, item) -> None:
    """What was just written, read back through its own declaration and held to its schema.

    The reading is DELEGATED, never repeated here. Whether a declared target is one document or a
    space of many records was decided once, by the shape the declaration states, and `collection`
    is where that decision lives. An installer that answered it a second time -- by reading every
    target as a file -- would stay locally correct right up to the moment it opened a DIRECTORY,
    which is a state no schema can describe and no message can explain.
    """
    if item.get("validates"):
        collection.read(ctx, item)


def _chosen(ctx, args, candidates, existing):
    """Where the host's set comes from -- and it comes from exactly ONE place at a time.

    Before a host has answered, the request on the command line is the choice. Afterwards the
    answers file IS the choice, and a flag that would contradict it is refused rather than
    quietly obeyed or quietly ignored: two homes for one truth, and the drift is guaranteed.
    """
    if existing is None:
        return ctx.select(candidates, args.enable, args.disable)
    if args.enable is not None or args.disable is not None:
        raise InstallError(
            f"this host has already declared its set as {existing['capabilities']} in "
            f"{ctx.install_of_mode('declaration')['target']}; --enable/--disable author that "
            f"file and may not contradict it. Edit the answers file, then run init again."
        )
    wanted = set(existing["capabilities"])
    return [c for c in candidates if c.id in wanted]


def run(ctx, args) -> int:
    # The BOUNDARY, measured before anything is trusted and before anything else is reported. A
    # host inside a host makes every reading below ambiguous about which law governs a path, so it
    # is the CAUSE and everything downstream of it is a consequence -- and a run that prints only
    # the consequence sends the reader looking for a defect that was never there. Measured only at
    # first contact, because a host that has already answered was measured when it did.
    if adoption.at_first_contact(ctx):
        adoption.require_unenclosed(ctx)

    reading = ctx.take_reading()
    candidates, unavailable, blocked = ctx.classify(reading["facts"])

    # The reading is REPORTED before the set is composed, and therefore before any refusal the
    # composition may raise. A measured absence is the cause; an unmet provision downstream of it
    # is the consequence -- and a run that prints only the consequence leaves the reader looking
    # for a declaration defect that is really a host they never measured.
    print(f"reading taken at {reading['taken_at']} on {reading['boundary']['os']}")
    for fact, value in reading["facts"].items():
        print(f"  fact  {fact} = {value}")
    for entry in unavailable:
        print(f"  unavailable  {entry['id']}: {entry['reason']}")

    existing = ctx.host_answers(required=False)
    chosen = _chosen(ctx, args, candidates, existing)
    for capability in candidates:
        if capability not in chosen:
            print(f"  disabled  {capability.id}: not in this host's declared set")
            for provision in capability.raw.get("provides", []):
                blocked[provision] = (
                    f"it is provided by {capability.id}, which this host chose to disable"
                )

    enabled = ctx.compose(chosen, blocked)

    # FIRST CONTACT. A host that has never answered is a host this kit has never installed into,
    # so the record of what it received is EMPTY -- and empty is not absent: it is a declared zero,
    # true by construction, and it lets the ORDINARY reconciliation answer for a tree the kit has
    # never touched. Every path that has no class is named, and the install stops WHOLE before a
    # byte moves. Without this the `adopt` verb would be advisory decoration, bypassed by anyone
    # who typed the installer's name instead. First contact is read from a DECLARATION -- this
    # host has never answered -- and never from a tree that happened to look untouched.
    if adoption.at_first_contact(ctx):
        _empty, foreign = adoption.survey(ctx, enabled, reading["taken_at"])
        adoption.roster(ctx, foreign, reading["taken_at"])
        adoption.require_adoptable(ctx, foreign)

    status = (existing or {}).get("status")
    approved = bool(args.approve) or status == "accepted"
    state = {
        "reading": reading,
        "enabled": enabled,
        "unavailable": unavailable,
        "existing": existing,
        "approver": args.approve,
        "approved": approved,
        "approving_draft": bool(args.approve) and status == "draft",
        "by_id": {c.id: c for c in enabled},
        "scopes": {c.id: ctx.workspace.scoped(c.targets()) for c in enabled},
    }

    writes = _install_plan(ctx, enabled, state)
    if getattr(args, "plan", False):
        if approved:
            writes = writes + render_verb.plan_entries(ctx, enabled)
            writes = writes + _record_plan(ctx, enabled, _signed(args, existing), writes)
        print(plan_module.report("init", writes))
        return 0

    _apply(ctx, state, writes)

    if not approved:
        answers = ctx.host_answers()
        raise PendingApproval(
            f"{ctx.install_of_mode('declaration')['target']} was drafted at "
            f"{answers['drafted_at']} choosing {answers['capabilities']}, and nobody has "
            f"accepted it. Nothing else has been written to this host. Read the draft, then: "
            f"init --root <host> --approve <who>"
        )

    render_verb.run(ctx, args, enabled)

    # The record is taken LAST, and it is taken by MEASURING what is now on disk rather than by
    # believing the plan that put it there. A record written from the plan would agree with the
    # plan by construction and could never contradict it, which is an attribution that cannot
    # fail. It carries the NAME on the door: what a machine did to a host, with nobody's name on
    # it, is a thing no one can be held to.
    for write in _record_plan(ctx, enabled, ctx.host_answers()[doors.SIGNED_BY], writes):
        if write.disposition != "keep":
            estate_module.take(ctx, enabled, reading["taken_at"],
                               ctx.host_answers()[doors.SIGNED_BY], writes=writes)
        print(f"  {write.accomplished:<9}  {write.target}")

    return check_verb.run(ctx, args)
