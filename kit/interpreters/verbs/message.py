"""message -- the hook before a change is recorded with its message: the message must take the declared form.

A version-control adapter's message hook hands this verb the message on stdin. It applies every
calibrated rule an enabled capability declares under the `message-rules` contract -- none, unless the
host opted in by taking a policy (Conventional Commits) or declaring its own -- and refuses a message
that breaks one, naming the rule, why, and what instead. An uncalibrated rule is named unjudged and not
applied; `check` fails it. Blocking: a message this hook cannot judge is not recorded.

Where the host weighs its work (ADR-025), the same moment holds the work-class floor: the staged change
is weighed, and a commit that declares a lighter class, or owes a card it does not name -- or names one
that is not being built, or is shaped lighter than the change -- is refused, naming what it owes.
"""

from __future__ import annotations

import sys

import declared
import hooks
import messages
import vcs
import weighing
import workclass
from errors import KitError

SUMMARY = "before a change is recorded: its message must take the form the host's message rules declare (blocking)"
MUTATES = False
REQUIRES_APPROVED_HOST = True
POSTURE = hooks.BLOCKING
STDOUT_IS_THE_PRODUCTS = True
SOURCES = ({declared.CONTRACT: "message-rules"}, messages.RULES)


class MessageRefused(KitError):
    """A commit message that breaks a calibrated message rule the host declares."""

    code = "KIT0082"


def run(ctx, args) -> int:
    hand = hooks.hand_of(ctx, getattr(args, "surface", None))
    rules = declared.rules(ctx, *SOURCES)
    message = sys.stdin.read()
    floor = _floor(ctx, message)
    for why in floor:
        print(f"message: REFUSED [KIT0086] work class -- {why}", file=sys.stderr)
    if not rules:
        return hand["refusal"]["exit"] if floor else 0
    refusing, unjudged = messages.judge(rules, message)
    for rule_id in unjudged:
        print(f"message: {rule_id} is UNCALIBRATED and was not applied -- `check` names why", file=sys.stderr)
    if not refusing:
        return hand["refusal"]["exit"] if floor else 0
    subject = (messages.cleaned(message).splitlines() or [""])[0]
    for rule in refusing:
        print(f"message: REFUSED [{MessageRefused.code}] {rule['id']} -- {subject!r}: {rule['because']} "
              f"Instead: {rule['instead']}", file=sys.stderr)
    return hand["refusal"]["exit"]


def _floor(ctx, message: str) -> list:
    """Why the staged change may not be recorded under this message by its work class -- empty on a
    host that does not weigh, and on every change whose class owes nothing beyond its commit."""
    found = workclass.declarations(ctx)
    if found is None:
        return []
    classes_doc, areas_doc = found
    staged = workclass.paths(vcs.staged_paths(ctx.workspace.root), "what the commit records")
    stood = workclass.accepted_areas(ctx, None)
    _sig, verdict = weighing.weigh(staged, classes_doc, stood or areas_doc,
                                   weighing.loosened(classes_doc, stood, areas_doc))
    before, after = workclass.reshaped_cards(ctx, staged)
    return (weighing.commit_refusals(classes_doc, verdict, message, workclass.cards(ctx))
            + weighing.demotions(classes_doc, before, after))
