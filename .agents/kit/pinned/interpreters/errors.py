"""One declared failure family for the whole interpreter.

Cardinal V, made structural: a defect the kit can name must reach the operator as a NAMED state,
not as a stack trace. A traceback is the interpreter telling the host about its own internals
instead of about the host's situation. Every port raises a subclass of `KitError`; the entry point
turns any of them into one line and a non-zero exit. Anything that is NOT a KitError is a bug in
the kit itself and is deliberately allowed to crash loudly -- an unknown failure must never be
dressed up as a handled one.

Every refusal also carries a stable CODE (ADR-005). The code is NAMED here, on the class that
raises it, and MEANT in exactly one place: `kit/diagnostics.json`, the append-only registry. The
prose is for the operator and may be rewritten; the code is for machines and never changes.
"""

from __future__ import annotations


class KitError(Exception):
    """A situation the kit understands and can state plainly."""

    exit_code = 1
    #: None on the root ONLY: a bare KitError is a refusal with no declared family, and it is
    #: rendered as honestly uncoded rather than handed a code that would mean "anything".
    code = None

    def __init_subclass__(cls, **kwargs):
        # Declared on the class ITSELF, never inherited: a subclass that inherited its parent's
        # code would be a second situation silently answering to the first one's code.
        super().__init_subclass__(**kwargs)
        if not isinstance(cls.__dict__.get("code"), str) or not cls.__dict__["code"]:
            raise TypeError(
                f"{cls.__module__}.{cls.__qualname__} is a refusal with no code of its own; "
                f"issue one in kit/diagnostics.json and name it on the class (ADR-005)"
            )


class PendingApproval(KitError):
    """Not a failure -- a DECLARED STATE. The host was measured, a set was resolved and an answer
    was drafted, and the one human door in the whole design has not been walked through. It gets
    its own exit code because a stalled install is not a broken one, and an operator who cannot
    tell the two apart will either ignore real defects or re-run a refusal forever."""

    exit_code = 3
    code = "KIT0007"
