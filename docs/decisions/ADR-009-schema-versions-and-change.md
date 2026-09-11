# ADR-009 — Schema versions and change: one version per document kind, one home for it, and a reader that refuses what it does not read

- **Status**: Accepted
- **Date**: 2026-09-11
- **Amends**: nothing in ADR-001 … ADR-008. ADR-005 gains two codes (`KIT0033`, `KIT0034`);
  `KIT0015` (a payload declaration that does not honour its contract) now also covers a schema that
  breaks the version policy. ADR-007's cure for the hold and the journal (the version is READ from
  the schema's `const`) becomes the rule for every document kind.
- **Rules on**: every schema registered in `kit/MANIFEST.json` (`kit/schemas/*.schema.json`), the
  manifest port `kit/interpreters/ports/manifest.py`, and every interpreter that writes a
  `schema_version` (`context.py`, `estate.py`, `lockfile.py`, `observers/receipt.py`,
  `verbs/evaluate.py`, `verbs/init.py`, `hostlock.py`, `journal.py`).

## The situation

Every document the kit reads or writes carries `schema_version`, and the field meant nothing:

1. **The field did not bind.** 24 registered schemas declared it as a bare `{"type": "integer"}`,
   one (`detector`) did not declare it at all, and three (`diagnostics`, `hold`, `journal`) pinned a
   `const`. A document stating version 99 validated. A reader could not tell a document from the
   future from one it understood — and the first thing it did with a future document was read it.
2. **The version had many homes.** Five modules held a `SCHEMA_VERSION = 1` of their own
   (`context`, `estate`, `lockfile`, `observers/receipt`, `verbs/evaluate`) and a sixth (`verbs/init`)
   imported `context`'s. Each would go on writing `1` the day the schema moved — a writer and its
   schema both locally correct, the host lied to.
3. **There was no change rule.** Nothing said what makes a change breaking, what a version bump
   means, or what a host holding an older document is told.

The kit is pre-1.0 and one real host is about to install it. The policy lands before that host's
documents exist, because afterwards every one of them is a document the policy must reach.

## The field

- **Protocol Buffers / Avro schema evolution.** Additive change is compatible (new optional
  fields; a reader ignores what it does not know). A field is never reused or re-meant. Avro makes the
  *writer's* schema and the *reader's* schema explicit and resolves between them.
- **Kubernetes API versioning.** The version belongs to the KIND (`apps/v1 Deployment`), not the
  cluster; `v1alpha1 → v1beta1 → v1`; one *storage version* is what is written; conversion happens
  on read; deprecation windows are declared.
- **Parallel Change / Expand–Contract** (Fowler, Sato). A breaking change is split into an additive
  EXPAND, a migration, and a CONTRACT that removes the old form — never one step.
- **JSON Schema `$id`/`$schema`.** Identity and dialect of a schema are declared IN the schema.
- **Terraform state.** State carries `version`; a newer Terraform upgrades older state
  automatically; an older Terraform **refuses** to read state written by a newer one. It never
  guesses.
- **Flyway / Alembic.** Migrations are ordered, append-only, checksummed and **never edited once
  applied** — the same rule ADR-005 gave the diagnostic registry.
- **Semver for data formats.** A MAJOR bump is a breaking shape change; MINOR is additive; a reader
  only needs to know majors, because additive change is invisible to it by construction.

The questions the field poses, and what it answers:

