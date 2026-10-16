"""Gate kind that holds a host to the kit it carries (ADR-016).

A host that cannot run a verb by itself is a host driven from outside, and one whose pinned copy
no longer equals the lock it carries is running something no release describes. Both are named
here, path by path, with the state the lock survey measured. A REFERENCED host (its lock carries a
`reference`) is judged where it holds the kit -- present, at the pinned commit, equal to the lock. The tree and the seat of the lock the
host was given are found through the declarations of the two install modes the params name --
never a path spelled in an interpreter.

Integrity only. Whether the lock is the one upstream published is a separate proposition that no
gate can measure until the kit's own lock is signed; `pin.UNSIGNED` says so on every surface that
states a release, and this gate never implies it by passing.
"""

from __future__ import annotations

import pin
import reference


def _pinned_kit_intact(ctx, params):
    item = ctx.install_of_mode(params["mode"], required=False)
    if item is None:
        return []
    # A REFERENCED host keeps no copy: the kit it holds in its own tree is judged against the same
    # lock -- present, at the pinned commit, byte for byte (ADR-024 decision 18).
    held = reference.of(ctx)
    if held is not None:
        print(f"        referenced: {held['path']}/ at {held['commit'][:12]} in {held['repository']}")
        return reference.verify(ctx, held)
    seat = ctx.install_of_mode(params["lock_mode"])
    failures, _pinned = pin.verify(ctx.manifest, ctx.workspace, item["target"], seat["target"])
    return failures


KINDS = {
    "pinned-kit-intact": _pinned_kit_intact,
}
