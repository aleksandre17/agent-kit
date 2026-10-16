"""extend -- scaffold a host's extension from its declared point, on demand; list the points; merge a
newer template into what the host wrote.

    ... cli.py extend --root <host> --list [--json]
    ... cli.py extend --root <host> --point <id> [--name <member>] [--plan] --approve <who>
    ... cli.py extend --root <host> --merge [--plan] --approve <who>

A member is written from its point's template, PENDING markers and all, and recorded in the host's
ledger with the template it came from. It is idempotent and never overwrites: a member that exists is
left as it is. `--merge` re-applies every newer template three ways (the template the member came
from, the template now, the host's file): a clean merge is written, a conflict is REPORTED and the
host's file kept. The kit's own copy is never edited.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import doors
import extensions
import validation

SUMMARY = "scaffold a host extension from its declared point, list the points, or merge a newer template"
MUTATES = True
REQUIRES_APPROVED_HOST = True
ARGUMENTS = [
    ("--list", {"action": "store_true", "help": "list every extension point, where it goes and its status"}),
    ("--json", {"action": "store_true", "help": "with --list: print the registry in the shared extension-points shape"}),
    ("--point", {"default": None, "help": "the extension point to scaffold"}),
    ("--name", {"default": None, "help": "the member's name, for a point that holds one per name"}),
    ("--merge", {"action": "store_true", "help": "merge every newer point template into the host's files"}),
]


def _ledger_item(ctx):
    return next(i for c in ctx.enabled_capabilities() for i in c.installs
                if i.get("validates") == extensions.LEDGER_CONTRACT)


def _ledger(ctx) -> dict:
    item = _ledger_item(ctx)
    if ctx.workspace.exists(item["target"]):
        return ctx.workspace.read_json(item["target"])
    return {"schema_version": ctx.manifest.version_of(extensions.LEDGER_CONTRACT), "generated": []}


def _write_ledger(ctx, ledger) -> None:
    item = _ledger_item(ctx)
    ctx.workspace.scoped((item["target"],)).write_json(item["target"], ledger)


def _merged(base: str, new: str, host: str):
    """(the three-way merge, clean?) -- git's own merge-file over three scratch files."""
    with tempfile.TemporaryDirectory() as scratch:
        paths = []
        for name, text in (("host", host), ("base", base), ("new", new)):
            path = Path(scratch) / name
            path.write_text(text, encoding="utf-8", newline="\n")
            paths.append(str(path))
        done = subprocess.run(["git", "merge-file", "-p", *paths], capture_output=True, text=True, encoding="utf-8")
        return done.stdout, done.returncode == 0


def _list(ctx, args) -> int:
    rows = extensions.registry(ctx)
    if getattr(args, "json", False):
        document = {"schema_version": 1, "points": [{k: v for k, v in r.items() if k not in ("capability", "root")}
                                                     for r in rows]}
        errors = validation.validate(document, ctx.manifest.schema("extension-points"))
        if errors:
            raise extensions.ExtensionError("the registry does not keep the shared shape:\n  " + "\n  ".join(errors))
        print(json.dumps(document, indent=2))
        return 0
    for row in rows:
        print(f"  {extensions.status(ctx, row):<9} {row['id']:<22} {row['host_path']}  -- {row['purpose']}")
    return 0


def _scaffold(ctx, args) -> int:
    row = extensions.point(ctx, args.point)
    rel = extensions.path_of(row, args.name)
    if ctx.workspace.exists(rel):
        print(f"extend: {rel} exists; an extension is never overwritten (run --merge for a newer template)")
        return 0
    text = extensions.template_text(ctx, row, args.name)
    print(f"extend: {row['id']} -> {rel} ({len(extensions.pending(text))} pending answer(s))")
    if getattr(args, "plan", False):
        return 0
    if not args.approve:
        doors.refuse(f"this host would gain {rel} at the point {row['id']!r}", "person who owns this host",
                     "extend --root <host> --point <id> [--name <n>] --approve <who>",
                     "An extension is the host's own file; whoever adds it is named on the ledger.")
    ctx.workspace.scoped((rel,)).write_text(rel, text)
    ledger = _ledger(ctx)
    ledger["generated"] = [g for g in ledger["generated"] if g["path"] != rel] + [
        {"point": row["id"], "path": rel, "template": row["template"], "base": text,
         "by": args.approve, "at": ctx.clock.now()}]
    _write_ledger(ctx, ledger)
    return 0


def merge(ctx, args) -> int:
    ledger = _ledger(ctx)
    conflicts = 0
    for entry in ledger["generated"]:
        name = next((n for n, rel in extensions.members(ctx, extensions.point(ctx, entry["point"]))
                     if rel == entry["path"]), None)
        new = extensions.template_text(ctx, extensions.point(ctx, entry["point"]), name)
        if new == entry["base"] or not ctx.workspace.exists(entry["path"]):
            continue
        text, clean = _merged(entry["base"], new, ctx.workspace.read_text(entry["path"]))
        if not clean:
            conflicts += 1
            print(f"  CONFLICT  {entry['path']}: the newer template of {entry['point']!r} conflicts with the "
                  f"host's text; the host's file is kept as it is")
            continue
        print(f"  merged    {entry['path']}: the newer template of {entry['point']!r}")
        if getattr(args, "plan", False) or not args.approve:
            continue
        ctx.workspace.scoped((entry["path"],)).write_text(entry["path"], text)
        entry["base"] = new
    if args.approve and not getattr(args, "plan", False):
        _write_ledger(ctx, ledger)
    return 1 if conflicts else 0


def run(ctx, args) -> int:
    if getattr(args, "list", False):
        return _list(ctx, args)
    if getattr(args, "merge", False):
        return merge(ctx, args)
    if not getattr(args, "point", None):
        raise extensions.ExtensionError("extend needs --list, --merge or --point <id>")
    return _scaffold(ctx, args)
