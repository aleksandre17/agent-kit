"""The spans the kit serves into host-owned files, as they stand now (ADR-021 decision 5).

A core reading of the serve record, so a gate that measures what a runtime is handed reaches it
through the core and never through the port that serves it.
"""

from __future__ import annotations

import derivation
import runtime as runtime_port


def sizes(ctx) -> list:
    """The size in bytes of every span the kit's record says it served and the file still marks out."""
    found = []
    for rel, row in runtime_port.prior_rows(ctx, ctx.enabled_capabilities()).items():
        if row.get("span") and ctx.workspace.exists(rel):
            held = derivation.span(ctx.workspace.read_text(rel), row["span"])
            if held is not None:
                found.append(len(held.encode("utf-8")))
    return found
