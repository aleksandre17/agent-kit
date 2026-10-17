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
    expedite = {row["id"] for row in classes_doc["classes"] if row.get("expedite")}
    floors = [(f"uncertainty {u['id']!r}", u["at_least"]) for u in classes_doc["uncertainty"]]
    floors += [(f"area {a['id']!r}", a["at_least"]) for a in areas_doc.get("areas", []) if "at_least" in a]
    for where, floor in floors:
        if floor in expedite:
            raise WeighError(f"{where} asks at least {floor!r}, an expedite class: an expedite class lands now "
                             f"and owes the rest, so it is no floor -- name the class the work must walk")
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
    # A record an area asks that is held ON A CARD (a review, a decision) is owed by a class that
    # keeps a card: a class whose whole record is its commit has nowhere to hold it, and the floor
    # would show it owed and refuse nothing.
    on_a_card = {row["id"] for row in classes_doc["records"] if row.get("held_by")}
    for area_id, hit in sorted(sig["touched"].items()):
        asked = [r for r in hit["area"].get("requires", []) if r in on_a_card]
        floor = lightest_with(classes_doc, "card")
        if asked and _heavier(classes_doc, floor, identity) != identity:
            identity, why = floor, f"{why}; area {area_id} requires {', '.join(asked)}, held on a card"
    row = classes_doc["classes"][_rank(classes_doc)[identity]]
    owed = list(row["requires"])
    for hit in sig["touched"].values():
        owed += [r for r in hit["area"].get("requires", []) if r not in owed]
    return {"class": row, "why": why, "requires": owed}


def _narrower(was, now) -> bool:
    """Whether a proof (`proved_by`) is narrower than the one it replaces. No proof declared is proof by
    EVERYTHING -- the strictest; a list is proof by those commands alone, and `[]` by `check` alone."""
    if now is None:
        return False
    return was is None or bool(set(was) - set(now))


def loosened(classes_doc: dict, before, after, commands=None) -> list:
    """How the areas a change leaves are LOOSER than the areas that stood before it -- empty when they
    are as strict or stricter. Tightening is anyone's act; loosening the scale a change is weighed by
    is a change of its own that owes a named record. With nothing before, nothing is loosened: no
    areas at all is the loosest a host can be.

    The PROOF is part of the scale: an area's or the default's `proved_by` narrowed, and -- given
    `commands`, the (before, after) command maps the proofs name -- a command removed or rewritten, are
    loosenings too. A command's text cannot be judged stronger or weaker, so any rewrite counts."""
    said = []
    if commands is not None:
        was_run, now_run = commands
        for key in sorted(was_run or {}):
            if key not in (now_run or {}):
                said.append(f"command {key} removed")
            elif now_run[key] != was_run[key]:
                said.append(f"command {key} rewritten ({was_run[key]!r} -> {now_run[key]!r})")
    if not before or not after:
        return said + ([] if not before else ["the areas declaration is removed"])
    scale, rank = _scale(classes_doc), _rank(classes_doc)
    if _narrower(before.get("default_proved_by"), after.get("default_proved_by")):
        said.append(f"default_proved_by {before.get('default_proved_by', 'everything')} -> "
                    f"{after.get('default_proved_by')}")

    def lower(a, b, order):  # a word the scale does not declare is read as the cheapest: fail closed
        return a in order and (b not in order or order[b] < order[a])

    if lower(before["default_undo"], after["default_undo"], scale):
        said.append(f"default_undo {before['default_undo']} -> {after['default_undo']}")
    was, now = before.get("max_areas", {}), after.get("max_areas", {})
    for cls, limit in sorted(was.items()):
        if cls not in now or now[cls] > limit:
            said.append(f"max_areas of {cls} {limit} -> {now.get(cls, 'unlimited')}")
    old_areas = {a["id"]: a for a in before.get("areas", [])}
    new_areas = {a["id"]: a for a in after.get("areas", [])}
    for identity, area in sorted(new_areas.items()):
        if identity not in old_areas and lower(before["default_undo"], area["undo"], scale):
            said.append(f"area {identity} added at {area['undo']}, cheaper than the {before['default_undo']} its "
                        f"paths stood at")
        if identity not in old_areas and _narrower(before.get("default_proved_by"), area.get("proved_by")):
            said.append(f"area {identity} added proved by {area.get('proved_by')}, narrower than the default "
                        f"proof its paths stood at ({before.get('default_proved_by', 'everything')})")
    for identity, area in sorted(old_areas.items()):
        kept = new_areas.get(identity)
        if kept is None:
            said.append(f"area {identity} removed")
            continue
        if kept["paths"] != area["paths"]:
            said.append(f"area {identity} paths {area['paths']!r} -> {kept['paths']!r}")
        if lower(area["undo"], kept["undo"], scale):
            said.append(f"area {identity} undo {area['undo']} -> {kept['undo']}")
        if _narrower(area.get("proved_by"), kept.get("proved_by")):
            said.append(f"area {identity} proved_by {area.get('proved_by', 'everything')} -> {kept.get('proved_by')}")
        if "at_least" in area and ("at_least" not in kept or lower(area["at_least"], kept["at_least"], rank)):
            said.append(f"area {identity} at_least {area['at_least']} -> {kept.get('at_least', 'none')}")
        dropped = sorted(set(area.get("requires", [])) - set(kept.get("requires", [])))
        if dropped:
            said.append(f"area {identity} no longer requires {', '.join(dropped)}")
        unfed = sorted(set(area.get("feeds", [])) - set(kept.get("feeds", [])))
        if unfed:  # a consumer no longer named is a consumer a change no longer reaches
            said.append(f"area {identity} no longer feeds {', '.join(unfed)}")
    return said


