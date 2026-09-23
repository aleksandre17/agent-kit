"""Write-ahead eviction -- nothing leaves a bounded artifact without being written down first.

ADR-020 decision 2, as a passage rather than as a rule anybody keeps. A bounded artifact that
carries the current POSITION may carry only that; what was true earlier is the RECORD, which is
append-only and unbounded and lives elsewhere. The instant a ceiling is placed over an artifact
holding both, the two compete for one budget and CURRENCY BECOMES PURCHASABLE WITH THE RECORD --
an exchange nobody ever chose, made at the moment of most pressure, by whoever hit the limit. It
was measured: five writes refused for being 403, 129, 9 and 191 characters over a ceiling, and the
cure each time was the deletion of true, dated history that left no trace.

The ceiling is not the defect and is never relaxed here. What this module adds is the ORDER:

    the before-image is journalled  ->  and only then is the artifact replaced

so the destructive act becomes impossible to PERFORM rather than merely discouraged, and deletion
becomes a move by construction. A write whose journal append fails is REFUSED and the artifact is
not touched: a writer that carried on would be exactly the silent deletion this exists against.

Four things this module refuses to decide, because each of them belongs to somebody else:

  * WHERE THE JOURNAL IS, and where the artifact is. Both arrive as a port and a path from the
    caller. A host's position surface and its journal are the host's declarations; an interpreter
    that knew either would be deciding where a host steers from (Cardinal IV).
  * WHAT A REMOVAL MEANS. It states the text that left and where it landed, and nothing about
    whether that was wise. An editorial cut with nowhere to land is LEGAL: it is counted, never
    refused, because a gate that fires on ordinary work is switched off within a week.
  * WHETHER THE COUNT IS TOO HIGH. That is a ceiling, a ceiling is a number, and every number is
    the host's (ADR-020 absence 4). The count is published as a MEASURE for the budget ratchet
    that already exists; this kit builds no second ratchet.
  * WHEN THE LOG MAY BE COMPACTED. Not decided (ADR-020 absence 5). Until a retention passage is
    declared the journal is append-only and is never compacted -- a compaction that dropped the
    unlanded events would re-create the measured loss in slow motion.

The log is AHEAD of the artifact and never behind it. If the write that follows an accepted append
fails, the before-image describes a removal that did not take effect: the text is then preserved
twice and lost zero times. That asymmetry is the whole purchase of the ordering, and it is stated
here rather than repaired, because the repair -- a second event saying the first did not happen --
would be a second mechanism whose own failure would need a third.
"""

from __future__ import annotations

import difflib
import json
import os
from pathlib import Path

from errors import KitError

#: The kit schema that is the ONE home of the event's shape. The version an event is written at is
#: read from the manifest through it; nothing here declares a second one.
SCHEMA = "eviction"

#: The word a line of the journal says it is. A journal may carry more than one mechanism's lines,
#: and a line that does not say what it is can only be read by guessing at its fields.
EVENT = "eviction"

#: The event's own field names -- the schema is their home; these are the ones this module and the
#: measure beside it resolve with.
REMOVED, CHARS, LANDED = "removed", "removed_chars", "landed"

#: The front-matter field a bounded artifact carries its unlanded count in (schema `front-matter`).
#: Declared HERE, in the module that owns the eviction vocabulary, and imported by the measure that
#: reads it -- one word, one home, so a rename cannot leave a gate counting a field nobody writes.
#: It is a STRING of digits on the surface because front matter interprets nothing by design: the
#: grammar reads one scalar per line and never types it, so an `integer` there would be a contract
#: the medium cannot satisfy. The arithmetic is done here, on the way in and on the way out.
UNLANDED = "unlanded_removals"


class EvictionRefused(KitError):
    """The before-image could not be written down, so the write it belonged to did not happen.

    This is the mechanism working, not a fault in it. The one ordering guarantee this module sells
    is that the record is ahead of the artifact; a writer that proceeded when the record could not
    be extended would be selling nothing at all."""

    code = "KIT0056"


class CounterUnreadable(KitError):
    """An artifact declares an unlanded count that is not a count. Refused rather than defaulted:
    a zero substituted for a value nobody can read is a corpus reporting that it has lost nothing,
    in exactly the case where the number it lost was the number of its losses."""

    code = "KIT0057"


def spans(prior: str, candidate: str) -> list:
    """Every contiguous run of lines that stood in `prior` and does not stand in `candidate`, in
    the order it stood.

    Line granularity, deliberately. A character-level image is arithmetically tighter and shreds a
    replaced paragraph into fragments around accidental common substrings -- and the purpose here
    is RECOVERY by a human who pastes a span back. It over-reports a removal (a reworded line
    counts whole, because the line that stood there is gone whole) and can never under-report one,
    which is the direction a record of losses must err in.
    """
    before, after = prior.splitlines(keepends=True), candidate.splitlines(keepends=True)
    matcher = difflib.SequenceMatcher(None, before, after, autojunk=False)
    return ["".join(before[i1:i2])
            for tag, i1, i2, _j1, _j2 in matcher.get_opcodes() if tag in ("delete", "replace")]


