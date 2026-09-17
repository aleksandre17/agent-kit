"""The arrow -- a HOST's layers and the direction a dependency between them may run, applied by one
generic interpreter over the tree (`check`) and over an edit's introduced text (the one judge).

This module knows no layer, no language and no syntax for a dependency. It knows three SHAPES:

  * a READING: which files it applies to, a pattern whose group 1 is a referenced name, and the
    templates that locate that name in the tree -- with its own calibration;
  * a LAYER: a directory it is walked under and a pattern its files match;
  * a RULE: a layer, the layers it may depend on, why, what instead -- with its own calibration.

An edge is a (file, located file) pair; it is against the arrow when the first file's layer has a
rule and the second's layer is not in its `may`. A name located nowhere in the tree lies in no
layer, and no rule reaches it: the arrow governs the host's own parts, never what it consumes.
"""

from __future__ import annotations

import posixpath
import re

import declared

KIND = "arrow-held"
READINGS, LAYERS, RULES = "imports", "layers", "rules"


def _compiled(row, field, flags=0):
    try:
        return re.compile(row[field], flags), None
    except re.error as exc:
        return None, f"{row['id']}: its {field} {row[field]!r} is not a pattern -- {exc}"


class Arrow:
    """One host's arrow, read once from every declared source of the contract."""

    def __init__(self, ctx, sources):
        self.readings = declared.rules(ctx, sources, READINGS)
        self.layers = declared.rules(ctx, sources, LAYERS)
        self.rules = declared.rules(ctx, sources, RULES)

    # -- classification ---------------------------------------------------------------------
    def layers_of(self, path: str) -> list:
        found = []
        for layer in self.layers:
            pattern, _ = _compiled(layer, "paths")
            if pattern and pattern.search(path):
                found.append(layer["id"])
        return found

    def refused_by(self, rule, source: str, target: str) -> bool:
        return (rule["from"] in self.layers_of(source)
                and any(layer not in rule["may"] for layer in self.layers_of(target)))

    # -- reading ----------------------------------------------------------------------------
    @staticmethod
    def names(reading, text: str) -> list:
        pattern, _ = _compiled(reading, "reference", re.MULTILINE)
        return [m.group(1) for m in pattern.finditer(text)] if pattern and pattern.groups else []

    @staticmethod
    def located(ws, reading, source: str, name: str) -> list:
        step = name.replace(reading["separator"], "/") if reading.get("separator") else name
        found = []
        for template in reading["locates"]:
            rel = posixpath.normpath(template.replace("{dir}", posixpath.dirname(source))
                                     .replace("{ref}", step))
            if not rel.startswith("../") and rel not in found and ws.path(rel).is_file():
                found.append(rel)
        return found

    # -- calibration ------------------------------------------------------------------------
    def reading_failures(self, reading) -> list:
        broken = [e for e in (_compiled(reading, "files")[1],
                              _compiled(reading, "reference", re.MULTILINE)[1]) if e]
        if broken:
            return broken
        failures = []
        if self.names(reading, reading["proves"]["text"]) != reading["proves"]["yields"]:
            failures.append(f"{reading['id']}: UNCALIBRATED -- it does not read "
                            f"{reading['proves']['yields']} out of the text it declares it reads.")
        if self.names(reading, reading["admits"]["text"]):
            failures.append(f"{reading['id']}: UNCALIBRATED -- it reads a name out of the lookalike "
                            f"it declares holds none.")
        return failures

    def rule_failures(self, rule) -> list:
        known = {layer["id"] for layer in self.layers}
        unknown = sorted({rule["from"], *rule["may"]} - known)
        if unknown:
            return [f"{rule['id']}: names undeclared layer(s) {unknown}; a direction between places "
                    f"nobody declared points nowhere."]
        broken = [e for layer in self.layers if (e := _compiled(layer, "paths")[1])]
        if broken:
            return broken
        failures = []
        if not self.refused_by(rule, rule["proves"]["path"], rule["proves"]["to"]):
            failures.append(f"{rule['id']}: UNCALIBRATED -- it does not refuse the edge it declares it "
                            f"refuses ({rule['proves']['path']!r} -> {rule['proves']['to']!r}).")
        if self.refused_by(rule, rule["admits"]["path"], rule["admits"]["to"]):
            failures.append(f"{rule['id']}: UNCALIBRATED -- it also refuses the lookalike edge it "
                            f"declares legitimate ({rule['admits']['path']!r} -> {rule['admits']['to']!r}).")
        return failures

    # -- judging ----------------------------------------------------------------------------
    def against(self, ws, source: str, text: str):
        """(violations, unjudged ids) for one file's text: every (rule, name, located file) edge
        against the arrow. Uncalibrated readings and rules are named, never trusted."""
        readings, rules, unjudged = [], [], []
        for reading in self.readings:
            (unjudged if self.reading_failures(reading) else readings).append(reading)
        for rule in self.rules:
            (unjudged if self.rule_failures(rule) else rules).append(rule)
        governing = [r for r in rules if r["from"] in self.layers_of(source)]
        found = []
        if governing:
            for reading in readings:
                if not re.search(reading["files"], source):
                    continue
                for name in self.names(reading, text):
                    for target in self.located(ws, reading, source, name):
                        found += [(rule, name, target) for rule in governing
                                  if self.refused_by(rule, source, target)]
        return found, [row["id"] for row in unjudged]


def _because(rule, source, name, target) -> str:
    return (f"{source} depends on {target} (read as {name!r}); layer {rule['from']!r} may depend "
            f"only on {sorted(rule['may'])} -- {rule['because']}")


# -- over an edit: one entry of the one judge's registry ----------------------------------------
def _judged(ctx, params, edits):
    arrow = Arrow(ctx, params["sources"])
    refusals, unjudged = [], set()
    for path, text in edits:
        found, blind = arrow.against(ctx.workspace, path, text)
        unjudged |= set(blind)
        refusals += [(path, rule["id"], _because(rule, path, name, target), rule["instead"])
                     for rule, name, target in found]
    return refusals, sorted(unjudged)


# -- over the tree ------------------------------------------------------------------------------
def _held(ctx, params):
    arrow = Arrow(ctx, params["sources"])
    failures = [f for reading in arrow.readings for f in arrow.reading_failures(reading)]
    failures += [f for rule in arrow.rules for f in arrow.rule_failures(rule)]
    ws = ctx.workspace
    walked = sorted({f for layer in arrow.layers for f in ws.files_under(layer["within"])})
    for path in walked:
        homes = arrow.layers_of(path)
        if len(homes) > 1:
            failures.append(f"{path}: claimed by layers {homes}; one file, one home.")
    if failures:
        return failures
    for path in walked:
        if not any(re.search(r["files"], path) for r in arrow.readings):
            continue
        found, _ = arrow.against(ws, path, ws.read_text(path))
        failures += [f"{path} -> {target}  {rule['id']}: {_because(rule, path, name, target)}"
                     for rule, name, target in found]
    return failures


KINDS = {KIND: _held}
EDITS = {KIND: _judged}
