"""message -- the hook before a change is recorded with its message: the message must take the declared form.

A version-control adapter's message hook hands this verb the message on stdin. It applies every
calibrated rule an enabled capability declares under the `message-rules` contract -- none, unless the
host opted in by taking a policy (Conventional Commits) or declaring its own -- and refuses a message
that breaks one, naming the rule, why, and what instead. An uncalibrated rule is named unjudged and not
applied; `check` fails it. Blocking: a message this hook cannot judge is not recorded.
"""

from __future__ import annotations

import sys

import declared
import hooks
import messages
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
    if not rules:
        return 0
    refusing, unjudged = messages.judge(rules, message)
    for rule_id in unjudged:
        print(f"message: {rule_id} is UNCALIBRATED and was not applied -- `check` names why", file=sys.stderr)
    if not refusing:
        return 0
    subject = (messages.cleaned(message).splitlines() or [""])[0]
    for rule in refusing:
        print(f"message: REFUSED [{MessageRefused.code}] {rule['id']} -- {subject!r}: {rule['because']} "
              f"Instead: {rule['instead']}", file=sys.stderr)
    return hand["refusal"]["exit"]
