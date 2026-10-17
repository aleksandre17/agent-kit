"""Gate kind: the work classes hold -- the host's areas use declared words, and every card that
declares a class keeps what that class owes (ADR-025).

A card that declares NO class is passed over: it is the ordinary way, and a gate that held every
card in existence to a vocabulary that did not exist when it was written would be back-filling a
declaration nobody made (ADR-020 decision 11). The moment a card names a class, the class is a
promise this gate reads:

  * the class and the uncertainty are words the catalogue declares;
  * the class is not lighter than its uncertainty asks;
  * every record the class owes is held by the card from the state its row names on -- reached
    meaning the card stands there now or has passed through it (its history), never a guess at an
    order the lifecycle does not declare.

Records with no `held_by` (the commit) are not read here; a record held by a criterion is held when
the card declares one that needs its class -- the verified passage then proves it.
"""

from __future__ import annotations

import collection
import criteria
import lifecycle as lifecycle_module
import lineage
import weighing
import workclass


def _reached(card: dict, state: str) -> bool:
    return card.get("state") == state or any(p.get("to") == state
                                             for p in card.get(lifecycle_module.HISTORY, []))


def _held(card: dict, holder: dict, records) -> bool:
    if holder.get("children"):
        return bool(lineage.children_of(records, card["id"]))
    if "criterion_needs" in holder:
        return any(c.get(criteria.NEEDS) == holder["criterion_needs"] for c in card.get("criteria") or [])
    value = card.get(holder["field"])
    return value not in (None, "", [], {})


def _work_classes_held(ctx, params):
    found = workclass.declarations(ctx)
    if found is None:
        return []
    classes_doc, areas_doc = found
    try:
        weighing.checked(classes_doc, areas_doc)
    except weighing.WeighError as refused:
        return [f"areas: {refused}"]
    installed = set(criteria.registry())
    failures = [f"evidence: the class {row['id']!r} names the kind of proof {kind!r}, which no resolver "
                f"installed here provides ({', '.join(sorted(installed))})"
                for row in classes_doc["evidence"] for kind in row["yielded_by"] if kind not in installed]
    try:
        criteria.evidence(classes_doc["evidence"])
    except criteria.CriterionError as refused:
        failures.append(f"evidence: {refused}")
    known = {row["id"] for row in classes_doc["evidence"]}
    classes = {row["id"]: row for row in classes_doc["classes"]}
    uncertainty = {row["id"]: row for row in classes_doc["uncertainty"]}
    records = {row["id"]: row for row in classes_doc["records"]}
    members = lineage.among(ctx) or []
    for card in sorted(members, key=lambda c: c["id"]):
        for item in card.get("criteria") or []:
            if criteria.NEEDS in item and item[criteria.NEEDS] not in known:
                failures.append(f"{card['id']}: the criterion {item.get('id')!r} needs {item[criteria.NEEDS]!r} "
                                f"evidence, which the scale does not declare ({', '.join(sorted(known))})")
        if "class" not in card:
            continue
        name, shaped = card["id"], card["class"]
        if shaped not in classes:
            failures.append(f"{name}: declares the class {shaped!r}, which the catalogue does not "
                            f"({', '.join(classes)})")
            continue
        domain = card.get("uncertainty")
        if domain is not None:
            if domain not in uncertainty:
                failures.append(f"{name}: declares the uncertainty {domain!r}, which the catalogue does "
                                f"not ({', '.join(uncertainty)})")
            elif not weighing.heavier_or_equal(classes_doc, shaped, uncertainty[domain]["at_least"]):
                failures.append(f"{name}: shaped {shaped}, but {domain} work walks at least "
                                f"{uncertainty[domain]['at_least']} -- re-shape it (a heavier class is the owner's bet)")
        for record in classes[shaped]["requires"]:
            holder = records[record].get("held_by")
            if holder and _reached(card, holder["from"]) and not _held(card, holder, members):
                where = ("a card hanging under it" if holder.get("children")
                         else f"a criterion that needs {holder['criterion_needs']}" if "criterion_needs" in holder
                         else f"`{holder['field']}`")
                failures.append(f"{name}: a {shaped} card owes its {record} from {holder['from']} on, "
                                f"held by {where}, and it has none")
    return failures


def _deferrals_held(ctx, params):
    """A deferred card whose trigger HOLDS is due, and is reported until it leaves the deferring state;
    a deferred card with no trigger is counted and named, never failed -- it is an honest state that
    has not yet said what would end it (ADR-025 decision 8)."""
    capabilities = ctx.enabled_capabilities()
    if not any(getattr(c, "governs", None) for c in capabilities):
        return []
    governed = lifecycle_module.the_governed(capabilities, collection.read_all(ctx, capabilities))
    deferring = {s["id"] for s in governed.states if s.get("defers")}
    failures, untriggered = [], []
    for card in sorted(governed.members.value, key=lambda c: c["id"]):
        if card.get(governed.state_field) not in deferring:
            continue
        trigger = card.get("due_when")
        if trigger is None:
            untriggered.append(card["id"])
            continue
        verdict = criteria.resolve(ctx, trigger, card)
        if verdict.holds is True:
            failures.append(f"{card['id']}: DUE -- the trigger it was deferred on holds ({verdict.reading}). "
                            f"Shape it again or park it with a new trigger, on the record")
    if untriggered:
        print(f"        deferred with no trigger: {len(untriggered)} -- {', '.join(untriggered)}")
    return failures


def _after_of(members: dict) -> dict:
    return {identity: list(card.get("after") or []) for identity, card in members.items()}


def _cycle(edges: dict):
    """One cycle through the `after` edges, as a path, or None."""
    state: dict = {}

    def visit(node, trail):
        state[node] = "open"
        for nxt in edges.get(node, []):
            if state.get(nxt) == "open":
                return trail + [node, nxt]
            if nxt in edges and state.get(nxt) is None:
                found = visit(nxt, trail + [node])
                if found:
                    return found
        state[node] = "done"
        return None

    for node in sorted(edges):
        if state.get(node) is None:
            found = visit(node, [])
            if found:
                return found
    return None


def _order_held(ctx, params):
    """The order between cards is an order: every name resolves, no card comes after itself through
    any chain, and finished work that STOPS holding is reported REGRESSED with everything that came
    after it -- invalidation read from the criteria, never kept in a ledger (ADR-025 decision 9)."""
    capabilities = ctx.enabled_capabilities()
    if not any(getattr(c, "governs", None) for c in capabilities):
        return []
    governed = lifecycle_module.the_governed(capabilities, collection.read_all(ctx, capabilities))
    members = {c["id"]: c for c in governed.members.value}
    edges = _after_of(members)
    failures = [f"{card}: comes after {name!r}, which this host does not hold"
                for card, names in sorted(edges.items()) for name in names if name not in members]
    loop = _cycle(edges)
    if loop:
        failures.append(f"the order is a cycle: {' -> '.join(loop)} -- no part of it can ever start")
    closed = {s["id"] for s in governed.states if s.get("closed")}
    for identity, card in sorted(members.items()):
        if card.get(governed.state_field) not in closed:
            continue
        refuted = [item.get("id") for item, verdict in criteria.read(ctx, card, governed.spec["criteria"]) if verdict.holds is False]
        if refuted:
            later = sorted(i for i, names in edges.items() if identity in names)
            failures.append(f"{identity}: REGRESSED -- finished, and {', '.join(map(str, refuted))} no longer "
                            f"holds" + (f"; it came before {', '.join(later)}" if later else ""))
    return failures


KINDS = {"work-classes-held": _work_classes_held, "deferrals-held": _deferrals_held, "order-held": _order_held}
