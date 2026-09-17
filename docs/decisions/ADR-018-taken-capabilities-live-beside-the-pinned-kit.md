# ADR-018 — Taken capabilities live beside the pinned kit, never inside it

- **Status:** Accepted (2026-09-17; owner-delegated under ADR-015 amendment 5). Implementation is a
  slice of link C (C1b), not yet built.
- **Decides:** where a capability a host TAKES (an adapter, a doctrine bundle) lives once the host
  carries a pinned kit, and how the release identity of the core survives the take.
- **Cures:** ADR-016 consequence *"A host that TAKES adapters pins a composition, labelled
  `+unreleased`"* — its named missing part: *"taken capabilities declared outside the issued
  `MANIFEST.json`"*. Recorded as GAP-T1 in `docs/reference/CANON-LEDGER.md`.
- **Amends:** ADR-014 decision 2 (the take is no longer "placed at `kit/capabilities/<id>/`, a
  manifest row"). **Relates:** ADR-008 (provenance of what a host takes) · ADR-016 · ADR-017 (C1).

## Context

ADR-014 makes a take an EDIT of the kit: copy the capability into `kit/capabilities/<id>/` and add a
manifest row. ADR-016 then holds the pinned tree to the lock it carries. The two are coherent only by
relabelling the whole pinned kit `+unreleased`, after which no surface can say "release 0.1.6" — the
core's identity is lost the moment anything is taken.

Measured on host #0 during C1a (2026-09-17): copying both runtime adapters into `.agents/kit/` made
`FF-KIT-PINNED` and `FF-PROVENANCE-PINNED` fail (`KIT0041`, 11 paths). Host #0 is the framework
repository itself, so the ADR-014 route (take into the source `kit/`) would put product-named
adapters into the SHIPPED kit, which ADR-014 decision 1 and the boundary row
`a-product-named-in-the-shipped-kit` forbid. Either way, C1's artifact — a runtime's hook served on
host #0 — cannot be walked.

The defect is structural: one tree carries two truths with different owners and different
lifecycles — what the publisher ISSUED (`replaced-by-release`) and what the host CHOSE (`living`).

## Decision

1. **The pinned kit is only ever the release.** `.agents/kit/` equals its own lock, byte for byte,
   always. Nothing a host takes is written into it.
2. **A taken capability has its own plane: `.agents/taken/<id>/`**, a verbatim copy of the
   capability as its source published it (declaration, documents, payload).
3. **The take is a DECLARATION in the host's plane: `.agents/project/taken.json`** — one row per
   taken capability: `id`, `source` (the release source it was read from), `digest` (h1 over the
   copied tree, ADR-008), `taken_by`, `at`. Validated by a new `taken` schema. This file is the
   one home of "what this host added to the kit"; `MANIFEST.json` is never edited by a host.
4. **The manifest loader COMPOSES**: issued manifest + every row of `taken.json`, each resolved to
   its plane. A taken id that collides with an issued id is refused (a take never shadows the
   release). Every interpreter keeps reading one `Manifest`; none learns where a capability came
   from (Cardinal VIII — the caller never asks *which kind are you*).
5. **Integrity is two gates over two homes, never one gate over a mixed tree.** `FF-KIT-PINNED`
   keeps judging `.agents/kit/` against its lock, unchanged. A new gate (`taken-intact`) judges each
   `.agents/taken/<id>/` against its row's digest. Surfaces print the composition honestly:
   `release 0.1.6 + taken: claude-code, codex` — authenticity of each take stated per ADR-008.
6. **The take is still a door.** `init --approve <who>` (or a `take` verb, decided at build time by
   the verb registry, not here) writes the plane and the row; the owner walks it.
7. **Records map (ADR-015 amendment 8):** `.agents/taken/` is a new `host_layout` place —
   holds `pinned-release`, writer `kit-verb`, lifecycle `replaced-by-release` (per take).
   `.agents/project/taken.json` holds a new kind `take-declaration`, writer `owner`, lifecycle `living`.

## Amendment 1 — the digest has one home (2026-09-17, found by building C1b)

Decision 3 put `digest` on the `taken.json` row, while ADR-008's provenance pin already records the
same h1 for every take: one reading, two homes (Cardinal III). **The row is a DECLARATION** — what the
host chose: `id`, `source`, `taken_by`, `at`. **The digest is a READING** of what arrived, and its one
home is the ADR-008 provenance pin. `taken-intact` reads the digest from the pin; `taken.json` drops the
field (expand-contract: optional now, removed at the schema's next version). Rejected: keep it on the row
and drop it from the pin — that would split ADR-008's one registry of what a host received into two
mechanisms by capability kind.

## Amendment 2 — the pin is written when the bytes arrive (2026-09-17, found by building amendment 1)

With the digest only in the provenance pin, a take not yet pinned by `init` has nothing to be judged
against: bytes changed between `take` and `init` would be pinned as if received. **`take` writes the
provenance pin itself, at arrival, marked `trust-on-first-use`** (the field's form: SSH `known_hosts`,
Go's `go.sum` on first fetch); `init --approve` later ATTESTS that same pin rather than creating it, and
refuses if the bytes no longer equal it. `taken-intact` then fails on any take with no pin — there is no
honest "not yet pinned" state. Rejected: (a) fail the gate between `take` and `init` — makes a normal,
approved step read red; (b) keep `NOT YET PINNED` as a pass — a window in which tampering is admitted
silently (Cardinal V). Not built at acceptance; the current code prints `NOT YET PINNED`.

## Rejected alternatives

**A. Keep composing inside the pinned tree, labelled `+unreleased` (status quo).** Rejected: the
core's release identity dies at the first take; the pin gate can no longer tell a host's chosen
addition from a host's tampering; and on the framework's own repository the route is impossible
without shipping product names.

**B. Ship the adapters inside the kit core.** Rejected: ADR-014 decision 1 — the kit ships no
surface; a product name in the shipped kit is a boundary defect, and every host would carry
runtimes it never chose.

**C. One lock covering pinned kit + takes (a merged lock).** Rejected: one document with two writers
(publisher and owner) and two lifecycles — the exact defect this ADR removes, moved into a file.

**D. Takes under `.agents/project/`.** Rejected: that plane holds the host's own DECLARATIONS
(`living`, owner-written); a verbatim copy of someone else's release is a different kind of record
and must not share a place with them.

## Consequences

- C1a's served hooks can be walked on host #0 once C1b builds this; the take itself remains an owner
  door.
- `test_280` (host #2 composition) changes meaning: the pinned kit stays a release, and the takes are
  accounted in their own plane — its assertions move to the new gate.
- ADR-016's `+unreleased` label survives only for a kit that is genuinely not a release (a working
  tree, a fixture), never for a host that merely took something.
- Migration for an existing host with takes inside its pinned tree: `upgrade` moves each
  `not-issued` path into `.agents/taken/<id>/` and writes its row — a pure step, because the lock
  already accounts those paths `not-issued` (ADR-009 rule 6 satisfied).
