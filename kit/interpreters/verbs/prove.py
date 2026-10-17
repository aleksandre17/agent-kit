"""prove -- run every command a MUST names as its enforcer, and fail if one is red (ADR-025 amendment 1).

    python .agents/kit/interpreters/cli.py prove --root . [--plan]

A norm that says MUST and names a COMMAND as its enforcer (`stack-kit:test`, vouched for by an adapter
that reads the host's own declaration) is enforced only where something runs that command. `check`
reads; it does not run a test suite. This verb is what runs them: the git adapter's pre-push hook calls
it after `check`, so a MUST whose command is red does not leave the machine. Each command runs once,
from the host root, however many norms name it; `--plan` names them and runs nothing.

Proof is weighed as the work is (ADR-025 amendment 4): what a push carries is weighed by the host's
areas, and it is proved by the commands the areas it touches declare (`proved_by`) -- a one-line change
to the web app runs the web app's tests, not every suite the repository has. A change heavy enough to
owe a decision, one touching an area that declares no proof, a host that weighs nothing, or `--full`, is
proved by EVERYTHING: every command a MUST names AND every command an area declares as its proof
(`proved_by`, `default_proved_by`), each once -- everything is never weaker than a scoped proof. Which it
was, and why, is printed.

A push cannot rewrite its own proof: its areas, work-class catalogue, commands and MUSTs are read as
they stood on the PUBLISHED side -- the merge-base of what is pushed with what the remote holds -- and the pushed
side only adds a command the published side did not have. A push that narrows a `proved_by`, the
default's, or rewrites a command is told so, and is proved as the published side says. What is pushed
is what git hands the hook (`--pushed "<local sha>:<remote sha> ..."`): exactly those ranges are
weighed -- `remote..local`, or what no remote holds for a new ref. A range that cannot be read is proved
by everything. prove judges the WORKING TREE, so a push whose sha is not HEAD, or made from a tree that is
not clean, is refused outright -- `--full` included: it would prove other bytes than those pushed. An area
downstream of a touched one is proved with it; a MUST is said to hold only when its own enforcer ran.

Nothing is proved twice on the same bytes (Cardinal IX): a command that went green on a clean tree is
recorded in the observed plane with that tree's id, and is not run again while the tree is the same --
a second push of what was proved, a retry after a refused push. The key is the exact bytes, never a
guess at what a command depends on: any change at all, a dirty tree, `--full`, or another command
string runs it again. A record is honoured only when its content names the same command, tree, kit
version and proof declarations (the areas and commands it was proved under). A red run is never
recorded. The record is a SPEED-UP, not a security boundary: whoever can write the observed plane can
forge one, as they could edit the hook or push with `--no-verify`. The hook is FEEDBACK; the authority is
CI, which runs `check` and `prove --full` on the exact pushed commit, on a clean runner that never reads
this record (ADR-025 amendment 5). A MUST whose
enforcer an adapter vouches for, but whose command cannot be read -- the host's declaration missing,
unreadable, or silent on that key -- is refused, never read as nothing to run: an enforcer nobody can
run does not hold.
"""

from __future__ import annotations

import hashlib
import json
import subprocess

import declared
import ephemeral
import norms as norms_gate
import vcs
import weighing
import workclass

SUMMARY = "run every command a MUST norm names as its enforcer -- the pre-push proof (blocking on red)"
MUTATES = False
REQUIRES_APPROVED_HOST = True
ARGUMENTS = [("--full", {"action": "store_true", "help": "prove with every command a MUST names, whatever the change"}),
             ("--pushed", {"default": None, "help": "the refs a push carries, as git hands them to the hook: "
                                                    "'<local sha>:<remote sha> ...'"})]

ZERO = set("0")


def _at(ctx, base, rel):
    """The JSON `rel` holds at `base` -- or None where it holds none, or none can be read."""
    if not base:
        return None
    text, _why = vcs.file_at(ctx.workspace.root, base, rel)
    if text is None:
        return None
    try:
        return json.loads(text)
    except ValueError:
        return None


def _pointed(value, pointer: str):
    for step in pointer.split("."):
        value = value.get(step) if isinstance(value, dict) else None
    return value


