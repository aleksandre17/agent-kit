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

import re

import declared

#: The field by which an edit-gate document carries its rows -- the schema's word, one home.
RULES = "gates"
KIND = "edit-gates-calibrated"


# -- the gates ----------------------------------------------------------------------------------
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
    # A hand that CARRIES a patch hands the patch itself: the whole event is its one body.
    bodies = [event] if isinstance(event, str) else _first(event, patch.get("from", []))
    for body in bodies:
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
    if isinstance(event, str):  # a patch handed as itself names its files in its own grammar
        return _patched(event, hand["patch"]) if hand.get("patch") else []
    texts ="\n".join(t for key in hand.get("texts", []) for t in _at(event, key))
    for path in _first(event, hand.get("paths", [])):
        found.append((path, texts))
    if hand.get("patch"):
        found += _patched(event, hand["patch"])
    return found


# -- the gate kind -----------------------------------------------------------------------------
def _edit_gates_calibrated(ctx, params):
    return [failure for rule in declared.rules(ctx, params["sources"], RULES)
            for failure in calibration(rule)]


def _published_roots(ctx) -> list:
    """Where a PUBLISHER's bytes sit on the host: the pinned kit and every taken capability. They are
    held by their digests (`pinned-kit-intact`, `taken-intact`), not by the host's text policy -- and
    a published policy carries, as each gate's `proves`, the very text it refuses, so judging those
    planes would refuse the commit that takes it."""
    roots = [p["root"].rstrip("/") + "/" for p in ctx.manifest.planes if p["class"] == "vendor"]
    roots += [i["target"] for c in ctx.manifest.capabilities for i in c.installs
              if i["mode"] == "taken"]
    return roots


def _judged(ctx, params, edits):
    """This kind's entry in the one judge's registry: (path, id, because, instead) per refusal.

    The declaration the gates live in is not judged by them: every gate carries, as its `proves`,
    the very text it refuses, so a gate whose paths reach its own declaration would refuse the edit
    that declares it -- and `check` already holds that file to its schema and its calibration."""
    own = declared.homes(ctx, params["sources"])
    published = _published_roots(ctx)
    edits = [(path, text) for path, text in edits
             if path not in own and not any(path.startswith(root) for root in published)]
    found, unjudged = judge(declared.rules(ctx, params["sources"], RULES), edits)
    return [(path, rule["id"], rule["because"], rule["instead"]) for path, rule in found], unjudged


KINDS = {KIND: _edit_gates_calibrated}
#: How a gate kind judges an EDIT, beside how it judges the tree: the judge verb reads every kind's
#: entry through one registry, so a new kind of edit rule is a module, never a second judge.
EDITS = {KIND: _judged}
