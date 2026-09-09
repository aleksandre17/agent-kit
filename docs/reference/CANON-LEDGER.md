# Canon Ledger — met concepts and declared gaps

> **Kind: REPORT.** This register records what the work MET, in the session it was met.
> It declares nothing binding on its own; a row becomes law only by restatement in an ADR.
> It grows in two directions: **upward** (a concept rising to its home) and **inward**
> (a question the design could not answer, declared *before* it is improvised around).
> A register whose rows never leave it has become a graveyard.

## Gaps — questions the design could not answer

Declared at the moment they were met. An improvised answer is allowed; an improvised answer
that leaves no trace is not.

| Gap | Met | Status |
|---|---|---|
| **An uninstalled host has no declared state.** The design has vocabulary for an *unavailable capability* and none for *"the kit is not installed here"* — only an absence. `init` exits non-zero and names the unmet fact, so the surface does not lie; but `check` afterwards reports the missing `project.json` rather than the unmet requirement that caused it, so the *second* reading names a symptom where the first named the cause. | 2026-09-09, slice A, `test_10` | OPEN |
| **`project.schema.json` requires `capabilities` with `minItems: 1`**, structurally forbidding a host that legitimately enables none. The schema encodes an optimism the mechanism does not require. Changing a BINDING schema was out of slice. | 2026-09-09, slice A | OPEN |
| **When has an interpreter's vocabulary become a privileged name?** The install modes (`seed` · `reading` · `declaration`) carry no proper noun and are generic — yet they are the closest thing to policy inside the interpreter, and Cardinal IV offers no test for the boundary. The proper-noun grep passes; the question it answers is narrower than the question that matters. | 2026-09-09, slice A | OPEN |
| **The kit does not ship itself.** `.agents/kit/` receives only what a capability declares, so `__pycache__` appeared *inside the payload* the first time the kit ran — the unclassed-state condition the layout proposal diagnoses, reproduced by the kit against itself. The declared cure is manifest-enumerated shipping via `kit.lock.json`, out of slice A. Fenced with `.gitignore` and named here rather than smuggled in early. | 2026-09-09, slice A | OPEN — cure named, deferred |
| **Schemas cannot compose.** `validation.py` implements no `$ref`, so no schema may reference another. Adequate for every schema in the kit today; it will bite at `role.schema.json`, where a role composes an archetype. | 2026-09-09, slice A | OPEN — dated trigger |
| **A capability may install outside every declared plane, and nothing classes it.** `knowledge` installs into `docs/`, which is MADR's canonical home and correctly NOT `.agents/`. Its files get a class from their exact target declarations, but `FF-KIT-CLASS` walks `.agents` only, so under `docs/` there is no totality: a stray file there resolves to no class and no gate says so. Extending class-totality to `docs/` was refused deliberately — it would forbid the host from keeping any document the kit did not declare, which is not the kit's business. The real question the design cannot answer: **what is the class of a path the framework writes into but does not own?** | 2026-09-09, slice B | OPEN |
| **"Append-only, immutable once accepted" is doctrine with no gate.** `docs/decisions/` declares, and an accepted ADR is supposed to be superseded rather than edited. Nothing measures that: the kit sees one filesystem state and has no history, so an edited decision is indistinguishable from one that always said this. Any cure needs a recorded prior reading (content digests in a lockfile, or git history read through a port) — both deferred with `kit.lock.json`. Until then the rule binds humans and no machine, and the ledger says so rather than the ADR implying otherwise. | 2026-09-09, slice B | OPEN — cure named, deferred |
| **`never_disabled` is a declaration nobody reads.** `MANIFEST.json` marks `governance` as never disabled; no interpreter consults the flag, because there is no selection mechanism for it to constrain — a capability is enabled iff its requirements are met. The flag anticipates a host CHOOSING its set, which does not exist yet. A declared field with no projection is exactly the drift Cardinal III warns about, only pre-emptive: it reads as enforced. Either a selection mechanism arrives and reads it, or the field goes. | 2026-09-09, slice B | OPEN — decide at selection |
| **Composition is proved for a set the KIT declares, never for one a HOST chose.** Every composition case in slice B is built by patching a fixture manifest, because a host cannot yet enable or disable anything. `requires`, `provides`, `conflicts`, ordering and shadowing are therefore proved as properties of *declarations*, not of *host choice* — and the difference is where the interesting failures live (a host disabling a capability something else needs). | 2026-09-09, slice B | OPEN |

