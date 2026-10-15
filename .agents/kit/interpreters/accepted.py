"""The previous ACCEPTED state of a place -- what HEAD holds, never what the tree holds now (ADR-019).

A core reading, so the ratchet that compares a declaration with its accepted predecessor reaches
version control through the core and never through the port directly. Both answers are a value or
the reason there is none, in its own words -- a missing tool, a tree that is no repository and a
path absent from HEAD are all the same kind of answer.
"""

from __future__ import annotations

import vcs


def listing(root, space: str) -> tuple:
    """(the file names under `space` at HEAD, None) or (None, why)."""
    return vcs.run(root, ["ls-tree", "-r", "--name-only", "--full-tree", f"HEAD:./{space}"])


def text(root, rel: str) -> tuple:
    """(the text of `rel` at HEAD, None) or (None, why)."""
    return vcs.run(root, ["show", f"HEAD:./{rel}"])
