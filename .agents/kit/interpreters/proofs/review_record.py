"""A reference to a REVIEW RECORD kept as evidence: did someone who is not the author approve this work?

ADR-025 decision 7. A review is a judgement of its own kind -- not a stronger test, not a weaker
runtime observation -- and the evidence scale says what its reading is worth (`yielded_by`).
Three readings stay three:

  * approved, by a principal who neither owns the card nor ever moved it -- held;
  * changes requested -- a review that was taken and did not pass, refuted;
  * absent, unreadable, about another card, or by the author -- nothing that proves a review.
"""

from __future__ import annotations

import json

import criteria
import lifecycle as lifecycle_module

SCHEMA = "review-record"


def _authors(card: dict) -> set:
    """Who did the work: the card's owner and every principal who moved it. Separation of duties is
    read from the record, never from a state name -- a reviewer judges, and does not move the card."""
    authors = {card.get("owner")} | {p.get("by") for p in card.get(lifecycle_module.HISTORY, [])}
    return {a for a in authors if a}


def _review_approved(request) -> criteria.Verdict:
    ctx, ref, card = request.ctx, request.ref, request.subject
    if not ctx.workspace.exists(ref):
        return criteria.Verdict.unreadable(f"no review record is at {ref}")
    try:
        record = json.loads(ctx.workspace.read_text(ref))
    except (ValueError, UnicodeDecodeError) as exc:
        return criteria.Verdict.unreadable(f"{ref} is not a readable review record -- {exc}")
    errors = ctx.manifest.validate(record, SCHEMA)
    if errors:
        return criteria.Verdict.unreadable(f"{ref} is not a review record: {'; '.join(errors[:3])}")
    if isinstance(card, dict) and record["card"] != card.get("id"):
        return criteria.Verdict.unreadable(f"{ref} reviews {record['card']!r}, not {card.get('id')!r}")
    if isinstance(card, dict) and record["reviewer"] in _authors(card):
        return criteria.Verdict.unreadable(f"{ref} was written by {record['reviewer']!r}, who authored this "
                                           f"work -- a review by its author proves nothing")
    if record["verdict"] != "approved":
        return criteria.Verdict(False, f"{record['reviewer']} requested changes on {record['reviewed']}")
    return criteria.Verdict(True, f"approved by {record['reviewer']} on {record['reviewed']} at {record['at']}")


RESOLVERS = {"review-approved": _review_approved}