def _commands(ctx, base=None) -> tuple:
    """(`<prefix>:<key>` -> the command string for every key a vouching document finds in the host,
    `<prefix>` -> why its declaration could not be read). With `base`, a key the published side declares
    is run as the published side declares it: a push does not rewrite its own proof."""
    found, unread = {}, {}
    for document in declared.sources(ctx, norms_gate.VOUCHED).values():
        if not ctx.workspace.exists(document["path"]):
            unread[document["prefix"]] = f"{document['path']} is not there"
            continue
        try:
            value = ctx.workspace.read_json(document["path"])
        except ValueError as exc:
            unread[document["prefix"]] = f"{document['path']} is not readable JSON -- {exc}"
            continue
        unread.setdefault(document["prefix"], f"{document['path']} declares no such command at {document['pointer']}")
        value = _pointed(value, document["pointer"])
        published = _pointed(_at(ctx, base, document["path"]), document["pointer"]) if base else None
        for source in (value, published):
            if isinstance(source, dict):
                found.update({f"{document['prefix']}:{key}": given for key, given in source.items()
                              if isinstance(given, str) and given.strip()})
    return found, unread


#: Where a green proof is remembered, in the observed plane: by command and by the exact tree it read.
SUBJECT = "proofs"


def _record(ctx, command: str, tree: str) -> str:
    key = hashlib.sha256(f"{command}\n{tree}".encode("utf-8")).hexdigest()[:32]
    return ephemeral.place(ctx, f"{SUBJECT}/{key}.json")


def _honoured(ctx, record: str, expected: dict) -> bool:
    """A record is honoured only when it names the same command, tree, kit version and declarations --
    never merely because a file with its name exists."""
    try:
        said = ctx.workspace.read_json(record)
    except (OSError, ValueError):
        return False
    return isinstance(said, dict) and said.get("green") is True and all(said.get(k) == v for k, v in expected.items())


def _zero(sha: str) -> bool:
    return not sha or set(sha) <= ZERO


def _boundary(root, local: str) -> tuple:
    """(the commits `local` brings that no remote holds, the published commit they rest on or None)."""
    shas, why = vcs.run(root, ["rev-list", local, "--not", "--remotes"])
    if shas is None:
        return None, None, why
    edge, _why = vcs.run(root, ["rev-list", "--boundary", local, "--not", "--remotes"])
    bases = [line[1:] for line in (edge or "").split() if line.startswith("-")]
    if len(bases) > 1:
        said, _why = vcs.run(root, ["merge-base", "--octopus", *bases])
        bases = [said.strip()] if said else []
    return shas.split(), (bases[0] if bases else None), None