def loosened_areas(classes_doc: dict, before, after) -> list:
    """The areas AS THEY STOOD that a change loosens -- what the loosening itself is weighed as.

    Making irreversible paths cheap is itself the irreversible decision, taken once: whoever removes
    or cheapens an area walks the class a change to that area asked, on the record, and every later
    change is then weighed by the new scale honestly. The host's default stands as an area of its own
    where it is lowered, where an added area undercuts it, or where the declaration goes; a loosened
    breadth limit stands as the class a change beyond it computed."""
    if not before:
        return []
    scale, rank = _scale(classes_doc), _rank(classes_doc)

    def lower(a, b, order):
        return a in order and (b not in order or order[b] < order[a])

    old = {a["id"]: a for a in before.get("areas", [])}
    new = {a["id"]: a for a in (after or {}).get("areas", [])}
    lost = []
    for identity, area in sorted(old.items()):
        kept = new.get(identity)
        if (kept is None or kept["paths"] != area["paths"] or lower(area["undo"], kept["undo"], scale)
                or ("at_least" in area and ("at_least" not in kept or lower(area["at_least"], kept["at_least"], rank)))
                or set(area.get("requires", [])) - set(kept.get("requires", []))):
            lost.append(area)
    if (not after or lower(before["default_undo"], after["default_undo"], scale)
            or any(i not in old and lower(before["default_undo"], a["undo"], scale) for i, a in new.items())):
        lost.append({"id": "default_undo", "paths": "", "undo": before["default_undo"],
                     "because": "the cost every path no area claims stood at"})
    rows = [row["id"] for row in classes_doc["classes"] if not row.get("expedite")]
    now = (after or {}).get("max_areas", {})
    for cls, limit in sorted(before.get("max_areas", {}).items()):
        if (cls not in now or now[cls] > limit) and cls in rows and rows.index(cls) + 1 < len(rows):
            lost.append({"id": f"max_areas of {cls}", "paths": "", "undo": classes_doc["undo"][0]["id"],
                         "at_least": rows[rows.index(cls) + 1], "because": "the breadth a lighter class stopped at"})
    return lost


def _alone(area: dict) -> dict:
    return {"touched": {area["id"]: {"area": area, "paths": []}}, "unclaimed": [], "undo": area["undo"]}


def weigh(paths, classes_doc: dict, areas_doc: dict, loosening=(), lost=()) -> tuple:
    """(signals, verdict) for a set of paths -- the one entry every caller weighs through.

    `loosening` names how the change loosens the areas it is weighed by (`loosened`), and `lost` the
    areas as they stood that it loosens (`loosened_areas`). Such a change is at least the lightest
    class that owes a card, and at least the class a change to each loosened area computed: whoever
    loosens the scale walks what the scale asked -- and tightening it costs nothing."""
    sig = signals(list(paths), classes_doc, areas_doc)
    verdict = computed(sig, classes_doc, areas_doc)
    if not loosening:
        return sig, verdict
    rank = _rank(classes_doc)
    plain = classes_doc["classes"][rank[lightest_with(classes_doc, "card")]]
    weights = [verdict, {"class": plain, "requires": list(plain["requires"])}]
    weights += [dict(computed(_alone(area), classes_doc, {"max_areas": {}}), area=area["id"]) for area in lost]
    heaviest = max(weights, key=lambda w: rank[w["class"]["id"]])
    owed = []
    for weight in [heaviest, *weights]:
        owed += [r for r in weight["requires"] if r not in owed]
    asked = [w["area"] for w in weights if w.get("area") and w["class"]["id"] == heaviest["class"]["id"]]
    return sig, {"class": heaviest["class"], "requires": owed,
                 "why": f"{verdict['why']}; it loosens the areas it is weighed by ({'; '.join(loosening)})"
                        + (f", and walks what {', '.join(asked)} asked as it stood" if asked else "")}


