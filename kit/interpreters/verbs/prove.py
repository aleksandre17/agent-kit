"""prove -- run every command a MUST names as its enforcer, and fail if one is red (ADR-025 amendment 1).

    python .agents/kit/interpreters/cli.py prove --root . [--plan]

A norm that says MUST and names a COMMAND as its enforcer (`stack-kit:test`, vouched for by an adapter
that reads the host's own declaration) is enforced only where something runs that command. `check`
reads; it does not run a test suite. This verb is what runs them: the git adapter's pre-push hook calls
it after `check`, so a MUST whose command is red does not leave the machine. Each command runs once,
from the host root, however many norms name it; `--plan` names them and runs nothing. A MUST whose
enforcer an adapter vouches for, but whose command cannot be read -- the host's declaration missing,
unreadable, or silent on that key -- is refused, never read as nothing to run: an enforcer nobody can
run does not hold.
"""

from __future__ import annotations

import subprocess

import declared
import norms as norms_gate

SUMMARY = "run every command a MUST norm names as its enforcer -- the pre-push proof (blocking on red)"
MUTATES = False
REQUIRES_APPROVED_HOST = True


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
    if not wanted:
        print("prove: no MUST names a command as its enforcer -- nothing to run")
        return 0
    if getattr(args, "plan", False):
        for enforcer, held in sorted(wanted.items()):
            print(f"  would run  {commands[enforcer]}  ({enforcer}, for {', '.join(map(str, held))})")
        return 0
    red = []
    for enforcer, held in sorted(wanted.items()):
        command = commands[enforcer]
        print(f"prove: {enforcer}: {command}", flush=True)
        done = subprocess.run(command, shell=True, cwd=str(ctx.workspace.root))
        verdict = "green" if done.returncode == 0 else f"RED (exit {done.returncode})"
        print(f"prove: {enforcer} is {verdict} -- it holds {', '.join(map(str, held))}", flush=True)
        if done.returncode != 0:
            red.append(enforcer)
    if red:
        print(f"prove: REFUSED -- {', '.join(red)} red; a MUST whose enforcer is red does not hold")
        return 1
    print(f"prove: {len(wanted)} enforcer command(s) green")
    return 0
