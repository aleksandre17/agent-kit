# ADR-013 — Serving a runtime: one port, a surface per product, projections outside the planes

- **Status:** Accepted (2026-09-13)
- **Closes:** GAP-R1 — the kit describes runtimes and serves none.
- **Relates:** ADR-003 (collision, adoption) · ADR-004 (doctrine bundle) · ADR-010 (leaving the seam) · ADR-011/012 (a prior system is migrated by `inherit`/`takeover`) · GAP-E1 (edit-time enforcement: hooks, settings).

## Context

A runtime product reads its instructions at FIXED paths the kit does not choose — an entry
document at the repository root, a directory of agent definitions beside it — and nowhere else.
Before this decision the kit projected only into its own plane (`.agents/generated/`), so a host
could declare every runtime it runs and not one of them read a byte the kit produced.

Three constraints held the design:

1. **The grammar already splits a runtime in two** — a CLASS (true of a kind; never a product
   name) and a DESCRIPTOR (what one host says of its tool; no field a proof can be written in).
   Where a product *looks* is true of the product everywhere and of no kind and no host, so it has
   no legitimate home in either.
2. **The four-class floor** (`FF-KIT-CLASS`): every path the kit produces resolves to exactly one
   of vendor · binding · projection · ephemeral. The fixed paths lie outside all four planes.
3. **A projection is deleted and re-rendered, never merged** (`FF-KIT-PROJECTION`), and a host may
   already hold hand-written bytes at those paths.

## Decision

1. **A third tier, the SURFACE** (`kit/schemas/runtime-surface.schema.json`,
   `kit/capabilities/runtimes/surfaces.json`): one row per product naming the paths it reads and
   the template that gives each file the form the product parses. It is the only declaration
   allowed to carry a product's name. A host SERVES a surface by naming it from its own descriptor
   (`runtime.surface`); the set of descriptors naming a surface is the host's ENABLED set.
2. **A Runtime PORT** (`kit/interpreters/ports/runtime.py`) states what the kit can hand any
   runtime: a *document view* assembled from sections the host already owns (its law page, its
   doctrine projection, its role roll) and a *collection view* — one file per record of a composed
   view, whose body is the projection the host already renders for that record (a role
   definition). Surfaces are the adapters, and they are pure data. The port names no product,
   path, view or surface; a third runtime is a surface row and zero interpreter edits.
3. **Served files are PROJECTIONS outside the planes, recorded inside one.** A `served`
   projection shape (a row in render's open shape registry, staged after the plane shapes because
   it projects *from* them) renders every served file with the rest of the plane, and writes
   `.agents/generated/SERVED.json` — every served path with the digest of its bytes. The record is
   the class declaration of each outside path; `FF-KIT-PROJECTION` holds every served file to
   byte reproduction exactly as it holds the plane.
4. **The collision rule — refuse, never clobber.** Before a byte moves, every outside path is
   judged: absent → written; bytes equal to what the kit renders now, or to the digest the kit's
   record says it last wrote → rewritten; anything else is somebody's file and the WHOLE render is
   refused (`KIT0039`), every such path named. A served path no longer rendered is removed only
   while it still holds the kit's recorded bytes; a hand-edited one refuses too. Two served files
   claiming one path refuse (`KIT0040`), both named — never last-writer-wins. A prior system at
   those paths is carried over by `inherit`/`takeover` (ADR-011/012), not overwritten here.
5. **Values cross the boundary in one form both sides read identically**: every scalar a
   role template embeds is a JSON string literal, which is at once a valid YAML double-quoted
   scalar and a valid TOML basic string — no escaping rule per format.

The seam GAP-E1 fills is declared, not built: a product setting (hooks, permissions) is another
`renders` row on the surface with another view offered by the served install. Nothing here writes
settings.

## The field — what is adopted

- **Language Server Protocol** — one protocol, many clients; the server never learns which editor
  it serves. Adopted as the port/adapter split: the port offers views, a surface consumes them.
- **Home-Manager** `home.file` + `checkLinkTargets` — targets outside the source tree, managed by
  a manifest, and a refusal to clobber a file it does not manage. Adopted: the record + refusal.
  Its symlinks are *not* adopted — links are a translation that differs by platform (Cardinal VII).
- **chezmoi** — target state computed from source state. Adopted as "the declaration is the
  truth"; its overwrite-on-apply is rejected.
- **`.editorconfig` / `CODEOWNERS` / `devcontainer.json`** — one file at a fixed path read by
  many tools: the reason a surface declares a path rather than the kit choosing one.
- **Backstage / Nx generators** — templates rendered from a model; here the model is the host's
  existing declarations, so nothing is invented at generation time.

## Rejected alternatives

1. **Hand-coded adapters per product** (a `claude.py`, a `codex.py`). Every new runtime costs an
   interpreter edit and the interpreter names a product — the privileged case Cardinal II forbids
   and `test_71` already refuses.
2. **Put the paths in the host's descriptor.** Where a product looks is true of the product in
   every host; each host restating it is one truth with N homes (Cardinal III), and the paths are
   a setting the descriptor schema was built to keep apart from anything believed about the tool.
3. **Put the paths in the runtime CLASS.** A class is a kind; a product name in it would be the
   one sentence guaranteed false of the kind, and the class registry would change every time a
   vendor ships.
4. **A thin entry file that imports/links the plane** (`@import`, symlinks). One product supports
   imports and the other does not; a reference can be left unfollowed; symlinks are a boundary
   translation that differs on this very platform. Rejected for rendered bytes.
5. **Merge into an existing hand-written file** (markers, managed blocks). A projection that
   merges has history and something to drift from; the kit's identity is rebuild, never merge.

## Consequences

- A host now serves the runtimes it enables; proven live on a clone of a real host with both
  installed products reading the served files (walk report kept with the delivering session).
- **Partial, named:** a surface a HOST declares for an in-house product is not built — the
  sources list admits a host document, but no host seed ships yet. `cede` (ADR-010) does not yet
  read `SERVED.json`, so leaving the kit leaves served files behind; succession's boundary does
  not yet count served paths as the kit's surface. `FF-KIT-CLASS` walks `.agents` only, so the
  record, not a walk, is what classes an outside path. Each is a follow-up, not a resting state.
- Fitness functions: `test_258`…`test_266` (tests/acceptance/fresh-repo/test_serving.py), and the
  data gate `FF-RUNTIME-SURFACE` (a descriptor serving a surface nobody declares).
