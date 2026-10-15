"""Claims -- two principals on one tree, arbitrated by a claim that BITES (ADR-022 decision 7).

The prior system learned this twice. A coordination note two runtimes promised to read was crossed
on the day it was written, without any resistance at all: a note is not a mechanism. And when two
writers share one tree, the last writer wins SILENTLY -- every validator passes, and the loss is not
merely unprevented but undetectable.

Two signals, composed, and neither alone is enough:

  * a CLAIM is DECLARED and forward-looking -- "I am taking these paths from here on". A write under
    another principal's standing claim is refused by the one judge, before the bytes land.
  * a WRITE RECORD is OBSERVED and backward-looking -- "someone wrote here recently". A peer's
    admitted write to the same path inside the host's declared window refuses mine, because writing
    now would erase work nobody has merged (optimistic concurrency: the version-token / If-Match form).

The forward signal must be able to SUPERSEDE stale history on the path it now holds: a foreign write
that PREDATES my own claim is superseded by it; one written AFTER my claim still refuses. Without
that ordering the backward signal vetoes the forward one, and a principal is locked out of a path it
legitimately holds.

A claim is never broken by elapsed time (ADR-007): it stands until its owner releases it or a person
breaks it BY NAME, and the break is recorded on the claim. Its age is printed with every refusal, so
a stale one is visible -- never silently expired.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta

import collection
import ephemeral
from errors import KitError

CLAIM, ARBITRATION = "claim", "arbitration"
WRITES = "writes"


class ClaimRefused(KitError):
    """A claim asked for incompletely, or a release of a claim this principal does not hold."""

    code = "KIT0071"


def _install(ctx, kind: str):
    return next((i for c in ctx.enabled_capabilities() for i in c.installs if i.get("validates") == kind), None)


def _place(ctx) -> "str | None":
    found = _install(ctx, CLAIM)
    return None if found is None else found["target"].rstrip("/")


def standing(ctx) -> list:
    """Every claim on this host that has not been released or broken."""
    found = _install(ctx, CLAIM)
    if found is None:
        return []
    return [record for _rel, record in collection.read(ctx, found, found.get("reads_as")).records
            if isinstance(record, dict) and not record.get("released_at")]


def _write(ctx, value: dict) -> str:
    rel = f"{_place(ctx)}/{value['principal']}.json"
    ctx.workspace.scoped((rel,)).write_json(rel, value)
    return rel


def take(ctx, principal: str, paths, reason: str, now: str) -> dict:
    if not principal or not paths or not reason:
        raise ClaimRefused("a claim names its principal (--by), the paths it takes (--path) and why (--reason); "
                           "a claim nobody can read the reason of cannot be weighed by the one it blocks")
    if _place(ctx) is None:
        raise ClaimRefused("this host enables no capability that declares where claims live")
    value = {"schema_version": ctx.manifest.version_of(CLAIM), "principal": principal,
             "paths": sorted(set(paths)), "reason": reason, "taken_at": now}
    errors = ctx.manifest.validate(value, CLAIM)
    if errors:
        raise ClaimRefused("the claim does not honour its schema:\n  " + "\n  ".join(errors))
    _write(ctx, value)
    return value


def release(ctx, principal: str, now: str, broken_by: str = None) -> dict:
    held = next((c for c in standing(ctx) if c["principal"] == principal), None)
    if held is None:
        raise ClaimRefused(f"{principal!r} holds no standing claim on this host")
    held = dict(held, released_at=now)
    if broken_by:
        held["broken_by"] = broken_by
    _write(ctx, held)
    return held


def _covers(claimed: str, path: str) -> bool:
    claimed = claimed.rstrip("/")
    return path == claimed or path.startswith(claimed + "/")


def _window(ctx) -> int:
    found = _install(ctx, ARBITRATION)
    if found is None or not ctx.workspace.exists(found["target"]):
        return 0
    return int(ctx.workspace.read_json(found["target"]).get("window_minutes", 0))


def _writes_place(ctx) -> "str | None":
    """The observed write log -- beside the claims, never inside their space, so a log line is never
    read as a claim."""
    return None if _place(ctx) is None else ephemeral.place(ctx, WRITES)


def recorded(ctx, principals, paths, now: str) -> None:
    """An admitted write, observed: one line per path, in each principal's own log (two writers never
    share a file). Never raises -- a record fault must not turn an admitted write into a crash."""
    base = _writes_place(ctx)
    if base is None:
        return
    try:
        for principal in principals:
            whole = ctx.workspace.path(f"{base}/{principal}.jsonl")
            whole.parent.mkdir(parents=True, exist_ok=True)
            handle = os.open(whole, os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_BINARY", 0))
            try:
                for path in paths:
                    os.write(handle, (json.dumps({"path": path, "at": now}) + "\n").encode("utf-8"))
            finally:
                os.close(handle)
    except OSError as exc:
        import sys
        print(f"claims: the admitted write was not recorded -- {exc}", file=sys.stderr)


def _peer_writes(ctx, principals) -> list:
    base = _writes_place(ctx)
    if base is None or not ctx.workspace.exists(base):
        return []
    found = []
    for rel in ctx.workspace.files_under(base):
        owner = rel.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        if owner in principals:
            continue
        for line in ctx.workspace.read_text(rel).splitlines():
            try:
                row = json.loads(line)
            except ValueError:
                continue
            found.append((owner, row["path"], row["at"]))
    return found


def _moment(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def refusals(ctx, principals, paths, now: str) -> list:
    """[(path, why)] for every path these principals may not write now: under another principal's
    standing claim, or written by a peer inside the declared window and not superseded by a claim of
    mine that predates that write."""
    claims = standing(ctx)
    mine = [c for c in claims if c["principal"] in principals]
    found = []
    for path in paths:
        theirs = next((c for c in claims if c["principal"] not in principals
                       and any(_covers(p, path) for p in c["paths"])), None)
        if theirs is not None:
            found.append((path, f"claimed by {theirs['principal']} since {theirs['taken_at']} -- "
                                f"{theirs['reason']}. It stands until released or broken by name"))
    window = _window(ctx)
    if window:
        horizon = _moment(now) - timedelta(minutes=window)
        for owner, path, at in _peer_writes(ctx, principals):
            if path not in paths or _moment(at) < horizon or any(p == path for p, _w in found):
                continue
            lease = next((c for c in mine if any(_covers(p, path) for p in c["paths"])), None)
            if lease is not None and _moment(lease["taken_at"]) >= _moment(at):
                continue
            found.append((path, f"{owner} wrote it at {at}, inside this host's {window}-minute window, and "
                                f"writing now would erase work nobody has merged -- claim it after reading "
                                f"what {owner} wrote, or wait"))
    return found
