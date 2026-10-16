"""The `contracts` resolver -- which contracts this host's enabled capabilities INSTALL, as plain data a
served setting can test with a logic-less section.

A served setting sometimes wires a hook only where the host took what the hook holds: the stop gate
holds a continuity capsule, so it is served where some enabled capability installs a document under
the `continuity-capsule` contract, and nowhere else (ADR-024). The answer is a reading of the host's
own declarations, never a list of bundles: `{"continuity_capsule": true}` -- each contract id with its
hyphens as underscores, the one spelling a template name may take. A contract nobody installs is
simply absent, and a section over it renders nothing.
"""

from __future__ import annotations


def _taken(ctx, params) -> dict:
    return {item["validates"].replace("-", "_"): True
            for capability in ctx.enabled_capabilities() for item in capability.installs
            if item.get("validates")}


RESOLVES = {"contracts": _taken}
