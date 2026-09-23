"""Gate kinds for a fact a capability declares it CONSUMES.

A consumption row names a fact and authors the words for its absence. That pairing has one failure
mode worth a sensor, and it is the one a reader cannot see: a row naming a fact NO DECLARED
DETECTOR CAN EVER EMIT projects its declared gap on every host in the world, forever, and reads
exactly like an honest measurement of a host that declares nothing. A typo, a renamed fact and a
withdrawn detector all land there. The gap is the same words either way; only this gate can tell
the difference (Cardinal V).

It judges the DECLARATION and never the host: a row whose fact is emitted by some detector and
absent from this tree is a host that said nothing, which is legal and stays green. Nothing here
names a fact, a field or a document -- the rows, the field they live under, the field that names
the fact, and the sentences a failure is explained in all arrive as params.
"""

from __future__ import annotations

import declared


def _consumed_fact_declared(ctx, params) -> list:
    emitted = {key: detector["id"]
               for detector in ctx.manifest.detectors for key in detector["emits"]}
    failures = []
    for row in declared.rules(ctx, params["sources"], params["list"]):
        fact = row[params["names"]]
        if fact in emitted:
            continue
        failures.append(
            f"{row['id']}: consumes the fact {fact!r}, which no declared detector emits -- "
            f"{params['because']} Instead: {params['instead']} "
            f"(the facts this kit can emit are {sorted(emitted)})"
        )
    return failures


KINDS = {"consumed-fact-declared": _consumed_fact_declared}
