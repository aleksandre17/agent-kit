# ADR-014 — Runtime adapters live outside the kit; surfaces are found by the contract they keep

- **Status:** Accepted (2026-09-13)
- **Amends:** ADR-013 point 1 (the RESIDENCE of a surface, not its kind).
- **Relates:** ADR-004 (the kit ships the carrier and the grammar, never an instance) · ADR-008
  (provenance of what a host takes) · ADR-010 (leaving the seam) · ADR-011/012 (succession).

## Context

ADR-013 made the SURFACE "the only declaration allowed to carry a product's name" and shipped two
of them in `kit/capabilities/runtimes/surfaces.json`, with their templates beside them and a gate
specimen admitting one product by name. The kind was right; the residence was not. The owner's
rule is that the framework is agnostic: no concrete brand or project identity in the kit core. A
surface shipped in the core is a runtime the framework chose for every host before meeting one —
the same defect ADR-004 already refused for doctrine.

Moving the rows out exposed the blocker the canon ledger records: a consumer reads its sources as
a FIXED list of names (`declared.rules`), so an open set of publishers cannot be read. The
doctrine carrier worked around it (each bundle projects its own roll); the served projection
cannot, because it must assemble ONE record over every surface.

## Decision

1. **The kit core ships the surface GRAMMAR (`runtime-surface` schema) and the Runtime port; it
   ships no surface.** With no adapter taken, the kit renders and checks green and serves nothing
   — a declared zero, never a default adapter.
2. **Every surface is published in an ADAPTER** at `adapters/<id>/` in the framework repository,
   OUTSIDE `kit/`: an ordinary capability (declaration, one `runtime-surface` document, its own
   templates, a vendor install of the surface so the host holds what it took). A host takes it
   exactly as it takes a doctrine bundle — placed at `kit/capabilities/<id>/`, a manifest row,
   and the ADR-008 door (h1 pin; `authenticity NOT ESTABLISHED` while unsigned).
3. **The open-set mechanism is contract-keyed collection**, built once in `declared.named`: a
   source set is either a list of names (closed, as before) or `{"validates": "<schema>"}` — every
   document any enabled capability ships, and every readable it declares, that keeps that schema.
   The word is the one documents already use to state their contract; the stance vocabulary is
   already found this way. Every reader of `declared.rules` (the served projection, every
   `reference-declared-across` gate) gains the open form with no change of its own.
4. **One home for "what outside the planes is ours":** `runtime.reach` (declared surface targets
   plus the served record). `succession.boundary` counts those paths as the kit's surface, and
   `cede` reads the served record (`runtime.served_rows`) — a served path is refused as SERVED,
   with its steward's own "no transfer" and the way out (stop serving; render removes it), never
   as "this host was never given it".
5. **Fitness functions:** a boundary row `a-product-named-in-the-shipped-kit` over a new scope,
   `shipped` (every file the kit's lock enumerates); `test_267`…`test_272`
   (`tests/acceptance/fresh-repo/test_adapters.py`); `test_266` strengthened to require that the
   surface gate — and only it — fails, under a stance that fails.

## Rejected alternatives

- **Keep the surfaces in the kit, "because a surface is the one place a name is allowed"** — right
  kind, wrong residence; every host inherits a vendor choice it never made, and the owner's rule
  is broken by the kit's own payload.
- **`provides`-keyed collection** (`{"provided_by": "runtime-surface"}`) — a provision is a
  CAPABILITY-grain token with no link to a particular document, so the consumer would need a
  second convention to pick which document of the provider to read, and `provides` already means
  "satisfies a `requires`" to the resolver: two meanings for one word. The contract a document
  keeps is already declared per document and already validated.
- **Each adapter projects its own served files (the doctrine-carrier workaround)** — N writers
  outside the planes, N records, and the collision rule (KIT0040: two surfaces claiming one path)
  becomes unenforceable because no single reader ever sees both claims.
- **Adapters under `kit/adapters/`, excluded from the lock** — the name is still in the kit's
  tree and in every clone of it; exclusion by a list is a privileged path, and the boundary scan
  would need an exemption field, which ADR-001 forbids.

## Consequences

- The runtimes gate `FF-RUNTIME-SURFACE` now admits `{}` (a descriptor serving nothing): with the
  set open and possibly empty, no concrete surface can be the calibration lookalike without the
  kit naming one. **Partial, named:** its edge against a REAL surface is proven by the acceptance
  suite (`test_268`, `test_270`), not by the gate's self-calibration.
- **Partial, named:** the capability schema does not yet declare the `{"validates": ...}` form of
  `serves.surfaces.sources` (it leaves `sources` untyped there); `declared.named` refuses any other
  shape (KIT0005), so a malformed selector is refused, but the contract is not yet stated in the
  schema. The doctrine carrier can now drop its per-bundle workaround — not done here.
- **Partial, named:** a served path whose steward DECLARES a transfer is refused as not built;
  today the projection steward declares none. `succession.measure` does not yet add a "served
  here" fact per path; the boundary root is what counts.
- ADR-013's `admits: {"surface": ...}` specimen and its surfaces document are gone from the kit;
  ADR-013 is otherwise unchanged.
