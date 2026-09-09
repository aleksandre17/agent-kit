"""The lifecycle interpreter -- it decides HOW, and holds no policy of its own.

Every rule it applies arrives as data: which states exist, which passages between them are
declared, which of those are doors, which are open only to a declared class of card, how many
cards this host will carry in a state and how long it tolerates one sitting there. Nothing in
this module names a state, a capability or a number. That is the whole point: a rule this file
cannot see is a rule a host can change without changing the machine, and a passage nobody
declared is one nobody can violate.

It holds no ports either. The workspace, the manifest and the clock are handed in as values.
"""

from __future__ import annotations

from datetime import datetime

import doors
from errors import KitError

#: What a card's own record of its passages is called. One home for the audit vocabulary.
HISTORY = "history"
CREATED_AT = "created_at"


class LifecycleError(KitError):
    """A card, a move or a board contradicts the lifecycle that was declared."""


class Governed:
    """A collection and the lifecycle it moves through, found by DECLARATION."""

    __slots__ = ("capability", "spec", "doc", "cards", "policy")

    def __init__(self, capability, spec, doc, cards, policy) -> None:
        self.capability = capability
        self.spec = spec
        self.doc = doc
        self.cards = cards
        self.policy = policy

    @property
    def state_field(self) -> str:
        return self.spec["state_field"]

    @property
    def states(self) -> list:
        return self.doc["states"]

    @property
    def state_ids(self) -> list:
        return [state["id"] for state in self.states]

    def state(self, identity: str):
        return next((s for s in self.states if s["id"] == identity), None)


def governed_of(capability, readings):
    """The governed collection a capability declares, or None. The names all point INSIDE the
    capability's own declaration; no path and no capability id reaches this module."""
    spec = capability.governs
    if not spec:
        return None
    return Governed(
        capability, spec,
        capability.documents[spec["lifecycle"]],
        readings[spec["collection"]],
        readings[spec["policy"]].value,
    )


def the_governed(capabilities, readings) -> Governed:
    """The one governed collection in an enabled set. Zero is an honest refusal; two is a
    question this design has not answered, and it says so rather than picking one."""
    found = [g for g in (governed_of(c, readings) for c in capabilities) if g]
    if len(found) != 1:
        raise LifecycleError(
            f"{len(found)} enabled capability/capabilities declare a governed collection; "
            f"exactly one is required for this verb to know what it is moving"
        )
    return found[0]


# -- derivations ------------------------------------------------------------------------------
def entered_at(card: dict) -> str:
    """DERIVED, never stored: the moment a card entered the state it is in now is the moment of
    its last passage, or its creation if it has never moved. Storing it beside `history` would be
    a second home for one truth, and the two would part company the first time anyone edited one."""
    history = card.get(HISTORY) or []
    return history[-1]["at"] if history else card[CREATED_AT]


def last_mover(card: dict) -> str:
    history = card.get(HISTORY) or []
    return history[-1]["by"] if history else "-"


def _moment(text: str) -> datetime:
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise LifecycleError(f"{text!r} is not a moment this kit can read -- {exc}") from exc


def days_between(earlier: str, later: str) -> float:
    return (_moment(later) - _moment(earlier)).total_seconds() / 86400.0


# -- the board: a projection, and one that may never quietly drop a card -----------------------
def columns(governed: Governed) -> list:
    limits = governed.policy.get("wip_limit", {})
    field = governed.state_field
    declared = set(governed.state_ids)
    for card in governed.cards.value:
        if card[field] not in declared:
            raise LifecycleError(
                f"card {card['id']!r} is in state {card[field]!r}, which lifecycle "
                f"{governed.doc['id']!r} does not declare. Declared states are "
                f"{governed.state_ids}. A board that simply omitted it would be a surface "
                f"stating that this card does not exist."
            )
    built = []
    for state in governed.states:
        items = [
            dict(card,
                 owner=card.get("owner", "-"),
                 **{"class": card.get("class", "-")},
                 entered_at=entered_at(card),
                 last_by=last_mover(card))
            for card in governed.cards.value if card[field] == state["id"]
        ]
        built.append(dict(state, items=items, count=len(items),
                          limit=limits.get(state["id"], "-")))
    return built


# -- the gates' rules, shared with the verb that would break them ------------------------------
def capacity_failures(governed: Governed, cards=None) -> list:
    """A limit the HOST declared, applied to a card set. The same function answers `check` and
    `move`, so a host cannot be refused a move it would then pass a gate with."""
    cards = governed.cards.value if cards is None else cards
    limits = governed.policy.get("wip_limit", {})
    failures = []
    for state_id, limit in sorted(limits.items()):
        held = [c["id"] for c in cards if c[governed.state_field] == state_id]
        if len(held) > limit:
            failures.append(
                f"state {state_id!r} holds {len(held)} card(s) -- {sorted(held)} -- and this host "
                f"declared a limit of {limit} in {governed.spec['policy']}"
            )
    return failures


