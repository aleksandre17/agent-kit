"""Probe port -- the single generic evaluator of detector declarations.

A detector states what would be true and what that would mean. This port states HOW any such
statement is checked, and knows no stack, no ecosystem, no repository. New evidence kinds join an
open registry by declaration; there is no ladder of known environments anywhere in this file, and
the day there is one, every new ecosystem needs the framework's permission to exist.

Capture semantics: an emitted value of the form "$N" is the value captured by the Nth evidence
item (1-based). A capture that is absent emits NOTHING for that key -- an unmeasured fact is a
declared absence, never a fabricated default.
"""

from __future__ import annotations

import json

from errors import KitError


def _dir_exists(ws, spec):
    return ws.path(spec["path"]).is_dir(), True


def _file_exists(ws, spec):
    return ws.path(spec["path"]).is_file(), True


def _glob_any(ws, spec):
    matches = sorted(p.name for p in ws.root.glob(spec["pattern"]))
    return bool(matches), matches or None


def _json_path(ws, spec):
    """Read one key path out of a JSON file. Pointer is dot-separated; no expression language."""
    target = ws.path(spec["path"])
    if not target.is_file():
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
    "glob_any": _glob_any,
    "json_path": _json_path,
}


class ProbeError(KitError):
    """A detector declared an evidence kind this interpreter does not know how to evaluate."""

    code = "KIT0016"


class Probe:
    """Evaluates detector declarations against a workspace. Reads only."""

    def __init__(self, workspace) -> None:
        self._ws = workspace

    def run(self, detectors: list) -> tuple[dict, list]:
        facts: dict = {}
        results: list = []
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
            ok, captured = EVIDENCE_KINDS[kind](self._ws, spec)
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
