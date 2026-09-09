"""The resolver -- composition semantics, and nothing else.

A pure function over declarations: it touches no filesystem, no clock and no port, so what it
decides can be reasoned about without running anything. It knows the name of no capability.

Two absences are distinguished ON PURPOSE, because they are not the same kind of fact:

  * A **fact** requirement is about the HOST. The host either is a git repository or is not, and
    nothing in the kit can change that. An unmet fact makes a capability UNAVAILABLE -- a declared
    state, recorded with its reason, and the rest of the install proceeds around it.

  * A **capability** requirement is about the DECLARED SET. If a capability needs a provision that
    the enabled set does not offer, no measurement will fix it: the set itself is incoherent. That
    is a DEFECT and it is REFUSED. The resolver does not helpfully enable the missing capability
    for you -- an interpreter that repairs a declaration has started deciding (Cardinal IV), and a
    host would end up running a set nobody chose.

A requirement of kind `capability` is matched against what capabilities PROVIDE, never against
their ids. A provision is a contract; an id is a name. Two capabilities offering the same
provision are substitutable, and the requirer never learns which one it got (Cardinal VIII).

Ordering is total and independent of declaration order: dependencies first, ties broken by id.
Byte-reproducibility downstream is worth nothing if the order that produced the bytes drifts.
"""

from __future__ import annotations

from errors import KitError


class CompositionError(KitError):
    """The declared set cannot compose: an unmet provision, a conflict, or two capabilities
    casting a shadow on one path. Never resolved by preference -- always refused."""


def _provisions(capabilities) -> dict:
    """provision -> [capability ids offering it]. A capability provides only what it DECLARES;
    its own id is not an implicit provision, because a name is not a contract."""
    offered: dict[str, list] = {}
    for capability in capabilities:
        for name in capability.raw.get("provides", []):
            offered.setdefault(name, []).append(capability.id)
    return offered


def _unmet_facts(capability, facts: dict) -> list:
    return [
        need for need in capability.requires
        if need["kind"] == "fact" and facts.get(need["id"], None) != need.get("equals", True)
    ]


def _shadows(a: str, b: str) -> bool:
    """Two install targets collide when they are the same path, or when one contains the other.
    Containment counts: a file inside a directory another capability owns is still two owners."""
    return a == b or a.startswith(b.rstrip("/") + "/") or b.startswith(a.rstrip("/") + "/")


def _refuse_shadow_collisions(capabilities) -> None:
    """Two capabilities installing to one path is a DEFECT, not a precedence question. There is
    no last-writer-wins here and there must never be one: the loser's declaration would still
    read as true while the bytes on disk came from somewhere else -- both locally correct, the
    system speaking with confidence and lying (Cardinal III)."""
    owned: list[tuple[str, str]] = []
    for capability in capabilities:
        for target in capability.targets():
            for other_target, other_id in owned:
                if _shadows(target, other_target):
                    raise CompositionError(
                        f"shadowed path: capability {capability.id!r} installs {target!r} and "
                        f"capability {other_id!r} installs {other_target!r}; one path may have "
                        f"exactly one owner, and this is refused rather than ordered"
                    )
            owned.append((target, capability.id))


def _refuse_conflicts(capabilities, offered: dict) -> None:
    for capability in capabilities:
        for name in capability.raw.get("conflicts", []):
            clashing = [cid for cid in offered.get(name, []) if cid != capability.id]
            if clashing:
                raise CompositionError(
                    f"declared conflict: capability {capability.id!r} conflicts with provision "
                    f"{name!r}, which {sorted(clashing)} offer"
                )


def _order(capabilities) -> list:
    """Dependencies before dependants; ties by id. Kahn's algorithm with a sorted frontier, so
    the result depends on the declarations and never on the order they were listed in."""
    by_id = {c.id: c for c in capabilities}
    offered = _provisions(capabilities)
    needs = {
        c.id: {
            provider
            for need in c.requires if need["kind"] == "capability"
            for provider in offered.get(need["id"], [])
            if provider != c.id
        }
        for c in capabilities
    }
    ordered: list = []
    placed: set = set()
    while len(ordered) < len(by_id):
        ready = sorted(cid for cid in by_id if cid not in placed and needs[cid] <= placed)
        if not ready:
            remaining = sorted(cid for cid in by_id if cid not in placed)
            raise CompositionError(
                f"requirement cycle among capabilities {remaining}: no order can satisfy them"
            )
        for cid in ready:
            ordered.append(by_id[cid])
            placed.add(cid)
    return ordered


def arrange(capabilities) -> list:
    """Order an already-decided set and hold it to the same composition rules. Used where the
    set comes from host truth rather than from a fresh measurement, so that a set which was
    coherent at install time cannot quietly become shadowed later and go unnoticed."""
    ordered = _order(capabilities)
    _refuse_conflicts(ordered, _provisions(ordered))
    _refuse_shadow_collisions(ordered)
    return ordered


def classify(capabilities, facts: dict) -> tuple[list, list]:
    """Split by what was MEASURED, and never refuse. Returns (candidates, unavailable).

    This half is deliberately separate from `compose` so that a caller can REPORT the measured
    absence before anything is refused because of it. A refusal that arrives before the reading
    it followed from names a symptom while the cause goes unsaid -- which is the same lie as a
    silent failure, only faster.
    """
    candidates, unavailable, blocked = [], [], {}
    for capability in capabilities:
        missing = _unmet_facts(capability, facts)
        if missing:
            reason = "unmet requirement: " + ", ".join(
                f"{need['kind']}:{need['id']}" for need in missing
            )
            unavailable.append({"id": capability.id, "reason": reason})
            for provision in capability.raw.get("provides", []):
                blocked.setdefault(provision, f"{capability.id} ({reason})")
        else:
            candidates.append(capability)
    return candidates, unavailable, blocked


def compose(candidates, blocked=None) -> list:
    """Hold the surviving set to the composition rules and put it in order, or REFUSE.

    `blocked` maps a provision to the capability that would have offered it and the measured
    reason it cannot, so the refusal can say WHY a provision is missing: a capability the host
    cannot support reads very differently from one nobody declared, and a message that cannot
    tell them apart sends the reader to the wrong place.
    """
    blocked = blocked or {}
    offered = _provisions(candidates)
    for capability in candidates:
        for need in capability.requires:
            if need["kind"] != "capability" or offered.get(need["id"]):
                continue
            because = (
                f"it is provided by {blocked[need['id']]}, which this host cannot support"
                if need["id"] in blocked else "no enabled capability provides it"
            )
            raise CompositionError(
                f"unmet requirement: capability {capability.id!r} requires "
                f"capability:{need['id']}, and {because}. The set is refused as declared; "
                f"nothing was enabled on its behalf."
            )

    _refuse_conflicts(candidates, offered)
    ordered = _order(candidates)
    _refuse_shadow_collisions(ordered)
    return ordered
