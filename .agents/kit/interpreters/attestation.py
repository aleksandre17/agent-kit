"""Attestation -- a capability is believed once a record of something that happened proves it (ADR-022).

A runtime descriptor CLAIMS what its runtime can do; a claim is testimony with an author. This module
writes the other kind of record: at the moment an interpreter of this kit OBSERVES an event it
provides, it records which runtime the event came through and which capability of the class
vocabulary that event observes. Which capability that is, is the vocabulary's own declaration
(`observed_on`), so no interpreter here spells a capability and a new one is a row, never an edit.

Observing never changes a verdict. The record is written after the judgement it observes, and a
fault writing it is named on stderr and swallowed: a telemetry fault must not turn a refusal into
an allowance, nor an allowance into a crash.
"""

from __future__ import annotations

import sys

import collection
import declared

#: An event is PROVIDED by the interpreter that observes it, and declared there: a module publishes
#: `EVENTS` (event -> what it observes), and the vocabulary row that is observed by it names it in
#: `observed_on`. This module holds no event of its own -- a new observed event is a constant in its
#: provider and a word in the vocabulary, never an edit here (ADR-023 amendment 5).
VOCABULARY = {"validates": "runtime-class"}
OBSERVATIONS, DESCRIPTOR = "runtime-observation", "runtime"


def _install(ctx, kind: str):
    return next(((c, i) for c in ctx.enabled_capabilities() for i in c.installs
                 if i.get("validates") == kind), (None, None))


def served_through(ctx, surface_id: str) -> list:
    """The runtime descriptor ids a surface serves -- the principals a hook's event came from."""
    _owner, descriptors = _install(ctx, DESCRIPTOR)
    if descriptors is None or not surface_id:
        return []
    return [record[collection.IDENTITY]
            for _rel, record in collection.read(ctx, descriptors, descriptors["reads_as"]).records
            if isinstance(record, dict) and record.get("surface") == surface_id]


def classes_through(ctx, surface_id: str) -> list:
    """The runtime CLASSES a surface serves -- what kind of writer a hook's event came from."""
    _owner, descriptors = _install(ctx, DESCRIPTOR)
    if descriptors is None or not surface_id:
        return []
    return sorted({record.get("class") for _rel, record in
                   collection.read(ctx, descriptors, descriptors["reads_as"]).records
                   if isinstance(record, dict) and record.get("surface") == surface_id})


def observe(ctx, surface_id: str, event: str, evidence: str) -> list:
    """Record `event`, with the provider's own statement of its `evidence`, for every runtime served
    through `surface_id`, against every capability whose `observed_on` is that event. Returns what
    was written; never raises."""
    try:
        owner, place = _install(ctx, OBSERVATIONS)
        _d_owner, descriptors = _install(ctx, DESCRIPTOR)
        if place is None or descriptors is None:
            return []
        capabilities = [row[collection.IDENTITY] for row in declared.rules(ctx, VOCABULARY, "capabilities")
                        if row.get("observed_on") == event]
        written = []
        scope = ctx.workspace.scoped((place["target"],))
        for runtime in served_through(ctx, surface_id):
            for capability in capabilities:
                rel = f"{place['target'].rstrip('/')}/{runtime}.{capability}.json"
                scope.write_json(rel, {"schema_version": ctx.manifest.version_of(OBSERVATIONS),
                                       "runtime": runtime, "capability": capability,
                                       "event": event, "observed_at": ctx.clock.now(), "evidence": evidence})
                written.append(rel)
        return written
    except Exception as exc:  # noqa: BLE001 -- an observation must never change the verdict it observes
        print(f"attestation: the observation of {event!r} was not recorded -- {exc}", file=sys.stderr)
        return []
