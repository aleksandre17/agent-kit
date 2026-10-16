"""Evidence about PATHS: that one is there, in which shape, or that a pattern matches what the
repository carries. Discovered by the probe through the kinds registry (`EVIDENCE`), so a new kind
of evidence is a module here and never an edit to the probe."""

from __future__ import annotations

import re


def _dir_exists(ws, spec, ours):
    return ws.path(spec["path"]).is_dir(), True


def _file_exists(ws, spec, ours):
    return spec["path"] not in ours and ws.path(spec["path"]).is_file(), True


def _path_exists(ws, spec, ours):
    """A path is THERE -- whether it is a file, a directory, or a link to either.

    Some truths are about presence, not shape, and asserting the shape is how a detector
    starts lying about a tree that is perfectly valid. `.git` is the standing example: a
    normal clone holds a DIRECTORY, while a submodule, a linked worktree and
    `--separate-git-dir` all hold a FILE pointing elsewhere. Git reads all four as a working
    tree; a `dir_exists` check reads three of them as "not a repository".
    """
    return spec["path"] not in ours and ws.path(spec["path"]).exists(), True


def _pattern(pattern: str):
    """A glob as a regular expression over `/`-separated paths: `**/` is any number of whole
    directories (none included), `*` and `?` never cross a `/`."""
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out, i = out + "(?:[^/]+/)*", i + 3
        elif pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pattern[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif pattern[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile(out + r"\Z")


def _glob_any(ws, spec, ours):
    carried = ws.carried()
    if carried is None:
        found = [p.relative_to(ws.root).as_posix() for p in ws.root.glob(spec["pattern"])]
    else:
        shape = _pattern(spec["pattern"])
        found = [rel for rel in carried if shape.match(rel)]
    matches = sorted(rel.rsplit("/", 1)[-1] for rel in found if rel not in ours)
    return bool(matches), matches or None


EVIDENCE = {
    "dir_exists": _dir_exists,
    "file_exists": _file_exists,
    "path_exists": _path_exists,
    "glob_any": _glob_any,
}
