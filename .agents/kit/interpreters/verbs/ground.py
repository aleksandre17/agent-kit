"""ground -- record a measured fact with the instrument that produced it, or read one back (ADR-022).

    python .agents/kit/interpreters/cli.py ground --root . --key K --fact "..." --instrument "<cmd>" --path a,b
    python .agents/kit/interpreters/cli.py ground --root . --key K

Recording needs all four: a key, the fact, the instrument and the narrowest paths the fact depends on.
Reading returns the fact only while those paths still hold the content they held when it was
measured; otherwise it is a DECLARED MISS (exit 4) that names what moved and hands back the
instrument. Like a run's receipt, a reading is observed state: it writes only the observed plane, so
this verb holds nothing and has nothing to plan.
"""

from __future__ import annotations

import readings

SUMMARY = "record a measured fact with its instrument and paths, or read one back while it still holds"
MUTATES = False
REQUIRES_APPROVED_HOST = True

#: What this verb may be asked for, beyond the arguments every verb shares -- declared here, beside
#: the verb, and merged by the entry point (a new verb's words never need an edit there).
ARGUMENTS = [
    ("--key", {"default": None, "help": "the name a measured fact is recorded and read under"}),
    ("--fact", {"default": None, "help": "the fact, as measured -- recording when given, reading when not"}),
    ("--instrument", {"default": None, "help": "the command or file the fact was measured with"}),
]


def run(ctx, args) -> int:
    if getattr(args, "fact", None) is None:
        row = readings.get(ctx, args.key)
        print(f"ground: HIT  {row['key']}  (measured {row['at']} with: {row['instrument']})")
        print(row["fact"])
        return 0
    row = readings.record(ctx, args.key, args.fact, args.instrument, args.path or [],
                          at=ctx.clock.now(), by=getattr(args, "by", None))
    print(f"ground: RECORDED  {row['key']}  over {row['paths']}  (with: {row['instrument']})")
    return 0
