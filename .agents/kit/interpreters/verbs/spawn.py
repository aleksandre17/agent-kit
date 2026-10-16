"""spawn -- the hook before a runtime starts a sub-agent: the brief is a PACKET, or it is not sent.

A sub-agent starts with nothing but its brief, and pays for every token of it on every call. So the
brief carries the declared packet fields (`spawn-packets`, a published policy: what to do, the ground it
stands on, its boundaries, what it returns, its budget) and stays under the declared ceiling. A
compliant brief is SILENT -- zero context tax; one over the ceiling is refused; one missing a field is
refused with one compact line naming exactly what to add. A full-history fork, where the product has
one, must say why it needs the history. Blocking: a spawn this hook cannot judge is not sent.
"""

from __future__ import annotations

import json
import math
import sys

import declared
import hooks

SUMMARY = "before a runtime starts a sub-agent: the brief must be a packet under its ceiling (blocking)"
MUTATES = False
REQUIRES_APPROVED_HOST = True
POSTURE = hooks.BLOCKING
STDOUT_IS_THE_PRODUCTS = True
PACKETS = ({declared.CONTRACT: "spawn-packets"}, "packets")


def run(ctx, args) -> int:
    hand = hooks.hand_of(ctx, getattr(args, "surface", None))
    rules = declared.rules(ctx, *PACKETS)
    if not rules:
        return 0
    try:
        event = json.loads(sys.stdin.read() or "null")
    except ValueError:
        event = None
    brief = hooks.first_of(event, hand.get("prompts", [])) if event is not None else None
    if brief is None:
        return 0
    refusal = hand["refusal"]["exit"]
    for rule in rules:
        tokens = math.ceil(len(brief.encode("utf-8")) / rule["bytes_per_token"])
        if tokens > rule["ceiling_tokens"]:
            print(f"spawn: REFUSED -- the brief is ~{tokens} tokens, over the ceiling of {rule['ceiling_tokens']}: "
                  f"point at the documents instead of pasting them.", file=sys.stderr)
            return refusal
        missing = [f["label"] for f in rule["fields"] if f["label"].lower() not in brief.lower()]
        fork = rule.get("fork")
        if fork and any(v == fork["equals"] for k in fork["keys"] for v in hooks.values_at(event, k)) \
                and fork["label"].lower() not in brief.lower():
            missing.append(fork["label"])
        if missing:
            print(f"spawn: REFUSED -- the brief lacks {', '.join(missing)}; add one line for each and send it "
                  f"again.", file=sys.stderr)
            return refusal
    return 0
