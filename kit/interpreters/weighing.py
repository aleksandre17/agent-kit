"""Weighing a change -- its class is computed from what it touches, never chosen by its author (ADR-025).

A host declares its AREAS: a set of paths, the cost of undoing a change to them, and why -- and, to
tailor, the lightest class a change there may be and the records it owes beyond its class. A
change's SIGNALS are the areas its paths fall in and the highest undo cost among them; its CLASS is
the lightest class of the work-class catalogue whose envelope admits those signals, raised to every
touched area's `at_least`. A declared class may be heavier than the computed one and never lighter:
the computed class is a floor.

Pure: paths, messages, cards and declarations in, a verdict out. No class, area, state, trailer or
number is named here -- the scales, the classes and the envelopes are the catalogue's and the host's.
"""

from __future__ import annotations

import re

from errors import KitError


class WeighError(KitError):
    """A work-class catalogue or an areas declaration that names a word nobody declared."""

    code = "KIT0085"


def _ids(rows) -> list:
    return [row["id"] for row in rows]


def _rank(classes_doc: dict) -> dict:
    return {row["id"]: rank for rank, row in enumerate(classes_doc["classes"])}


def _scale(classes_doc: dict) -> dict:
    return {identity: rank for rank, identity in enumerate(_ids(classes_doc["undo"]))}


def checked(classes_doc: dict, areas_doc: dict) -> None:
    """Every word the catalogue and the areas use is one somebody declared; one area id, one home."""
    scale, classes, records = _scale(classes_doc), set(_ids(classes_doc["classes"])), set(_ids(classes_doc["records"]))
    words = [("default_undo", areas_doc["default_undo"], scale, "undo cost")]
    for area in areas_doc.get("areas", []):
        where = f"area {area['id']!r}"
        words.append((where, area["undo"], scale, "undo cost"))
        if "at_least" in area:
            words.append((where, area["at_least"], classes, "class"))
        words += [(where, r, records, "record") for r in area.get("requires", [])]
    for row in classes_doc["classes"]:
        if row.get("admits"):
            words.append((f"class {row['id']!r}", row["admits"]["undo"], scale, "undo cost"))
        words += [(f"class {row['id']!r}", r, records, "record") for r in row["requires"]]
    words += [(f"uncertainty {u['id']!r}", u["at_least"], classes, "class") for u in classes_doc["uncertainty"]]
    words += [("max_areas", c, classes, "class") for c in areas_doc.get("max_areas", {})]
    for where, word, declared, what in words:
        if word not in declared:
            raise WeighError(f"{where} names the {what} {word!r}, which is not declared "
                             f"({', '.join(sorted(declared))}): a word nobody declared cannot be compared")
    seen = set()
    for area in areas_doc.get("areas", []):
        if area["id"] in seen:
            raise WeighError(f"the area {area['id']!r} is declared twice: one name, two sets of paths")
        seen.add(area["id"])
    for area in areas_doc.get("areas", []):
        unknown = sorted(set(area.get("feeds", [])) - seen)
        if unknown:
            raise WeighError(f"area {area['id']!r} feeds {unknown}, which no area declares")


def signals(paths, classes_doc: dict, areas_doc: dict) -> dict:
    """What a change touches: each declared area with the paths that fell in it, the paths no area
    claims, and the highest undo cost among all of them."""
    checked(classes_doc, areas_doc)
    scale = _scale(classes_doc)
    compiled = [(area, re.compile(area["paths"])) for area in areas_doc.get("areas", [])]
    touched, unclaimed = {}, []
    for path in sorted(set(paths)):
        hits = [area for area, pattern in compiled if pattern.search(path)]
        for area in hits:
            touched.setdefault(area["id"], {"area": area, "paths": []})["paths"].append(path)
        if not hits:
            unclaimed.append(path)
    costs = [hit["area"]["undo"] for hit in touched.values()]
    if unclaimed:
        costs.append(areas_doc["default_undo"])
    undo = max(costs, key=scale.__getitem__) if costs else None
    return {"touched": touched, "unclaimed": unclaimed, "undo": undo,
            "downstream": downstream(areas_doc, set(touched))}


def downstream(areas_doc: dict, touched: set) -> list:
    """Every area the touched ones feed, transitively, that the change does not itself touch -- the
    consumers that must move with it. A cycle in the map is walked once, never forever."""
    feeds = {a["id"]: a.get("feeds", []) for a in areas_doc.get("areas", [])}
    reached, frontier = set(), list(touched)
    while frontier:
        for nxt in feeds.get(frontier.pop(), []):
            if nxt not in reached and nxt not in touched:
                reached.add(nxt)
                frontier.append(nxt)
    return sorted(reached)


