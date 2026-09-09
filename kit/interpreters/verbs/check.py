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

import importlib
from pathlib import Path

from errors import KitError

SUMMARY = "run the declared fitness functions and report"
MUTATES = False
REQUIRES_APPROVED_HOST = True

GATES = Path(__file__).resolve().parents[1] / "gates"


class GateError(KitError):
    """A declaration named a gate kind no discovered module can evaluate, or two modules claim
    one kind -- which is a name resolving to two meanings, refused rather than ordered."""


def registry() -> dict:
    kinds: dict = {}
    owners: dict = {}
    for path in sorted(GATES.glob("*.py")):
        if path.stem.startswith("_"):
            continue
        module = importlib.import_module(path.stem)
        for kind, evaluate in getattr(module, "KINDS", {}).items():
            if kind in kinds:
                raise GateError(
                    f"gate kind {kind!r} is declared by both {owners[kind]!r} and {path.stem!r}"
                )
            owners[kind] = path.stem
            kinds[kind] = evaluate
    return kinds


def run(ctx, args) -> int:
    kinds = registry()
    failed = 0
    for capability in ctx.enabled_capabilities():
        for gate in capability.gates:
            kind = gate["kind"]
            if kind not in kinds:
                raise GateError(
                    f"capability {capability.id!r} declares gate kind {kind!r}; "
                    f"registered kinds are {sorted(kinds)}"
                )
            failures = kinds[kind](ctx, gate.get("params", {}))
            print(f"  {'FAIL' if failures else 'PASS'}  {gate['id']}  ({kind})")
            for failure in failures:
                print(f"        {failure}")
            failed += 1 if failures else 0
    print(f"check: {failed} gate(s) failed")
    return 1 if failed else 0
