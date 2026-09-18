"""check -- run the declared gates, report, never repair.

The gates are not listed here, and now neither are the gate KINDS. Each capability DECLARES the
gates that hold its own installs; each gate module DECLARES the kinds it can evaluate; this verb
discovers the modules the same way the CLI discovers verbs. A new gate is a row in a capability
declaration; a new gate kind is a FILE, never an edit here.

That last step is the one this slice had to take: a dict of kinds inside the verb would have had
to grow an entry the moment a capability arrived with rules of its own, and an interpreter that
must be modified to admit a new capability is not open, however generic its evaluators are.
"""

from __future__ import annotations

import declared
import gatekinds
import stance as stance_of
from errors import KitError
from gatekinds import GateError, registry  # noqa: F401  (this verb's long-published names)

SUMMARY = "run the declared fitness functions and report"
MUTATES = False
REQUIRES_APPROVED_HOST = True

#: Where gate kinds are discovered, and the error a clash raises: the core's, not this verb's.
GATES = gatekinds.GATES


class ThroughUnknown(KitError):
    """`check --surface` named a surface no taken adapter declares."""

    code = "KIT0048"


#: The contract a surface document keeps -- the schema's own name, as every reader of it uses.
SURFACES = {"validates": "runtime-surface"}


def _through(ctx, surface_id: "str | None") -> "dict | None":
    """The surface this check is run THROUGH, or None. Its declaration -- never the caller's word --
    says what kind of clone the check runs in; a name no taken adapter declares is refused, because
    a check that silently fell back to reading every setting would be answering another question."""
    if surface_id is None:
        return None
    surfaces = {row["id"]: row for row in declared.rules(ctx, SURFACES, "surfaces")}
    if surface_id not in surfaces:
        raise ThroughUnknown(
            f"check is asked to run through the surface {surface_id!r}, and no taken adapter declares "
            f"it (declared: {sorted(surfaces)}). Nothing was checked.")
    return surfaces[surface_id]


def run(ctx, args) -> int:
    """Every gate runs and every failure is printed, whatever its stance. The stance decides one
    thing only -- whether that failure fails this verb -- and it is printed beside the verdict with
    its author, so an observed failure is shown, counted and named, never a silent green."""
    kinds = registry()
    ctx.through = _through(ctx, getattr(args, "surface", None))
    enabled = ctx.enabled_capabilities()
    stances, unbound = stance_of.resolve(ctx.manifest, ctx.host_answers(), enabled)
    failed = 0
    observed, clean = [], []
    for capability in enabled:
        for gate in capability.gates:
            kind = gate["kind"]
            if kind not in kinds:
                raise GateError(
                    f"capability {capability.id!r} declares gate kind {kind!r}; "
                    f"registered kinds are {sorted(kinds)}"
                )
            held = stances[(capability.id, gate["id"])]
            failures = kinds[kind](ctx, gate.get("params", {}))
            print(f"  {'FAIL' if failures else 'PASS'}  {gate['id']}  ({kind})  {held.label()}")
            for failure in failures:
                print(f"        {failure}")
            if held.fails:
                failed += 1 if failures else 0
            else:
                (observed if failures else clean).append(f"{gate['id']} [{held.stance}]")
    for entry in unbound:
        print(f"  STANCE  {entry['gate']}  [{entry['stance']}: declared by {entry['by']} at "
              f"{entry['at']}] names no gate an enabled capability declares -- it binds nothing")
    if observed:
        print(f"check: {len(observed)} gate(s) failed under a stance that does not fail check: "
              f"{', '.join(observed)} -- shown, counted, and not enforced")
    if clean:
        print(f"check: {len(clean)} gate(s) held under a stance that does not fail check are "
              f"clean: {', '.join(clean)} -- no failure stands between them and a stance that "
              f"fails; raising one is a declaration only the host makes")
    print(f"check: {failed} gate(s) failed")
    return 1 if failed else 0
