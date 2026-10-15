"""What a runtime is handed on every turn, measured (ADR-021 decision 5).

An entry file a runtime loads at the start of every session is the most expensive text a host
owns: every byte of it is paid on every turn, before any work. The kit serves one span of it, and
this module publishes the one count a host may hold that span to -- through the corpus plane's
ordinary budget (ADR-019 decision 9), never a ceiling spelled here. A host writes the number.
"""

from __future__ import annotations

import runtime as runtime_port

SPAN_BYTES = "served_span_bytes"


def _span_bytes(ctx, params) -> "int | None":
    """The largest span the kit serves on this host, in bytes. `None` where it serves none: a host
    that is handed nothing has no size to be held to, and 0 would read as a span that is empty."""
    import derivation
    sizes = []
    for rel, row in runtime_port.prior_rows(ctx, ctx.enabled_capabilities()).items():
        if row.get("span") and ctx.workspace.exists(rel):
            held = derivation.span(ctx.workspace.read_text(rel), row["span"])
            if held is not None:
                sizes.append(len(held.encode("utf-8")))
    return max(sizes) if sizes else None


KINDS = {}

#: What this module can be held to a BUDGET on (ADR-019 decision 9).
MEASURES = {SPAN_BYTES: _span_bytes}
