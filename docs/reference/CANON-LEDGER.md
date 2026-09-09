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

## Rule earned here, stated without the vocabulary of its case

> **Half-built state is not partial success; it is unverified state.** A run that dies mid-way
> leaves artifacts that read exactly like finished ones. Six defects sat in the half of slice A
> written by a mind that never got to execute anything — including a template in the wrong
> language and a declaration class nobody validated. The cure is not vigilance: it is that
> nothing counts as built until it has been RUN, and that the first green is never trusted
> without an adversarial probe designed to make it fail.