def _ranges(ctx, args) -> tuple:
    """(paths, the published base or None, None) -- or (None, None, why): every command."""
    root = ctx.workspace.root
    pushed = [pair for pair in str(getattr(args, "pushed", None) or "").split() if pair.strip()]
    if not pushed:
        upstream, _ = vcs.run(root, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
        if upstream:
            pushed = [f"HEAD:{upstream.strip()}"]
        else:
            pushed = ["HEAD:"]
    head, why = vcs.run(root, ["rev-parse", "HEAD"])
    if head is None:
        return None, None, f"HEAD cannot be read ({why})"
    head = head.strip()
    paths, bases = set(), []
    for pair in pushed:
        local, _, remote = pair.partition(":")
        if _zero(local):
            continue  # a ref deleted carries nothing to prove
        said, why = vcs.run(root, ["rev-parse", local])
        if said is None:
            return None, None, f"the pushed {local} cannot be read ({why})"
        if said.strip() != head:
            return None, None, (f"the pushed {local[:12]} is not HEAD ({head[:12]}), the tree the commands run "
                                f"over")
        if _zero(remote):
            shas, base, why = _boundary(root, head)
            if shas is None:
                return None, None, f"what the new ref carries cannot be read ({why})"
            for sha in shas:
                got, why = vcs.commit_paths(root, sha)
                if got is None:
                    return None, None, f"commit {sha[:12]} cannot be read ({why})"
                paths |= set(got)
        else:
            base, why = vcs.run(root, ["merge-base", remote, head])
            if base is None:
                return None, None, f"the range {remote[:12]}..{head[:12]} cannot be read ({why})"
            base = base.strip()
            got, why = vcs.range_paths(root, base, head)
            if got is None:
                return None, None, f"the range {remote[:12]}..{head[:12]} cannot be read ({why})"
            paths |= set(got)
        if base:
            bases.append(base)
    if len(set(bases)) > 1:
        said, _why = vcs.run(root, ["merge-base", "--octopus", *sorted(set(bases))])
        bases = [said.strip()] if said else []
        if not bases:
            return None, None, "the pushed ranges share no published base"
    return sorted(paths), (bases[0] if bases else None), None


def _published_areas(ctx, base, catalogue, working):
    """The areas as the published side holds them; absent there, no area at all -- every path at the
    default, proved by everything. With nothing published, the working declaration."""
    if base is None:
        return working
    target = workclass.areas_target(ctx)
    stood = _at(ctx, base, target) if target else None
    return stood if isinstance(stood, dict) else {"default_undo": catalogue["undo"][0]["id"], "max_areas": {},
                                                  "areas": []}


def _published_catalogue(ctx, base, pushed):
    """The work-class catalogue as the published side holds it: a push that edits class rows cannot make
    itself weigh lighter. Absent there -- nothing published, or a catalogue this repository does not
    carry -- the pushed one, said so."""
    if base is None:
        return pushed
    home = workclass.catalogue_home(ctx)
    stood = _at(ctx, base, home) if home else None
    if isinstance(stood, dict) and isinstance(stood.get("classes"), list) and isinstance(stood.get("undo"), list):
        return stood
    where = f"{home} is not at the published base" if home else "this repository does not carry it"
    print(f"prove: the work-class catalogue is weighed as pushed -- {where}")
    return pushed


def _scope(ctx, args) -> tuple:
    """(the commands that prove what this push carries or None for every command, why, the published base,
    the areas it was weighed by, whether the tree the commands read is the tree pushed)."""
    if getattr(args, "full", False):
        return None, "--full: every command a MUST names", None, None, False
    paths, base, why = _ranges(ctx, args)
    if paths is None:
        return None, f"{why}: every command a MUST names", None, None, not why.startswith("the pushed")
    found = workclass.declarations(ctx)
    if found is None:
        return None, "this host weighs nothing (no work classes): every command a MUST names", base, None, True
    catalogue, working = found
    catalogue = _published_catalogue(ctx, base, catalogue)
    areas = _published_areas(ctx, base, catalogue, working)
    commands, why = weighing.proof_for(paths, catalogue, areas)
    return (commands, (why if commands is None else f"{why}: proved by {', '.join(commands) or 'check alone'}"),
            base, areas, True)


def _other_bytes(ctx, args):
    """Why the tree prove would run its commands over is not what a push carries, or None: a pushed sha
    that is not HEAD, or a working tree that is not clean. Only a push names its shas (`--pushed`)."""
    pushed = [pair.partition(":")[0] for pair in str(getattr(args, "pushed", None) or "").split() if pair.strip()]
    if not pushed:
        return None
    root = ctx.workspace.root
    head, why = vcs.run(root, ["rev-parse", "HEAD"])
    if head is None:
        return f"HEAD cannot be read ({why})"
    for local in pushed:
        if _zero(local):
            continue
        said, why = vcs.run(root, ["rev-parse", local])
        if said is None or said.strip() != head.strip():
            return f"the pushed {local[:12]} is not HEAD ({head.strip()[:12]})"
    if ctx.workspace.clean_tree() is None:
        return "the working tree is not clean"
    return None


def _area_proof(areas) -> list:
    """Every command an area declares as its proof, and the default's, once each, in their order."""
    found = []
    for area in (areas or {}).get("areas") or []:
        found += [c for c in area.get("proved_by") or [] if c not in found]
    found += [c for c in (areas or {}).get("default_proved_by") or [] if c not in found]
    return found


def run(ctx, args) -> int:
    other = _other_bytes(ctx, args)
    if other:
        print(f"prove: REFUSED -- {other}: prove judges the working tree: push from a clean checkout of what you "
              f"push, or let CI prove it")
        return 1
    scoped, why, base, areas, same_tree = _scope(ctx, args)
    commands, unread = _commands(ctx, base)
    if base is not None:
        working = workclass.declarations(ctx)
        pushed_commands, _ = _commands(ctx)
        loosening = weighing.loosened(working[0], areas, working[1], (commands, pushed_commands)) if working and areas \
            else []
        if loosening:
            print(f"prove: this push loosens its own proof ({'; '.join(loosening)}) -- it is proved as the published "
                  f"side declares it; the loosening is a change of its own, weighed at commit")
    musts = norms_gate.norms_of(ctx)
    if base is not None:  # the MUSTs as published: a push does not drop the enforcer that proves it
        musts, unheld = norms_gate.norms_held(ctx, lambda rel: vcs.file_at(ctx.workspace.root, base, rel)[0])
        for rel in unheld:
            print(f"prove: {rel} is not at the published base -- the norms it holds are read as pushed")
    wanted, missing = {}, {}
    for norm in musts:
        if str(norm.get("modality", "")).upper() != "MUST":
            continue
        for enforcer in norm.get("enforced_by") or []:
            held = norm.get("law") or norm.get("id")
            if enforcer in commands:
                wanted.setdefault(enforcer, []).append(held)
            elif isinstance(enforcer, str) and enforcer.split(":", 1)[0] in unread and ":" in enforcer:
                missing.setdefault(enforcer, []).append(held)
    for enforcer, held in sorted(missing.items()):
        print(f"prove: {enforcer} cannot be run -- {unread[enforcer.split(':', 1)[0]]}; it holds "
              f"{', '.join(map(str, held))}")
    if missing:
        print(f"prove: REFUSED -- {len(missing)} enforcer(s) a MUST names cannot be read; an enforcer nobody can "
              f"run does not hold")
        return 1
    # An area's `proved_by` is the host's own declaration of what proves it, so a scoped proof runs with
    # or without a MUST; everything -- the unscoped path -- is what the MUSTs name AND what every area
    # declares, so it is never weaker than a scoped proof.
    if scoped is not None:
        print(f"prove: {why}")
        unknown = [c for c in scoped if c not in commands]
        if unknown:
            print(f"prove: REFUSED -- an area names {', '.join(unknown)} as its proof, which no vouching declaration "
                  f"runs")
            return 1
        for enforcer, held in sorted(wanted.items()):
            if enforcer not in scoped:  # a MUST holds only where its own enforcer ran
                print(f"prove: {enforcer} not run -- this push touches nothing it proves; "
                      f"{', '.join(map(str, held))} not proved by this push")
        wanted = {c: wanted.get(c) or ["the areas the change touches"] for c in scoped}
        if not wanted:
            print("prove: nothing beyond `check` proves this change")
            return 0
    else:
        if areas is None:  # --full, an unreadable range, a host that weighs nothing: the areas as they stand
            areas = (workclass.declarations(ctx) or (None, None))[1]
        everything = _area_proof(areas)
        unknown = [c for c in everything if c not in commands]
        if unknown:
            print(f"prove: REFUSED -- an area names {', '.join(unknown)} as its proof, which no vouching declaration "
                  f"runs")
            return 1
        if wanted:
            print(f"prove: {why}")
        else:
            declared_test = (ctx.take_reading().get("facts") or {}).get("quality.tests.command")
            if declared_test:
                # From the first day: what the host's briefing already says proves a change is what proves it
                # here (`areas` refines it by module).
                print(f"prove: {why}; no MUST names a command -- proved by the test command this host declares: "
                      f"{declared_test}")
                commands = {**commands, "declared:test": declared_test}
                wanted = {"declared:test": ["the host's declared test command"]}
            elif not everything:
                print(f"prove: {why}; no MUST names a command, no area declares one, and this host's reading "
                      f"declares no test command -- nothing to run")
                return 0
            else:
                print(f"prove: {why}; no MUST names a command")
        for command in everything:
            wanted.setdefault(command, ["an area's own proof"])
        if everything:
            print(f"prove: everything includes every area's own proof: {', '.join(everything)}")
    if getattr(args, "plan", False):
        for enforcer, held in sorted(wanted.items()):
            print(f"  would run  {commands[enforcer]}  ({enforcer}, for {', '.join(map(str, held))})")
        return 0
    red = []
    tree = ctx.workspace.clean_tree() if same_tree and not getattr(args, "full", False) else None
    digest = hashlib.sha256(json.dumps({"areas": areas, "commands": commands}, sort_keys=True,
                                       default=str).encode("utf-8")).hexdigest()
    for enforcer, held in sorted(wanted.items()):
        command = commands[enforcer]
        record = _record(ctx, command, tree) if tree else None
        expected = {"command": command, "tree": tree, "kit_version": ctx.manifest.version, "declarations": digest}
        if record and ctx.workspace.exists(record) and _honoured(ctx, record, expected):
            print(f"prove: {enforcer} already went green on these exact bytes (tree {tree[:12]}) -- not run again; "
                  f"it holds {', '.join(map(str, held))}", flush=True)
            continue
        print(f"prove: {enforcer}: {command}", flush=True)
        done = subprocess.run(command, shell=True, cwd=str(ctx.workspace.root))
        verdict = "green" if done.returncode == 0 else f"RED (exit {done.returncode})"
        print(f"prove: {enforcer} is {verdict} -- it holds {', '.join(map(str, held))}", flush=True)
        if done.returncode != 0:
            red.append(enforcer)
        elif record and ctx.workspace.clean_tree() == tree:  # a command that wrote into the tree proved other bytes
            ctx.workspace.scoped((ephemeral.place(ctx, SUBJECT) + "/",)).write_json(
                record, dict(expected, green=True))
    if red:
        print(f"prove: REFUSED -- {', '.join(red)} red; a MUST whose enforcer is red does not hold")
        return 1
    print(f"prove: {len(wanted)} enforcer command(s) green")
    return 0
