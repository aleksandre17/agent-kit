"""Unit: every event a runtime capability is proven by is one an interpreter PROVIDES (ADR-022 d. 6).

A vocabulary row says `observed_on: <event>`; the interpreter that observes that event declares it
in its own `EVENTS`. A row naming an event nobody provides is a capability that can never be
proven -- it would read as unproven forever, for a reason no reader could find. And an event
provided twice is a name resolving to two meanings.
"""

from __future__ import annotations

import importlib
import json
import sys
from collections import Counter
from pathlib import Path

KIT = Path(__file__).resolve().parents[2] / "kit"
INTERPRETERS = KIT / "interpreters"
for extra in [INTERPRETERS, *sorted(p for p in INTERPRETERS.iterdir() if p.is_dir() and not p.name.startswith("_"))]:
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))


def _provided() -> Counter:
    found = Counter()
    for path in sorted(INTERPRETERS.rglob("*.py")):
        if "__pycache__" in path.parts or path.stem.startswith("_") or path.stem == "cli":
            continue
        if "EVENTS" not in path.read_text(encoding="utf-8"):
            continue
        module = importlib.import_module(path.stem)
        found.update(list(getattr(module, "EVENTS", {})))
    return found


def test_every_observed_event_is_provided_once():
    provided = _provided()
    assert all(n == 1 for n in provided.values()), f"an event provided twice: {provided}"
    classes = json.loads((KIT / "runtimes" / "classes.json").read_text(encoding="utf-8"))
    observed = {row["observed_on"] for row in classes["capabilities"] if "observed_on" in row}
    assert observed, "the kit's vocabulary is proven by at least one event"
    assert observed <= set(provided), f"observed on events nobody provides: {sorted(observed - set(provided))}"
