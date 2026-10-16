"""Gate kind for an EXECUTION GRAPH: a unit's obligations are DERIVED from what it operates on, never
declared by the unit itself (ADR-024).

A plan of risky work is units with dependencies. A unit that could declare its own way out of a
safeguard ("not destructive", "no backup needed") is a rule satisfied by editing the flag on the thing
being checked. So a unit declares only WHAT it does -- operations, each a verb on a governed object --
and the OBJECT REGISTRY says what each verb on that object obliges (a backup, a rollback class, an
owner's decision, evidence). This gate derives every unit's obligations from the registry and holds
it to them: each derived obligation is satisfied by a pointer to a file that exists. It also holds the
graph to be a graph: ids unique, dependencies declared, no cycle. It certifies the plan's structure,
and runs nothing.
"""

from __future__ import annotations

import changes
import declared

KIND = "execution-graph-held"
GRAPHS = ({declared.CONTRACT: "execution-graph"},)


def derived(registry: dict, unit: dict) -> set:
    """Every obligation a unit's operations carry, from the registry alone."""
    found = set()
    for operation in unit.get("operations", []):
        found |= set((registry.get(operation["object"]) or {}).get("obliges", {}).get(operation["verb"], []))
    return found


def judged(graph: dict, exists) -> list:
    failures = []
    registry = {row["id"]: row for row in graph["objects"]}
    units = {}
    for unit in graph["units"]:
        if unit["id"] in units:
            failures.append(f"unit {unit['id']!r} is declared twice")
        units[unit["id"]] = unit
    for unit in units.values():
        for operation in unit.get("operations", []):
            obj = registry.get(operation["object"])
            if obj is None:
                failures.append(f"{unit['id']}: operates on {operation['object']!r}, which the registry does not declare")
            elif operation["verb"] not in obj.get("obliges", {}):
                failures.append(f"{unit['id']}: {operation['verb']!r} on {operation['object']!r} is not a verb the "
                                f"registry declares for it")
        for need in sorted(derived(registry, unit) - set(unit.get("satisfies", {}))):
            failures.append(f"{unit['id']}: owes {need!r} (derived from what it operates on) and satisfies it nowhere")
        for need, pointer in sorted(unit.get("satisfies", {}).items()):
            if not exists(pointer):
                failures.append(f"{unit['id']}: satisfies {need!r} with {pointer}, which does not exist")
        for dep in unit.get("depends_on", []):
            if dep not in units:
                failures.append(f"{unit['id']}: depends on {dep!r}, which the graph does not declare")
    state = {}

    def visit(node, trail):
        if state.get(node) == 1:
            failures.append(f"a dependency cycle: {' -> '.join(trail + [node])}")
            return
        if state.get(node) == 2 or node not in units:
            return
        state[node] = 1
        for dep in units[node].get("depends_on", []):
            visit(dep, trail + [node])
        state[node] = 2

    for node in units:
        visit(node, [])
    return failures


def _held(ctx, params) -> list:
    failures = []
    found = changes.seeded(ctx, GRAPHS[0][declared.CONTRACT])
    for name, graph in ([(GRAPHS[0][declared.CONTRACT], found)] if found else []):
        print(f"        READ {name}: {len(graph['units'])} unit(s) over {len(graph['objects'])} governed object(s)")
        failures += [f"{name}: {f}" for f in judged(graph, ctx.workspace.exists)]
    return failures


def _calibrate(host):
    """A unit that writes a governed object without the backup the registry obliges is flagged; the
    same unit pointing at its backup is admitted."""
    registry = [{"id": "ledger", "obliges": {"write": ["backup"]}}]
    owing = {"objects": registry, "units": [{"id": "u1", "operations": [{"verb": "write", "object": "ledger"}]}]}
    paid = {"objects": registry, "units": [{"id": "u1", "operations": [{"verb": "write", "object": "ledger"}],
                                            "satisfies": {"backup": "backup.txt"}}]}
    return judged(owing, lambda rel: True), judged(paid, lambda rel: True)


KINDS = {KIND: _held}
CALIBRATIONS = {KIND: _calibrate}
