"""Version ranges -- the grammar a `requires` entry may state, and nothing else.

A pure module over strings: no filesystem, no clock, no capability. It privileges no id and no
version; it only answers whether a declared version falls inside a declared range.

THE DIALECT, NAMED. This is a SUBSET of npm's node-semver range grammar
(https://github.com/npm/node-semver#ranges), adopted whole for the part it covers:

    range          ::= comparator-set ( "||" comparator-set )*      -- OR of sets
    comparator-set ::= comparator ( whitespace comparator )*          -- AND inside a set
    comparator     ::= operator? MAJOR "." MINOR "." PATCH

and every operator desugars EXACTLY as node-semver documents it, including the 0.x rule for the
caret, which is the one most dialects get wrong and the one that matters here -- every capability
this kit ships is 0.x:

    1.2.3 / =1.2.3   :=  =1.2.3
    >1.2.3 >=1.2.3 <1.2.3 <=1.2.3  -- primitive comparisons
    ^1.2.3  :=  >=1.2.3 <2.0.0      ^0.2.3  :=  >=0.2.3 <0.3.0      ^0.0.3  :=  >=0.0.3 <0.0.4
    ~1.2.3  :=  >=1.2.3 <1.3.0

DECLARED MISSING -- the part of node-semver this subset does not build, refused by name rather
than silently misread: partial versions (`1.2`, `1`), X-ranges (`1.x`, `*`), hyphen ranges
(`1.2.3 - 2.3.4`), whitespace between an operator and its version (`>= 1.2.3`), and pre-release
or build tags (`1.2.3-beta`, `1.2.3+sha`). The last is not only unbuilt but unneeded: the
capability schema forbids a version carrying one, so there is nothing for such a range to match.
The schema's `pattern` holds the SHAPE above, so a partial version never reaches this module; an
operator outside the table below reaches it and is refused here, naming the operators that exist.

REJECTED, with reasons:
  * Cargo (caret-by-default): a bare `1.2.3` means `^1.2.3` in Cargo and `=1.2.3` in npm. The
    same string meaning two things across the field is exactly the ambiguity a declaration must
    not carry; npm's reading is the literal one, so a bare version here means that version.
  * PEP 440 `packaging.specifiers` (`~=`, `===`, `,` as AND): a third-party package, which this
    kit may not depend on, and a grammar built around pre/post/dev/local releases that a
    MAJOR.MINOR.PATCH-only schema has no use for.
  * Composer: node-semver plus `,` and `-stability` flags -- a superset of what is wanted, with
    no operator the subset above needs that it lacks.
  * Go minimal version selection: not a range grammar at all but a SELECTION algorithm over
    minimum requirements. Here nothing is selected -- the enabled set is the host's choice, and
    the resolver only judges it (resolver.py). MVS answers a question this kit refuses to ask.

NO RANGE MEANS ANY VERSION. A `requires` entry without `version` is satisfied by every version
of every provider, which is how every requirement declared before ranges existed keeps resolving
exactly as it did. That rule lives in the resolver, beside the requirement it reads.

OPEN BY DECLARATION. `OPERATORS` is a registry: a new operator is one row mapping its symbol to
the primitive bounds it desugars to. Nothing else changes -- no parser branch, no schema edit.
"""

from __future__ import annotations

import operator
import re

_VERSION = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
_COMPARATOR = re.compile(r"^(?P<op>[^0-9]*)(?P<version>[0-9].*)$")

#: The only comparisons anything desugars to. A sugar operator never compares by itself.
PRIMITIVES = {
    "=": operator.eq, ">": operator.gt, ">=": operator.ge, "<": operator.lt, "<=": operator.le,
}


def _caret(v):
    """Bump the left-most NON-ZERO part -- node-semver's rule, 0.x included."""
    major, minor, patch = v
    upper = (major + 1, 0, 0) if major else (0, minor + 1, 0) if minor else (0, 0, patch + 1)
    return [(">=", v), ("<", upper)]


def _tilde(v):
    major, minor, _ = v
    return [(">=", v), ("<", (major, minor + 1, 0))]


#: operator symbol -> version -> [(primitive, bound)]. The bare version (empty symbol) is `=`.
OPERATORS = {
    "": lambda v: [("=", v)],
    **{symbol: (lambda s: lambda v: [(s, v)])(symbol) for symbol in PRIMITIVES},
    "^": _caret,
    "~": _tilde,
}


class RangeError(ValueError):
    """A range this grammar cannot read. Never guessed at: a range read loosely is a requirement
    that goes on reading as satisfied while it constrains nothing."""


def parse_version(text: str) -> tuple:
    match = _VERSION.match(text)
    if not match:
        raise RangeError(
            f"{text!r} is not a full MAJOR.MINOR.PATCH version; partial versions, X-ranges and "
            f"pre-release tags are not in the implemented subset of node-semver"
        )
    return tuple(int(part) for part in match.groups())


def _comparator(token: str) -> list:
    match = _COMPARATOR.match(token)
    if not match:
        raise RangeError(f"comparator {token!r} names no version")
    symbol = match.group("op")
    if symbol not in OPERATORS:
        raise RangeError(
            f"operator {symbol!r} in {token!r} is not in the implemented subset of node-semver; "
            f"the operators that exist are {sorted(s for s in OPERATORS if s)} and a bare version"
        )
    return OPERATORS[symbol](parse_version(match.group("version")))


def parse(text: str) -> list:
    """A range -> [comparator-set], each set a list of (primitive, bound). Refuses, never guesses."""
    sets = []
    for alternative in text.split("||"):
        tokens = alternative.split()
        if not tokens:
            raise RangeError(f"range {text!r} has an empty alternative")
        sets.append([bound for token in tokens for bound in _comparator(token)])
    return sets


def satisfies(version: str, text: str) -> bool:
    """True when `version` meets EVERY comparator of AT LEAST ONE set of the range."""
    v = parse_version(version)
    return any(all(PRIMITIVES[p](v, bound) for p, bound in group) for group in parse(text))
