"""init -- measure the host, draft its bindings, seed once, vendor, render, check.

Everything this verb writes was declared by a capability, and it writes through a workspace scoped
to exactly that capability's declared targets: the interpreter cannot write somewhere no
declaration named, even by mistake. Re-running is not a re-generation -- BINDING is created only
if absent -- so a second `init` is, by construction, `render` + `check`.

Install modes are an OPEN registry keyed by the mode a declaration states. A new kind of install
is a new registration; no verb branches on the identity of any particular capability, path or
stack, and none may.
"""

from __future__ import annotations

import check as check_verb
import render as render_verb
from errors import KitError
from context import SCHEMA_VERSION

SUMMARY = "measure, draft bindings, seed, vendor, render, check"


def _mode_reading(ctx, ws, item, state):
    """The measured environment. Written once; a later reading is compared, never imposed."""
    if ws.exists(item["target"]):
        return "kept"
    ws.write_json(item["target"], state["reading"])
    return "created"


def _mode_declaration(ctx, ws, item, state):
    """What this host has decided. Host truth: an upgrade never writes here again."""
    if ws.exists(item["target"]):
        return "kept"
    ws.write_json(item["target"], {
        "schema_version": SCHEMA_VERSION,
        "status": "draft",
        "kit_version": ctx.manifest.version,
        "capabilities": sorted(c.id for c in state["enabled"]),
        "unavailable": state["unavailable"],
        "drafted_at": state["reading"]["taken_at"],
    })
    return "created"


def _mode_seed(ctx, ws, item, state):
    """Created once if absent, never re-applied, never diffed. The host owns it from then on."""
    if ws.exists(item["target"]):
        return "kept"
    ws.write_text(item["target"], ctx.manifest.payload_text(item["source"]))
    return "created"


def _mode_vendor(ctx, ws, item, state):
    """Framework payload. Replaced wholesale; never edited downstream."""
    ws.write_text(item["target"], ctx.manifest.payload_text(item["source"]))
    return "vendored"


INSTALL_MODES = {
    "reading": ("install", _mode_reading),
    "declaration": ("install", _mode_declaration),
    "seed": ("install", _mode_seed),
    "vendor": ("install", _mode_vendor),
    "projection": ("render", None),
}


class InstallError(KitError):
    """A declaration named an install mode this interpreter does not know, or wrote an invalid file."""


def run(ctx, args) -> int:
    reading = ctx.take_reading()
    enabled, unavailable = ctx.resolve(reading["facts"])
    state = {"reading": reading, "enabled": enabled, "unavailable": unavailable}

    print(f"reading taken at {reading['taken_at']} on {reading['boundary']['os']}")
    for fact, value in reading["facts"].items():
        print(f"  fact  {fact} = {value}")
    for entry in unavailable:
        print(f"  unavailable  {entry['id']}: {entry['reason']}")

    for capability in enabled:
        scoped = ctx.workspace.scoped(capability.targets())
        for item in capability.installs:
            mode = item["mode"]
            if mode not in INSTALL_MODES:
                raise InstallError(
                    f"capability {capability.id!r} declares install mode {mode!r}; "
                    f"registered modes are {sorted(INSTALL_MODES)}"
                )
            phase, apply = INSTALL_MODES[mode]
            if phase != "install":
                continue
            outcome = apply(ctx, scoped, item, state)
            print(f"  {outcome:<9}  {item['target']}")
            _validate(ctx, scoped, item)

    render_verb.run(ctx, args)
    return check_verb.run(ctx, args)


def _validate(ctx, ws, item) -> None:
    schema = item.get("validates")
    if not schema:
        return
    errors = ctx.manifest.validate(ws.read_json(item["target"]), schema)
    if errors:
        raise InstallError(
            f"{item['target']} does not honour schema {schema!r}:\n  " + "\n  ".join(errors)
        )
