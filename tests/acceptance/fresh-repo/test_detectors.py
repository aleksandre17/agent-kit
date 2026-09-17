"""Acceptance: the DETECTOR plane -- a reading of the host that is pure data.

A detector states what would be true of a tree and what that would MEAN. It carries no branch and
no knowledge of any ecosystem; the Probe port states how any such statement is checked. Two
failure modes follow, and both are attacked here rather than asserted:

  1. **The detector that cannot fire.** A declaration whose evidence no real tree can satisfy is
     indistinguishable, on every host anyone owns, from a detector that works. So each declared
     detector is met with a tree built FROM ITS OWN EVIDENCE and must be measured as matching,
     with every fact it promises actually emitted -- captures included, since a capture that
     silently vanishes is the fabricated absence Cardinal V forbids.

  2. **The detector that always fires.** Worse, because it reads as a successful measurement. A
     detector all of whose evidence is optional, or whose pattern matches anything, would report
     an ecosystem onto hosts that have none. So each is also met with a tree that carries NO
     evidence at all, and must stay silent there.

Nothing here names a detector, a fact, a filename or a pattern. The trees are MATERIALISED from
the evidence declarations themselves, which is why this file does not go stale the day a new
ecosystem is declared: a detector added to the manifest is tested by arriving.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from harness import KIT, Fixtures
from manifest import Manifest
from ports.probe import EVIDENCE_KINDS, Probe
from workspace import Workspace

#: Read from the declaration that owns them -- never a list kept here.
DETECTORS = Manifest(KIT).detectors

#: A glob is turned back into ONE name it must match: the wildcard stands for a single ordinary
#: character and a character class for the first alternative it offers. Derived from the pattern,
#: so a pattern nobody could satisfy produces a tree that does not satisfy it either.
_FILLER = "x"


def concrete(pattern: str) -> str:
    out, i = "", 0
    while i < len(pattern):
        char = pattern[i]
        if char == "*":
            out += _FILLER
            while i < len(pattern) and pattern[i] == "*":
                i += 1
            continue
        if char == "[":
            close = pattern.index("]", i)
            out += pattern[i + 1]
            i = close + 1
            continue
        out += char
        i += 1
    return out


def _put_json(target: Path, pointer: str | None) -> None:
    value = {}
    if target.is_file():
        try:
            value = json.loads(target.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            value = {}
    if pointer:
        cursor = value
        steps = pointer.split(".")
        for step in steps[:-1]:
            cursor = cursor.setdefault(step, {})
        cursor[steps[-1]] = _FILLER
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def materialise(root: Path, detector: dict) -> None:
    """Build, from a detector's OWN evidence, the smallest tree that satisfies all of it."""
    for spec in detector["evidence"]:
        kind = spec["kind"]
        if kind == "dir_exists":
            (root / spec["path"]).mkdir(parents=True, exist_ok=True)
        elif kind == "path_exists":
            # Presence, not shape -- so the tree is built with the shape the kind exists to
            # admit and a `dir_exists` check would reject: a FILE. `.git` is the standing case
            # (a submodule, a linked worktree and --separate-git-dir all hold a file), and
            # materialising a directory here would let the kind silently narrow back to
            # `dir_exists` without a single test noticing.
            target = root / spec["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                target.write_text("", encoding="utf-8")
        elif kind == "file_exists":
            target = root / spec["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.is_file():
                target.write_text("{}\n", encoding="utf-8")
        elif kind == "glob_any":
            target = root / concrete(spec["pattern"])
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                target.write_text("", encoding="utf-8")
        elif kind == "json_path":
            _put_json(root / spec["path"], spec.get("pointer"))
        else:  # pragma: no cover -- an unknown kind is the interpreter's refusal, not ours
            raise AssertionError(f"this suite cannot materialise evidence kind {kind!r}")


def measure(root: Path) -> tuple[dict, dict]:
    facts, results = Probe(Workspace(root)).run(DETECTORS)
    return facts, {row["id"]: row["matched"] for row in results}


class DetectorDeclarations(Fixtures, unittest.TestCase):

    def test_168_every_declared_detector_fires_on_a_tree_built_from_its_own_evidence(self):
        self.assertTrue(DETECTORS, "the kit declares no detectors at all")
        for detector in DETECTORS:
            with self.subTest(detector=detector["id"]):
                root = self._temp(f"kit-det-{detector['id']}-")
                materialise(root, detector)
                _facts, matched = measure(root)
                self.assertTrue(matched[detector["id"]],
                                f"{detector['id']} cannot be satisfied by its own evidence")

    def test_169_every_fact_a_firing_detector_promises_is_actually_emitted(self):
        for detector in DETECTORS:
            with self.subTest(detector=detector["id"]):
                root = self._temp(f"kit-emit-{detector['id']}-")
                materialise(root, detector)
                facts, _matched = measure(root)
                for key, value in detector["emits"].items():
                    self.assertIn(key, facts, f"{detector['id']} promised {key} and emitted nothing")
                    if isinstance(value, str) and value.startswith("$"):
                        self.assertNotIsInstance(facts[key], bool,
                                                 f"{key} was declared a capture and came back a constant")

    def test_170_no_detector_fires_on_a_tree_that_carries_none_of_its_evidence(self):
        root = self._temp("kit-det-bare-")
        facts, matched = measure(root)
        self.assertEqual({}, facts, "a tree with no evidence was read as having an ecosystem")
        self.assertEqual([], [i for i, hit in matched.items() if hit],
                         "a detector fired on an empty tree")


if __name__ == "__main__":
    unittest.main()
