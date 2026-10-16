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


def _numbered(ctx, params) -> list:
    """The rows of one named readable that carry the numbering field, in that number's order, each
    with exactly the fields the view lays out -- an optional one absent from a row is carried as
    None, so a logic-less template asks whether it is present instead of naming what no row holds."""
    found = []
    for value in declared.sources(ctx, [params["reads"]]).values():
        found += [row for row in (value if isinstance(value, list) else []) if params["field"] in row]
    fields = [params["field"], *params["carries"]]
    return [{name: row.get(name) for name in fields} for row in sorted(found, key=lambda r: r[params["field"]])]


RESOLVES["numbered"] = _numbered
