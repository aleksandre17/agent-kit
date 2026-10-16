"""What dispatched workers handed back -- the returns the port recorded on their tasks (ADR-022).

A core reading, so a gate that measures the work's cost reaches it through the core and never
through the port that wrote it (the arrow: a gate judges, a port adapts the world).
"""

from __future__ import annotations

import json

import dispatching
import ephemeral


def recorded(ctx) -> list:
    """Every structured return a dispatch on this host recorded, read from its task record."""
    home = ephemeral.place(ctx, dispatching.HOME)
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
