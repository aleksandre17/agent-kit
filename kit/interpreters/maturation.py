"""MATURATION -- an undertaking that has run out, and the concession it therefore spends.

A host caps a count it means to drive down, and while the count is above that cap the judgement
that reads it is one the host may legitimately watch rather than be stopped by. The cap is the
whole of the reason: it is a promise to reach a number, and the day the promise is *nothing of
this*, the grace it bought has been spent. That is what this module computes -- not a stance, and
not anybody's policy. It reads two declarations that already exist and reports a FACT about their
relationship, which the stance reading then resolves in the one place stances are resolved.

**Nothing here is written anywhere, and no consequence is spelled.** The host declares the cap in
its own map; the vocabulary declares what an unanswered judgement stands in; the publisher declares
which of its judgements a count is the reading of. This module owns none of those three and adds no
fourth, because a framework that wrote a stance into a host's declaration -- or held one of its own
to write -- would have made the host's policy its own, whatever the number that triggered it.

**The reading is of a DECLARATION and never of the world.** What matures a judgement is the cap a
host undertook, not the count measured this minute. The distinction is the dangerous case and it is
decided deliberately: a count that cannot be taken today answers `None` (never 0), and a maturation
that leaned on the measurement would silently hand a judgement its concession back on the day the
world became unreadable -- a regression nobody declared, on a surface that would go on printing
green. An undertaking stands until the host restates it, and the one restatement available is a
lowering, because the ratchet refuses every raise.

**What cannot be reached from here.** What matures is looked up among the JUDGEMENTS this kit
publishes -- the registry of who can evaluate what. A passage that a declaration says a principal
holds is in no such registry and has no key in it: it carries a party, not a consequence a run can
resolve, and no cap, at any value, produces a party. So a passage cannot be matured here, and the
reason is not a rule written against it -- it is that this mechanism addresses judgements and a
passage is not one. An undertaking that points at anything else resolves to NOTHING, and nothing is
refused out loud rather than passed over, because a cap that quietly matured nothing would read, on
every later run, exactly like a host still working its way down.
"""

from __future__ import annotations

import gatekinds
from errors import KitError

#: The registry entry a module publishes when it can read a host's UNDERTAKINGS out of the
#: declaration that carries them, keyed by the gate kind whose declared row says where that
#: declaration lives. One module answers it -- the one that already reads those rows -- and a
#: second would be a second answer to *what has this host undertaken* (Cardinal III).
EXHAUSTED = "EXHAUSTED"

#: The registry entry a module publishes to say which of ITS OWN judgements a count it takes is
#: the reading of. Published beside the count, by the module that owns both words, and discovered
#: by the one discovery that finds every other registry here -- so this module names no count, no
#: judgement and no capability, and a new pairing is a row in a module, never an edit here.
JUDGED_BY = "JUDGED_BY"


class MaturationError(KitError):
    """An undertaking that has run out points at something this kit cannot mature: a name no
    module publishes as a judgement. Refused rather than skipped -- a cap that matures nothing
    while claiming to reads exactly like a cap still being worked down."""

    code = "KIT0066"


class Matured:
    """One judgement whose concession a host's own undertaking has spent, and the file that says
    so. The source travels with the fact for the same reason a stance carries its author: a
    consequence whose origin a reader cannot check is indistinguishable from one the machine chose.
    """

    __slots__ = ("kind", "measure", "where")

    def __init__(self, kind: str, measure: str, where: str) -> None:
        self.kind, self.measure, self.where = kind, measure, where

    def says(self) -> str:
        return (f"matured -- this host undertook {self.measure!r} at nothing, in {self.where}, and "
                f"the grace that undertaking bought is spent")


def honoured(exhausted: dict, pairings: dict, judged, running) -> tuple:
    """`(kind -> Matured, the undertakings that mature nothing, each in its own words)`.

    Every input is a declaration somebody else already read, and nothing is read here: the one
    reading of a host's caps stays where it is taken, and this resolution can be driven whole by a
    caller holding declarations in its hand -- which is what makes the refusal below testable
    without a tree, a clock or a repository.
    """
    matured: dict = {}
    idle: list = []
    for measure in sorted(exhausted):
        where = exhausted[measure]
        kind = pairings.get(measure)
        if kind is None:
            idle.append(
                f"{where}: {measure!r} is undertaken at nothing, and no module of this kit says "
                f"which judgement that count is the reading of. It matures nothing -- stated here "
                f"rather than passed over, because an undertaking fulfilled and an undertaking "
                f"nothing reads look identical from the outside."
            )
            continue
        if kind not in judged:
            raise MaturationError(
                f"{where}: {measure!r} is undertaken at nothing and is paired with {kind!r}, which "
                f"no module of this kit publishes as a judgement; the judgements published are "
                f"{sorted(judged)}. What matures is the consequence a FAILURE carries, and only a "
                f"judgement has one. A passage a declaration puts in a party's hands carries that "
                f"party and no consequence at all, so no cap -- at nothing or at any other number "
                f"-- can reach it, and this kit will not invent the party it would have to replace."
            )
        if kind not in running:
            idle.append(
                f"{where}: {measure!r} is undertaken at nothing, and no capability this host has "
                f"enabled declares anything of the kind that reads it. It matures nothing here, "
                f"and would the moment that capability is enabled."
            )
            continue
        matured[kind] = Matured(kind, measure, where)
    return matured, idle


def spent(ctx, enabled) -> tuple:
    """What this host's exhausted undertakings mature, taken from where each is already declared.

    The undertakings are read THROUGH the declared rows that say where they live, by the module
    that publishes itself able to read them -- never by locating the host's declaration a second
    time here (Cardinal III), and never by a discovery loop of this module's own (Cardinal II).
    """
    readers = gatekinds.registry(EXHAUSTED)
    exhausted: dict = {}
    for capability in enabled:
        for gate in capability.gates:
            read = readers.get(gate["kind"])
            if read is not None:
                exhausted.update(read(ctx, gate.get("params", {})))
    running = {gate["kind"] for capability in enabled for gate in capability.gates}
    return honoured(exhausted, gatekinds.registry(JUDGED_BY), gatekinds.registry(), running)
