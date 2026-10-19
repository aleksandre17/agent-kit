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

import collection
import doors
from errors import KitError

#: What a card's own record of its passages is called. One home for the audit vocabulary.
HISTORY = "history"
CREATED_AT = "created_at"

#: The field a state declares when work SPENDS its appetite while it stands there (ADR-020
#: amendment 2). The states that carry it are the lifecycle's to name; this is only the FIELD.
SPENDS = "spends"

#: The two modes a passage may declare, as the grammar carries them: the principal who holds a
#: judgement, and the reference that decides a computation. The words themselves are the host's
#: vocabulary; these are the FIELDS the declaration puts them in.
DOOR = "door"
COMPUTED = "computed"
PROOF = "proof"


class LifecycleError(KitError):
    """A card, a move or a board contradicts the lifecycle that was declared."""

    code = "KIT0011"


class UncomputedPassage(KitError):
    """A passage a machine decides was asked for, and the reference that decides it did not hold
    -- or could not be read, which is not the same thing and is not treated as one."""

    code = "KIT0061"


class Governed:
    """A collection and the lifecycle it moves through, found by DECLARATION."""

    __slots__ = ("capability", "spec", "doc", "members", "policy")

    def __init__(self, capability, spec, doc, members, policy) -> None:
        self.capability = capability
        self.spec = spec
        self.doc = doc
        self.members = members
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


def declared_states(capabilities) -> list:
    """The states of the one governed lifecycle among these capabilities, read from its declaration
    alone -- no record is opened, so a reading that needs only the vocabulary of states (which ones
    spend, which ones close) does not pay for reading every card to learn it."""
    found = [c.documents[c.governs["lifecycle"]]["states"] for c in capabilities if c.governs]
    if len(found) != 1:
        raise LifecycleError(
            f"{len(found)} enabled capability/capabilities declare a governed collection; "
            f"exactly one is required to know which states it declares"
        )
    return found[0]


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
        return datetime.fromisoformat(str(text).replace("Z", "+00:00"))  # 3.10 reads no trailing Z
    except ValueError as exc:
        raise LifecycleError(f"{text!r} is not a moment this kit can read -- {exc}") from exc


def days_between(earlier: str, later: str) -> float:
    return (_moment(later) - _moment(earlier)).total_seconds() / 86400.0


# -- the board: a projection, and one that may never quietly drop a card -----------------------
def _with_their_programs(items: list, every: list) -> list:
    """A column's cards with each program's parts right after it (a `parent` chain, read over every card,
    so a part whose program sits in another column still keeps its program's place): grouping is a
    view, never a folder -- a card moved to group it would be a card whose links and history moved too."""
    by_id = {card["id"]: card for card in every}

    def chain(card) -> list:
        seen, out = set(), [card["id"]]
        while isinstance(by_id.get(out[0], {}).get("parent"), str) and out[0] not in seen:
            seen.add(out[0])
            out.insert(0, by_id[out[0]]["parent"])
        return out

    first = {}
    for index, card in enumerate(items):
        first.setdefault(chain(card)[0], index)
    return sorted(items, key=lambda card: (first[chain(card)[0]], len(chain(card))))


def columns(governed: Governed, counted=None) -> list:
    """The board, computed. `counted` is a function from one record to whatever NUMBERS a surface
    may show about it beyond its own fields, or None where nothing counts anything.

    It is handed in rather than reached for, like the clock and the workspace: a count that has to
    read the host's tree is a reading, this module holds no ports, and a module that acquired one
    to fill in a column would have made the board's honesty depend on what it could reach. What
    the numbers MEAN is not known here either -- they are merged into the record and rendered by
    whatever the surface declares about them.
    """
    limits = governed.policy.get("wip_limit", {})
    field = governed.state_field
    declared = set(governed.state_ids)
    for card in governed.members.value:
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
                 parent=card["parent"] if isinstance(card.get("parent"), str) else "",
                 **{"class": card.get("class", "-")},
                 entered_at=entered_at(card),
                 last_by=last_mover(card),
                 **(counted(card) if counted else {}))
            for card in governed.members.value if card[field] == state["id"]
        ]
        count, recent = len(items), governed.policy.get("board_recent")
        if state.get("closed") and recent is not None and count > recent:
            # Finished work is COUNTED whole and LISTED by its newest few (ADR-025 decision 13): the
            # board a project reads to work stays one size however old the project grows, and the
            # count says out loud how many it does not list -- nothing is dropped in silence.
            items = sorted(items, key=lambda c: _moment(c["entered_at"]), reverse=True)[:recent]
        items = _with_their_programs(items, governed.members.value)
        built.append(dict(state, items=items, count=count, hidden=count - len(items),
                          limit=limits.get(state["id"], "-")))
    return built


