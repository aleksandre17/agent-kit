"""upgrade -- the first verb that meets a tree the kit did not create.

Everything else this kit does was proved on a repository it made itself, where nothing had moved
because nothing was ever supposed to have. An upgrade meets a host a human has been living in,
and the whole difficulty is one distinction that is invisible in the bytes on disk: *the host
edited this* against *upstream changed this*. Neither can be recovered by looking at the file.
The estate is what makes them separable, and a host without one is refused rather than guessed at.

    python kit/interpreters/cli.py upgrade --root <host> --plan   # read, report, write nothing
    python kit/interpreters/cli.py upgrade --root <host>          # reconcile, refuse or install
    python kit/interpreters/cli.py upgrade --root <host> --approve <who>   # walk the door
    python <kit-in-tree>/interpreters/cli.py upgrade --root <host> --mode referenced --approve <who>

`--mode laws` (ADR-024 decision 21) moves each numbered law of the deprecated law page into a rule in
the host's norms (`law: <n>`, its title, what it says and its enforcement note), removes the page and
renders: the served law list is then rendered from those rules, and the host completes each one
(`derives_from`, `modality`, `subject`) where the normative tree's gate names it.

`--mode referenced` (ADR-024 decision 18) moves a host that holds the kit in its own tree (a
submodule) off its vendored copy: the lock is rewritten to reference that kit at its commit, every
projection is rendered to run it from there, `check` is run, and only when it is green are the copies
(`.agents/kit/`, each referenced take under `.agents/taken/`) removed. Run again after the submodule
moves, to pin the new commit.

This verb WRITES NOTHING ITSELF, and that is a design decision rather than an economy. `init`
already carries out every install mode correctly -- vendor replaces, seeds are created once,
projections are rebuilt -- so a second installer here would be a second home for the one thing
that must never have two. What was missing was never the writing. It was the judgement of whether
the writing is SAFE, and that is all this verb is: a gate in front of the installer.

It also cannot delete. A capability's `installs` IS its write permission, so a path the new kit
no longer declares is a path nothing gives it permission to touch -- which settles what happens
to a withdrawn file without anyone having to choose: it stays, and the record goes on accounting
for it as ORPHANED, so it never becomes an unexplained path in a governed plane.

The door: a refusal that a NAMED HUMAN may accept is declared adoptable by the steward, and
nothing else can be waved through. Adoption is recorded on the row -- who, when, and the digest
it superseded -- because a decision whose only record is a terminal session answers differently
on Tuesday. The bytes are not archived: the refusal happens BEFORE the write, so the host still
holds its own file at the moment it decides.
"""

from __future__ import annotations

import json

import declared
import laws
import lawsource
import norms as norms_gate

import check as check_verb
import doors
import estate as estate_module
import hostlock
import installmodes
import extend as extend_verb
import init as init_verb
import pin
import provenance
import reconcile
import reference
import relocation
import render as render_verb
from errors import KitError

SUMMARY = "reconcile what was shipped, what the host has, and what this kit ships -- then install"
MUTATES = True
REQUIRES_APPROVED_HOST = True
#: An upgrade is how a new state of a REFERENCED kit is pinned, so the entry point's drift guard does
#: not stand in front of it (ADR-024 decision 18).
REPINS = True
ARGUMENTS = [
    ("--mode", {"default": None, "choices": ["referenced", "vendored", "laws", "addresses"],
                "help": "referenced: run the kit this host holds in its own tree (a submodule) at its "
                        "commit, and remove the vendored copies once check is green (a referenced host "
                        "upgrades so by default); vendored: return a referenced host to vendored copies; "
                        "laws: move each numbered law of the deprecated law page into a rule in the "
                        "host's norms; addresses: re-address each doctrine stance a new version of its "
                        "bundle left answering nothing (NT-READDRESS)"}),
]


class UpgradeRefused(KitError):
    """The three readings could not be reconciled. The paths are named and so are both moments."""

    code = "KIT0029"


def _report(ctx, recorded, rows, stewards) -> None:
    print(f"upgrade: kit {ctx.manifest.version} against a host recorded at "
          f"{recorded['taken_at']} as kit {recorded['kit_version']}, signed by "
          f"{recorded['signed_by']}")
    reconcile.report(stewards, rows, reconcile.UNCHANGED)


