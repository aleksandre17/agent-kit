"""The ground ledger -- a measured fact, dated to the evidence that produced it (ADR-022 decision 4).

THE PROBLEM IT REMOVES. Measured in the prior system: in:out was ~100:1, and the waste was SEARCHING,
not thinking -- three runs mapped overlapping territory because each booted cold, and a router briefed
a worker with hours-old facts that the worker, correctly, refused. Both are one defect: a measured
fact carried no WHEN and no ON WHAT, so it could be neither trusted nor reused.

THE MECHANISM. A reading is recorded with the INSTRUMENT that produced it and the narrowest PATHS it
depends on, and stamped with a digest of only those paths' content -- the working tree's, read through
what the repository carries, because the movements that matter are uncommitted and a fact that
survives an uncommitted edit is a lie. It is returned only while those paths still digest the same.
Otherwise the answer is a DECLARED MISS that names which paths moved and hands back the instrument, so
re-measuring is one paste. A fact about one directory never expires because another one moved.

It lives in the observed plane: a cache with an expiry rule, never an archive and never doctrine. A
clone that has none is correct. The store is append-only; the last reading of a key wins.
"""

from __future__ import annotations

import hashlib
import json
import os

import ephemeral
from errors import KitError

KIND = "ground-reading"
LEDGER = "ground/ledger.jsonl"


class GroundRefused(KitError):
    """A reading that cannot be recorded or read as asked: no key, no instrument, or no path to expire
    with -- a fact that depends on nothing never expires, and so is never true for long."""

    code = "KIT0069"


class GroundMiss(KitError):
    """A DECLARED MISS: the key was never measured here, or what it depends on has moved since. A
    verdict, not a failure -- it names what moved and hands back the instrument."""

    code = "KIT0070"
    exit_code = 4


def digest(ctx, paths) -> dict:
    """{path: sha256 of the content under it} -- only the files the repository carries (ADR-021
    decision 8), or every file where no repository answers. A path holding nothing digests as
    absent, which is itself a state that can move."""
    carried = ctx.workspace.carried()
    folded = {}
    for rel in paths:
        prefix = rel.rstrip("/")
        if carried is None:
            names = ([prefix] if ctx.workspace.path(prefix).is_file()
                     else ctx.workspace.files_under(prefix))
        else:
            names = [p for p in carried if p == prefix or p.startswith(prefix + "/")]
        lines = []
        for name in sorted(names):
            if ctx.workspace.path(name).is_file():
                lines.append(f"{hashlib.sha256(ctx.workspace.read_bytes(name)).hexdigest()}  {name}")
        folded[rel] = (hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest() if lines else "absent")
    return folded


def _place(ctx) -> str:
    return ephemeral.place(ctx, LEDGER)


def _read(ctx) -> tuple:
    """({key: the last reading recorded under it}, how many lines did not honour the kind): a line that
    cannot be read is skipped and COUNTED, never silently dropped."""
    rel = _place(ctx)
    if not ctx.workspace.exists(rel):
        return {}, 0
    found, skipped = {}, 0
    for line in ctx.workspace.read_text(rel).splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            skipped += 1
            continue
        if ctx.manifest.validate(row, KIND):
            skipped += 1
        else:
            found[row["key"]] = row
    return found, skipped


def readings(ctx) -> dict:
    """{key: the last reading recorded under it} -- the lines that cannot be read are counted by `_read`."""
    return _read(ctx)[0]


def record(ctx, key: str, fact: str, instrument: str, paths, at: str, by: str = None) -> dict:
    if not key or not fact or not instrument:
        raise GroundRefused("a reading needs a key, a fact and the instrument that produced it -- a fact "
                            "without its instrument cannot be checked against the question it answers")
    if not paths:
        raise GroundRefused("a reading names the narrowest paths it depends on, and expires with them; a "
                            "fact that depends on nothing never expires, and so is never true for long")
    row = {"schema_version": ctx.manifest.version_of(KIND), "key": key, "fact": fact,
           "instrument": instrument, "paths": list(paths), "digest": digest(ctx, paths), "at": at}
    if by:
        row["by"] = by
    errors = ctx.manifest.validate(row, KIND)
    if errors:
        raise GroundRefused("the reading does not honour its own schema:\n  " + "\n  ".join(errors))
    rel = _place(ctx)
    whole = ctx.workspace.path(rel)
    whole.parent.mkdir(parents=True, exist_ok=True)
    # One append, one line: two writers may interleave lines, never tear one.
    handle = os.open(whole, os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_BINARY", 0))
    try:
        os.write(handle, (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))
    finally:
        os.close(handle)
    return row


def get(ctx, key: str) -> dict:
    """The reading under `key` while its paths still digest the same -- or a declared MISS."""
    found, skipped = _read(ctx)
    row = found.get(key)
    if row is None:
        unread = (f" -- or it was, on one of the {skipped} ledger line(s) that cannot be read ({_place(ctx)})"
                  if skipped else "")
        raise GroundMiss(f"{key!r} has never been measured on this host{unread}. Measure it, then record it "
                         f"with the instrument that produced it.")
    now = digest(ctx, row["paths"])
    moved = sorted(p for p in row["paths"] if now.get(p) != row["digest"].get(p))
    if moved:
        raise GroundMiss(f"{key!r} was measured at {row['at']} and {moved} have moved since, so the "
                         f"reading no longer holds. Re-measure with: {row['instrument']}")
    return row
