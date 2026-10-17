"""A reference to a RULE this host already declares: does it hold, right now, as it stands?

The strongest proof a criterion can name is one the host was already going to run. This resolver
takes the name of a declared rule, finds the capability that declares it, asks the module
registered for that rule's kind to evaluate it, and reports what came back -- the verdict and the
findings it was given, never a summary of them.

It privileges nothing and knows no rule. The name arrives as data on the card; the params arrive
from the declaration that owns the rule, never from the card, because a criterion that could
restate a rule's parameters would be judging itself against a rule of its own invention.

A name this host declares nowhere is READ AS NOTHING rather than as a failure: the criterion names
a referent that is not there, which is an absence and stays one until somebody declares it.
"""

from __future__ import annotations

import collection
import criteria
import gatekinds

#: What a capability's declaration of a rule carries beside its name. Declaration vocabulary.
OF_KIND = "kind"
WITH = "params"
#: The entry a gate module publishes beside `KINDS` for each kind whose verdict is read from the
#: governed records: such a rule may judge them, and may never be the proof of one of them.
READS_THE_RECORDS = "READS_THE_RECORDS"

#: The rules being evaluated right now, in this process. A rule that reads the records whose criteria
#: name it -- a gate over cards, proved by a card -- would otherwise evaluate itself forever: the
#: reference trail of `criteria` cannot see through a judge it does not call. The second reading of a
#: rule inside its own evaluation is a reading that stands on itself, and it proves nothing.
_EVALUATING: set = set()


def _declared_rule_holds(request) -> criteria.Verdict:
    named = [
        (capability, rule)
        for capability in request.ctx.enabled_capabilities()
        for rule in capability.gates
        if rule[collection.IDENTITY] == request.ref
    ]
    if not named:
        return criteria.Verdict.unreadable(
            f"no capability enabled on this host declares a rule called {request.ref!r}, so there "
            f"is nothing to evaluate. The criterion names a referent that is not here"
        )
    if len(named) > 1:
        return criteria.Verdict.unreadable(
            f"{request.ref!r} is declared by {sorted(c.id for c, _ in named)}; a name that resolves "
            f"to two rules resolves to none, and this reading is not taken on a guess"
        )
    capability, rule = named[0]
    judges = gatekinds.registry()
    if rule[OF_KIND] not in judges:
        return criteria.Verdict.unreadable(
            f"{request.ref!r} is declared by {capability.id!r} as kind {rule[OF_KIND]!r}, and no "
            f"module installed here evaluates that kind; the reading could not be taken"
        )
    if criteria.PROVING in request.seen and rule[OF_KIND] in gatekinds.registry(READS_THE_RECORDS):
        return criteria.Verdict.unreadable(
            f"{request.ref!r} is a rule of kind {rule[OF_KIND]!r}, which judges by reading the governed "
            f"records themselves -- this record among them. Evidence for a claim may not be the claim "
            f"(ISO/IEC/IEEE 15026; ADR-025 decision 16): name a proof that does not read the record")
    if request.ref in _EVALUATING:
        return criteria.Verdict.unreadable(
            f"{request.ref!r} is being evaluated already, and this reading is part of that evaluation; "
            f"a rule that stands on its own reading proves nothing and is not followed")
    _EVALUATING.add(request.ref)
    try:
        findings = judges[rule[OF_KIND]](request.ctx, rule.get(WITH, {}))
    finally:
        _EVALUATING.discard(request.ref)
    if findings:
        return criteria.Verdict(False, f"{request.ref} was evaluated and did not hold: "
                                       + "; ".join(str(f) for f in findings))
    return criteria.Verdict(True, f"{request.ref} was evaluated as declared by {capability.id} "
                                  f"and held")


#: The kind of reference this module answers. A row here and a function beside it -- and the
#: registry finds it because it is in this directory, not because anything names this file.
RESOLVERS = {"declared-rule-holds": _declared_rule_holds}
