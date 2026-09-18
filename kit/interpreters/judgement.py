"""Judgement -- the ONE application of a host's declared edit gates to a set of edits.

Two writers now reach a host with a change in hand: a runtime's hook, before the write (the
`judge` verb), and a dispatched worker's isolated tree, after it (the dispatch port's admission on
return). ADR-017 decision 5 makes them deliberately unequal in WHEN they act -- verification at
return replaces prevention at write for a runtime that cannot be stopped mid-command -- and just as
deliberately equal in WHAT they apply. If the two ever applied different rule sets, a host would
hold two answers to "may this text enter?", each locally correct, and which one a change met would
depend on who happened to be carrying it (Cardinal III).

So the loop lives here, once, and both call it. This module knows no gate kind, no product, no
runtime and no path: it asks the same registry `check` asks, hands every enabled gate the edits,
and returns what was refused beside what could not be judged at all. A gate that could not be
applied is NAMED and never counted as a pass -- an uncalibrated rule that silently admits is worse
than no rule, because the host believes it has one.
"""

from __future__ import annotations

import gatekinds

#: The entry a gate module offers for judging an EDIT, beside the one it offers for judging a tree
#: (ADR-017 amendment 1). Found through the registry, so a new kind of edit rule is a module and
#: never a second judge.
ENTRY = "EDITS"


def refusals(ctx, edits: list) -> tuple:
    """(refused, unjudged) for these (host-relative path, introduced text) pairs.

    `refused` is (path, gate id, because, instead) per violation, in the gates' own words -- this
    module supplies none of its own, because a refusal a host cannot recognise as its own rule is
    an interpreter having an opinion.
    """
    refused, unjudged = [], []
    judges = gatekinds.registry(ENTRY)
    for capability in ctx.enabled_capabilities():
        for gate in capability.gates:
            if gate["kind"] in judges:
                found, blind = judges[gate["kind"]](ctx, gate.get("params", {}), edits)
                refused += found
                unjudged += blind
    return refused, unjudged