# -- the gates' rules, shared with the verb that would break them ------------------------------
def capacity_failures(governed: Governed, members=None) -> list:
    """A limit the HOST declared, applied to a member set. The same function answers `check` and
    `move`, so a host cannot be refused a move it would then pass a gate with."""
    members = governed.members.value if members is None else members
    limits = governed.policy.get("wip_limit", {})
    failures = []
    for state_id, limit in sorted(limits.items()):
        held = [c["id"] for c in members if c[governed.state_field] == state_id]
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
    for card in governed.members.value:
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
        if edge.get(DOOR):
            note += (f"; and {edge['from']} -> {edge['to']} is a DOOR only the {edge[DOOR]} "
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
    door = edge.get(DOOR)
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


def decided_by(edge: dict) -> "dict | None":
    """The reference that DECIDES this passage, or None where the declaration names none.

    A passage that declares a principal AND a reference is refused before anything is read: it
    claims at once a judgement no machine may make and a computation no principal may declare, and
    nothing can honour both. A passage that declares NEITHER is not refused -- most lifecycles in
    the world are written that way, and a rule that reddened every one of them on the day it
    arrived would be switched off by the end of the week -- but it is an unowned passage, and an
    unowned passage is how work silently advances.
    """
    condition = edge.get(COMPUTED)
    if condition is None:
        return None
    if edge.get(DOOR):
        raise LifecycleError(
            f"the passage {edge['from']} -> {edge['to']} declares both a principal who holds it "
            f"and a reference that decides it. Those are the two modes a passage may have and "
            f"they exclude each other: one says no machine may make this move, the other says no "
            f"principal may. Declare one"
        )
    return condition[PROOF]


def refuse_uncomputed(card: dict, edge: dict, verdict) -> None:
    """The machine's own refusal to enter a state it computes.

    This is what makes such a state mean anything: it is not entered because somebody said so, and
    the reading that refused it is printed rather than summarised. A reference that could not be
    read at all refuses the passage exactly as a refuted one does -- nothing may pass on an
    unobserved proof -- but it is NAMED differently, because the cure for the two is different:
    one is work to finish, the other is a reference to fix.
    """
    if verdict.holds is True:
        return
    unread = verdict.holds is None
    raise UncomputedPassage(
        f"card {card[collection.IDENTITY]!r} may not enter {edge['to']!r}: that passage is decided "
        f"by a machine, and the reference that decides it "
        + ("could not be read" if unread else "was read and did not hold")
        + f" -- {verdict.reading}. "
        + ("Nothing was observed, so nothing is claimed in either direction: fix what the "
           "reference points at, or point it at something that is there."
           if unread else
           "This is a fact about the work, not about the record.")
        + " No principal may declare this passage instead; a state anybody could type is a "
          "state that means only that somebody said so"
    )


def moved(governed: Governed, card: dict, edge: dict, when: str, by: str, approver=None) -> dict:
    """The card, moved. Its state has ONE home and this writes it; the passage is recorded with
    who and when, exactly as an install approval is."""
    passage = {"from": edge["from"], "to": edge["to"], "at": when, "by": by}
    if approver:
        passage.update(doors.record(approver, when))
    return dict(card, **{governed.state_field: edge["to"]},
                **{HISTORY: list(card.get(HISTORY) or []) + [passage]})
