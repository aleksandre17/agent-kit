"""A declared match over a flat reading -- the one place a declaration may say WHICH ones.

A declaration states what is true; it may not compute. So the only question this answers is the
only one a declaration can ask without becoming behaviour: *do these named fields hold exactly
these values?* Equality, and nothing else. No operators, no comparisons, no ordering, no absence
of a field standing in for a wildcard -- because the instant a declaration can express `greater
than` it can express a policy, and a policy inside a declaration is a thing no machine may
generate and no host may safely edit.

Two consequences are deliberate and worth stating, since both look like limitations until the
alternative is written out:

  * **A field the reading does not carry reads as nothing.** That is how a declaration names an
    ABSENCE, which is very often the state that matters: the record of something that never
    happened is a record with a hole in it, not a record with a value in it.
  * **There is no `or`.** A rule that must match two shapes is declared TWICE, as two rows with
    one shape each. Two rows say plainly what a boolean expression would bury, and each row keeps
    its own reason and its own calibration -- which an expression could never carry.

It is used wherever one declaration has to select among many readings, and it lives here rather
than inside any one of them: a matching rule with two homes is two rules that agree until they
do not.
"""

from __future__ import annotations

#: What a reading says about a field it does not carry. One home for that answer.
ABSENT = None


def matches(spec: dict, reading) -> bool:
    """True when every field the spec names holds exactly the value it names."""
    if not isinstance(reading, dict):
        return False
    return all(reading.get(field, ABSENT) == expected for field, expected in spec.items())
