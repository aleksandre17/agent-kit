"""What dispatched workers handed back -- the returns the port recorded on their tasks (ADR-022).

A core reading, so a gate that measures the work's cost reaches it through the core and never
through the port that wrote it (the arrow: a gate judges, a port adapts the world).
"""

from __future__ import annotations

import json

import dispatching
import ephemeral


def _read(ctx) -> tuple:
    """(records, unreadable): every task record a dispatch on this host left, and the path of each one
    that could not be read -- named by its reader, never skipped silently (CWE-223)."""
    home = ephemeral.place(ctx, dispatching.HOME)
    found, unread = [], []
    for rel in ctx.workspace.files_under(home):
        if not rel.endswith("/task.json"):
            continue
        try:
            found.append(json.loads(ctx.workspace.read_text(rel)))
        except (OSError, ValueError):
            unread.append(rel)
    return found, unread


def tasks(ctx) -> list:
    """Every readable task record a dispatch on this host left -- its route, its ending, its admission
    and what it cost (`telemetry`). The ones that cannot be read are `unreadable`."""
    return _read(ctx)[0]


def unreadable(ctx) -> list:
    """The task records that exist and cannot be read: no figure counts them, so every figure says so."""
    return _read(ctx)[1]


def recorded(ctx) -> list:
    """Every structured return a dispatch on this host recorded, read from its task record."""
    return [record["return"] for record in tasks(ctx) if isinstance(record.get("return"), dict)]
