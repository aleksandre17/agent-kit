"""takeover -- carry out the host's signed migration map: the APPLY half of succession (ADR-012).

    python kit/interpreters/cli.py takeover --root <host> --plan
    python kit/interpreters/cli.py takeover --root <host> --approve <who> --roster <digest>

`inherit` reads a prior system and prints what the host's map assigns. This verb carries that
roster OUT: every path a row relocates is renamed into a kit space, and every path a row removes is
renamed aside into the observed plane. It reads only the map at its declared RESIDENCE -- a map
passed from anywhere is a judgement with no home -- and it acts only at a DOOR that accepts the
digest of the whole roster, re-read at the moment of the act, so what is carried out is provably
what was signed and the tree has not moved since.

A refusal is WHOLE and is computed before a byte moves; `--plan` is the same computation, printed.
A run killed mid-act leaves its act open in the observed plane; the next run reconciles it against
the tree and finishes exactly that act, at the same door, or names what it cannot reconcile.
"""

from __future__ import annotations

import hashlib
import uuid

import doors
import ephemeral
import estate as estate_module
import hostlock
import plan as plan_module
import succession
import succession_act as acts
from errors import KitError
from journal import Journal

SUMMARY = "carry out the host's signed migration map, through a door that accepts its roster digest"
MUTATES = True
REQUIRES_APPROVED_HOST = True

#: The journal this verb keeps in the observed plane, and the phases it declares. Data: the journal
#: reads them and branches on none.
JOURNAL = "takeover.journal"
PHASES = (
    {"id": "record", "does": "write the accepted act into the observed plane before any path moves"},
    {"id": "carry", "does": "rename every pending path of the act, each re-measured before it moves"},
    {"id": "account", "does": "append the whole act to the estate, then close its record"},
)


def _class_of(ctx, path: str) -> str:
    return next((p["class"] for p in ctx.manifest.planes
                 if succession._under(path, p["root"].rstrip("/"))), "-")


def _writes(ctx, act: dict, mapped_by: str, pending: list) -> list:
    writes = []
    for item in pending:
        writes.append(plan_module.Write("remove", _class_of(ctx, item["path"]), item["disposition"],
                                        mapped_by, item["path"]))
        writes.append(plan_module.Write("create", _class_of(ctx, item["to"]), item["disposition"],
                                        mapped_by, item["to"]))
    record = acts.record_path(ctx, act["digest"])
    writes.append(plan_module.Write("create", _class_of(ctx, record), acts.SCHEMA, "kit", record))
    item = ctx.install_of_mode(estate_module.MODE)
    writes.append(plan_module.Write("replace", item["class"], item["mode"], "kit", item["target"]))
    return writes


def _report(act: dict, pending: list, carried: list, outside: int, resumed) -> None:
    roster = act["roster"]
    if resumed:
        print(f"takeover: an act signed by {resumed['signed_by']} at {resumed['signed_at']} was "
              f"INTERRUPTED -- {len(carried)} of {len(roster['paths'])} path(s) already carried, "
              f"{len(pending)} pending; this run finishes exactly that act and nothing else")
    for item in roster["paths"]:
        state = "carried" if item in carried else "pending"
        print(f"  {item['disposition']}  {item['path']}  -> {item['to']}  ({item['effect']}, "
              f"{state}, sha256 {item['digest'][:12]})")
    print(f"  map     {roster['residence']}  sha256 {roster['map']}")
    print(f"  roster  {act['digest']}")
    print(f"  count  paths = {len(roster['paths'])}")
    if outside:
        print(f"  count  unanswered outside the prior boundary = {outside} -- the kit's own planes, "
              f"answered for by the estate and adopt, not by this act")


def _door(act: dict, args, resumed) -> None:
    how = f"takeover --root <host> --approve <who> --roster {act['digest']}"
    if not args.approve or not getattr(args, "roster", None):
        doors.refuse(
            f"{len(act['roster']['paths'])} path(s) of a prior system would leave the host's tree "
            f"or move into this kit's spaces (roster {act['digest']})",
            "person who owns this host",
            how,
            "Accept the roster BY ITS DIGEST, as printed by --plan: the act re-reads the host and "
            "refuses if what it reads is not what you signed.",
        )
    if args.roster != act["digest"]:
        raise acts.RosterMoved(
            f"the roster accepted is {args.roster}, and the roster "
            f"{'of the interrupted act' if resumed else 'read now'} is {act['digest']}. The map at "
            f"its residence or a path of the prior system changed since the reading that was "
            f"signed -- nothing moves. Read again with --plan and sign what is there now")


