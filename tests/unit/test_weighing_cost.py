"""Weighing stays on the fast path: the class of a large change against many areas is computed well
inside the budget a commit hook may spend (ADR-025 decision 14). A regression here is a hook that
makes every commit slower for every principal, so it is held by a number, not by a hope."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

KIT = Path(__file__).resolve().parents[2] / "kit"
sys.path.insert(0, str(KIT / "interpreters"))

import weighing  # noqa: E402

CLASSES = json.loads((KIT / "capabilities" / "delivery" / "work-classes.json").read_text(encoding="utf-8"))

#: Seconds one weighing of the change below may take. The hook's whole budget is a second; weighing
#: is held to a fraction of it on any machine that runs this suite.
BUDGET = 1.0


def test_ten_thousand_paths_against_fifty_areas_weigh_inside_the_budget():
    areas = {"default_undo": "reversible", "max_areas": {},
             "areas": [{"id": f"area-{n}", "paths": f"^src/module{n}/", "undo": "costly", "because": "a fixture"}
                       for n in range(50)]}
    paths = [f"src/module{n % 60}/file{n}.py" for n in range(10_000)]
    started = time.perf_counter()
    _sig, verdict = weighing.weigh(paths, CLASSES, areas)
    took = time.perf_counter() - started
    assert verdict["class"]["id"] == "normal"
    assert took < BUDGET, f"weighing took {took:.2f}s, over the {BUDGET}s a commit hook may spend"
