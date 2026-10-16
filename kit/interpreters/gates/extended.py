"""Gate kind for extension points: every pending answer named, a required one held red (ADR-024).

A pending marker is an answer only the host can give, left where the template put it: printed by path,
never read as a silent empty. A point whose `required_by` is set fails until every member is answered.
A file at a point's place that no member name accounts for is REPORTED: an extension reaches the kit
only through a point.
"""

from __future__ import annotations

import re

import extensions

KIND = "extensions-held"


def _held(ctx, params) -> list:
    failures = []
    rows = extensions.registry(ctx)
    for row in rows:
        for _name, rel in extensions.members(ctx, row):
            for answer in extensions.pending(ctx.workspace.read_text(rel)):
                print(f"        PENDING  {rel}: {answer}")
                if row.get("required_by"):
                    failures.append(f"{rel}: the point {row['id']!r} is required ({row['required_by']}) and still "
                                    f"pending: {answer}")
    # A place several points share is accounted for by ALL their member shapes together.
    places = {}
    for row in rows:
        if row["cardinality"] == "many":
            shape = re.compile("^" + re.escape(row["host_path"]).replace(re.escape("{name}"), "[a-z0-9][a-z0-9-]*") + "$")
            places.setdefault(row["root"], []).append((row["id"], shape))
            if "{name}/" in row["host_path"]:
                # A member that is a DIRECTORY (a skill with its scripts) holds everything under it.
                head = row["host_path"].split("{name}/", 1)[0]
                places[row["root"]].append((row["id"], re.compile("^" + re.escape(head) + "[a-z0-9][a-z0-9-]*/")))
    for root, shapes in places.items():
        for rel in ctx.workspace.files_under(root.rstrip("/")):
            if rel.rsplit("/", 1)[-1].startswith(".") or any(shape.match(rel) for _i, shape in shapes):
                continue
            print(f"        REPORTED  {rel}: lies at the point(s) {[i for i, _s in shapes]} and no member name "
                  f"accounts for it -- an extension reaches the kit through a point")
    return failures


KINDS = {KIND: _held}