def run(ctx, args) -> int:
    hostlock.arrive(ctx, args)
    if getattr(args, "map", None):
        raise acts.ActRefused(
            "takeover reads the map at its declared residence only; a map passed by --map from "
            "anywhere is a judgement with no home. Put it at the residence, review and commit it")
    recorded = estate_module.read(ctx)
    if recorded is None:
        raise acts.ActRefused(f"{estate_module.target(ctx)}: this host has no record of what it was "
                              f"given, so nothing can tell a prior path from the kit's own. Run "
                              f"`init` first")
    words = succession.vocabulary(ctx)
    home = succession.residence(words)
    if not ctx.workspace.path(home).is_file():
        raise acts.ActRefused(f"{home}: no migration map resides here, and an act is carried out "
                              f"only from the map at its residence")
    reading = succession.read(ctx, ctx.workspace.path(home))

    resumed = acts.open_act(ctx)
    if resumed is not None:
        if reading["map"] and resumed["roster"]["map"] != hashlib.sha256(
                reading["map"]["file"].read_bytes()).hexdigest():
            raise acts.RosterMoved(f"the map at {home} changed while the act {resumed['digest']} "
                                   f"was open; a person must decide which of them is true")
        act, outside = resumed, 0
        pending, carried, conflicts = acts.reconcile(ctx, resumed)
        if conflicts:
            raise acts.RosterMoved(f"the interrupted act {resumed['digest']} cannot be reconciled "
                                   f"with this tree:\n  " + "\n  ".join(conflicts))
    else:
        composed = acts.compose(ctx, reading, recorded)
        if not composed["roster"]["paths"]:
            print("takeover: no path of the prior boundary is answered by a row -- nothing to "
                  "carry out, and nothing was written")
            return 0
        act = {"roster": composed["roster"], "digest": composed["digest"]}
        pending, carried, outside = list(composed["roster"]["paths"]), [], composed["outside"]
    _report(act, pending, carried, outside, resumed)

    writes = _writes(ctx, act, reading["map"]["declared_by"] or "-", pending)
    if getattr(args, "plan", False):
        print(plan_module.report("takeover", writes))
        return 0
    _door(act, args, resumed)

    run_id = uuid.uuid4().hex
    hold = hostlock.writer(ctx, args, run_id)
    journal, code, message = None, 1, None
    try:
        journal = Journal.opened(ctx, ephemeral.place(ctx, JOURNAL), verb=args.verb, phases=PHASES,
                                 now=ctx.clock.now(), run_id=run_id, broke=hold.broke)
        code = _carry_out(ctx, act, resumed, pending, recorded, journal, args, run_id)
        return code
    except KitError as refusal:
        code, message = refusal.exit_code, str(refusal)
        raise
    except BaseException as unforeseen:  # noqa: BLE001 -- re-raised; only the record is added
        message = f"{type(unforeseen).__name__}: {unforeseen}"
        raise
    finally:
        if journal is not None:
            journal.close(code, message)
        hold.release(code, message)


def _carry_out(ctx, act, resumed, pending, recorded, journal, args, run_id) -> int:
    observed = ephemeral.scope(ctx)
    where = acts.record_path(ctx, act["digest"])
    journal.enter("record")
    if resumed is None:
        act = {"schema_version": ctx.manifest.version_of(acts.SCHEMA), "digest": act["digest"],
               "roster": act["roster"], **doors.record(args.approve, ctx.clock.now()),
               "started_at": ctx.clock.now(), "runs": [run_id]}
    else:
        act = dict(act, runs=[*act.get("runs", []), run_id])
    observed.write_json(where, acts.honoured(ctx, act, "as this run writes it"))
    journal.conclude("record")

    journal.enter("carry")

    def said(item):
        print(f"  {plan_module.DISPOSITIONS['remove']}  {item['path']}")
        print(f"  {plan_module.DISPOSITIONS['create']}  {item['to']}")

    acts.carry(ctx, act, pending, said)
    journal.conclude("carry")

    journal.enter("account")
    act = dict(act, carried_at=ctx.clock.now())
    acts.honoured(ctx, act, "as this run closes it")
    already = [a for a in recorded.get(estate_module.SUCCESSION, []) if a["digest"] == act["digest"]]
    if not already:
        enabled = ctx.enabled_capabilities()
        estate_module.take(ctx, enabled, recorded["taken_at"], recorded["signed_by"],
                           entries=recorded["files"], taken=recorded.get("taken", []),
                           acts=[*recorded.get(estate_module.SUCCESSION, []), act])
        print(f"  {plan_module.DISPOSITIONS['replace']}  {estate_module.target(ctx)}")
    observed.write_json(where, act)
    journal.conclude("account")
    print(f"takeover: {len(act['roster']['paths'])} path(s) carried and accounted in the estate; "
          f"removed paths are set aside under {ephemeral.place(ctx, acts.PLACE)}, never destroyed")
    return 0