def demotions(classes_doc: dict, before: dict, after: dict, closed=frozenset()) -> list:
    """Every card a change shapes LIGHTER than it stood, without the owner's door recorded on it.

    `before` and `after` map a card's PATH to the card as it stood and as the change leaves it (None:
    removed). Raising a class is anyone's act; lowering one is the owner's (ADR-025 decision 4),
    recorded by `reshape` as the card's last `reshaped` entry -- from the old class, to the new,
    approved by a named owner. Moving a card to or from an expedite class is never a raise: an
    expedite class owes nothing beyond its commit. Removing a classed card that has not finished is
    the heaviest demotion of all. A card with no class reads as the lightest class that owes a card,
    so dropping `class` from such a card lowers nothing."""
    rank, refused = _rank(classes_doc), []
    expedite = {row["id"] for row in classes_doc["classes"] if row.get("expedite")}
    plain = lightest_with(classes_doc, "card")
    for rel, was_card in sorted(before.items()):
        was = (was_card or {}).get("class")
        if was not in rank:
            continue
        card = after.get(rel)
        identity = (was_card or {}).get("id", rel)
        if card is None:
            if (was_card or {}).get("state") not in closed:
                refused.append(f"the card {identity} ({was}) is removed before it finished: removing a classed "
                               f"card is lowering it to nothing -- the owner's door")
            continue
        now = card.get("class")
        if now is not None and now not in rank:
            continue
        effective = now if now is not None else plain
        if effective == was:
            continue
        crosses_expedite = was in expedite or effective in expedite
        lowered = crosses_expedite or rank[effective] < rank[was]
        if not lowered:
            continue
        last = (card.get("reshaped") or [{}])[-1]
        fresh = last not in ((was_card or {}).get("reshaped") or [])  # an approval is a moment: this change's own
        if fresh and last.get("from") == was and last.get("to") == now and last.get("approved_by"):
            continue
        refused.append(f"the card {identity} is shaped {now or 'with no class'} where it stood {was}: "
                       + ("an expedite class is declared in a commit's trailer, never as a card's" if crosses_expedite
                          else "lowering a class is the owner's door")
                       + f" -- `reshape --card {identity} --class {now or '<class>'} --approve <owner>` records it")
    return refused


# -- a commit, and the card it names ----------------------------------------------------------
_TRAILER = re.compile(r"^([A-Za-z][A-Za-z0-9-]*)(\s*):\s*(\S.*?)\s*$")
_BLANK = re.compile(r"\n[ \t]*\n")


def _last_paragraph(message: str):
    """The last paragraph of a message as git reads it after its cleanup -- a line of only blanks
    separates paragraphs, comment lines are not the message -- or None for a one-paragraph message."""
    lines = [line for line in message.replace("\r\n", "\n").split("\n") if not line.startswith("#")]
    paragraphs = [p for p in _BLANK.split("\n".join(lines).strip()) if p.strip()]
    return paragraphs[-1] if len(paragraphs) >= 2 else None


def trailers(message: str) -> dict:
    """The trailers of a commit message, by lower-cased key: the `Key: value` lines of its last
    paragraph (git interpret-trailers). Comment lines are not the message and are dropped."""
    last = _last_paragraph(message)
    if last is None:
        return {}
    found = {}
    for line in last.splitlines():
        hit = _TRAILER.match(line)
        if hit:
            found.setdefault(hit.group(1).lower(), hit.group(3))
    return found