| Question | The field's answer |
|---|---|
| Version per document kind, or one for the kit? | Per kind (Kubernetes, Avro). The kit's version already exists (`kit_version`) and means something else: which release WROTE the document. |
| A reader meeting a NEWER version? | Refuse, never guess (Terraform, and any reader without the writer's schema). |
| A reader meeting an OLDER version? | Migrate if a migration is declared; otherwise refuse and name what is missing. |
| Migrations: data or code? | Code (Alembic, Kubernetes conversion) where the change is not a pure rename; declared data (an ordered ledger) for WHICH migrations exist. |
| Can a shipped migration be edited? | Never (Flyway checksums; ADR-005's registry). |

## The decision

1. **One version per DOCUMENT KIND, and its only home is the kind's schema.** Every schema the
   manifest registers declares `schema_version` as `{"type": "integer", "const": N}` with `N >= 1`,
   on the object that carries it — the document, or each record of a document that is a list
   (`cardinal`). The version is a plain integer: the MAJOR of semver for data. There is no minor,
   because additive change (below) does not move it and a reader never needs to see it.
2. **Writers are projections.** Every writer stamps `manifest.version_of(<kind>)`, where the kind is
   the one its declaration names (`validates`) or, for a document the interpreter owns (`hold`,
   `journal`, `lock`), the schema it already names. No module holds a version. A kit that declares
   no reading install stamps no version on its in-memory reading: no version is invented for a
   document no declaration will store.
3. **The reader rule is ONE mechanism for every kind, in the manifest port — the one door every
   validation passes.** Before a document's shape is judged, the version it STATES is compared with
   the kind's `const`:
   - **newer** → refused, `KIT0033`. Never read as if understood; shape errors against today's
     schema would describe nothing true.
   - **older** (≥ 1) → refused, `KIT0034`, naming the version found, the version read, and that no
     migration is declared.
   - **unknown** (absent where required, not an integer, below 1) → ordinary shape validation, which
     names it under the reading module's own code.
   The rule reads the schema's SHAPE (object vs list of records), never its name; no kind is
   privileged.
4. **The policy is held where schemas are loaded.** The manifest refuses to load (`KIT0015`) a kit
   with a registered schema that does not pin its version as an integer `const >= 1`, or a kind past
   version 1 that does not `require` the statement. The second clause is what makes absence safe:
   an absent version can only ever be meant for a kind that has only ever had version 1.
5. **What changes a version.** EXPAND is free: a new *optional* property, a widened `enum`, a
   relaxed constraint — the version does not move, because every existing document still honours
   the schema. Anything else is BREAKING and bumps the kind's `const` by one: removing, renaming or
   re-typing a property, making an optional property required, narrowing an `enum`, tightening a
   constraint. A property name is never reused with a new meaning (Protobuf): a meaning that changes
   takes a new name, and the old one is retired through expand–contract.
6. **Migrations: none before 1.0 — said plainly.** Every kind is at version 1, so no migration has
   ever been needed, and a migration engine with nothing to migrate would be speculation. A host
   holding a document at an older version is told by `KIT0034`: run the kit version that wrote it,
   or re-create the document with this one. **When the first kind moves to version 2, migrations
   arrive in the same change, in this form:** one ordered, append-only ledger of declared steps
   (`kind`, `from`, `to`, the interpreter step that performs it), a step being pure (document in,
   document out) and followed by validation against the new schema; a migrated document is
   rewritten only under the host hold (ADR-007) and only through the step chain `from → from+1 → …`.
   A step once shipped is **never edited** — a mistake is corrected by a NEW step, exactly as a
   diagnostic code is never re-meant (ADR-005). `KIT0034` then narrows to "no step chain reaches
   the current version".

## Rejected alternatives

1. **One kit-wide version stamped on every document.** Rejected: it moves every kind whenever any
   kind breaks, so a host's untouched documents become "older" for no reason, and it duplicates
   `kit_version`, which already records which release wrote the document. Kubernetes versions kinds,
   not clusters, for exactly this reason.
2. **Semver strings (`"1.2.0"`) per document.** Rejected: the reader only ever needs the breaking
   axis. A minor carried in the document is either ignored (and so a field that lies about mattering)
   or compared (and then an additive change a reader could have read becomes a refusal). The
   integer is the major; additive change is invisible by construction.
3. **Read newer documents best-effort (ignore unknown fields, Protobuf style).** Rejected for this
   kit: the documents are host TRUTH (answers, estate, hold) that gate writes. Protobuf's forward
   compatibility works because its evolution rules forbid breaking changes; our version bump is
   exactly the signal that one happened. Reading past it is a guess acting as understanding.
4. **Keep module constants and add a test that they equal the schema.** Rejected: that synchronises
   two homes instead of removing one. ADR-007 already removed the constant for the hold and the
   journal; a check that the copies agree is the discipline this identity forbids.
5. **Build the migration engine now.** Rejected pre-1.0: with every kind at version 1 there is no
   step to run, so the engine's contract would be designed against no case. The form is fixed
   above so the first breaking change cannot improvise it.

## Consequences

- A document from a newer kit can no longer be read by an older one — by design. An operator sees
  `KIT0033` and the kind, not a list of shape errors.
- `detector` gained an optional `schema_version` (an EXPAND): detector declarations may state it and
  are gated when they do. It becomes required (the CONTRACT) in the change that adds it to every
  shipped detector — and the load-time rule forbids moving `detector` past version 1 before then.
- A kind moved to version 2 in its schema alone is written at 2 by every writer with no code change
  (fitness below) — and every host document at 1 is refused until migrations exist.
- Five module constants and one import are removed; the hold and the journal read through the same
  `version_of` as everyone else.

## Fitness functions

`tests/acceptance/fresh-repo/test_schema_versions.py`, every set derived from the manifest and
asserted non-empty:

- `test_212` — every registered schema pins its version as an integer `const >= 1` (required past 1).
- `test_213` — every registered kind refuses a newer document with `KIT0033` before shape judgement.
- `test_214` — no interpreter module holds a version constant or stamps a literal version.
- `test_215` — every interpreter-written kind moved to version 2 in its schema alone is written at 2.
- `test_216` — a host document from a newer kit is refused end-to-end by code and left untouched.
- `test_217` — a host document at an older version with no migration is refused by code.
- `test_218` — a kit whose schema breaks the policy refuses to load (`KIT0015`, naming ADR-009).