def heavier_or_equal(classes_doc: dict, declared: str, floor: str) -> bool:
    """Whether a declared class stands at or above a floor. An expedite class stands for any weight:
    it lands now and owes the floor's records afterwards."""
    rank = _rank(classes_doc)
    if declared not in rank:
        raise WeighError(f"the class {declared!r} is not declared ({', '.join(rank)})")
    row = classes_doc["classes"][rank[declared]]
    return bool(row.get("expedite")) or rank[declared] >= rank[floor]


def _heavier(classes_doc: dict, a: str, b: str) -> str:
    rank = _rank(classes_doc)
    return a if rank[a] >= rank[b] else b


def computed(sig: dict, classes_doc: dict, areas_doc: dict) -> dict:
    """The verdict: the class (row), why, and every record it owes -- the class's own and each
    touched area's. Past every envelope the heaviest class stands; an expedite class is never
    computed; an area's `at_least` raises the class and never lowers it."""
    scale = _scale(classes_doc)
    rows = [row for row in classes_doc["classes"] if not row.get("expedite")]
    breadth = len(sig["touched"])
    limits = areas_doc.get("max_areas", {})
    chosen, why = rows[-1], f"beyond every envelope: {breadth} area(s), undo cost {sig['undo']}"
    for row in rows:
        admits = row.get("admits")
        if not admits:
            continue
        if sig["undo"] is not None and scale[sig["undo"]] > scale[admits["undo"]]:
            continue
        if row["id"] in limits and breadth > limits[row["id"]]:
            continue
        chosen = row
        why = ("nothing changed" if sig["undo"] is None
               else f"undo cost {sig['undo']} across {breadth} declared area(s)")
        break
    identity = chosen["id"]
    for area_id, hit in sorted(sig["touched"].items()):
        floor = hit["area"].get("at_least")
        if floor and _heavier(classes_doc, floor, identity) != identity:
            identity, why = floor, f"{why}; area {area_id} asks at least {floor}"
    row = classes_doc["classes"][_rank(classes_doc)[identity]]
    owed = list(row["requires"])
    for hit in sig["touched"].values():
        owed += [r for r in hit["area"].get("requires", []) if r not in owed]
    return {"class": row, "why": why, "requires": owed}


def loosened(classes_doc: dict, before, after) -> list:
    """How the areas a change leaves are LOOSER than the areas that stood before it -- empty when they
    are as strict or stricter. Tightening is anyone's act; loosening the scale a change is weighed by
    is a change of its own that owes a named record. With nothing before, nothing is loosened: no
    areas at all is the loosest a host can be."""
    if not before or not after:
        return [] if not before else ["the areas declaration is removed"]
    scale, rank = _scale(classes_doc), _rank(classes_doc)
    said = []

    def lower(a, b, order):
        return a in order and b in order and order[b] < order[a]

    if lower(before["default_undo"], after["default_undo"], scale):
        said.append(f"default_undo {before['default_undo']} -> {after['default_undo']}")
    was, now = before.get("max_areas", {}), after.get("max_areas", {})
    for cls, limit in sorted(was.items()):
        if cls not in now or now[cls] > limit:
            said.append(f"max_areas of {cls} {limit} -> {now.get(cls, 'unlimited')}")
    old_areas = {a["id"]: a for a in before.get("areas", [])}
    new_areas = {a["id"]: a for a in after.get("areas", [])}
    for identity, area in sorted(old_areas.items()):
        kept = new_areas.get(identity)
        if kept is None:
            said.append(f"area {identity} removed")
            continue
        if kept["paths"] != area["paths"]:
            said.append(f"area {identity} paths {area['paths']!r} -> {kept['paths']!r}")
        if lower(area["undo"], kept["undo"], scale):
            said.append(f"area {identity} undo {area['undo']} -> {kept['undo']}")
        if "at_least" in area and ("at_least" not in kept or lower(area["at_least"], kept["at_least"], rank)):
            said.append(f"area {identity} at_least {area['at_least']} -> {kept.get('at_least', 'none')}")
        dropped = sorted(set(area.get("requires", [])) - set(kept.get("requires", [])))
        if dropped:
            said.append(f"area {identity} no longer requires {', '.join(dropped)}")
    return said


def weigh(paths, classes_doc: dict, areas_doc: dict, loosening=()) -> tuple:
    """(signals, verdict) for a set of paths -- the one entry every caller weighs through.

    `loosening` names how the change loosens the areas it is weighed by (`loosened`). Such a change is
    at least the lightest class that owes a card: whoever loosens the scale leaves a named,
    criteria-bearing record of doing it -- and tightening it costs nothing."""
    sig = signals(list(paths), classes_doc, areas_doc)
    verdict = computed(sig, classes_doc, areas_doc)
    floor = lightest_with(classes_doc, "card")
    if loosening and _heavier(classes_doc, floor, verdict["class"]["id"]) != verdict["class"]["id"]:
        row = classes_doc["classes"][_rank(classes_doc)[floor]]
        owed = list(row["requires"]) + [r for r in verdict["requires"] if r not in row["requires"]]
        verdict = {"class": row, "why": f"{verdict['why']}; it loosens the areas it is weighed by "
                   f"({'; '.join(loosening)})", "requires": owed}
    return sig, verdict


