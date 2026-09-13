"""Gate kind that holds a host to the kit it carries (ADR-016).

A host that cannot run a verb by itself is a host driven from outside, and one whose pinned copy
no longer equals the lock it carries is running something no release describes. Both are named
here, path by path, with the state the lock survey measured. The target is found through the
declaration of the install mode the params name -- never a path spelled in an interpreter.

Integrity only. Whether the lock is the one upstream published is a separate proposition that no
gate can measure until the kit's own lock is signed; `pin.UNSIGNED` says so on every surface that
states a release, and this gate never implies it by passing.
"""

from __future__ import annotations

import pin


def _pinned_kit_intact(ctx, params):
    item = ctx.install_of_mode(params["mode"], required=False)
    if item is None:
        return []
    failures, _pinned = pin.verify(ctx.workspace, item["target"])
    return failures


KINDS = {
    "pinned-kit-intact": _pinned_kit_intact,
}
