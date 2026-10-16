"""The `declared` resolver -- the rows every enabled source keeping one contract declares, as plain data
a served view lays out.

Some served files are nothing but a host's declared rows in a product's grammar: the review owners in
an owners file, for one. A resolver per contract would be one module per list that says nothing the
contract does not; so the view declares the contract and the field its schema gives the rows
(`{"validates": "<contract>", "list": "<field>"}`), and the rows come back in declared order, each id
claimed once (`declared.rules`). A contract nobody declares is a declared zero: an empty list.
"""

from __future__ import annotations

import declared


def _rows(ctx, params) -> list:
    return declared.rules(ctx, {declared.CONTRACT: params["validates"]}, params["list"])


RESOLVES = {"declared": _rows}
