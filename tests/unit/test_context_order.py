"""Unit: an always-loaded file puts what changes least first, so a product's prompt cache reuses the
prefix (ADR-024). The order is the declaration's within each volatility, and stable before volatile."""

from __future__ import annotations

import sys
from pathlib import Path

INTERPRETERS = Path(__file__).resolve().parents[2] / "kit" / "interpreters"
for extra in [INTERPRETERS, *sorted(p for p in INTERPRETERS.iterdir() if p.is_dir() and not p.name.startswith("_"))]:
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

import serve  # noqa: E402 -- the served shape, discovered beside the others


def test_stable_sections_precede_volatile_ones_and_keep_their_declared_order():
    volatile = next(k for k, v in serve.VOLATILITY.items() if v == max(serve.VOLATILITY.values()))
    sections = [{"id": "a"}, {"id": "b", "volatility": volatile}, {"id": "c"}, {"id": "d", "volatility": volatile}]
    assert [s["id"] for s in serve._ordered(sections)] == ["a", "c", "b", "d"]
