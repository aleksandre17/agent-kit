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

Records with no `held_by` (the commit; a review, decided by a proof) are not read here.
"""

from __future__ import annotations

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
    classes = {row["id"]: row for row in classes_doc["classes"]}
    uncertainty = {row["id"]: row for row in classes_doc["uncertainty"]}
    records = {row["id"]: row for row in classes_doc["records"]}
    members = lineage.among(ctx) or []
    failures = []
    for card in sorted(members, key=lambda c: c["id"]):
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
                where = "a card hanging under it" if holder.get("children") else f"`{holder['field']}`"
                failures.append(f"{name}: a {shaped} card owes its {record} from {holder['from']} on, "
                                f"held by {where}, and it has none")
    return failures


KINDS = {"work-classes-held": _work_classes_held}
