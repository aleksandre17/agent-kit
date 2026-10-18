"""The cost frontier (gates/economy.py): a run that reported no token count is unmeasured, never zero --
the cost it reports is a floor, and the per-change measure a budget holds is not measurable while any
run is unmeasured (CWE-636: a blind reading never passes a budget)."""

from __future__ import annotations

import sys
from pathlib import Path

INTERPRETERS = Path(__file__).resolve().parents[2] / "kit" / "interpreters"
for extra in [INTERPRETERS, *sorted(p for p in INTERPRETERS.iterdir() if p.is_dir() and not p.name.startswith("_"))]:
    sys.path.insert(0, str(extra))

import economy  # noqa: E402


def _task(tokens, accepted=True):
    task = {"route": {"task_class": "edit"}, "telemetry": {} if tokens is None else {economy.OUT_TOKENS: tokens}}
    if accepted:
        task.update({"state": economy.dispatching.COMPLETED, "admission": {"verdict": economy.admission.ADMITTED}})
    return task


def test_an_unreported_run_is_counted_unmeasured_and_the_budget_measure_is_not_measurable(monkeypatch):
    monkeypatch.setattr(economy.returns, "tasks", lambda _ctx: [_task(100), _task(None)])
    monkeypatch.setattr(economy.returns, "unreadable", lambda _ctx: [])
    assert economy.frontier(None) == {"edit": (2, 2, 100, 50, 1)}
    assert economy._per_accepted(None, {}) is None


def test_every_run_measured_gives_the_cost(monkeypatch):
    monkeypatch.setattr(economy.returns, "tasks", lambda _ctx: [_task(100), _task(300)])
    monkeypatch.setattr(economy.returns, "unreadable", lambda _ctx: [])
    assert economy._per_accepted(None, {}) == 200


def test_a_task_record_that_cannot_be_read_makes_every_budget_measure_unmeasurable(monkeypatch):
    monkeypatch.setattr(economy.returns, "tasks", lambda _ctx: [_task(100)])
    monkeypatch.setattr(economy.returns, "unreadable", lambda _ctx: [".agents/runtime/dispatch/x/task.json"])
    assert economy._per_accepted(None, {}) is None
    assert economy._peak(None, {}) is None and economy._calls(None, {}) is None
