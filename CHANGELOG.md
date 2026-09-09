# Changelog

Upstream only. This file is never vendored into a host: an append-only release record grows with
the framework's age rather than the host's needs. A host's legitimate question is narrower — *what
changed between the version I have and the version I am moving to* — and it is answered at the
moment of need by `upgrade`, which is not built yet.

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
