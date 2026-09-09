"""One declared failure family for the whole interpreter.

Cardinal V, made structural: a defect the kit can name must reach the operator as a NAMED state,
not as a stack trace. A traceback is the interpreter telling the host about its own internals
instead of about the host's situation. Every port raises a subclass of `KitError`; the entry point
turns any of them into one line and a non-zero exit. Anything that is NOT a KitError is a bug in
the kit itself and is deliberately allowed to crash loudly -- an unknown failure must never be
dressed up as a handled one.
"""

from __future__ import annotations


class KitError(Exception):
    """A situation the kit understands and can state plainly."""

    exit_code = 1


class PendingApproval(KitError):
    """Not a failure -- a DECLARED STATE. The host was measured, a set was resolved and an answer
    was drafted, and the one human door in the whole design has not been walked through. It gets
    its own exit code because a stalled install is not a broken one, and an operator who cannot
    tell the two apart will either ignore real defects or re-run a refusal forever."""

    exit_code = 3