def _refuse(rows) -> None:
    """Every refusal at once, and the upgrade stops. Not the path skipped and the rest applied: a
    partial upgrade leaves a host in a state no version describes, and nothing can then say what
    it is. Adoptable refusals are told apart from structural ones, because they are answered by
    different things -- one by a person, the other by a repair."""
    refusals = reconcile.refused(rows)
    if not refusals:
        return
    adoptable = [row for row in refusals if row["adoptable"]]
    structural = [row for row in refusals if not row["adoptable"]]
    lines = "\n  ".join(f"{row['state']}  {row['path']}  --  {row['why']}" for row in refusals)
    if structural:
        raise UpgradeRefused(
            f"{len(structural)} path(s) this upgrade cannot reconcile, and no name resolves "
            f"them:\n  {lines}"
        )
    doors.refuse(
        f"{len(adoptable)} path(s) this host has changed and this kit also changes:\n  {lines}",
        "person who owns these files",
        "upgrade --root <host> --approve <who>",
        "Keeping them silently and overwriting them silently are both decisions nobody would be "
        "able to read afterwards, so neither is taken. Revert the file to be rid of the change, "
        "or accept the replacement by name -- the digest it supersedes is recorded either way.",
    )


def _introduced(ctx, apply: bool = True) -> list:
    """Create every host-owned install (`binding` class) an enabled capability declares and the host
    does not yet hold -- through its install mode, foreseen first, applied only where it would CREATE."""
    created = []
    for capability in ctx.enabled_capabilities():
        scoped = ctx.workspace.scoped(capability.targets())
        for item in capability.installs:
            if item.get("class") != "binding":
                continue
            mode = installmodes.mode_of(capability, item)
            state = {"manifest": ctx.manifest}
            if mode.phase != "install" or mode.foresee is None or mode.foresee(scoped, item, state) != "create":
                continue
            if apply:
                mode.apply(ctx, scoped, item, state)
            created.append(item["target"])
    return created


def _referenced(ctx, args) -> int:
    """Pin the kit this run IS, in the host's own tree, as the host's kit -- and drop the copies once
    the referenced host checks green. Nothing is removed on a red check: the copies stay, and say why."""
    moment = ctx.clock.now()
    lock, copies, retaken = reference.pinning(ctx, moment)
    held = lock[reference.FIELD]
    print(f"upgrade: reference {held['path']}/ at {held['commit'][:12]} in {held['repository']}; "
          f"{len(held['takes'])} take(s) read where the host holds them; copies to remove once check is green: "
          + (", ".join(c for c in copies if ctx.workspace.exists(c.rstrip("/"))) or "none"))
    for row in retaken:
        print(f"upgrade: take again {row['id']}@{row['version']} {row['digest']} (pinned {row['prior']['version']} "
              f"{row['prior']['digest']} by {row['prior']['pinned_by']}) -- a newer version at its referenced source")
    if getattr(args, "plan", False):
        for target in _introduced(ctx, apply=False):
            print(f"upgrade: create {target} -- a host truth this kit introduces, created once")
        return 0
    if not args.approve:
        doors.refuse("this host would run the kit it holds in its own tree and drop its vendored copies"
                     + (f", and take again {', '.join(r['id'] + '@' + r['version'] for r in retaken)}"
                        if retaken else ""),
                     "person who owns this host", "upgrade --root <host> --mode referenced --approve <who>",
                     "Which kit a host runs, and from where, is the host's choice, and the record names who chose.")
    seat = pin.seats(ctx.manifest)[1]
    writes = _retaken(ctx, retaken, args.approve, moment)

    def write() -> int:
        for target, (owner, document) in writes.items():
            ctx.workspace.scoped(owner.targets()).write_json(target, document)
        ctx.workspace.scoped((seat,)).write_text(seat, json_text(lock))
        # The host read again: its takes are now read where its lock says it holds them.
        ctx.reread()
        # A newer capability may declare a host truth this host was never given -- a seed or a space.
        # Each is created ONCE, by its own install mode, exactly as `init` would; nothing the host
        # already holds is touched. Without this a referenced host could not read its own declarations
        # after the upgrade that introduced one.
        for created in _introduced(ctx):
            print(f"  created    {created}  (introduced by this kit)")
        code = render_verb.run(ctx, args)
        if code == 0:
            code = check_verb.run(ctx, args)
        if code != 0:
            print(f"upgrade: the referenced host is not green, so the vendored copies are KEPT; fix what "
                  f"check names and run this again")
            return code
        gone = [c for c in copies if ctx.workspace.exists(c.rstrip("/"))]
        for copy in gone:
            ctx.workspace.scoped((copy,)).remove_tree(copy.rstrip("/"))
        print(f"upgrade: REFERENCED by {args.approve} -- {len(gone)} copy(ies) removed; this host now runs "
              f"python {held['path']}/interpreters/cli.py <verb> --root .")
        ctx.reread()
        return check_verb.run(ctx, args)

    return hostlock.held(ctx, args, write)