def demotions(classes_doc: dict, before: dict, after: dict) -> list:
    """Every card a change shapes LIGHTER than it stood, without the owner's door recorded on it.

    `before` and `after` map card ids to the card as it stood and as the change leaves it. Raising a
    class is anyone's act; lowering one is the owner's (ADR-025 decision 4), recorded by `reshape` as
    the card's last `reshaped` entry -- from the old class, to the new, approved by a named owner."""
    rank, refused = _rank(classes_doc), []
    for identity, card in sorted(after.items()):
        was, now = (before.get(identity) or {}).get("class"), card.get("class")
        if was not in rank or (now is not None and now not in rank):
            continue
        lowered = now is None or rank[now] < rank[was]
        if not lowered:
            continue
        last = (card.get("reshaped") or [{}])[-1]
        if last.get("from") == was and last.get("to") == now and last.get("approved_by"):
            continue
        refused.append(f"the card {identity} is shaped {now or 'with no class'} where it stood {was}: lowering a "
                       f"class is the owner's door -- `reshape --card {identity} --class {now or '<class>'} "
                       f"--approve <owner>` records it")
    return refused


# -- a commit, and the card it names ----------------------------------------------------------
_TRAILER = re.compile(r"^([A-Za-z][A-Za-z0-9-]*)\s*:\s*(\S.*?)\s*$")


def trailers(message: str) -> dict:
    """The trailers of a commit message, by lower-cased key: the `Key: value` lines of its last
    paragraph (git interpret-trailers). Comment lines are not the message and are dropped."""
    lines = [line for line in message.replace("\r\n", "\n").split("\n") if not line.startswith("#")]
    paragraphs = [p for p in "\n".join(lines).strip().split("\n\n") if p.strip()]
    if len(paragraphs) < 2:
        return {}
    found = {}
    for line in paragraphs[-1].splitlines():
        hit = _TRAILER.match(line)
        if hit:
            found.setdefault(hit.group(1).lower(), hit.group(2))
    return found


def card_floor(classes_doc: dict, card: dict, fallback: str) -> tuple:
    """(class, why) a card stands at: its declared class, else the fallback a card with none is read
    as. Its uncertainty is reported, not merged -- a card lighter than its uncertainty is a defect of
    the card, named by its gate."""
    return card.get("class", fallback), ("declared on the card" if "class" in card
                                         else f"no class on the card, read as {fallback}")


def lightest_with(classes_doc: dict, record: str) -> str:
    """The lightest computed class that owes a record: what a card with no class is read as."""
    return next(row["id"] for row in classes_doc["classes"]
                if not row.get("expedite") and record in row["requires"])


def commit_refusals(classes_doc: dict, verdict: dict, message: str, cards: dict) -> list:
    """Why a commit of this weight, with this message, may not be recorded -- empty when it may.

    The declared class (a trailer) is a floor's claimant: lighter than computed is refused, an
    expedite class is admitted with what it owes. A class that owes a card needs the card trailer,
    a card that exists, stands in a working state and is not shaped lighter than the change."""
    keys = classes_doc["trailers"]
    said = trailers(message)
    computed_id = verdict["class"]["id"]
    declared = said.get(keys["class"].lower())
    refusals = []
    if declared is not None:
        if not heavier_or_equal(classes_doc, declared, computed_id):
            refusals.append(f"the message declares {keys['class']}: {declared}, but the change computes "
                            f"{computed_id} ({verdict['why']}): a declared class may be heavier, never lighter")
        row = classes_doc["classes"][_rank(classes_doc)[declared]]
        if row.get("expedite"):
            return refusals
    if "card" not in verdict["requires"]:
        return refusals
    named = said.get(keys["card"].lower())
    if named is None:
        return refusals + [f"the change computes {computed_id} ({verdict['why']}), which owes a card: "
                           f"name it with a trailer `{keys['card']}: <card id>`"]
    card = cards.get(named)
    if card is None:
        return refusals + [f"{keys['card']}: {named} names no card this host holds"]
    if card.get("state") not in classes_doc["working_states"]:
        refusals.append(f"the card {named} is {card.get('state')!r}; work is committed to a card in "
                        f"{', '.join(classes_doc['working_states'])}")
    shaped, why = card_floor(classes_doc, card, lightest_with(classes_doc, "card"))
    if shaped not in _rank(classes_doc):
        refusals.append(f"the card {named} declares the class {shaped!r}, which is not declared")
    elif not heavier_or_equal(classes_doc, shaped, computed_id):
        refusals.append(f"the card {named} is shaped {shaped} ({why}), but this change computes "
                        f"{computed_id} ({verdict['why']}): re-shape the card -- a heavier class is the "
                        f"owner's bet -- or narrow the change")
    return refusals