def miswritten(message: str, keys: dict) -> list:
    """The trailer lines of the declared keys that are not written canonically (`Key: value`): a space
    before the colon, or a key in another case. Every reader of trailers -- the hook, CI, the debt
    search -- reads the canonical form, so a variant is refused rather than read by some and not by
    others (the measured side door)."""
    last = _last_paragraph(message)
    if last is None:
        return []
    wanted = {key.lower(): key for key in keys.values()}
    said, seen = [], set()
    for line in last.splitlines():
        hit = _TRAILER.match(line)
        if not hit or hit.group(1).lower() not in wanted:
            continue
        key = hit.group(1).lower()
        if hit.group(2) or hit.group(1) != wanted[key]:
            said.append(f"the trailer {line.strip()!r} is not written `{wanted[key]}: <value>`: "
                        f"every reader reads that form and no other")
        if key in seen:
            said.append(f"the trailer `{wanted[key]}` is written twice: one commit, one answer -- a reader "
                        f"reads the first and never the second")
        seen.add(key)
    return said


def holds(card: dict, holder: dict, cards, decided=None) -> bool:
    """Whether a card holds a record as its `held_by` row says: a field present and not empty, cards
    hanging under it, or a criterion needing a class of evidence. `decided` -- handed in by a caller
    that can read the tree -- says whether a field's reference resolves to what the record requires
    (an `origin` that is a decision document)."""
    if holder.get("children"):
        return any(c.get("parent") == card.get("id") for c in cards)
    if "criterion_needs" in holder:
        return any(c.get("needs") == holder["criterion_needs"] for c in card.get("criteria") or [])
    value = card.get(holder["field"])
    if value in (None, "", [], {}):
        return False
    return decided(card, holder) if decided is not None and holder.get("kind_of_record") else True


def bet(card: dict, door_states) -> bool:
    """Whether the card passed through a door -- a passage into a state only a door opens, signed."""
    return any(p.get("to") in door_states and p.get("signed_by") for p in card.get("history") or [])


def card_floor(classes_doc: dict, card: dict, fallback: str) -> tuple:
    """(class, why) a card stands at: its declared class, else the fallback a card with none is read
    as -- raised to what its declared uncertainty asks, so no card stands lighter than the work it says
    it is. A declared class lighter than its uncertainty is also a defect its gate names."""
    shaped = card.get("class", fallback)
    why = "declared on the card" if "class" in card else f"no class on the card, read as {fallback}"
    asked = next((u["at_least"] for u in classes_doc["uncertainty"] if u["id"] == card.get("uncertainty")), None)
    rank = _rank(classes_doc)
    if (asked and shaped in rank and not classes_doc["classes"][rank[shaped]].get("expedite")
            and rank[asked] > rank[shaped]):
        return asked, f"{why}, raised to {asked} by its uncertainty {card['uncertainty']}"
    return shaped, why


def proof_for(paths, classes_doc: dict, areas_doc: dict, *rest) -> tuple:
    """(the commands that prove this change, why) -- or (None, why) when it is proved by EVERY command a
    MUST names (ADR-025 amendment 4). Proof is weighed as the work is: a change is proved by what proves
    the areas it touches, and only a change heavy enough to owe a decision, or one touching an area that
    declares no proof, is proved by everything. An area downstream of a touched one (`feeds`) moves with
    the change, so its proof is added -- and one that declares none proves by everything. A catalogue in
    which no class owes a decision cannot say what is heavy, so it proves by everything. No paths: nothing
    new, nothing to prove."""
    paths = list(paths)
    if not paths:
        return [], "nothing new to prove"
    sig, verdict = weigh(paths, classes_doc, areas_doc, *rest)
    heavy = next((row["id"] for row in classes_doc["classes"]
                  if not row.get("expedite") and "decision" in row["requires"]), None)
    if heavy is None:
        return None, "no class of this catalogue owes a decision, so none can be told apart as heavy: proved by everything"
    if heavier_or_equal(classes_doc, verdict["class"]["id"], heavy):
        return None, f"the change weighs {verdict['class']['id']}: what owes a decision is proved by everything"
    commands, unproved = [], []
    for hit in sig["touched"].values():
        declared = hit["area"].get("proved_by")
        if declared is None:
            unproved.append(hit["area"]["id"])
        commands += [c for c in declared or [] if c not in commands]
    if sig["unclaimed"]:
        declared = areas_doc.get("default_proved_by")
        if declared is None:
            unproved.append("(no area)")
        commands += [c for c in declared or [] if c not in commands]
    by_id = {area["id"]: area for area in areas_doc.get("areas", [])}
    for identity in sig.get("downstream", []):
        declared = by_id[identity].get("proved_by")
        if declared is None:
            unproved.append(f"{identity} (downstream)")
        commands += [c for c in declared or [] if c not in commands]
    if unproved:
        return None, f"{', '.join(sorted(unproved))} declare(s) no proof (proved_by): proved by everything"
    touched = ", ".join(sorted(sig["touched"])) or "no area"
    fed = f", feeds {', '.join(sig['downstream'])}" if sig.get("downstream") else ""
    return commands, f"the change touches {touched}{fed}, weighs {verdict['class']['id']}"