def age_failures(governed: Governed, now: str) -> list:
    """The Clock's one real rule. A card older than the host's declared tolerance is REPORTED,
    never moved: parking is a passage, every passage records who made it, and a machine that
    parked a card would be a machine deciding -- which is the one thing an interpreter may not do."""
    ages = governed.policy.get("max_age_days", {})
    failures = []
    for card in governed.cards.value:
        limit = ages.get(card[governed.state_field])
        if limit is None:
            continue
        age = days_between(entered_at(card), now)
        if age > limit:
            failures.append(
                f"card {card['id']!r} entered {card[governed.state_field]!r} at "
                f"{entered_at(card)} and has sat there {age:.1f} day(s); this host declared "
                f"{limit} in {governed.spec['policy']}. Park it, bet on it, or drop it -- "
                f"reading at {now}"
            )
    return failures


# -- the transition ----------------------------------------------------------------------------
def _guard_holds(edge: dict, card: dict) -> bool:
    guard = edge.get("when")
    return guard is None or card.get(guard["field"]) == guard["equals"]


def _guard_note(edge: dict, card: dict) -> str:
    guard = edge["when"]
    return (f"the declared edge {edge['from']} -> {edge['to']} is open only when "
            f"{guard['field']}={guard['equals']!r}; this card declares "
            f"{guard['field']}={card.get(guard['field'])!r}")


def _route(governed: Governed, card: dict, start: str, target: str, skip: list) -> list:
    """The declared way from one state to another FOR THIS CARD: the passages already ruled out
    are ignored, and so is any guarded passage whose guard this card does not satisfy.

    A refusal that names only the illegal edge tells an operator nothing about the door they were
    supposed to walk through. But a refusal that routed them through a guard they cannot pass
    would be worse than silence -- a surface confidently naming a way that is not open to them,
    and one they would discover was shut only by being refused a second time."""
    frontier = [(start, [])]
    seen = {start}
    while frontier:
        state, path = frontier.pop(0)
        for edge in governed.doc["transitions"]:
            if edge["from"] != state or edge in skip or edge["to"] in seen:
                continue
            if not _guard_holds(edge, card):
                continue
            if edge["to"] == target:
                return path + [edge]
            seen.add(edge["to"])
            frontier.append((edge["to"], path + [edge]))
    return []


def _route_note(governed: Governed, card: dict, start: str, target: str, skip: list) -> str:
    route = _route(governed, card, start, target, skip)
    if not route:
        return (f"and this lifecycle declares no way at all from {start!r} to {target!r}; "
                f"the exits from {start!r} are "
                f"{sorted(e['to'] for e in governed.doc['transitions'] if e['from'] == start)}")
    drawn = " -> ".join([start] + [edge["to"] for edge in route])
    note = f"the declared way from {start!r} to {target!r} is: {drawn}"
    for edge in route:
        if edge.get("door"):
            note += (f"; and {edge['from']} -> {edge['to']} is a DOOR only the {edge['door']} "
                     f"may open (--approve <who>). You may skip neither a state nor a door.")
    return note


def resolve(governed: Governed, card: dict, target: str, approver) -> dict:
    """Which declared passage this move is, or a refusal that names what was missing."""
    field = governed.state_field
    state = card[field]
    for name in (state, target):
        if governed.state(name) is None:
            raise LifecycleError(
                f"{name!r} is not a state lifecycle {governed.doc['id']!r} declares; "
                f"declared states are {governed.state_ids}"
            )
    if state == target:
        raise LifecycleError(f"card {card['id']!r} is already in state {target!r}")

    edges = [e for e in governed.doc["transitions"] if e["from"] == state and e["to"] == target]
    usable = [e for e in edges if _guard_holds(e, card)]
    if not usable:
        reasons = [_guard_note(e, card) for e in edges if e.get("when")]
        if not edges:
            reasons.append(f"{state} -> {target} is not a declared passage")
        raise LifecycleError(
            f"card {card['id']!r} may not move {state} -> {target}: "
            + "; ".join(reasons) + ". " + _route_note(governed, card, state, target, edges)
        )

    edge = usable[0]
    door = edge.get("door")
    if door and not approver:
        doors.refuse(
            what=(f"card {card['id']!r} stands at {state} -> {target}, and the lifecycle declares "
                  f"that passage a door"),
            who_may=door,
            how=f"move --card {card['id']} --to {target} --approve <who>",
            because=f"Exit criterion: {edge['exit']}.",
        )
    if approver and not door:
        raise LifecycleError(
            f"{state} -> {target} declares no door, so there is nothing here for {approver!r} to "
            f"accept. An approval recorded where none was required is a name against a decision "
            f"nobody made; use --by <who> for a passage a machine may make."
        )
    return edge


def moved(governed: Governed, card: dict, edge: dict, when: str, by: str, approver=None) -> dict:
    """The card, moved. Its state has ONE home and this writes it; the passage is recorded with
    who and when, exactly as an install approval is."""
    passage = {"from": edge["from"], "to": edge["to"], "at": when, "by": by}
    if approver:
        passage.update(doors.record(approver, when))
    return dict(card, **{governed.state_field: edge["to"]},
                **{HISTORY: list(card.get(HISTORY) or []) + [passage]})
