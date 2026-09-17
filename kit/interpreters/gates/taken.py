"""Gate kind for what a host TOOK from outside the kit -- held, on every check, to its pin.

The door that pins a capability is walked once; this is the reading taken every time after it. It
re-measures every capability the kit's lock does not account for and fails on anything that is not
held to a pin: bytes that drifted, a version older than the one pinned, a capability this host has
never pinned. It does NOT re-run a verifier: authenticity is a reading taken at the door and dated
there, and integrity is what carries it forward -- a check that re-verified would make every check
depend on a tool and a trust root that the pin exists to make unnecessary.

It reports and never repairs, and it never re-pins: a gate that could take a fresh digest would
certify whatever it found. The measuring and the vocabulary are `provenance`'s; this only asks.
"""

from __future__ import annotations

import estate as estate_module
import pin
import provenance


def _pinned(ctx, params) -> list:
    recorded = estate_module.read(ctx)
    rows = provenance.survey(ctx, ctx.enabled_capabilities(), (recorded or {}).get("taken", []))
    provenance.report(ctx, rows)
    return [f"{row['state']}  {row['capability']}@{row['version']}  {row['digest']} -- "
            f"{provenance._says(ctx, 'states', row['state'], 'state')}"
            for row in rows if row["disposition"] not in (provenance.HOLD, provenance.CARRY)]


def _taken_intact(ctx, params) -> list:
    """Each take in its plane, judged against the digest its row declares (ADR-018 decision 5).

    The pinned kit is judged elsewhere, against its lock, and never here: two homes, two gates. This
    gate states the composition first -- `release <v> + taken: <ids>` -- and then fails on a take
    whose bytes are not the ones its row pinned, a row whose plane is gone, and a directory in the
    plane that no row declares (a take nobody took is the tampering this gate exists to see)."""
    plane = ctx.install_of_mode(params["plane_mode"], required=False)
    statement = ctx.install_of_mode(params["declaration_mode"], required=False)
    if plane is None or statement is None or not ctx.workspace.exists(statement["target"]):
        return []
    rows = ctx.binding(statement["target"], statement["validates"])["takes"]
    print(f"        {pin.identity(ctx.manifest)}")
    declared = {c.id: c.raw for c in ctx.manifest.capabilities if c.id in ctx.manifest.taken}
    failures = []
    for row in rows:
        at = plane["target"] + row["id"]
        home = ctx.workspace.path(at)
        if not home.is_dir():
            failures.append(f"{at}/: declared taken by {row['taken_by']} at {row['at']}, and its "
                            f"plane is absent")
            continue
        signature = ((declared.get(row["id"]) or {}).get(provenance.CLAIM) or {}).get("signature")
        measured = provenance.tree_digest(home, f"{plane['namespace']}{row['id']}/", signature)
        if measured != row["digest"]:
            failures.append(f"{at}/: measures {measured}, and the take declared {row['digest']} "
                            f"(taken by {row['taken_by']} at {row['at']} from {row['source']})")
    root = ctx.workspace.path(plane["target"])
    held = {row["id"] for row in rows}
    for found in sorted(p.name for p in root.iterdir() if p.is_dir()) if root.is_dir() else []:
        if found not in held:
            failures.append(f"{plane['target']}{found}/: present in the take plane, and no row of "
                            f"{statement['target']} declares it taken")
    return failures


KINDS = {"provenance-pinned": _pinned, "taken-intact": _taken_intact}
