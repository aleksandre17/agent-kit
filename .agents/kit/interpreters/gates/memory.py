"""Memory held to its contract -- a product's persistent memory POINTS, never copies (ADR-024).

Some runtimes keep notes across sessions outside the repository (a product's memory directory). What
lands there is read on later turns like any briefing, so it is held to two rules a host takes as a
policy:

  * it carries no SECRET -- every edit gate this host holds is applied to its text, as to an edit;
  * it duplicates no fact the repository already holds -- a line of memory that is also a line of a
    file the repository carries is a second home for that fact, and the two drift. Memory names WHERE
    a fact lives; the repository holds it (one source of truth).

Where a product keeps its memory is the product's fact, declared on its surface (`memory`), never here.
A home that is absent is NOT MEASURED -- a fresh machine or a clone made for one run holds none -- and
is said so in those words.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import declared
import judgement
import serving

KIND = "memory-held"
SURFACES = ({declared.CONTRACT: "runtime-surface"}, "surfaces")


def home_of(ctx, memory: dict) -> Path:
    """The directory a surface's product keeps this repository's memory in: its declared template,
    with `{repo_slug}` the host root's absolute path in the product's declared slug form."""
    slug = memory.get("slug") or {}
    root = str(ctx.workspace.root)
    named = re.sub(slug["replace"], slug["with"], root) if slug else root
    return Path(os.path.expanduser(memory["home"].replace("{repo_slug}", named)))


def _lines(text: str, shortest: int) -> set:
    return {line.strip() for line in text.splitlines() if len(line.strip()) >= shortest}


def copies(text: str, carried: dict, shortest: int) -> list:
    """(line, the repository file holding it) for every line of `text` that the repository holds."""
    return [(line, carried[line]) for line in sorted(_lines(text, shortest)) if line in carried]


def _held(ctx, params) -> list:
    shortest = params.get("shortest_shared_line", 60)
    served = serving.served_surfaces(ctx, ctx.enabled_capabilities())
    failures = []
    carried = None
    for surface in declared.rules(ctx, *SURFACES):
        memory = surface.get("memory")
        if not memory or surface["id"] not in served:
            continue
        home = home_of(ctx, memory)
        notes = sorted(home.glob("**/*.md")) if home.is_dir() else []
        if not notes:
            print(f"        NOT MEASURED  {surface['id']}: no memory at {home} on this machine")
            continue
        if carried is None:
            carried = {}
            for rel in ctx.workspace.carried() or []:
                try:
                    carried.update({line: rel for line in _lines(ctx.workspace.read_text(rel), shortest)})
                except (OSError, UnicodeDecodeError):
                    continue
        for note in notes:
            text = note.read_text(encoding="utf-8", errors="replace")
            refused, _blind = judgement.refusals(ctx, [(f"{surface['id']}-memory/{note.name}", text)])
            failures += [f"{note}: {gate} -- {because}" for _p, gate, because, _i in refused]
            failures += [f"{note}: copies {where} ({line[:60]}...) -- point to it instead"
                         for line, where in copies(text, carried, shortest)]
        print(f"        MEASURED  {surface['id']}: {len(notes)} memory file(s) at {home}")
    return failures


def _calibrate(host):
    """A memory line copying a repository file is flagged; a pointer to that file is admitted."""
    line = "The deploy targets are declared per environment in the targets file, one row per server."
    carried = {line: "ops/notes.md"}
    return copies(line + "\n", carried, 60), copies("Deploy targets: see ops/notes.md.\n", carried, 60)


KINDS = {KIND: _held}
CALIBRATIONS = {KIND: _calibrate}
