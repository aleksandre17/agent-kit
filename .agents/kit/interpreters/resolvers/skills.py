"""The `skills` resolver -- every skill this host serves, read from every document keeping the `skills`
contract: a published bundle's, a policy's, the host's own (ADR-024).

A skill is the Agent Skills unit (agentskills.io): a name, a description that is loaded on every turn,
a body loaded only when the skill is activated, and supporting files read or run only when the body
says so. Its declaration holds the name and the description ONCE; the body file holds prose only, so
the front matter every product parses is a projection of the declaration and never a second copy.

Every path a document names is relative to the DOCUMENT -- a published one is read from the kit's
namespace (its pin), the host's from its own tree -- and may not leave it. A name declared twice is
refused: one skill, one meaning (Cardinal III).
"""

from __future__ import annotations

import posixpath

import collection
import declared
from errors import KitError

CONTRACT, LIST = "skills", "skills"
#: The directory of a skill whose files are run, not read (agentskills.io, optional directories).
SCRIPTS = "scripts/"


class SkillError(KitError):
    """A skill names a file outside its own document's directory, a supporting file outside its own
    skill, or a name another skill already holds."""

    code = "KIT0074"


def _within(base: str, rel: str, where: str) -> str:
    joined = posixpath.normpath(posixpath.join(base, rel))
    if rel.startswith("/") or ":" in rel or "\\" in rel or joined == ".." or joined.startswith("../") \
            or (base and not (joined + "/").startswith(base.rstrip("/") + "/")):
        raise SkillError(f"{where}: {rel!r} leaves the directory of the document that declares it")
    return joined


def origins(ctx, contract: str) -> list:
    """(source name, document, base directory, reader) for every source keeping `contract`: a shipped
    document is read through the manifest (the publisher's pinned bytes), an authored one from the
    host. Shared with every resolver whose documents name files beside themselves."""
    capabilities = ctx.enabled_capabilities()
    names = set(declared.named(capabilities, {declared.CONTRACT: contract}))
    found = []
    for capability in capabilities:
        for row in capability.raw.get("documents", []):
            if row["id"] in names:
                found.append((row["id"], capability.documents[row["id"]], posixpath.dirname(row["source"]),
                              ctx.manifest.payload_text))
        for item in capability.installs:
            if item.get("reads_as") in names and ctx.workspace.exists(item["target"]):
                found.append((item["reads_as"], collection.read(ctx, item).value,
                              posixpath.dirname(item["target"]), ctx.workspace.read_text))
    return sorted(found, key=lambda row: row[0])


def _skills(ctx, params) -> list:
    members, owners = [], {}
    for name, document, base, read in origins(ctx, params.get("contract", CONTRACT)):
        for skill in document.get(LIST, []):
            where = f"{name}: skill {skill['id']!r}"
            if skill["id"] in owners:
                raise SkillError(f"{where} is already declared by {owners[skill['id']]!r}; one name, one skill")
            owners[skill["id"]] = name
            body = _within(base, skill["body"], where)
            home = posixpath.dirname(body)
            files = []
            for rel in skill.get("files", []):
                path = _within(base, rel, where)
                if not path.startswith(home + "/"):
                    raise SkillError(f"{where}: its file {rel!r} lies outside the skill's own directory "
                                     f"{home!r}; a skill travels as one directory")
                served = path[len(home) + 1:]
                # The Agent Skills convention: `scripts/` is EXECUTED, never loaded into context; every
                # other supporting file is read when the body points at it.
                files.append({"path": served, "text": read(path),
                              "layer": "" if served.startswith(SCRIPTS) else "on-demand"})
            members.append({"id": skill["id"], "description": skill["description"],
                            "body": read(body).rstrip("\n") + "\n",
                            "allowed_tools": " ".join(skill.get("allowed_tools", [])),
                            "task_class": skill.get("task_class", ""),
                            "files": files, "declared_by": name})
    return sorted(members, key=lambda m: m["id"])


RESOLVES = {CONTRACT: _skills}
