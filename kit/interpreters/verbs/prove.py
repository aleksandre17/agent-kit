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
proved by every command a MUST names. Which it was, and why, is printed.

Nothing is proved twice on the same bytes (Cardinal IX): a command that went green on a clean tree is
recorded in the observed plane with that tree's id, and is not run again while the tree is the same --
a second push of what was proved, a retry after a refused push. The key is the exact bytes, never a
guess at what a command depends on: any change at all, a dirty tree, `--full`, or another command
string runs it again. A red run is never recorded. A MUST whose
enforcer an adapter vouches for, but whose command cannot be read -- the host's declaration missing,
unreadable, or silent on that key -- is refused, never read as nothing to run: an enforcer nobody can
run does not hold.
"""

from __future__ import annotations

import subprocess

import hashlib

import declared
import ephemeral
import norms as norms_gate
import weighing
import workclass

SUMMARY = "run every command a MUST norm names as its enforcer -- the pre-push proof (blocking on red)"
MUTATES = False
REQUIRES_APPROVED_HOST = True
ARGUMENTS = [("--full", {"action": "store_true", "help": "prove with every command a MUST names, whatever the change"})]


def _commands(ctx) -> tuple:
    """(`<prefix>:<key>` -> the command string for every key a vouching document finds in the host,
    `<prefix>` -> why its declaration could not be read)."""
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
        for step in document["pointer"].split("."):
            value = value.get(step) if isinstance(value, dict) else None
        if isinstance(value, dict):
            found.update({f"{document['prefix']}:{key}": given for key, given in value.items()
                          if isinstance(given, str) and given.strip()})
    return found, unread


#: Where a green proof is remembered, in the observed plane: by command and by the exact tree it read.
SUBJECT = "proofs"


def _record(ctx, command: str, tree: str) -> str:
    key = hashlib.sha256(f"{command}\n{tree}".encode("utf-8")).hexdigest()[:32]
    return ephemeral.place(ctx, f"{SUBJECT}/{key}.json")


def _scope(ctx, args) -> tuple:
    """(the commands that prove what this push carries, why) -- or (None, why): every command."""
    if getattr(args, "full", False):
        return None, "--full: every command a MUST names"
    found = workclass.declarations(ctx)
    if found is None:
        return None, "this host weighs nothing (no work classes): every command a MUST names"
    paths, why = ctx.workspace.unpushed_paths()
    if paths is None:
        return None, f"what this push carries could not be read ({why}): every command a MUST names"
    commands, why = weighing.proof_for(paths, *found)
    return commands, (why if commands is None else f"{why}: proved by {', '.join(commands) or 'check alone'}")


def run(ctx, args) -> int:
    commands, unread = _commands(ctx)
    wanted, missing = {}, {}
    for norm in norms_gate.norms_of(ctx):
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
    # or without a MUST; everything -- the unscoped path -- is what the MUSTs name.
    scoped, why = _scope(ctx, args)
    if scoped is not None:
        print(f"prove: {why}")
        unknown = [c for c in scoped if c not in commands]
        if unknown:
            print(f"prove: REFUSED -- an area names {', '.join(unknown)} as its proof, which no vouching declaration "
                  f"runs")
            return 1
        musts = [h for held in wanted.values() for h in held]
        wanted = {c: musts or ["the areas the change touches"] for c in scoped}
        if not wanted:
            print("prove: nothing beyond `check` proves this change")
            return 0
    elif not wanted:
        declared_test = (ctx.take_reading().get("facts") or {}).get("quality.tests.command")
        if not declared_test:
            print("prove: no MUST names a command, no area declares a proof, and this host's reading declares no test "
                  "command -- nothing to run")
            return 0
        # From the first day: what the host's briefing already says proves a change is what proves it here
        # (`areas` refines it by module).
        print(f"prove: no MUST names a command and no area declares a proof -- proved by the test command this "
              f"host declares: {declared_test}")
        commands = {**commands, "declared:test": declared_test}
        wanted = {"declared:test": ["the host's declared test command"]}
    else:
        print(f"prove: {why}")
    if getattr(args, "plan", False):
        for enforcer, held in sorted(wanted.items()):
            print(f"  would run  {commands[enforcer]}  ({enforcer}, for {', '.join(map(str, held))})")
        return 0
    red = []
    tree = None if getattr(args, "full", False) else ctx.workspace.clean_tree()
    for enforcer, held in sorted(wanted.items()):
        command = commands[enforcer]
        record = _record(ctx, command, tree) if tree else None
        if record and ctx.workspace.exists(record):
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
                record, {"command": command, "tree": tree, "green": True})
    if red:
        print(f"prove: REFUSED -- {', '.join(red)} red; a MUST whose enforcer is red does not hold")
        return 1
    print(f"prove: {len(wanted)} enforcer command(s) green")
    return 0
