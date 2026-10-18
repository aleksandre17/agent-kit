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

import contextlib
import io
import time

import declared
import gatekinds
import maturation
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


ARGUMENTS = [("--brief", {"action": "store_true",
                          "help": "print what fails and the summary only -- the listing an agent reads (Cardinal IX)"})]

def run(ctx, args) -> int:
    """Every gate runs and every failure is printed, whatever its stance. The stance decides one
    thing only -- whether that failure fails this verb -- and it is printed beside the verdict with
    its author, so an observed failure is shown, counted and named, never a silent green."""
    kinds = registry()
    # A kind whose READING is worth a line on every check, pass or fail (the tree audit's counts).
    reports = registry("REPORTS")
    ctx.through = _through(ctx, getattr(args, "surface", None))
    enabled = ctx.enabled_capabilities()
    matured, idle = maturation.spent(ctx, enabled)
    stances, unbound = stance_of.resolve(ctx.manifest, ctx.host_answers(), enabled, matured)
    failed = 0
    observed, clean = [], []
    # A passing gate whose own lines `--brief` leaves out -- NOT MEASURED, a reading's counts -- is named,
    # so a brief check never reads as one that measured everything (CWE-222).
    unshown = []
    brief = getattr(args, "brief", False)
    timed, began = [], time.perf_counter()
    for capability in enabled:
        for gate in capability.gates:
            started = time.perf_counter()
            kind = gate["kind"]
            if kind not in kinds:
                raise GateError(
                    f"capability {capability.id!r} declares gate kind {kind!r}; "
                    f"registered kinds are {sorted(kinds)}"
                )
            held = stances[(capability.id, gate["id"])]
            crashed = False
            said = io.StringIO()  # a gate's own lines are shown with its header, never without it
            try:
                with contextlib.redirect_stdout(said):
                    failures = kinds[kind](ctx, gate.get("params", {}))
            except KitError:
                raise  # a refusal by name is the kit speaking, and it is reported as itself
            except Exception as exc:  # noqa: BLE001 -- a gate that crashed decided nothing
                # Fail-safe defaults (Saltzer & Schroeder): a gate exists to deny, so a gate whose
                # decision is UNKNOWN denies. It fails under its own stance -- never a pass, and never
                # a crash that takes every other gate's verdict down with it (ADR-022 decision 8).
                crashed = True
                failures = [f"the gate kind {kind!r} crashed ({type(exc).__name__}: {exc}) -- an "
                            f"unjudged gate is not a passed one"]
            if not failures and brief and (said.getvalue().strip() or (kind in reports and not crashed)):
                unshown.append(gate["id"])
            if failures or not brief:
                print(f"  {'FAIL' if failures else 'PASS'}  {gate['id']}  ({kind})  {held.label()}")
                if said.getvalue():
                    print(said.getvalue().rstrip("\n"))
                for failure in failures:
                    print(f"        {failure}")
                if kind in reports and not crashed:
                    print(f"        {reports[kind](ctx, gate.get('params', {}))}")
            if held.fails:
                failed += 1 if failures else 0
            else:
                (observed if failures else clean).append(f"{gate['id']} [{held.stance}]")
            timed.append((time.perf_counter() - started, gate["id"]))
    for sentence in idle:
        print(f"  MATURED {sentence}")
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
    # What judging cost, every time (Cardinal IX): a check that grows slow says which gates made it so.
    slowest = ", ".join(f"{gid} {spent:.1f} s" for spent, gid in sorted(timed, reverse=True)[:3])
    print(f"check: {len(timed)} gate(s) judged in {time.perf_counter() - began:.1f} s -- the slowest: {slowest}")
    if unshown:
        print(f"check: {len(unshown)} passing gate(s) said more than PASS, left out by --brief: "
              f"{', '.join(unshown)} -- `check` shows each of their lines")
    print(f"check: {failed} gate(s) failed")
    return 1 if failed else 0