def event(ctx, *, prior: str, candidate: str, at: str, artifact: str, section: str = None,
          rev: int = None, runtime: str = None, landed: dict = None) -> "dict | None":
    """The before-image of one accepted write, or `None` when the write removes nothing.

    `None` is not an empty event: a write that only adds has evicted nothing, and a journal line
    saying so would be a record of a removal that never happened. Validated against its schema
    HERE, before anything is appended anywhere -- an event that cannot be read is not a record, and
    appending one would leave the log holding a line no later reader can trust.
    """
    removed = spans(prior, candidate)
    if not removed:
        return None
    value = {
        "schema_version": ctx.manifest.version_of(SCHEMA),
        "event": EVENT,
        "at": at,
        "artifact": artifact,
        CHARS: sum(len(span) for span in removed),
        REMOVED: removed,
        LANDED: landed,
    }
    for field, given in (("section", section), ("rev", rev), ("runtime", runtime)):
        if given is not None:
            value[field] = given
    errors = ctx.manifest.validate(value, SCHEMA)
    if errors:
        raise EvictionRefused(
            f"the eviction from {artifact!r} cannot be written down as an event of schema "
            f"{SCHEMA!r}, so the write it belongs to is refused and {artifact!r} is untouched:\n  "
            + "\n  ".join(errors))
    return value


def accept(ctx, *, prior: str, candidate: str, append, write, at: str, artifact: str,
           section: str = None, rev: int = None, runtime: str = None,
           landed: dict = None) -> "dict | None":
    """One accepted write, in the only order that is safe: journal, then replace.

    The ORDER is held here rather than asked of the caller, which is the difference between a
    mechanism and a convention. A writer given two calls would eventually make them in the other
    order under pressure -- which is the condition every measured deletion happened under.

    THE LOCK BOUNDARY SITS OUTSIDE THIS CALL. The caller holds the artifact's lock across it and
    performs its compare-and-swap inside `write`; this passage acquires nothing, releases nothing
    and knows nothing about how exclusivity is obtained. Two reasons, and they are the same reason
    twice: the writer already holds that lock when it validates its candidate, so a second
    acquisition here would either deadlock it or be a second answer to who holds the artifact
    (Cardinal III); and a passage that locked would be a passage that could not be composed into a
    writer that locks differently.

    `append` is a port: any callable that durably extends the record, raising if it cannot.
    `write` is the caller's own replacement of the artifact, called with the candidate text and
    never called at all if the record could not be extended first.
    """
    accepted = event(ctx, prior=prior, candidate=candidate, at=at, artifact=artifact,
                     section=section, rev=rev, runtime=runtime, landed=landed)
    if accepted is not None:
        try:
            append(accepted)
        except Exception as exc:
            raise EvictionRefused(
                f"THE WRITE IS REFUSED AND {artifact!r} IS UNCHANGED: {accepted[CHARS]} character(s) "
                f"were to be removed from it and the record of them could not be extended -- "
                f"{type(exc).__name__}: {exc}. The removed text is therefore still in the artifact "
                f"and still nowhere else, which is the one state this passage exists to keep: a "
                f"removal that cannot be written down is not performed. Repair the journal it "
                f"appends to and write again; nothing here is retried silently."
            ) from exc
    write(candidate)
    return accepted


def landing(kind: str, at: str) -> dict:
    """Where a removed span was curated to, in the two words the event's schema declares it in:
    WHAT the destination is -- a record kind -- and WHERE it is.

    A constructor rather than two field names a caller spells for itself. The words belong to this
    event and the schema is their home; a second passage that wrote them out would be a second
    home for the vocabulary of a landing, and the two would stay internally correct while they
    drifted (Cardinal III). Nothing is validated here: the event this is handed to is validated
    whole, by the schema, before anything is appended anywhere.
    """
    return {"kind": kind, "at": at}


def appender(path):
    """A durable line-appender over one journal file, as a closure the caller hands to `accept`.

    Shipped because the guarantee is DURABILITY and not intent: a line that reached a buffer and
    not a disk is preserved by nothing, and the failure mode that costs the record is precisely
    the one where the process does not come back. So the line is flushed and fsynced before the
    call returns, and any failure on the way -- an unwritable path, a parent that is not a
    directory, a full disk -- is raised where `accept` turns it into a refusal.

    LF is written explicitly. A journal rewritten with the platform's line endings is a diff of
    every line that was ever appended, and the record is the one document whose history must not
    be noise.
    """
    target = Path(path)

    def append(value: dict) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    return append


def count(raw, where: str = None) -> int:
    """The unlanded count an artifact declares, as a number. `None` and an absent field are 0 --
    an artifact that has never evicted anything has honestly lost nothing."""
    if raw is None:
        return 0
    text = str(raw).strip()
    if not text.isdigit():
        raise CounterUnreadable(
            f"{where or 'an artifact'} declares {UNLANDED} as {raw!r}, which is not a count. It is "
            f"refused rather than read as zero: this field is the number of removals that landed "
            f"nowhere, and a zero put here by an interpreter would report a corpus that has lost "
            f"nothing in exactly the case where the count of its losses is unreadable (Cardinal V). "
            f"Write digits, or remove the field and let the artifact say nothing.")
    return int(text)


def restated(raw, accepted: "dict | None", where: str = None) -> str:
    """The artifact's unlanded count after one accepted write, in the form its front matter holds.

    ONE removal is one increment, whatever it removed: the count is of removals that were curated
    nowhere, not of the characters in them -- a count of characters would make a large honest
    editorial cut read as a larger loss than a small deliberate destruction of history. A removal
    that states where it landed increments nothing; it is a MOVE, and a move is what this whole
    passage is for.
    """
    current = count(raw, where)
    return str(current + (1 if accepted is not None and accepted[LANDED] is None else 0))
