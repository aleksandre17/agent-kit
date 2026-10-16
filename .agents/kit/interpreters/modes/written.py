"""Install modes that WRITE one document: the reading, the host's answer, a seed, vendored payload.

Each is a `Mode` -- the phase it runs in, its foresight and its apply (`installmodes`).
"""

from __future__ import annotations

from installmodes import Mode


def _once(ws, item, state):
    """Created if absent, never re-applied. The host owns it from then on."""
    return "keep" if ws.exists(item["target"]) else "create"


def _always(ws, item, state):
    """Framework payload: replaced wholesale, never edited downstream."""
    return "replace" if ws.exists(item["target"]) else "create"


def _answer(ws, item, state):
    """The answers file is create-once like any host truth -- except for the approval, which is
    the owner's own act passing through the kit, and is therefore a PLANNED replace rather than
    an edit nobody saw coming."""
    if not ws.exists(item["target"]):
        return "create"
    return "replace" if state["approving_draft"] else "keep"


def _reading(ctx, ws, item, state):
    """The measured environment. Written once; a later reading is compared, never imposed."""
    ws.write_json(item["target"], state["reading"])


def _declaration(ctx, ws, item, state):
    """What this host has decided: its set, its status, and who accepted it. A prior answer is
    carried forward field by field -- approving a draft must not silently re-answer it."""
    prior = state["existing"] or {}
    answer = {
        "schema_version": ctx.manifest.version_of(item["validates"]),
        "status": "accepted" if state["approver"] else "draft",
        "kit_version": ctx.manifest.version,
        "capabilities": prior.get("capabilities") or sorted(c.id for c in state["enabled"]),
        "unavailable": prior.get("unavailable", state["unavailable"]),
        "drafted_at": prior.get("drafted_at", state["reading"]["taken_at"]),
    }
    if state["approver"]:
        answer["signed_by"] = state["approver"]
        answer["signed_at"] = state["reading"]["taken_at"]
    ws.write_json(item["target"], answer)


def _payload(ctx, ws, item, state):
    """The declared source's bytes at the target -- created once (a seed) or replaced (vendor):
    which one is the foresight's decision, never this function's."""
    ws.write_text(item["target"], ctx.manifest.payload_text(item["source"]))


#: The `answer` phase is the ONLY thing an unapproved host may write: it is the draft the owner is
#: being asked to accept, and nothing moves until they do. The take declaration is seeded once as
#: a declared zero; the `take` verb writes it after (ADR-018).
MODES = {
    "reading": Mode("install", _once, _reading),
    "declaration": Mode("answer", _answer, _declaration),
    "seed": Mode("install", _once, _payload),
    "vendor": Mode("install", _always, _payload),
    "taken-declaration": Mode("install", _once, _payload),
}
