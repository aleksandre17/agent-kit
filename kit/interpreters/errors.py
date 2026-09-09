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