def lightest_with(classes_doc: dict, record: str) -> str:
    """The lightest computed class that owes a record: what a card with no class is read as."""
    return next(row["id"] for row in classes_doc["classes"]
                if not row.get("expedite") and record in row["requires"])


def commit_refusals(classes_doc: dict, verdict: dict, message: str, cards: dict, door_states=frozenset(),
                    decided=None) -> list:
    """Why a commit of this weight, with this message, may not be recorded -- empty when it may.

    The declared class (a trailer) is a floor's claimant: lighter than computed is refused; an expedite
    class -- only ever from the trailer, never from a card -- is admitted with what it owes; a heavier
    one owes its own records. A class that owes a card needs the card trailer and a card that exists,
    stands in a working state, is not shaped lighter than the change, holds every record the change
    owes (its class's and every touched area's), and -- where its class has doors -- passed the bet."""
    keys = classes_doc["trailers"]
    rank = _rank(classes_doc)
    said = trailers(message)
    refusals = miswritten(message, keys)
    computed_id = verdict["class"]["id"]
    owed = list(verdict["requires"])
    declared = said.get(keys["class"].lower())
    if declared is not None:
        declared = declared.lower()
        if declared not in rank:
            return refusals + [f"the message declares {keys['class']}: {declared}, which is not a declared class "
                               f"({', '.join(rank)})"]
        row = classes_doc["classes"][rank[declared]]
        if row.get("expedite"):
            return refusals
        if not heavier_or_equal(classes_doc, declared, computed_id):
            refusals.append(f"the message declares {keys['class']}: {declared}, but the change computes "
                            f"{computed_id} ({verdict['why']}): a declared class may be heavier, never lighter")
        else:
            computed_id = declared  # a heavier declaration owes the heavier class's records
            owed += [r for r in row["requires"] if r not in owed]
    if "card" not in owed:
        return refusals
    named = said.get(keys["card"].lower())
    if named is None:
        stray = re.search(rf"^{re.escape(keys['card'])}\s*:", message, re.M | re.I)
        hint = (" -- a `" + keys["card"] + ":` line is in the message, but not in its LAST paragraph, the one "
                "block git reads trailers from; put it beside the other trailers") if stray and not refusals else ""
        return refusals + [f"the change computes {computed_id} ({verdict['why']}), which owes a card: "
                           f"name it with a trailer `{keys['card']}: <card id>`{hint}"]
    card = cards.get(named)
    if card is None:
        return refusals + [f"{keys['card']}: {named} names no card this host holds"]
    if card.get("state") not in classes_doc["working_states"]:
        refusals.append(f"the card {named} is {card.get('state')!r}; work is committed to a card in "
                        f"{', '.join(classes_doc['working_states'])}")
    shaped, why = card_floor(classes_doc, card, lightest_with(classes_doc, "card"))
    if shaped not in rank:
        return refusals + [f"the card {named} declares the class {shaped!r}, which is not declared"]
    shaped_row = classes_doc["classes"][rank[shaped]]
    if shaped_row.get("expedite"):
        return refusals + [f"the card {named} is shaped {shaped}, an expedite class: an emergency is declared in "
                           f"the commit's trailer and its card is shaped as the work it repays"]
    if not heavier_or_equal(classes_doc, shaped, computed_id):
        refusals.append(f"the card {named} is shaped {shaped} ({why}), but this change computes "
                        f"{computed_id} ({verdict['why']}): re-shape the card -- a heavier class is the "
                        f"owner's bet -- or narrow the change")
    if shaped_row.get("doors") and door_states and not bet(card, door_states):
        refusals.append(f"the card {named} is shaped {shaped}, whose class has doors, and it never passed one: "
                        f"the owner bets it (walk-a-door) before work is committed to it")
    records = {row["id"]: row for row in classes_doc["records"]}
    listed = list(cards.values())
    for record in owed:
        holder = records.get(record, {}).get("held_by")
        if holder and not holds(card, holder, listed, decided):
            where = ("a card hanging under it" if holder.get("children")
                     else f"a criterion that needs {holder['criterion_needs']}" if "criterion_needs" in holder
                     else f"`{holder['field']}`")
            refusals.append(f"this change owes {record} (its class or a touched area asks it), held on the card "
                            f"by {where}, and {named} has none")
    return refusals
