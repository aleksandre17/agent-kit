# Changelog

Upstream only. This file is never vendored into a host: an append-only release record grows with
the framework's age rather than the host's needs. A host's legitimate question is narrower — *what
changed between the version I have and the version I am moving to* — and it is answered at the
moment of need by `upgrade`, which is not built yet.

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
