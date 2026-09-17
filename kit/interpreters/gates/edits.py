"""Edit gates -- a HOST's judgement over the edits made in it, applied by one generic judge.

This module knows no gate, no path, no product and no runtime. It knows two SHAPES:

  * an edit gate: a path pattern, a pattern over the text an edit introduces, and its own
    calibration (one edit it must refuse, one lookalike it must admit);
  * a HAND: how some product passes a hook the edit it is making -- dotted keys into the event,
    and, where the product speaks in patches, the two patterns that read one. Both arrive as data
    from a runtime surface; which product declared them is never asked here.

Where the gates live is not spelled here either: it is the `sources` of every gate of this kind
an enabled capability declares, so `check` (which calibrates) and `judge` (which applies) read one
declaration and cannot disagree about which rules exist.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import declared

#: The field by which an edit-gate document carries its rows -- the schema's word, one home.
RULES = "gates"
KIND = "edit-gates-calibrated"


# -- the gates ----------------------------------------------------------------------------------
def rules_of(ctx) -> list:
    """Every edit gate this host holds, found through the gate declarations of this kind."""
    rows = []
    for capability in ctx.enabled_capabilities():
        for gate in capability.gates:
            if gate["kind"] == KIND:
                rows += declared.rules(ctx, gate["params"]["sources"], RULES)
    return rows


def _pattern(rule, field, flags=0):
    try:
        return re.compile(rule[field], flags), None
    except re.error as exc:
        return None, f"{rule['id']}: its {field} {rule[field]!r} is not a pattern -- {exc}"


def refusals(rule, path: str, text: str) -> bool:
    paths, _ = _pattern(rule, "paths")
    forbids, _ = _pattern(rule, "forbids", re.MULTILINE)
    return bool(paths and forbids and paths.search(path) and forbids.search(text))


def calibration(rule) -> list:
    """What a gate can prove about itself before any edit is judged on its word."""
    broken = [e for e in (_pattern(rule, "paths")[1], _pattern(rule, "forbids", re.MULTILINE)[1]) if e]
    if broken:
        return broken
    failures = []
    if not refusals(rule, rule["proves"]["path"], rule["proves"]["text"]):
        failures.append(f"{rule['id']}: UNCALIBRATED -- it does not refuse the edit it declares it "
                        f"refuses ({rule['proves']['path']!r}). No edit is judged on its word.")
    if refusals(rule, rule["admits"]["path"], rule["admits"]["text"]):
        failures.append(f"{rule['id']}: UNCALIBRATED -- it also refuses the lookalike it declares "
                        f"legitimate ({rule['admits']['path']!r}). No edit is judged on its word.")
    return failures


def judge(rules: list, edits: list) -> tuple:
    """(refusals, unjudged): every (path, gate) an edit violates, and every gate that could not be
    applied because it is uncalibrated -- named, never silently skipped and never trusted."""
    calibrated, unjudged = [], []
    for rule in rules:
        (unjudged if calibration(rule) else calibrated).append(rule)
    found = [(path, rule) for path, text in edits for rule in calibrated if refusals(rule, path, text)]
    return found, [rule["id"] for rule in unjudged]


# -- the hand: what a product passes a hook ----------------------------------------------------
def _at(value, dotted: str) -> list:
    """Every value at a dotted key; `*` fans over a list. Absent is an empty list, never a guess."""
    found = [value]
    for part in dotted.split("."):
        nxt = []
        for item in found:
            if part == "*" and isinstance(item, list):
                nxt += item
            elif isinstance(item, dict) and part in item:
                nxt.append(item[part])
        found = nxt
    # A blank string names nothing: read as a path it would resolve to the host root itself.
    return [v for v in found if isinstance(v, str) and v.strip()]


def _first(event, keys) -> list:
    for key in keys:
        values = _at(event, key)
        if values:
            return values
    return []


def _patched(event, patch: dict) -> list:
    """(raw path, introduced text) per file a patch touches, read by the two declared patterns."""
    header, added = re.compile(patch["file"]), re.compile(patch["line"])
    files: dict = {}
    for body in _first(event, patch["from"]):
        current = None
        for line in body.splitlines():
            named = header.match(line)
            if named:
                # A header naming a blank path names no file: its lines belong to nothing.
                current = named.group(1) if named.group(1).strip() else None
                if current is not None:
                    files.setdefault(current, [])
                continue
            line_added = added.match(line)
            if current is not None and line_added:
                files[current].append(line_added.group(1))
    return [(path, "\n".join(lines)) for path, lines in files.items()]


def edits_in(event, hand: dict) -> list:
    """(raw path, introduced text) for every file this event says is being edited."""
    found = []
    texts = "\n".join(t for key in hand.get("texts", []) for t in _at(event, key))
    for path in _first(event, hand.get("paths", [])):
        found.append((path, texts))
    if hand.get("patch"):
        found += _patched(event, hand["patch"])
    return found


def host_relative(root: Path, raw: str) -> "str | None":
    """A path a product handed across the boundary, as the host-relative POSIX path a gate reads --
    or None when it lies outside this host, whose gates do not reach it. Measured, never assumed:
    a product may hand an absolute Windows path, a relative one, or either case of a drive."""
    candidate = Path(raw) if os.path.isabs(raw) else root / raw
    full, base = os.path.normcase(os.path.abspath(candidate)), os.path.normcase(os.path.abspath(root))
    if full != base and not full.startswith(base.rstrip(os.sep) + os.sep):
        return None
    return Path(os.path.relpath(os.path.abspath(candidate), os.path.abspath(root))).as_posix()


# -- the gate kind -----------------------------------------------------------------------------
def _edit_gates_calibrated(ctx, params):
    return [failure for rule in declared.rules(ctx, params["sources"], RULES)
            for failure in calibration(rule)]


KINDS = {KIND: _edit_gates_calibrated}
