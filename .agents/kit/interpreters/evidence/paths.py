"""Evidence about PATHS: that one is there, in which shape, or that a pattern matches what the
repository carries. Discovered by the probe through the kinds registry (`EVIDENCE`), so a new kind
of evidence is a module here and never an edit to the probe."""

from __future__ import annotations

import os
import re
from pathlib import Path


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
    directories (none included), `*` and `?` never cross a `/`, and `[...]` (`[!...]` negated) is one
    character of a class, never a `/`."""
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
        elif pattern[i] == "[" and "]" in pattern[i + 2:]:
            end = pattern.index("]", i + 2)
            body = pattern[i + 1:end]
            negated = body.startswith("!")
            body = body[1:] if negated else body
            klass = "".join("\\" + c if c in "\\^[]" else c for c in body)
            out, i = out + (f"(?!/)[^{klass}]" if negated else f"[{klass}]"), end + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile(out + r"\Z")


def _walked(ws, prune: dict) -> list:
    """Every file under the host root, as a walk finds it where no repository answers -- never inside
    the kit's own planes (`roots`), a directory an adapter names to prune (`names`), a directory holding
    a vendored kit's manifest (`markers`), or a repository's own store or a repository of its own."""
    names = set(prune.get("names") or ())
    roots = {str(r).strip("/") for r in prune.get("roots") or ()}
    markers = tuple(prune.get("markers") or ())
    out = []
    for here, dirs, files in os.walk(ws.root):
        rel = Path(here).relative_to(ws.root).as_posix()
        prefix = "" if rel == "." else rel + "/"
        dirs[:] = sorted(d for d in dirs if d not in names and prefix + d not in roots
                         and not ws.outside_tree(prefix + d)
                         and not any((Path(here) / d / m).is_file() for m in markers))
        out += [prefix + f for f in files]
    return sorted(out)


def _glob_any(ws, spec, ours):
    carried = ws.carried()
    if carried is None:
        carried = _walked(ws, spec.get("prune") or {})
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
