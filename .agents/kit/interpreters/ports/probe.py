"""Probe port -- the single generic evaluator of detector declarations.

A detector states what would be true and what that would mean. This port states HOW any such
statement is checked, and knows no stack, no ecosystem, no repository. New evidence kinds join an
open registry by declaration; there is no ladder of known environments anywhere in this file, and
the day there is one, every new ecosystem needs the framework's permission to exist.

Capture semantics: an emitted value of the form "$N" is the value captured by the Nth evidence
item (1-based). A capture that is absent emits NOTHING for that key -- an unmeasured fact is a
declared absence, never a fabricated default.

A file the repository does not carry is never evidence either (ADR-021 decision 8). A pattern is
matched against what the repository carries -- tracked, and untracked but not ignored -- so a
dependency directory or a build output can never become a fact about the host, and a reading taken
on a working copy reads the same on a clean clone. Where no repository answers, the filesystem is
read, and the reading says no more than either could.

A path the kit SERVED is never evidence about the host. A detector reads what the host brings; a
file the kit itself projected there is the kit's own output, and a measurement that observes its
own output is a loop: the reading would change because a render ran, and a profile taken before
the render would read stale after it with nothing about the host having moved. Which paths are the
kit's is one reading, handed in by the context from the kit's own record -- never guessed here.
"""

from __future__ import annotations

import json
import re

from errors import KitError


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


def _json_path(ws, spec, ours):
    """Read one key path out of a JSON file. Pointer is dot-separated; no expression language."""
    target = ws.path(spec["path"])
    if spec["path"] in ours or not target.is_file():
        return False, None
    try:
        value = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False, None
    for step in spec["pointer"].split("."):
        if not isinstance(value, dict) or step not in value:
            return False, None
        value = value[step]
    return True, value


EVIDENCE_KINDS = {
    "dir_exists": _dir_exists,
    "file_exists": _file_exists,
    "path_exists": _path_exists,
    "glob_any": _glob_any,
    "json_path": _json_path,
}


class ProbeError(KitError):
    """A detector declared an evidence kind this interpreter does not know how to evaluate."""

    code = "KIT0016"


class Probe:
    """Evaluates detector declarations against a workspace. Reads only."""

    def __init__(self, workspace, ours=None) -> None:
        self._ws = workspace
        #: A callable answering which host-relative paths the kit served -- read once per run.
        self._ours = ours or (lambda: set())

    def run(self, detectors: list) -> tuple[dict, list]:
        facts: dict = {}
        results: list = []
        self._served = set(self._ours())
        for detector in sorted(detectors, key=lambda d: d["id"]):
            matched, captures = self._evaluate(detector)
            results.append({"id": detector["id"], "matched": matched})
            if matched:
                facts.update(self._emit(detector, captures))
        return dict(sorted(facts.items())), results

    def _evaluate(self, detector) -> tuple[bool, list]:
        matched = True
        captures: list = []
        for spec in detector["evidence"]:
            kind = spec["kind"]
            if kind not in EVIDENCE_KINDS:
                raise ProbeError(
                    f"detector {detector['id']!r}: unknown evidence kind {kind!r}; "
                    f"declared kinds are {sorted(EVIDENCE_KINDS)}"
                )
            ok, captured = EVIDENCE_KINDS[kind](self._ws, spec, self._served)
            captures.append(captured if ok else None)
            if not ok and not spec.get("optional", False):
                matched = False
        return matched, captures

    @staticmethod
    def _emit(detector, captures) -> dict:
        emitted = {}
        for key, value in detector["emits"].items():
            if isinstance(value, str) and value.startswith("$") and value[1:].isdigit():
                index = int(value[1:]) - 1
                if index < 0 or index >= len(captures):
                    raise ProbeError(
                        f"detector {detector['id']!r}: {key!r} refers to evidence {value} "
                        f"but only {len(captures)} evidence items are declared"
                    )
                captured = captures[index]
                if captured is None:
                    continue
                emitted[key] = captured
            else:
                emitted[key] = value
        return emitted
