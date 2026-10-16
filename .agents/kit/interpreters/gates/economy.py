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

import statistics

import admission
import dispatching
import returns

PEAK, CALLS = "peak_context", "calls_per_delivery"
PER_ACCEPTED = "tokens_per_accepted_change"
#: The GenAI semantic-convention attribute a run's output tokens are recorded under (`dispatching`).
OUT_TOKENS = "gen_ai.usage.output_tokens"
UNCLASSED = "unclassed"


def _peak(ctx, params) -> "int | None":
    peaks = [r["economy"]["peak_context"] for r in returns.recorded(ctx)
             if isinstance(r.get("economy"), dict) and isinstance(r["economy"].get("peak_context"), int)]
    return max(peaks) if peaks else None


def _calls(ctx, params) -> "int | None":
    calls = [r["economy"]["calls"] for r in returns.recorded(ctx)
             if (r.get("deliverable") or {}).get("status") == "delivered"
             and isinstance((r.get("economy") or {}).get("calls"), int)]
    return int(statistics.median(calls)) if calls else None


def accepted(task) -> bool:
    """A change accepted on its FIRST pass: completed, admitted, and not escalated."""
    return (task.get("state") == dispatching.COMPLETED and (task.get("admission") or {}).get("verdict") == admission.ADMITTED
            and not task.get("escalate"))


def _out_tokens(task) -> int:
    value = (task.get("telemetry") or {}).get(OUT_TOKENS)
    return value if isinstance(value, int) else 0


def frontier(ctx) -> dict:
    """task class -> (runs, first-pass accepted, output tokens, output tokens per accepted change)."""
    found = {}
    for task in returns.tasks(ctx):
        cls = (task.get("route") or {}).get("task_class") or UNCLASSED
        runs, ok, out = found.get(cls, (0, 0, 0))[:3]
        found[cls] = (runs + 1, ok + (1 if accepted(task) else 0), out + _out_tokens(task))
    return {cls: (runs, ok, out, (out // ok) if ok else None) for cls, (runs, ok, out) in found.items()}


def candidates(ctx, times: int) -> list:
    """(instruction, count) for every task given the same instruction `times` or more: deterministic work
    a model was paid to repeat -- a candidate to become a verb or a script."""
    counts = {}
    for task in returns.tasks(ctx):
        said = " ".join(((task.get("packet") or {}).get("instruction") or "").lower().split())
        if said:
            counts[said] = counts.get(said, 0) + 1
    return sorted((said, n) for said, n in counts.items() if n >= times)


def _reported(ctx, params) -> list:
    """The FRONTIER, measured: per class of work, how many runs, how many accepted on their first pass,
    and the output tokens each accepted change cost -- and the repeated work that should be a script.
    Reported, never failed: the cheapest route is kept while these numbers and the evals hold."""
    table = frontier(ctx)
    if not table:
        print("        NOTHING DISPATCHED -- no task record on this host, so no cost was measured")
    for cls, (runs, ok, out, per) in sorted(table.items()):
        print(f"        FRONTIER {cls}: {runs} run(s), {ok} accepted on the first pass "
              f"({(100 * ok) // runs}%), {out} output token(s), {per if per is not None else 'n/a'} per accepted change")
    for said, n in candidates(ctx, params.get("repeated", 3)):
        print(f"        CANDIDATE  the same task {n} times -- make it a verb or a script: {said[:100]}")
    return []


def _per_accepted(ctx, params) -> "int | None":
    table = frontier(ctx)
    ok = sum(row[1] for row in table.values())
    return (sum(row[2] for row in table.values()) // ok) if ok else None


KINDS = {"frontier-reported": _reported}

#: What this module can be held to a BUDGET on (ADR-019 decision 9).
MEASURES = {PEAK: _peak, CALLS: _calls, PER_ACCEPTED: _per_accepted}
