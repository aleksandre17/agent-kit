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

from pathlib import Path

import kinds
from errors import KitError


class ProbeError(KitError):
    """A detector declared an evidence kind this interpreter does not know how to evaluate."""

    code = "KIT0016"


#: Every evidence kind, by the name its module declares -- discovered, never listed here: a new kind
#: of evidence is a module in `evidence/`, and this port is not edited (Cardinal II).
EVIDENCE_KINDS = kinds.registry(Path(__file__).resolve().parents[1] / "evidence", "EVIDENCE",
                                "evidence kind", ProbeError)


class Probe:
    """Evaluates detector declarations against a workspace. Reads only."""

    def __init__(self, workspace, ours=None, planes=None) -> None:
        self._ws = workspace
        #: A callable answering which host-relative paths the kit served -- read once per run.
        self._ours = ours or (lambda: set())
        #: A callable answering (the kit's own plane roots, the file a vendored kit is known by): where a
        #: walk of the host's tree does not go when no repository answers what it carries.
        self._planes = planes or (lambda: ((), ()))

    def run(self, detectors: list) -> tuple[dict, list]:
        facts: dict = {}
        results: list = []
        self._served = set(self._ours())
        roots, markers = self._planes()
        self._skip = {"roots": list(roots), "markers": list(markers)}
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
            walk = {**self._skip, "names": list(detector.get("prune") or ())}
            ok, captured = EVIDENCE_KINDS[kind](self._ws, {**spec, "prune": walk}, self._served)
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
