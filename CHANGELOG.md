# Changelog

Upstream only. This file is never vendored into a host: an append-only release record grows with
the framework's age rather than the host's needs. A host's legitimate question is narrower — *what
changed between the version I have and the version I am moving to* — and it is answered at the
moment of need by `upgrade`, which is not built yet.

## 0.1.6 — unreleased

**Fixed — `judge` never admits an edit it could not place (Cardinal VII)**
- On a drive-lettered filesystem a drive spelled as a POSIX mount (`/c/...`, `/cygdrive/c/...`) is
  normalised by ONE form rule in `gates/edits.py`; any other rooted path without a drive raises
  `Unplaceable` and `judge` REFUSES. Previously both read as "outside this host" and passed (fail-open).

**Changed — the pin is written when the bytes arrive (ADR-018 amendment 2; closes the take→init window)**
- `take --approve` writes the ADR-008 provenance pin for each take AT ARRIVAL, marked
  `trust: {basis: trust-on-first-use}` with authenticity `not-yet-read` (new declared word in
  `provenance.json`); a retake of equal bytes keeps its pin, a newer version supersedes it, changed
  bytes at the same version or an older version are refused (KIT0045).
- `take` now HOLDS the host as its one writer (ADR-007): its writes run under `hostlock.held`.
  Still not built: a take journal.
- `init --approve` ATTESTS a trust-on-first-use pin (authenticity read, `trust: {basis: attested,
  attested_by, attested_at}`); bytes that no longer equal the pin read `drifted` and init refuses.
  Without an approval an unattested pin waits at the provenance door like a first contact.
- `taken-intact` FAILS on a take with no pin; the `NOT YET PINNED` pass state is removed. A pin
  written before amendment 2 carries no `trust` field and reads as attested (it was pinned at an
  approved door). `estate.schema.json` gains optional `trust`.

**Changed — the take digest has one home (ADR-018 amendment 1)**
- `taken-intact` judges each take against its ADR-008 provenance pin, never its row; a take not yet
  pinned is printed `NOT YET PINNED` (not failed). `take` no longer writes `digest` and sheds it from
  carried rows; `taken.schema.json` makes `digest` optional and deprecated (removed next version).

**Added — link C, slice C1b: TAKEN CAPABILITIES LIVE BESIDE THE PINNED KIT (ADR-018; cures GAP-T1)**
- **Two homes, one composition.** Governance declares the take PLANE (install mode `taken`,
  `.agents/taken/`, opened as a space; `declaration` + `namespace` are new optional install fields) and
  the take DECLARATION (mode `taken-declaration`, `.agents/project/taken.json`, schema `taken`, seeded as
  a declared zero). `.agents/kit/` is never written by a take and stays byte-equal to its lock.