def _retaken(ctx, retaken: list, who: str, moment: str) -> dict:
    """target -> (owning capability, document): the estate and take statement once every take whose
    referenced source holds a NEWER version is taken again -- what `take` writes, less the copy a
    referenced host never keeps. The upgrade's approver walks the door, so the pin is attested by them
    at arrival; a signature its verifier refutes is refused (KIT0032), as at any door."""
    if not retaken:
        return {}
    at = estate_module.target(ctx)
    recorded = estate_module.read(ctx)
    pins = {p["capability"]: p for p in recorded.get("taken", [])}
    statement = ctx.install_of_mode(reference.TAKEN_DECLARATION)
    current = ctx.workspace.read_json(statement["target"])
    rows = {row["id"]: row for row in current["takes"]}
    declared = {c.id: c for c in ctx.manifest.capabilities}
    for row in retaken:
        fresh = provenance.arrival(ctx, row["id"], row["version"], row["digest"], who, moment, row["prior"])
        found = provenance.authenticate(ctx, declared[row["id"]], row["digest"], moment)
        if found["state"] == provenance.REFUTED:
            raise provenance.ProvenanceRefused(
                f"{row['id']}@{row['version']} claims a signature by {found['signer']!r} that "
                f"{found['verifier']} rejected against this host's trust root: {found['evidence']}")
        pins[row["id"]] = dict(fresh, authenticity=found,
                               trust={"basis": provenance.basis_at(ctx, provenance.APPROVAL),
                                      "attested_by": who, "attested_at": moment})
        rows[row["id"]] = dict(rows[row["id"]], taken_by=who, at=moment)
    estate = dict(recorded, taken=[pins[k] for k in sorted(pins)])
    document = dict(current, takes=[rows[k] for k in sorted(rows)])
    for value, schema, target in ((estate, ctx.install_of_mode(estate_module.MODE)["validates"], at),
                                  (document, statement["validates"], statement["target"])):
        errors = ctx.manifest.validate(value, schema)
        if errors:
            raise UpgradeRefused(f"{target} would not honour its schema:\n  " + "\n  ".join(errors))
    owner = {i["target"]: c for c in ctx.manifest.capabilities for i in c.installs}
    return {at: (owner[at], estate), statement["target"]: (owner[statement["target"]], document)}


