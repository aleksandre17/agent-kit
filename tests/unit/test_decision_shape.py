"""Unit: a decision the work owes keeps its kind's declared shape -- the question, the options and why
the rejected lost, the decision, its consequences, and at least one source weighed (ADR-024 amendment 1,
engineering 1.2.0 decisions-recorded). The shape is data in the record-keeping vocabulary; the reader only
finds headings and counts what stands under them."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "kit" / "interpreters"))

import workclass  # noqa: E402

SHAPE = next(k for k in json.loads((ROOT / "kit" / "capabilities" / "governance" / "record-keeping.json")
                                   .read_text(encoding="utf-8"))["kinds"] if k["id"] == "decision")["shape"]

WHOLE = """# ADR-9 -- one queue per tenant

## Context
Tenants starve each other.

## Considered options
- one shared queue (rejected: the starvation itself)
- one queue per tenant

## Decision
One queue per tenant.

## Consequences
More queues to watch.

## Sources
- RabbitMQ, "Quorum queues and fairness", https://www.rabbitmq.com/docs/quorum-queues
""".splitlines()


def test_a_whole_decision_keeps_the_shape():
    assert workclass.shape_misses(SHAPE, WHOLE) == []


def test_a_decision_without_sources_or_options_is_named_short():
    body = [line for line in WHOLE if "Sources" not in line and "RabbitMQ" not in line]
    body = [line for line in body if not line.startswith(("## Considered", "- one"))]
    missing = workclass.shape_misses(SHAPE, body)
    assert any("sources" in m for m in missing) and any("options" in m for m in missing)


def test_an_empty_sources_section_is_not_a_source():
    body = [line for line in WHOLE if "RabbitMQ" not in line]
    assert workclass.shape_misses(SHAPE, body) == ["the sources weighed (a standard, prior art, research) (it is empty)"]


def test_prose_that_names_a_section_is_not_a_heading():
    body = [line.replace("## Sources", "We list sources below.") for line in WHOLE]
    assert any("sources" in m for m in workclass.shape_misses(SHAPE, body))
