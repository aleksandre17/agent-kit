"""The version-control port -- the one place the kit asks the repository what it carries.

Two readings need it and must never disagree: the ratchet's previous ACCEPTED state, and the set
of files a reading may depend on (ADR-021 decision 8). A reading of the tree that counted a file
the repository does not carry -- a dependency directory, a build output -- would change the day
someone ran an install, and read stale on every clean clone with nothing about the host having
moved. So both readings go through here, and so does every later one.

Bytes are decoded here and nowhere else, as UTF-8 and never as the machine's locale: two sides
agreeing on a name and disagreeing on its encoding is the failure that reads as a thing simply not
being there (Cardinal VII). A missing tool, a tree that is not a repository and a path that is not
in HEAD all arrive as the same kind of answer -- a REASON, which the caller states instead of
guessing past it.
"""

from __future__ import annotations

import subprocess


def run(root, argv: list) -> tuple:
    """`(what version control said, None)` or `(None, why it could not say it)`."""
    try:
        done = subprocess.run(["git", "-C", str(root), *argv], capture_output=True)
    except (OSError, ValueError) as exc:
        return None, f"git could not be run over this tree -- {exc}"
    if done.returncode != 0:
        said = done.stderr.decode("utf-8", "replace").strip()
        return None, said or f"git exited {done.returncode} and said nothing"
    return done.stdout.decode("utf-8", "replace"), None


def carried(root) -> "list | None":
    """Every file the repository at `root` carries or would carry: tracked, plus untracked and not
    ignored -- host-relative, `/`-separated, sorted. `None` where no repository answers: the caller
    then reads the filesystem, and says nothing it could not have read either way."""
    said, _why = run(root, ["ls-files", "-z", "--cached", "--others", "--exclude-standard"])
    if said is None:
        return None
    return sorted({p for p in said.split("\0") if p})


def tracked(root) -> "list | None":
    """Every file the repository at `root` TRACKS -- what a clone receives, never an untracked file
    a person left beside it -- host-relative, `/`-separated, sorted; `None` where no repository
    answers (the whole-tree audit, ADR-024 decision 20)."""
    said, _why = run(root, ["ls-files", "-z", "--cached"])
    if said is None:
        return None
    return sorted({p for p in said.split("\0") if p})


def _paths(root, argv: list) -> tuple:
    said, why = run(root, argv)
    return (None, why) if said is None else ([p for p in said.split("\0") if p], None)


def _born(root) -> bool:
    return run(root, ["rev-parse", "--verify", "--quiet", "HEAD"])[0] is not None


def staged_paths(root) -> tuple:
    """`(paths, None)` the next commit records -- the index against HEAD, or the whole index before
    the first commit -- or `(None, why)`."""
    if not _born(root):
        return _paths(root, ["ls-files", "-z"])
    return _paths(root, ["diff", "--cached", "--no-renames", "--name-only", "-z", "HEAD", "--"])


def working_paths(root) -> tuple:
    """`(paths, None)` of the working change -- what differs from HEAD, staged or not, and what is
    untracked and not ignored -- or `(None, why)`."""
    tracked = (_paths(root, ["diff", "--no-renames", "--name-only", "-z", "HEAD", "--"]) if _born(root)
               else _paths(root, ["ls-files", "-z"]))
    others = _paths(root, ["ls-files", "--others", "--exclude-standard", "-z"])
    for found in (tracked, others):
        if found[0] is None:
            return found
    return sorted(set(tracked[0]) | set(others[0])), None


def range_paths(root, base: str, head: str) -> tuple:
    """`(paths, None)` changed between two revisions, or `(None, why)`."""
    return _paths(root, ["diff", "--no-renames", "--name-only", "-z", base, head, "--"])
