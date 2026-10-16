"""guard -- the hook before a command a runtime is about to run: a whole-tree destructive command gets a
recovery point first.

A command that discards work across the tree (`git reset --hard`, `git clean`, a recursive delete, a
worktree removal) is the one act an edit gate never sees: it writes no text. So before it runs, this
hook takes a side-effect-free RECOVERY POINT -- `git stash create` records the tracked changes as a
commit object without touching the tree or the stash list, and a ref under `refs/kit/recovery/` keeps
it reachable -- and lets the command through (advisory: the owner's act stays the owner's). Which
commands count is DECLARED (`destructive-commands`, a published policy); a host that takes none is
guarded against nothing, and says so by holding no rows. Untracked files are not in a stash object,
and the hook says that too.
"""

from __future__ import annotations

import json
import re
import sys

import declared
import hooks
import vcs

SUMMARY = "before a command a runtime runs: a destructive one gets a recovery point first (advisory)"
MUTATES = False
REQUIRES_APPROVED_HOST = True
POSTURE = hooks.ADVISORY
STDOUT_IS_THE_PRODUCTS = True
PATTERNS = ({declared.CONTRACT: "destructive-commands"}, "commands")
REFS = "refs/kit/recovery/"


def run(ctx, args) -> int:
    hand = hooks.hand_of(ctx, getattr(args, "surface", None))
    try:
        event = json.loads(sys.stdin.read() or "null")
    except ValueError:
        event = None
    command = hooks.first_of(event, hand.get("commands", [])) if event is not None else None
    if not command:
        return 0
    hit = next((row for row in declared.rules(ctx, *PATTERNS) if re.search(row["matches"], command)), None)
    if hit is None:
        return 0
    root = ctx.workspace.root
    made, why = vcs.run(root, ["stash", "create", f"kit recovery point before: {command[:120]}"])
    sha = (made or "").strip()
    if not sha:
        print(f"guard: {hit['id']} -- nothing tracked to keep ({why or 'the tree is clean'}); untracked files "
              f"are never in a recovery point", file=sys.stderr)
        return 0
    ref = f"{REFS}{ctx.clock.now().replace(':', '').replace('-', '')}"
    vcs.run(root, ["update-ref", ref, sha])
    print(f"guard: {hit['id']} -- recovery point {ref} ({sha[:12]}) taken before `{command[:80]}`; "
          f"restore tracked changes with `git stash apply {sha[:12]}`. Untracked files are not covered.",
          file=sys.stderr)
    return 0
