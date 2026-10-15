"""What the work cost, measured from what the workers SAID it cost (ADR-022 decision 5).

The prior system ran on four numbers, and the one it watched above all was PEAK CONTEXT -- the
quadratic driver: every token a run holds is paid for again on every later call. This module
publishes the two of them a host can take TODAY without reading any product's transcript, because
they are fields of the return every dispatched worker now hands back (ADR-022 decision 2):

  * `peak_context`       -- the largest peak context any returned task reported;
  * `calls_per_delivery` -- the median of tool calls across tasks that DELIVERED.

A host holds them to a number through its corpus map, exactly as every other budgetable fact
(ADR-019 decision 9): the kit ships the measure and never the ceiling. Where no task has returned an
economy, the answer is `None` -- nothing was measured, which is not the same as nothing was spent.
"""

from __future__ import annotations

import json
import statistics

import dispatch_port
import ephemeral

PEAK, CALLS = "peak_context", "calls_per_delivery"


def _returns(ctx) -> list:
    """Every structured return this host's dispatches recorded, read from their task records."""
    home = ephemeral.place(ctx, dispatch_port.HOME)
    found = []
    for rel in ctx.workspace.files_under(home):
        if not rel.endswith("/task.json"):
            continue
        try:
            record = json.loads(ctx.workspace.read_text(rel))
        except (OSError, ValueError):
            continue
        if isinstance(record.get("return"), dict):
            found.append(record["return"])
    return found


def _peak(ctx, params) -> "int | None":
    peaks = [r["economy"]["peak_context"] for r in _returns(ctx)
             if isinstance(r.get("economy"), dict) and isinstance(r["economy"].get("peak_context"), int)]
    return max(peaks) if peaks else None


def _calls(ctx, params) -> "int | None":
    calls = [r["economy"]["calls"] for r in _returns(ctx)
             if (r.get("deliverable") or {}).get("status") == "delivered"
             and isinstance((r.get("economy") or {}).get("calls"), int)]
    return int(statistics.median(calls)) if calls else None


KINDS = {}

#: What this module can be held to a BUDGET on (ADR-019 decision 9).
MEASURES = {PEAK: _peak, CALLS: _calls}