- **The loader composes.** `manifest.composed(kit, host)` = issued `MANIFEST.json` + every take row,
  each resolved to its plane by `Manifest.path` (the one resolver; `_read`, `payload_text` and
  provenance's signature read go through it). Context speaks with the composed manifest; no projection
  learns where a capability came from. An issued id taken again is refused at the take and at every
  load: `TakeShadows`, **KIT0044**. A row whose plane is gone is refused at load (KIT0015).
- **`take` verb** (new file, a DOOR): `take --root . --path <dir>[,<dir>] [--approve <who>]` copies
  each published capability verbatim into its plane and writes its row (`id`, `source`, `digest` =
  h1 over the whole copied tree in the kit namespace, `taken_by`, `at`). Unapproved it names the takes
  and refuses (KIT0007); a bad take is **KIT0045**. Enabling the take (`project.json`) and pinning its
  provenance (`init --approve`) remain the acts they were.
- **`FF-TAKEN-INTACT`** (kind `taken-intact`, `gates/taken.py`) judges each take against its row's
  digest and fails a directory in the plane no row declares. `FF-KIT-PINNED` unchanged. Provenance's
  digest of a take is the same h1 over the same tree (one algorithm, `provenance.h1`).
- **Surfaces state the composition:** the CLI's first line and `pin.identity` print
  `release <v> + taken: <ids>`.
- Records map: host_layout rows `.agents/taken/` (pinned-release / kit-verb / replaced-by-release) and
  `.agents/project/taken.json` (new kind `take-declaration` / owner / living); stewardship modes rows.
- Tests: `test_taken.py` 300-304 (fresh fixture host takes both adapters, serves `.claude/settings.json`
  + `.codex/hooks.json`, `check: 0 gate(s) failed`); `test_280` now proves the take accounted in its
  own plane (the pinned lock carries no `not-issued` path).

**Not built (C1b)**
- **Migration of a host whose takes sit inside its pinned tree** (ADR-018 consequence: `upgrade` moves
  each `not-issued` path into `.agents/taken/<id>/` and writes its row). Not small: `upgrade` delegates
  every write to `init`, which has no mode that relocates a vendor-tree path into another plane; needs
  its own slice. Such a host keeps working on the old `+unreleased` route.
- `adapters/README.md` still describes the ADR-014 take (copy into `kit/capabilities/` + manifest
  row); outside this slice's write set.
- The `take` verb does not take the host hold as a writer (it `arrive`s only) and is not journalled.
- The take row's `digest` and the estate's provenance pin carry the same measured value in two
  documents (ADR-018 decision 3 vs ADR-008 pin) -- a Cardinal III tension, recorded, not resolved here.

**Added — link C, slice C1a: THE ENFORCEMENT LINE (ADR-017 row C1, first part; UNFINISHED on host #0 — see Blocked)**
- **`enforcement` capability** (kit core, names no product): the host declares EDIT GATES in
  `.agents/project/enforcement/edit-gates.json` (schema `edit-gate`: a path pattern, a pattern over the
  text an edit INTRODUCES, `because`/`instead`, and a calibration pair `proves`/`admits`). The kit ships
  zero gates. `FF-EDIT-GATE` (kind `edit-gates-calibrated`) fails an uncalibrated gate. Gates judge the
  introduced text, never the whole file -- a ratchet: new lines are held, the edit repairing an old one
  is not refused.
- **`judge` verb -- the hook.** Vendored in the pinned kit; reads the product event on stdin; resolves
  `--surface <id>` to that surface's new `hands` block (dotted event keys for paths and introduced text,
  an optional patch grammar as two patterns, the refusal exit code). Holds no policy and no product
  (`test_291`). An event naming no path is REFUSED as unjudged; an uncalibrated gate is named as NOT
  APPLIED (and `check` fails it) rather than refusing every edit on its word. Refusal code KIT0043.
- **Served settings.** The runtimes served install offers a new `enforcement` view; `vendor` (the
  manifest's vendor plane root) joins the served frame so a template never spells `.agents/kit`. Adapters:
  claude-code serves `.claude/settings.json` (PreToolUse, `Write|Edit|MultiEdit|NotebookEdit`, blocks
  before the write); codex serves `.codex/hooks.json` (post_tool_use, `apply_patch`, flags AFTER the write
  -- codex has not proven `pre_exec_block`; ADR-017 decision 5). New CLI option `--surface`.
- Host #0 enables `enforcement` (`project.json`); `check: 0 gate(s) failed` with FF-EDIT-GATE PASS.
- Tests: `test_enforcement.py` 288-291.

**UNVERIFIED (Cardinal VII)**
- codex: every `tool_input.*` key and the apply_patch grammar in `hands`; the `.codex/hooks.json` location
  and exit-2 semantics on `post_tool_use` are taken from a prior hand-built system's receipts on this
  machine, not observed through THIS kit. claude-code keys and exit-2 PreToolUse refusal: same provenance.
- Neither product has been observed RUNNING the served hook. Windows 8.3 short vs long path forms are
  compared by `normcase`/`abspath` only.

**Blocked -- the host #0 live walk of served settings (GAP, owner door + a seam defect)**
- Taking an adapter on a host that carries a pinned kit is IMPOSSIBLE today: ADR-014 takes an adapter by
  placing it in the kit tree and adding a MANIFEST row, and ADR-016 holds that tree to its own lock.
  Measured on a scratch copy of host #0: `init --approve` pins both adapters and then refuses KIT0041
  (pinned kit no longer equals its lock, 11 paths); `check` fails FF-KIT-PINNED and FF-PROVENANCE-PINNED.
  Proposed cure (needs an ADR): a TAKEN capability resides outside the vendor tree in its own declared
  place, found by the manifest loader beside the pinned kit, pinned by provenance, never by the kit lock.
- The take is also a DOOR only the owner may walk; no agent approved it on host #0. On the scratch copy
  the served hook commands, run verbatim, refused a violating Claude Write (absolute Windows path, exit 2),
  passed a clean Edit (exit 0), refused a violating codex patch (exit 2) and an unreadable event (exit 2).

The host tree meets the drawn floor (link L3a of ADR-015's line), and the last thing that kept it
from meeting it: a declared empty directory could not survive a clone.

**Fixed within C1a -- the suite made green again (4 failures, each at its root)**
- `KIT0043` was appended but the registry's `issued` high-water mark stayed 42; now 43
  (`test_180` held the density law, correctly).
- `test_260` asserted the host's law in EVERY document render; it now selects by the render's
  declared VIEW -- only a view with a section reading the binding plane carries law. A settings
  file is not a briefing; the design was right, the test inferred shape from "not a directory".
- `test_264` built its third runtime as "briefing = document, every other view = collection", a
  privileged view name: the `enforcement` document became a collection with no `over`
  (`KeyError`). The copied row now keeps the SHAPE of the row it copies; interpreter untouched.

**Fixed**
- **A declared space now survives the repository.** `mode: space` and a collection projection over
  a set the host has not filled each own a directory whose honest state is EMPTY. The kit made it;
  git carries files, not directories; the path was gone on the next checkout, and `FF-HOST-FLOOR`
  then reported a DRAWN path as MISSING on a host where nothing was wrong (Cardinal VII — the kit
  and git agreed on the name and disagreed on whether it existed, each locally right). The emptiness
  is now carried in a form both read the same way: one marker, written UNCONDITIONALLY into every
  declared space and every collection projection, and PLANNED rather than applied as a side effect
  (a path the plan did not promise is a path nothing renders). Its sentence states the space and
  never its contents, because a marker that appeared only in EMPTY collections was a variation
  between hosts with no declared cause.
- `.agents/project/roles/`, `.agents/generated/roles/` and `.agents/generated/runtimes/` — three
  drawn paths — are present on host #0, which now checks with **0 gates failed**.

**Added — link L3b: the layout is the RECORDS MAP (ADR-015 amendment 8)**
- **Every drawn host place declares its record keeping.** Each of the 29 `host_layout` entries now
  carries `holds` (the kind of truth living there), `writer` (who may write it), `read_when` (the task
  triggers that pull it into context) and `lifecycle` (how it ages, ISO 15489's disposition) --
  pending places included, because a place with no content yet still has a declared home.
- **`record_keeping`, an OPEN vocabulary** (`capabilities/governance/record-keeping.json`, schema
  `record-keeping`): three registries -- 26 `kinds`, 11 `writers`, 10 `lifecycles` -- each a list of
  `{id, summary}`. The schema bounds the shape of a row, never the set of rows.
- **`FF-RECORDS-DECLARED`** (`reference-declared-across`, floor `enforce`): every `holds`, `writer`
  and `lifecycle` resolves to a vocabulary row; calibrated per reference; no new gate kind.
- **`.agents/generated/INDEX.md`, the map projected** (`payload/RECORDS-MAP.md.mustache`): one row
  per place with its four words and its state -- `PENDING -- link X`, `ONLY WITH <capability>` or
  `always` -- then the three registries as legends. `.agents/generated/governance/INDEX.md` is
  unchanged. The floor row loses `pending: L3b`.

**Changed -- an EXPAND, not a version move (ADR-009 rule 5)**
- The four fields are OPTIONAL in `layout` v1. Required would be breaking (rule 5), would refuse
  `docs/reference/UPSTREAM-LAYOUT.json` (the upstream box, not yet mapped) and adapter `floor` rows,
  and rule 6 would demand a migration whose only step cannot exist: `holds`/`writer`/`lifecycle`
  are judgements no pure step can derive. Presence on every host place is held by
  `test_285` over the one shipped declaration. CONTRACT (const 2, required) is owed once the upstream
  box and adapter floor rows are mapped.

**Added**
- **`space.marker` — a capability declares how a directory is carried.** The marker's FILENAME
  (`.gitkeep`, the field's own convention, so it explains itself to a reader who has never met this
  kit) is a DECLARATION in the capability that can never be disabled, not a constant in an
  interpreter: a filename written into a host is policy, and a path segment no declaration carries
  is a name no host was ever told. Schema-bound; `KIT0042` refuses a kit where no capability
  declares one, or more than one does. `kit/interpreters/space.py` is its one home.

**Changed**
- `test_90`/`test_100` asserted *the plane holds nothing, the same fact told by the filesystem*.
  That was true of a filesystem and false of a clone; they now assert the stronger claim — no page
  is projected, and the space still exists.

## 0.1.5 — unreleased

The host carries its kit (ADR-016, link B of ADR-015's line). Until now a host held doctrine pages
and no interpreter, and was driven from outside by a framework checkout.

**Added**
- **The pinned kit.** `governance` installs the WHOLE kit — every path its lock enumerates,
  verbatim, beside the lock — at `.agents/kit/pinned/` (install mode `pinned`, steward `release`). A
  host runs `python .agents/kit/pinned/interpreters/cli.py <verb> --root .` with no framework on the
  machine. The tree is staged and swapped in by rename (`Workspace.write_tree`).
- **What a release is.** A kit whose bytes equal its own lock; identity = SHA-256 of that lock. A
  working tree pins as `X.Y.Z+unreleased`. `release` states the identity — and `authenticity NOT
  ESTABLISHED`, because the lock is not signed — or refuses a working tree.
- **`--kit git+<repo>@<rev>#subdirectory=<dir>`**: a release read at a revision, never a working tree.
- Gate `FF-KIT-PINNED`; diagnostic `KIT0041`; every run's first line names the kit that spoke.

**Not recorded:** 0.1.3 and 0.1.4 shipped without a section here. The absence is declared, not
reconstructed.

## 0.1.2 — unreleased

Host choice, and the one door where a human stands. Until now a `capabilities` field existed that
no interpreter read as a CHOICE, so composition was proved as a property of DECLARATIONS and never
of a host's decision — and the interesting failures live exactly there.

**Added**
- **Selection.** `--enable` / `--disable` author the answers file *before it exists*; afterwards
  `.agents/project/project.json` IS the set and a flag that contradicts it is refused. `select` is
  a pure function beside `classify` and `compose`: it refuses an id no capability declares, and it
  reads `never_disabled` — which now decides something instead of describing an intention.
- **`--plan`**, a flag on every verb declaring `MUTATES`, never a sixth verb. It prints path,
  class, mode, owning capability and whether each path would be created, kept, replaced or
  removed, and exits without touching a byte. It is not a preview: each install mode has a
  FORESEE half and an APPLY half, and the apply is handed the foreseen disposition. A plan cannot
  drift from its apply because there is only one decision.
- **P3, the human door.** `init` measures, resolves and DRAFTS; nothing else is written until an
  owner approves with `--approve <who>`, recorded as `signed_by` / `signed_at`. An install whose
  approval never came is a dated `draft` on disk with its own exit code (3), and every verb
  declaring `REQUIRES_APPROVED_HOST` refuses while it stands, naming the date.
- Verb-declared preconditions, read generically: the CLI still knows no verb's name.
- Acceptance grew from 27 to 31 assertions and was split into `harness.py` + three suites; the
  disposition vocabulary is now IMPORTED by the tests rather than restated in them.

**Changed**
- `enabled_capabilities` and `render` no longer hold the answers-file path as a constant: the path
  and its schema are found by asking the DECLARATIONS which install works in that mode.
- The blocked-provision clause is written where the block was decided, so a refusal says
  *cannot support* (a measured fact) or *chose to disable* (a decision), not merely *missing*.

**Fixed**
- Looking up the answers file refused before the composition refusal that explained why the
  declaration was missing — the slice-B failure shape, in a new layer. Zero installs in a mode is
  now refused only where the answer is needed; two is always refused.

## 0.1.1 — unreleased

The second capability, and therefore the first time composition is exercised rather than designed.

**Added**
- `resolver.py`: composition semantics as a pure function over declarations — no port, no state,
  no capability's name. `classify` measures and never refuses; `compose` refuses and never
  measures. `requires` of kind `capability` is matched against what capabilities **provide**;
  ordering is topological with a sorted frontier, so it cannot depend on declaration order;
  `conflicts` and shadowed install paths are refused before the first byte.
- `capabilities/knowledge/`: a document's KIND decides whether it may declare a rule. Diátaxis
  crossed with MADR (canonical `docs/decisions/`, adopted rather than invented) and the Kind Law.
- Gate kind `title-claim-within-authority` (`FF-KIND-AUTHORITY`): compares a name's CLAIM with a
  location's GRANT, both arriving as declaration data. It reads no content, because authority
  was never a property of prose.
- Eight composition assertions, each negative case built from a throwaway copy of the real kit
  with its declarations patched — no real capability was deformed to manufacture a failure.

**Changed**
- `init` reports the reading and every unavailable capability BEFORE the set is composed. Adding
  capability-level requirements had made the refusal fire first, so the honest report of a
  measured absence — slice A's `unavailable governance` — was swallowed by its own consequence.
  The assertion that caught it was right; the design was wrong, and the design moved.

## 0.1.0 — unreleased

The walking skeleton: one capability, three verbs, four ports, and an acceptance test that
installs into a repository the kit has never met.

**Added**
- `MANIFEST.json` declaring four classes, four planes, one capability, three detectors and the
  schema registry; schemas for manifest, capability, project, profile and detector.
- Ports: `Manifest` (the only reader of declarations, validating each as it reads),
  `Workspace` (root measured once, writes confined to a declared scope), `Probe` (the single
  generic detector evaluator, with an open registry of evidence kinds), `Clock` (so a reading can
  state when it was taken).
- Verbs `init`, `render`, `check`, discovered by name from `interpreters/verbs/`.
- `template.py`: a Mustache subset, so the projection renderer needs no dependency and cannot
  branch.
- Gates `FF-BINDING-SCHEMA-*`, `FF-KIT-CLASS`, `FF-KIT-PROJECTION`, `FF-READING-FRESH`, declared by
  the capability and interpreted by kind.
- `tests/acceptance/fresh-repo/`: eleven assertions against a scratch git repository.

**Fixed, in the half that existed before anything had ever been run**
- `capabilities/governance/payload/INDEX.md.mustache` was Handlebars (`{{#each}}` / `{{this.x}}`)
  under a Mustache name. Rewritten as Mustache; the renderer refuses the syntax that was there.
- Detector declarations had no schema and were therefore the only unvalidated declarations in the
  kit. Added `schemas/detector.schema.json` and registered it in the manifest.
- A malformed host binding surfaced as a Python traceback instead of a named refusal. Added
  `errors.KitError`, read every binding through its schema, and gave the entry point one line and
  a non-zero exit.
- The console was assumed to be UTF-8 and was not; the kit now measures and sets that boundary
  before it prints.

**Deliberately not built** — `upgrade`, `eject`, `kit.lock.json`, roles, playbooks, runtime
descriptors, and adoption of a non-empty repository.
