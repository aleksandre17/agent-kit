"""Standing -- the violations already IN the tree, by the edit gates in force (ADR-024 decision 20).

An edit gate judges the text a change INTRODUCES, never the whole file: a ratchet, so a gate declared
today holds every new line without refusing the edit that repairs an old one. Its blind side is the
line that was there first -- a violation committed before the gate, or through a path no hook guards,
is never seen again. This module is the other half of the same judgement: every calibrated edit gate
an enabled capability declares (the host's own, and every taken policy's), over the FULL text of every
tracked file its `paths` reach, with the reach the judge itself has -- the gates' own declarations and
the publisher's pinned planes are not read, for the reasons `edits` states.

A finding that is known is ACKNOWLEDGED by declaration, never by silencing the gate: a host lists
{gate, path, tracking, until?} in a document keeping the `known-violations` contract. An
acknowledgement whose `until` has passed acknowledges nothing (its findings stand again); one that
matches no finding is STALE -- a declaration the tree contradicts, named so it is removed.

It never holds a matched value: a finding is a path, a line, a gate and the gate's own `because`, so
a secret the audit finds is located, never repeated.
"""

from __future__ import annotations

import re

import declared
import edits
from errors import KitError

#: The contract an acknowledgement document keeps, and the word its schema gives its rows.
ACKNOWLEDGEMENTS = ({declared.CONTRACT: "known-violations"}, "acknowledgements")
#: The edit-gate contract: the gates in force are every document that keeps it.
GATES = {declared.CONTRACT: "edit-gate"}


class AuditError(KitError):
    """The whole-tree audit cannot be taken honestly: no repository says what is tracked, or one
    (gate, path) is acknowledged twice -- two tracking answers for one violation."""

    code = "KIT0084"


class Finding:
    """One violation standing in the tree. It carries no matched text, by construction."""

    __slots__ = ("path", "line", "gate", "because", "acknowledged")

    def __init__(self, path, line, gate, because, acknowledged=None):
        self.path, self.line, self.gate, self.because = path, line, gate, because
        self.acknowledged = acknowledged

    @property
    def where(self) -> str:
        return f"{self.path}:{self.line}"


class Audit:
    """What the tree holds: open findings (none acknowledged, or acknowledged until a date passed),
    known ones, stale acknowledgements, gates not applied, and how many files were read."""

    def __init__(self):
        self.open, self.known, self.expired, self.stale, self.unjudged = [], [], [], [], []
        self.read = self.not_text = 0

    def counts(self) -> str:
        return (f"{len(self.open)} finding(s), {len(self.known)} known, {len(self.expired)} expired, "
                f"{len(self.stale)} stale acknowledgement(s), over {self.read} tracked file(s)")


def _today(ctx) -> str:
    return ctx.clock.now()[:10]


def _acknowledgements(ctx) -> dict:
    """(gate, path) -> its acknowledgement, from every document under the contract (none is a zero)."""
    names = declared.named(ctx.enabled_capabilities(), ACKNOWLEDGEMENTS[0])
    found: dict = {}
    for name, document in declared.sources(ctx, names).items():
        for row in document[ACKNOWLEDGEMENTS[1]]:
            key = (row["gate"], row["path"])
            if key in found:
                raise AuditError(f"{name} acknowledges {row['gate']} in {row['path']} a second time; "
                                 f"one violation has one tracking answer")
            found[key] = row
    return found


def _lines(text: str, pattern) -> list:
    """The 1-based lines a pattern matches, each once -- positions only, never the matched text."""
    return sorted({text.count("\n", 0, m.start()) + 1 for m in pattern.finditer(text)})


def judge(texts, gates: list, acknowledged: dict, today: str, result: "Audit | None" = None) -> Audit:
    """The audit itself, over (path, full text) pairs and calibrated gates -- no tree, no clock read.
    `acknowledged` maps (gate id, path) -> its acknowledgement row; `today` is `YYYY-MM-DD`."""
    result = result or Audit()
    compiled = [(g, re.compile(g["paths"]), re.compile(g["forbids"], re.MULTILINE)) for g in gates]
    used = set()
    for path, text in texts:
        reaching = [(g, f) for g, paths, f in compiled if paths.search(path)]
        if not reaching:
            continue
        if text is None:
            result.not_text += 1
            continue
        result.read += 1
        for gate, forbids in reaching:
            lines = _lines(text, forbids)
            row = acknowledged.get((gate["id"], path))
            if lines and row is not None:
                used.add((gate["id"], path))
            for line in lines:
                finding = Finding(path, line, gate["id"], gate["because"], row)
                if row is None:
                    result.open.append(finding)
                elif row.get("until") and row["until"] < today:
                    result.expired.append(finding)
                else:
                    result.known.append(finding)
    result.stale = [row for key, row in acknowledged.items() if key not in used]
    return result


def _text(ctx, path):
    """The file's full text, or None where it is not UTF-8 text (no edit gate reads bytes)."""
    try:
        return ctx.workspace.path(path).read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        return None


def audit(ctx) -> Audit:
    """Every calibrated edit gate in force, over every tracked file its `paths` reach -- read once
    per run: `check` asks for the verdict and for the counts, and the tree cannot move between."""
    if getattr(ctx, "_audit", None) is not None:
        return ctx._audit
    tracked = ctx.workspace.tracked()
    if tracked is None:
        raise AuditError("no repository answers at this root, so what the tree tracks cannot be "
                         "read; an audit of a guessed file list would pass on what it never saw")
    names = declared.named(ctx.enabled_capabilities(), GATES)
    gates = declared.rules(ctx, names, edits.RULES)
    result = Audit()
    result.unjudged = [g["id"] for g in gates if edits.calibration(g)]
    calibrated = [g for g in gates if not edits.calibration(g)]
    skipped, published = declared.homes(ctx, names), edits.published_roots(ctx)
    # A submodule's gitlink is another repository's tree, audited there; it is not a file here.
    files = [p for p in tracked if p not in skipped and not any(p.startswith(r) for r in published)
             and ctx.workspace.path(p).is_file()]
    paths = [re.compile(g["paths"]) for g in calibrated]
    texts = ((p, _text(ctx, p)) for p in files if any(r.search(p) for r in paths))
    ctx._audit = judge(texts, calibrated, _acknowledgements(ctx), _today(ctx), result)
    return ctx._audit