## Canon met — status per Law 13

| Concept | Status | Note |
|---|---|---|
| **Mustache (logic-less templating)** | *adopted as a NAMED SUBSET* | Sections, inverted sections, dotted paths, standalone-line stripping. Refuses partials, lambdas, `{{{ }}}`. **Deviation named:** a missing key RAISES rather than rendering empty — the projection plane may not lie (Cardinal V). This refusal is what exposed a `.mustache` file that was actually Handlebars. |
| **Ports & Adapters** | *adopted whole* | `Manifest · Workspace · Probe · Clock` at the verb boundary. |
| **Capability-declared write scope** (least privilege / object-capability) | *newly met, adopted* | A capability's `installs` list is simultaneously its manifest AND its permission set. A second home for that truth is impossible because it is one list. This is our addition beyond the ports pattern. |
| **JSON Schema** | *partial, missing part NAMED* | No `$ref`, no combinators. Unsupported keywords are refused loudly rather than ignored — a validator that silently skips what it cannot check is worse than none. |
| **Debian conffile / copier answers-file** (create-once host truth) | *adopted in part* | Realised as the `seed` / `reading` / `declaration` install modes. The lockfile half is proposed, not built. |
| **Git end-of-line normalisation as a measured boundary** | *adopted* | The kit asserts `render` is byte-reproducible; the first commit emitted 26 LF→CRLF rewrites. Both git and the renderer behaved correctly and the guarantee was false outside this machine — while still reading as true from inside, because the local test passed. `.gitattributes` pins LF everywhere. **Cardinal VII, found in this repository's own first commit.** |
| **FF-KIT-SECOND-HOST** | *built and GREEN* | The framework's central claim — that it is portable — is now measured rather than asserted. Eleven assertions against a scratch repository it has never met. |
| **Diátaxis × MADR × the Kind Law** | *adopted, crossed* | Diátaxis says what a document is FOR; MADR says how a decision is RECORDED (canonical `docs/decisions/`, adopted rather than invented); the Kind Law says what a LOCATION may grant. The cross is the capability: authority is a property of location, never of prose, so the gate reads a name and a path and never a word of content. |
| **Dependency resolution (topological, total order)** | *adopted whole* | Kahn with a sorted frontier: dependencies first, ties by id, result independent of declaration order — asserted by reversing the manifest and demanding the same emitted order. |
| **Provision over identity (substitutability)** | *newly met, adopted* | A `requires` of kind `capability` matches what capabilities **provide**, never their ids; a capability's own id is not an implicit provision, because a name is not a contract. Measured both ways: renaming the provision breaks the requirer, renaming it on both sides installs cleanly. |
| **Shadowed path = defect, not precedence** | *newly met, adopted* | Two capabilities installing to one path is refused before the first byte, naming both owners. There is no last-writer-wins and there must never be one: the loser's declaration would go on reading as true while the bytes came from elsewhere — both locally correct (Cardinal III). |
| **Measurement is reported before composition refuses** | *earned in slice B* | Adding a capability-level requirement silently swallowed slice A's honest `unavailable governance` report: the refusal fired first and named the consequence. The cure was structural, not a weakened assertion — `classify` (measures, never refuses) is separated from `compose` (refuses, never measures), and the caller reports between them. **The general rule: when a new layer of judgement is added above an existing one, the existing one's report must still reach the surface first — a cause that arrives after its consequence is not a report, it is a correction nobody asked for.** |

## Rule earned here, stated without the vocabulary of its case

> **Half-built state is not partial success; it is unverified state.** A run that dies mid-way
> leaves artifacts that read exactly like finished ones. Six defects sat in the half of slice A
> written by a mind that never got to execute anything — including a template in the wrong
> language and a declaration class nobody validated. The cure is not vigilance: it is that
> nothing counts as built until it has been RUN, and that the first green is never trusted
> without an adversarial probe designed to make it fail.
