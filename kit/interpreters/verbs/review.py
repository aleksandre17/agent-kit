"""review -- a review range COVERED by verified change records, read on a clean checkout of its head.

    python kit/interpreters/cli.py review --root <host> [--base <rev> --head <rev>]

Every path changed between the two revisions must be covered by a VERIFIED change record whose sources
still match what it verified. The checkout must BE the head and be clean: a range read against a tree
that differs from it certifies a change nobody can point at. Without a range the records are read for
structure alone and coverage is NOT_ASSERTED. The report is JSON, tri-state, and says what it cannot
assert: runtime conformance and production readiness belong to an external authority.
"""

from __future__ import annotations

import json

import changes
import vcs
from errors import KitError

SUMMARY = "check that a review range is covered by verified change records (tri-state JSON report)"
MUTATES = False
REQUIRES_APPROVED_HOST = True
ARGUMENTS = [
    ("--base", {"default": None, "help": "the revision a review range starts from"}),
    ("--head", {"default": None, "help": "the revision a review range ends at; the checkout must be it"}),
]


class ReviewRefused(KitError):
    """A review range that cannot be read honestly: half a range, an unresolvable revision, a checkout
    that is not the head or not clean."""

    code = "KIT0079"


def _git(root, *argv) -> str:
    said, why = vcs.run(root, list(argv))
    if said is None:
        raise ReviewRefused(f"git {' '.join(argv)} could not be read -- {why}")
    return said


def run(ctx, args) -> int:
    base, head = getattr(args, "base", None), getattr(args, "head", None)
    if bool(base) != bool(head):
        raise ReviewRefused("--base and --head name ONE range: give both or neither")
    changed = None
    if base:
        root = ctx.workspace.root
        start = _git(root, "rev-parse", "--verify", f"{base}^{{commit}}").strip()
        end = _git(root, "rev-parse", "--verify", f"{head}^{{commit}}").strip()
        if _git(root, "rev-parse", "HEAD").strip() != end:
            raise ReviewRefused(f"the checkout is not {head}: a range is read on a checkout of its head")
        if _git(root, "status", "--porcelain", "--untracked-files=normal").strip():
            raise ReviewRefused("the checkout is not clean: a range is read on exactly the bytes it ends at")
        changed = [p for p in _git(root, "diff", "--no-renames", "--name-only", "-z", start, end, "--").split("\0") if p]
    report = changes.validate(ctx, changed)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1