def _vendored(ctx, args) -> "int | None":
    """Return a REFERENCED host to vendored copies, asked for by name: each referenced take is copied
    into the take plane from the source its pin holds, the lock loses its `reference` block, and the
    ordinary upgrade then delivers the kit's copy beside it. Never the default: a referenced host that
    is upgraded stays referenced. None for a host that is already vendored."""
    held = reference.of(ctx)
    if not held:
        return None
    plane = ctx.install_of_mode(reference.TAKEN)
    print(f"upgrade: leave the reference to {held['path']}/ at {held['commit'][:12]}; copy "
          f"{len(held['takes'])} take(s) into {plane['target']} and the kit into {pin.seats(ctx.manifest)[0]}")
    if getattr(args, "plan", False):
        return 0
    if not args.approve:
        doors.refuse("this host would stop running the kit it holds in its own tree and keep vendored copies",
                     "person who owns this host", "upgrade --root <host> --mode vendored --approve <who>",
                     "Which kit a host runs, and from where, is the host's choice, and the record names who chose.")
    seat = pin.seats(ctx.manifest)[1]
    lock = {k: v for k, v in ctx.workspace.read_json(seat).items() if k != reference.FIELD}
    owner = next(c for c in ctx.manifest.capabilities for i in c.installs if i["mode"] == reference.TAKEN)

    def write() -> int:
        for take in held["takes"]:
            source = ctx.workspace.path(take["path"])
            files = {p.relative_to(source).as_posix(): p.read_bytes()
                     for p in sorted(source.rglob("*")) if p.is_file()}
            ctx.workspace.scoped(owner.targets()).write_tree(plane["target"] + take["id"], files)
        ctx.workspace.scoped((seat,)).write_text(seat, json_text(lock))
        return 0

    return hostlock.held(ctx, args, write)


#: Where a host's own rules are published: the address the normative tree gives a host norm.
HOST_ADDRESS = "host@1.0.0"


def _laws(ctx, args) -> int:
    """Move the deprecated law page's numbered laws into the host's norms, then retire the page."""
    gate = next(g for c in ctx.enabled_capabilities() for g in c.gates if g["kind"] == lawsource.KIND)
    page, reads = gate["params"]["deprecated"], gate["params"]["rules_from"]
    target = next(i["target"] for c in ctx.enabled_capabilities() for i in c.installs if i.get("reads_as") == reads)
    if not ctx.workspace.exists(page):
        print(f"upgrade: {page} is absent; this host's laws already have one source")
        return 0
    norms = next(iter(declared.sources(ctx, [reads]).values()))
    text = ctx.workspace.read_text(page)
    moved = laws.rules(text, HOST_ADDRESS, args.approve or "<who>",
                       gate["params"]["genre"], ctx.manifest.version_of(laws.CONTRACT))
    taken = {n["id"] for n in norms} & {r["id"] for r in moved}
    if laws.numbered(norms) or taken:
        raise UpgradeRefused(f"{target} already carries numbered laws or the addresses {sorted(taken)}; "
                             f"a law moved over one would be a law with two homes. Reconcile {page} by hand")
    for rule in moved:
        print(f"upgrade: law {rule['law']} -> {target} as {rule['id']} ({rule['title']})")
    for line in laws.outside(text):  # removed with the page and carried by no rule: named, every one
        print(f"upgrade: NOT MOVED (removed with {page}): {line}")
    print(f"upgrade: {page} is removed once its {len(moved)} law(s) are rules; complete each rule's "
          f"derives_from, modality and subject where `check` names it")
    if getattr(args, "plan", False):
        return 0
    if not args.approve:
        doors.refuse(f"this host's laws would move from {page} into {target}, and the page would be removed",
                     "person who owns this host", "upgrade --root <host> --mode laws --approve <who>",
                     "Where a host's laws are written is the host's choice, and the record names who chose.")

    def write() -> int:
        ctx.workspace.scoped((target,)).write_text(target, json.dumps(norms + moved, indent=2, ensure_ascii=False) + "\n")
        ctx.workspace.scoped((page,)).remove_file(page)
        ctx.reread()
        return render_verb.run(ctx, args)

    return hostlock.held(ctx, args, write)


def _addresses(ctx, args) -> int:
    """Re-address every host stance a new version of its bundle left answering nothing (`NT-READDRESS`)."""
    local = next((i for c in ctx.enabled_capabilities() for i in c.installs if i.get("validates") == "doctrine"), None)
    if local is None or not ctx.workspace.exists(local["target"]):
        print("upgrade: this host declares no doctrine stances; nothing to re-address")
        return 0
    body = ctx.workspace.read_json(local["target"])
    moves = norms_gate.readdressed(norms_gate.norms_of(ctx), body.get("stances", []))
    if not moves:
        print(f"upgrade: every stance in {local['target']} answers a norm in force; nothing to re-address")
        return 0
    for old, new in sorted(moves.items()):
        print(f"upgrade: stance {old} -> {new}")
    if getattr(args, "plan", False):
        return 0
    if not args.approve:
        doors.refuse(f"{len(moves)} stance(s) in {local['target']} would answer the version of the norm now in force",
                     "person who owns this host", "upgrade --root <host> --mode addresses --approve <who>",
                     "A stance is the host's answer; moving it to a new version of the question is the host's act.")

    def write() -> int:
        body["stances"] = [dict(s, id=moves.get(s.get("id"), s.get("id"))) for s in body.get("stances", [])]
        ctx.workspace.scoped((local["target"],)).write_text(local["target"],
                                                            json.dumps(body, indent=2, ensure_ascii=False) + "\n")
        ctx.reread()
        return render_verb.run(ctx, args)

    return hostlock.held(ctx, args, write)


