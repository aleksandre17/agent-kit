"""ledger -- the hook after a product's own sub-agent stops: what it was ASKED to run on, what it RAN on,
and what it cost, one line in the observed plane.

The dispatch port records its own workers (run records, ADR-024). A product's in-session sub-agents
are started by the product, so the only witness is the product's own record of the run: its
transcript. The surface declares where the sub-agent-stop event names it and how one transcript line
carries a model turn (`hands.ledger`); this verb reads that and nothing else -- one turn per declared
key (the last line of a key wins), numbers summed, strings collected -- and appends one row under
OpenTelemetry GenAI attribute names. A requested model the turns did not run on is NAMED, never
smoothed over: that is the check the ledger exists for. Advisory: a ledger never stops a sub-agent.

    ... cli.py ledger --root <host> --surface <id>   # the hook: the event on stdin
    ... cli.py ledger --root <host>                  # read the ledger back: one line per agent kind
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import ephemeral
import hooks

SUMMARY = "after a product's sub-agent stops: requested vs verified model and tokens, one ledger row (advisory)"
MUTATES = False
REQUIRES_APPROVED_HOST = True
POSTURE = hooks.ADVISORY
STDOUT_IS_THE_PRODUCTS = True
LEDGER = "ledger"
OPERATION, AGENT_ID, AGENT_NAME, PROVIDER = ("gen_ai.operation.name", "gen_ai.agent.id", "gen_ai.agent.name",
                                             "gen_ai.provider.name")
REQUESTED, RESPONDED = "gen_ai.request.model", "gen_ai.response.model"


def _at(value, key: str):
    for part in key.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def read(hand: dict, event, root: Path) -> dict:
    """One ledger row for one sub-agent-stop event, read through a surface's declared `ledger`. Pure but
    for reading the transcript the event names; a transcript that cannot be read is `reported: false`."""
    spec = hand["ledger"]
    row = {OPERATION: "invoke_agent", PROVIDER: spec["provider"],
           AGENT_ID: hooks.first_of(event, spec["agent"]), AGENT_NAME: hooks.first_of(event, spec.get("name", []))}
    named = hooks.first_of(event, spec["transcript"])
    path = Path(named).expanduser() if named else None
    if path is not None and not path.is_absolute():
        path = root / path
    if path is None or not path.is_file():
        return {**row, "reported": False, "turns": 0}
    entries, turns = spec["entries"], {}
    for text in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            line = json.loads(text)
        except ValueError:
            continue
        if isinstance(line, dict) and all(line.get(k) == v for k, v in (entries.get("where") or {}).items()):
            key = _at(line, entries["key"])
            if key is not None:
                turns[key] = line
    for name, key in entries["fields"].items():
        values = [v for v in (_at(t, key) for t in turns.values()) if v is not None]
        if values and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values):
            row[name] = sum(values)
        elif values:
            seen = sorted({str(v) for v in values})
            row[name] = seen[0] if len(seen) == 1 else seen
    asked, ran = row.get(REQUESTED), row.get(RESPONDED)
    if asked is not None and ran is not None:
        row["mismatch"] = asked != ran
    return {**row, "reported": bool(turns), "turns": len(turns)}


def _files(ctx) -> list:
    base = ephemeral.place(ctx, LEDGER)
    folder = ctx.workspace.path(base)
    return [f"{base}/{p.name}" for p in sorted(folder.glob("*.jsonl"))] if folder.is_dir() else []


def _summary(ctx) -> int:
    rows = []
    for rel in _files(ctx):
        rows += [json.loads(t) for t in ctx.workspace.read_text(rel).splitlines() if t.strip()]
    if not rows:
        print("ledger: no sub-agent has been recorded on this host")
        return 0
    kinds: dict = {}
    for row in rows:
        kind = kinds.setdefault(row.get(AGENT_NAME) or "unnamed", {"runs": 0, "mismatch": 0, "in": 0, "out": 0})
        kind["runs"] += 1
        kind["mismatch"] += 1 if row.get("mismatch") else 0
        kind["in"] += row.get("gen_ai.usage.input_tokens") or 0
        kind["out"] += row.get("gen_ai.usage.output_tokens") or 0
    for name, kind in sorted(kinds.items()):
        print(f"  {name}: {kind['runs']} run(s), {kind['mismatch']} on a model other than the one requested, "
              f"{kind['in']} input / {kind['out']} output tokens")
    return 0


def run(ctx, args) -> int:
    surface = getattr(args, "surface", None)
    if surface is None:
        return _summary(ctx)
    hand = hooks.hand_of(ctx, surface)
    try:
        event = json.loads(sys.stdin.read() or "null")
    except ValueError:
        event = None
    if "ledger" not in hand or not isinstance(event, dict):
        print(f"ledger: nothing recorded -- the surface {surface!r} declares no `hands.ledger`, or handed no "
              f"event", file=sys.stderr)
        return 0
    row = {"at": ctx.clock.now(), "surface": surface, **read(hand, event, ctx.workspace.root)}
    path = ctx.workspace.path(ephemeral.place(ctx, f"{LEDGER}/{surface}.jsonl"))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as out:
        out.write(json.dumps(row) + "\n")
    if row.get("mismatch"):
        print(f"ledger: the sub-agent {row[AGENT_NAME] or row[AGENT_ID]} was asked to run on {row[REQUESTED]} and "
              f"ran on {row[RESPONDED]}", file=sys.stderr)
    return 0
