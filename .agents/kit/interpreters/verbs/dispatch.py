"""dispatch -- hand one task to the port that starts workers, and let the port answer.

This verb is a MOUTH, not a gate. It reads the packet a caller put on stdin and hands it over; the
refusing, the leasing, the isolating, the starting and the recording are the port's, so that a task
handed over by a runtime hook, by another verb, by a shell or by a second intelligence meets
exactly the same judgement (ADR-017 decision 1). A verb that checked anything itself would be a
second home for the gate, and the runtime whose hook called the port directly would bypass it.

    ... cli.py dispatch --root <host>  < packet.json
    ... cli.py dispatch --root <host> --plan  < packet.json   # read, report, write nothing
    ... cli.py dispatch --root <host>  < answer.json          # resume a worker that asked

The second act is the same mouth, deliberately. WHICH act a document is, the DOCUMENT says -- a
packet states a route and an instruction, an answer names the task it resumes -- and that reading
is the port's like every other. A flag here would make the distinction a property of the caller,
and a hook that called the port directly would be handing over an act nobody had classified.

    {"resume": "<DISPATCH-ID>", "answer": "...", "by": "<who answered>"}   (+ the schema
    version the task schema declares -- stated THERE, never restated in this module)

What it mutates is its OWN subject -- the leased workspace of one task and that task's record --
never the host tree `--root` names, so it takes the host's hold from nobody (ADR-007). The hold it
does take is on the path it is about to write in, and it is the same hold mechanism.
"""

from __future__ import annotations

import sys

import dispatch_port

SUMMARY = ("hand one act to the dispatch port: start a worker for a task, or carry an operator's "
           "answer back into one that asked")
MUTATES = True
#: What this verb writes is one leased workspace and one task record, never the host as a whole.
SUBJECT = "dispatch"
REQUIRES_APPROVED_HOST = True


def run(ctx, args) -> int:
    return dispatch_port.dispatch(ctx, args, sys.stdin.read())
