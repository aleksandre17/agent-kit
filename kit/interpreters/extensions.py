"""Extension points -- where a host EXTENDS the kit, declared once, scaffolded on demand (ADR-024).

The kit is a rich base, and a host writes only its own specifics -- at a declared EXTENSION POINT. A
point is declared on the install that opens its place (`points` on a seed or a space): what it is for,
its cardinality (one file, or one member per name), the template a member is written from, whether the
host's profile requires it answered, and what it merges into. The registry is DERIVED from those
declarations, so it has one home, and it is printed in the shape both kits share
(`extension-points`, schemas/extension-points.schema.json).

Three properties of the grammar:

  * ON DEMAND -- nothing is scaffolded until the host asks (`extend`): an empty file rots, costs tokens
    and reads as complete;
  * PENDING IS VISIBLE -- a template carries PENDING markers for the answers only the host can give,
    and `check` names each one; a point the host's profile requires stays red until answered;
  * TEMPLATES MERGE -- a member written from a template is recorded in the host's ledger with the
    template it came from, so a newer template is merged three ways (base, new, host) and a conflict is
    reported with the host's file left as it is. The kit's copy is never edited.
"""

from __future__ import annotations

import hashlib
import re

from errors import KitError

#: The marker a template carries where only the host can answer -- the one grammar this kit PROVIDES
#: for "not yet answered", in Markdown (`<!-- pending: ... -->`) and in a JSON string (`"<pending: ...>"`).
PENDING = re.compile(r"<!--\s*pending:(.*?)-->|<pending:([^>]*)>")
LEDGER_CONTRACT = "extension-ledger"
NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")
#: The status of a point, each with the reading that decides it, in order -- the vocabulary this kit
#: PROVIDES for `extend --list`: no member yet; a member still carrying a pending answer; all answered.
STATUSES = {
    "unused": lambda found, open_answers: not found,
    "drafted": lambda found, open_answers: bool(open_answers),
    "answered": lambda found, open_answers: True,
}


class ExtensionError(KitError):
    """A point nobody declares, a name that is not one, or a member that already exists."""

    code = "KIT0080"


def registry(ctx) -> list:
    """Every point an enabled capability declares, in the shared shape."""
    found = []
    for capability in ctx.enabled_capabilities():
        for item in capability.installs:
            for point in item.get("points", []):
                many = point["cardinality"] == "many"
                found.append({"id": point["id"], "purpose": point["purpose"],
                              "host_path": item["target"] + point["named"] if many else item["target"],
                              "template": point.get("template") or item.get("source"),
                              "schema": point.get("schema") or item.get("validates"),
                              "cardinality": point["cardinality"], "required_by": point.get("required_by"),
                              "merges_into": point["merges_into"], "capability": capability.id,
                              "root": item["target"]})
    return sorted(found, key=lambda p: p["id"])


def point(ctx, identity: str) -> dict:
    found = next((p for p in registry(ctx) if p["id"] == identity), None)
    if found is None:
        raise ExtensionError(f"no extension point {identity!r}; the points are {[p['id'] for p in registry(ctx)]}")
    return found


def members(ctx, row: dict) -> list:
    """(name, host path) of every file at a point."""
    if row["cardinality"] == "one":
        return [(None, row["host_path"])] if ctx.workspace.exists(row["host_path"]) else []
    pattern = re.compile("^" + re.escape(row["host_path"]).replace(re.escape("{name}"), "([a-z0-9][a-z0-9-]*)") + "$")
    return [(m.group(1), rel) for rel in ctx.workspace.files_under(row["root"].rstrip("/"))
            if (m := pattern.match(rel))]


def pending(text: str) -> list:
    return [(a or b).strip() for a, b in PENDING.findall(text)]


def status(ctx, row: dict) -> str:
    found = members(ctx, row)
    open_answers = [a for _n, rel in found for a in pending(ctx.workspace.read_text(rel))]
    return next(word for word, reads in STATUSES.items() if reads(found, open_answers))


def path_of(row: dict, name) -> str:
    if row["cardinality"] == "many":
        if not name or not NAME.match(name):
            raise ExtensionError(f"the point {row['id']!r} holds one member per name, and {name!r} is not a name")
        return row["host_path"].replace("{name}", name)
    return row["host_path"]


def template_text(ctx, row: dict, name) -> str:
    return ctx.manifest.payload_text(row["template"]).replace("{name}", name or "")


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
