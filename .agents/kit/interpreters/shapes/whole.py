"""The `document` projection shape -- one template, one file: a surface ABOUT a set.

Its target is stated in the declaration, so a plan names it before a single binding exists.
"""

from __future__ import annotations

import template
from shaping import Shape

def _project_one(ctx, item, view) -> dict:
    """One template, one file. The ordinary projection: a surface ABOUT a set."""
    return {item["target"]: template.render(ctx.manifest.payload_text(item["source"]), view)}




SHAPES = {"document": Shape(stage=0, project=lambda ctx, item, view, produced, capabilities:
                            _project_one(ctx, item, view),
                            foresee=lambda ctx, item, view, capabilities: [item["target"]],
                            reads_view=False)}
