"""Gate kind for the STANDARDS CONFORMANCE MAP: "meets the standard" is a row with evidence, never prose
(ADR-024).

Each row names a standard and a clause, the kit mechanism that meets it, the EVIDENCE (a test, a gate, an
edit gate, a verb or a file) and a status. A `conformant` row whose evidence does not exist in this host
is refused -- and its tests are part of the suite, so evidence that does not pass fails the suite. Every
other status (partial, gap, mapping, non-goal, not-asserted) states why: a gap is an honest row, never
an omission, and a management-system standard a repository cannot meet alone is a `mapping`.
"""

from __future__ import annotations

import re

import declared

KIND = "conformance-held"
CONFORMANT = "conformant"
MAP = ({declared.CONTRACT: "conformance"}, "rows")


def _exists(ctx, evidence: str, known: set) -> bool:
    kind, _sep, name = evidence.partition(":")
    if kind == "test":
        path, _sep, function = name.partition("::")
        return ctx.workspace.exists(path) and bool(
            re.search(rf"^\s*def {re.escape(function)}\w*\(", ctx.workspace.read_text(path), re.M))
    if kind == "path":
        return ctx.workspace.exists(name)
    return evidence in known


def _known(ctx) -> set:
    known = {f"gate:{g['id']}" for c in ctx.enabled_capabilities() for g in c.gates}
    known |= {f"edit-gate:{r['id']}" for r in declared.rules(ctx, {declared.CONTRACT: "edit-gate"}, "gates")}
    known |= {f"verb:{p.stem}" for p in (ctx.manifest.root / "interpreters" / "verbs").glob("*.py")}
    return known


def judged(rows: list, exists) -> list:
    failures, counts = [], {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
        if row["status"] == CONFORMANT:
            missing = [e for e in row.get("evidence", []) if not exists(e)]
            if not row.get("evidence") or missing:
                failures.append(f"{row['id']}: conformant to {row['standard']} {row['clause']} with evidence that does "
                                f"not exist here ({missing or 'none named'})")
    return failures, counts


def _held(ctx, params) -> list:
    known = _known(ctx)
    rows = declared.rules(ctx, *MAP)
    failures, counts = judged(rows, lambda e: _exists(ctx, e, known))
    print("        READ the conformance map: " + (", ".join(f"{n} {s}" for s, n in sorted(counts.items())) or "no row"))
    return failures


def _calibrate(host):
    """A conformant row citing evidence nobody has is flagged; one citing evidence that exists is admitted."""
    row = {"id": "r", "standard": "S", "clause": "1", "status": CONFORMANT, "evidence": ["gate:G"]}
    return judged([row], lambda e: False)[0], judged([row], lambda e: True)[0]


KINDS = {KIND: _held}
CALIBRATIONS = {KIND: _calibrate}