def json_text(value) -> str:
    """A lock as every lock is written: sorted keys, two-space indent, one trailing newline."""
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def run(ctx, args) -> int:
    if getattr(args, "mode", None) == "laws":
        hostlock.arrive(ctx, args)
        return _laws(ctx, args)
    if getattr(args, "mode", None) == "addresses":
        hostlock.arrive(ctx, args)
        return _addresses(ctx, args)
    mode = getattr(args, "mode", None)
    if mode is None and reference.of(ctx):
        # A referenced host stays referenced: only `--mode vendored`, asked for by name, gives it copies.
        print("upgrade: this host references the kit in its own tree, so it is upgraded as referenced "
              "(`--mode vendored` returns it to copies)")
        mode = "referenced"
    if mode == "referenced":
        hostlock.arrive(ctx, args)
        return _referenced(ctx, args)
    if mode == "vendored":
        hostlock.arrive(ctx, args)
        left = _vendored(ctx, args)
        if left is not None:
            if left != 0 or getattr(args, "plan", False):
                return left
            ctx.reread()
    # Guarded on arrival, so a held host is named as the cause before a reconciliation is printed
    # against a tree somebody else is writing. The hold itself is taken by the installer this verb
    # hands its verdict to, at the moment that installer writes, and under THIS verb's name.
    hostlock.arrive(ctx, args)
    recorded = estate_module.read(ctx)
    if recorded is None:
        raise UpgradeRefused(
            f"{estate_module.target(ctx)}: this host has no record of what it was given, so "
            f"nothing here can tell a file the host edited from one this kit changed. A tree "
            f"states what it IS and never what it RECEIVED. Take a first record with `init "
            f"--root <host>` on the kit this host is already running, then upgrade"
        )

    stewards = estate_module.stewardship(ctx)
    enabled = ctx.enabled_capabilities()
    # The relocations this host owes are reconciled AS IF carried out (ADR-021): `init` carries
    # them out first, so the verdict printed here is the verdict over the tree it will write.
    moved = relocation.view(relocation.planned(ctx, enabled))
    rows = reconcile.survey(ctx, enabled, recorded, stewards, ctx.adopted, moved)
    _report(ctx, recorded, rows, stewards)

    if args.approve:
        # The door is walked ONCE, against the plan just printed -- not once per file. Every row
        # it accepts carries the name, the moment and the digest it supersedes onto the record.
        ctx.adopted = {
            row["path"]: doors.record(args.approve, ctx.clock.now()) | {"superseded": row["here"]}
            for row in reconcile.refused(rows) if row["adoptable"] and row["here"]
        }
        rows = reconcile.survey(ctx, enabled, recorded, stewards, ctx.adopted, moved)

    _refuse(rows)

    # The reconciliation's verdict is handed to the installer as DATA. `init` carries it out and
    # decides nothing again -- which is the only construction under which what was just printed
    # and what is about to be written cannot be two different things.
    ctx.decided = {row["path"]: row for row in rows}

    if getattr(args, "plan", False):
        print(f"upgrade: reconciled; the writes below are {init_verb.SUMMARY}")
    code = init_verb.run(ctx, args)
    if code == 0 and args.approve and not getattr(args, "plan", False):
        # A newer template of an extension point is merged three ways into what the host wrote there:
        # clean merges land, a conflict is reported and the host's file is kept (ADR-024).
        extend_verb.merge(ctx, args)
    return code
