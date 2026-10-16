"""One source for a host's laws -- `check`'s reading of where the served law list comes from (ADR-024 d. 21).

The law list a runtime is served is rendered from the host's rules that carry a `law` number. A host
that has not moved yet still has its deprecated law page served; one that authors both is FAILED, by
name, because a law with two homes is two laws the day one is edited. The numbers run 1..n in the
order the rules are declared, so the rendered order is the declared one.
"""

from __future__ import annotations

import declared
import laws

KIND = "laws-one-source"


def _reading(ctx, params) -> tuple:
    norms = []
    for value in declared.sources(ctx, [params["rules_from"]]).values():
        norms += value if isinstance(value, list) else []
    return ctx.workspace.exists(params["deprecated"]), norms


def _held(ctx, params):
    present, norms = _reading(ctx, params)
    return laws.judged(present, params["deprecated"], norms)


def _report(ctx, params) -> str:
    present, norms = _reading(ctx, params)
    if present and not laws.numbered(norms):
        return (f"laws: served from the DEPRECATED page {params['deprecated']}; `upgrade --mode laws "
                f"--approve <who>` moves each numbered law into a rule in the norms")
    return f"laws: {len(laws.numbered(norms))} law(s) served from this host's numbered rules"


def _calibrate(host):
    """Both sources authored are flagged; the numbered rules alone are admitted."""
    rule = {"id": "host@1.0.0#law-1", laws.FIELD: 1}
    return laws.judged(True, "laws.md", [rule]), laws.judged(False, "laws.md", [rule])


KINDS = {KIND: _held}
CALIBRATIONS = {KIND: _calibrate}
REPORTS = {KIND: _report}
