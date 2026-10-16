"""Install modes that PIN the kit: the whole kit verbatim, and the lock it is judged against (ADR-016).

Decided by `pin`, which owns what a release is.
"""

from __future__ import annotations

import pin
from installmodes import Mode


def _foresee_tree(ws, item, state):
    """The kit itself: created where nothing is pinned, KEPT where the host already holds exactly
    this kit intact, replaced otherwise -- and refused here, in the plan, where it cannot be done
    honestly (ADR-016)."""
    tree, lock = pin.seats(state["manifest"])
    return pin.foresee(state["manifest"], ws, tree, lock)


def _foresee_lock(ws, item, state):
    """The seat of the lock the host was given: one act with the tree, so one decision."""
    tree, lock = pin.seats(state["manifest"])
    return pin.foresee_lock(state["manifest"], ws, tree, lock)


def _tree(ctx, ws, item, state):
    """The WHOLE kit, verbatim, beside the lock it is judged against: from now on this host can
    run every verb by itself, from its own copy (ADR-016)."""
    given = pin.deliver(ctx.manifest, ws, item["target"], state["reading"]["taken_at"])
    what = "a release" if given["released"] else f"a working tree (+{pin.UNRELEASED})"
    print(f"  pinned     {given['count']} path(s) of {what}, lock sha256:{given['lock'][:16]} -- "
          f"this host now runs: python {item['target']}interpreters/cli.py <verb> --root .")


def _lock(ctx, ws, item, state):
    """The lock the host was given, at its declared seat -- the other half of the pinned act."""
    tree, _lock = pin.seats(ctx.manifest)
    pin.deliver_lock(ctx.manifest, ws, tree, item["target"], state["reading"]["taken_at"])


MODES = {
    "pinned": Mode("install", _foresee_tree, _tree),
    "pinned-lock": Mode("install", _foresee_lock, _lock),
}
