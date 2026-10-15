"""Registers -- rows a host keeps about one subject, held to the statuses their kind declares (ADR-022).

One gate, three properties, and none of them a word of any register: every row's status is a status
of its register's kind; a row carries every field its status requires; and a row PROMOTED out of a
register names a place that exists and cites the row back as `<register>#<row>` -- a promotion
recorded at one end only is how a rule acquires clauses nobody can date. Nothing is moved and
nothing is rewritten: a row is a host's, and so is its repair.
"""

from __future__ import annotations

import collection
import declared

REQUIRES, PROMOTED_TO = "requires", "promoted_to"


def _kinds(ctx, params) -> dict:
    return {row["id"]: row for row in declared.rules(ctx, params["kinds"], "kinds")}


def _registers(ctx, params) -> list:
    found = []
    for name in declared.named(ctx.enabled_capabilities(), params["sources"]):
        for capability in ctx.enabled_capabilities():
            for item in capability.installs:
                if item.get("reads_as") == name:
                    found += collection.read(ctx, item, name).records
    return found


def _held(ctx, registers, kinds) -> list:
    failures = []
    for rel, register in registers:
        kind = kinds.get(register.get("kind"))
        if kind is None:
            failures.append(f"{rel}: kind {register.get('kind')!r} is declared by no register kind "
                            f"(declared: {sorted(kinds)})")
            continue
        statuses = {s["id"]: s for s in kind["statuses"]}
        for row in register.get("rows", []):
            where = f"{rel}: {register['id']}#{row['id']}"
            status = statuses.get(row.get("status"))
            if status is None:
                failures.append(f"{where} is {row.get('status')!r}, which kind {kind['id']!r} does not declare "
                                f"(it declares {sorted(statuses)})")
                continue
            for field in status.get(REQUIRES, []):
                if not row.get(field):
                    failures.append(f"{where} is {status['id']!r}, which requires {field!r}, and the row has none")
            target = row.get(PROMOTED_TO)
            if target:
                cite = f"{register['id']}#{row['id']}"
                if not ctx.workspace.exists(target):
                    failures.append(f"{where} was promoted to {target}, which does not exist")
                elif cite not in ctx.workspace.read_text(target):
                    failures.append(f"{where} was promoted to {target}, which does not cite {cite!r} back -- "
                                    f"a promotion is recorded at both ends")
    return failures


def _register_held(ctx, params) -> list:
    return _held(ctx, _registers(ctx, params), _kinds(ctx, params))


def _calibrate_register_held(host):
    """A row in an undeclared status, and a promotion its target never cites back, are flagged; a row
    whose status is declared and whose promotion is cited is admitted."""
    kinds = {"k": {"id": "k", "statuses": [{"id": "a-plain-status", "means": "m"},
                                            {"id": "a-status-that-moves", "means": "m", "requires": [PROMOTED_TO]}]}}
    bad = [("r.json", {"id": "r", "kind": "k", "rows": [
        {"id": "a", "status": "nobody-declares-this"},
        {"id": "b", "status": "a-status-that-moves", PROMOTED_TO: "law.md"}]})]
    good = [("r.json", {"id": "r", "kind": "k", "rows": [
        {"id": "a", "status": "a-plain-status"}, {"id": "b", "status": "a-status-that-moves", PROMOTED_TO: "law.md"}]})]
    specimen = host({"law.md": "a law with no citation"})
    lookalike = host({"law.md": "a law, from r#b"})
    return _held(specimen, bad, kinds), _held(lookalike, good, kinds)


KINDS = {"register-held": _register_held}
CALIBRATIONS = {"register-held": _calibrate_register_held}
