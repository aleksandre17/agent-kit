# Agent framework — installed surface

> PROJECTION. Do not edit: delete this whole plane and run `render`, and it comes back byte-identical.
> Kit version 0.2.0 · project status accepted.

## Capabilities installed here

### delivery 0.2.0

Declares the task lifecycle as data: cards are BINDING and carry exactly one state, the board is a PROJECTION of them, the owner's acceptance is a declared door no machine may open, and capacity and staleness are limits the host declares. It requires no provision, and the emptiness is deliberate: everything it reads -- its lifecycle, its policy, its cards -- it declares itself, and a capability that listed a dependency it never consumes would be promising a coupling nobody keeps. That the kit cannot stand without governance is the KIT's statement, made once on the manifest entry as never_disabled; restating it here would be a second home for it.

| path | class | mode |
| --- | --- | --- |
| `.agents/project/delivery/policy.json` | binding | seed |
| `.agents/project/delivery/areas.json` | binding | seed |
| `docs/work/cards/` | binding | space |
| `docs/work/evidence/` | binding | space |
| `docs/work/archive/` | binding | space |
| `docs/work/BOARD.md` | projection | projection |

Gates declared by this capability:

- **FF-DELIVERY-WIP** — `capacity-within-limit`
- **FF-DELIVERY-AGE** — `state-age-within-limit`
- **FF-DELIVERY-LINEAGE** — `lineage-resolves`
- **FF-WORK-CLASSES** — `work-classes-held`
- **FF-WORK-DEFERRALS** — `deferrals-held`
- **FF-WORK-ORDER** — `order-held`
- **FF-WORK-EMERGENCY** — `emergencies-repaid`
- **FF-WORK-CEREMONY** — `ceremony-reported`
- **FF-DELIVERY-APPETITE** — `appetite-within-limit`
- **FF-DELIVERY-RESTATED** — `section-restating-a-record`

### evaluation 0.1.0

Declares the GRAMMAR of judgement and never a judgement. A run's receipt proves that it fired; this is the other half -- whether it HIT -- and that question is domain, so the framework ships the shape of a rubric, the verb that evaluates, the schema of a quality receipt and the vocabulary of a verdict, while every case, every criterion and every threshold belongs to the host. What it therefore ships is a ZERO MEASURE: the declaration arrives with no rubric, no case and no judge in it, and the surface says so in those words. An evaluation page that reports nothing because nothing was declared reads exactly like one reporting that everything is fine, and this capability exists so that the two can never be confused. The blank is materialised rather than implied: a judgement is opened UNJUDGED the moment a case and a rubric are known to need each other, so `never judged` is a record that can be counted instead of an absence that cannot.

| path | class | mode |
| --- | --- | --- |
| `.agents/project/evaluation/evaluation.json` | binding | seed |
| `.agents/project/evaluation/readings.json` | binding | seed |
| `.agents/runtime/evaluation/judgements/` | ephemeral | space |
| `.agents/generated/evaluation/QUALITY.md` | projection | projection |
| `.agents/generated/evaluation/VERIFICATION.md` | projection | projection |
| `.agents/generated/evaluation/COMMANDS.md` | projection | projection |

Gates declared by this capability:

- **FF-VERIFICATION-MEASURABLE** — `consumed-fact-declared`
- **FF-QUALITY-JUDGEMENT** — `record-disposition`
- **FF-QUALITY-REFERENT** — `reference-declared`

### governance 0.2.0

Declares the four-class seam for a host: the reading, the declaration, the seeded law page, the pinned kit a host runs by itself with the lock it was given, and the index projection, plus the gates that hold them.

| path | class | mode |
| --- | --- | --- |
| `.agents/project/profile.json` | binding | reading |
| `.agents/project/project.json` | binding | declaration |
| `.agents/project/estate.json` | binding | estate |
| `.agents/project/allowed_signers` | binding | seed |
| `.agents/project/doctrine/law-scopes.json` | binding | seed |
| `.agents/project/doctrine/laws/` | binding | space |
| `.agents/project/position/` | binding | space |
| `.agents/.gitignore` | binding | seed |
| `.agents/.gitattributes` | binding | seed |
| `.agents/kit/` | vendor | pinned |
| `.agents/project/kit.lock.json` | binding | pinned-lock |
| `.agents/taken/` | vendor | taken |
| `.agents/project/taken.json` | binding | taken-declaration |
| `.agents/generated/governance/CAPABILITIES.md` | projection | projection |
| `.agents/project/succession/migration-map.json` | binding | seed |
| `.agents/generated/INDEX.md` | projection | projection |
| `.agents/project/extensions.json` | binding | seed |
| `.agents/project/conformance.json` | binding | seed |

Gates declared by this capability:

- **FF-BINDING-SCHEMA-PROJECT** — `schema-valid`
- **FF-BINDING-SCHEMA-PROFILE** — `schema-valid`
- **FF-KIT-CLASS** — `path-class-total`
- **FF-KIT-PROJECTION** — `projection-reproducible`
- **FF-READING-FRESH** — `reading-current`
- **FF-PROVENANCE-PINNED** — `provenance-pinned`
- **FF-PLANE-WRITER** — `plane-held-by-its-writer`
- **FF-KIT-PINNED** — `pinned-kit-intact`
- **FF-TAKEN-INTACT** — `taken-intact`
- **FF-HOST-FLOOR** — `layout-floor-present`
- **FF-RECORDS-DECLARED** — `reference-declared-across`
- **FF-POSITION-SHAPE** — `reference-declared-across`
- **FF-EXTENSIONS** — `extensions-held`
- **FF-CONFORMANCE** — `conformance-held`

### observability 0.1.0

Declares that a run leaves a RECEIPT: written the moment it begins, holding a status that means nothing has been concluded yet, and rewritten exactly once when the run reports its end. The order is the mechanism -- a receipt written only at the end proves nothing about a run that never reached the end, and a run killed mid-way leaves artifacts that read exactly like finished ones. It is the LIFE half of observation and only that half: it records that a run fired, never that it hit. Whether the work was any good is a domain question, it is asked of cases and rubrics a host owns, and this capability deliberately ships no opinion about it. It is a sensor and never a broom: a record naming a run that died is evidence, and evidence is not swept up by the thing being questioned.

| path | class | mode |
| --- | --- | --- |
| `.agents/project/observability/observation.json` | binding | seed |
| `.agents/runtime/receipts/` | ephemeral | space |
| `.agents/generated/observability/RUNS.md` | projection | projection |

Gates declared by this capability:

- **FF-RUN-RECEIPT** — `run-disposition`

### doctrine 0.1.0

Carries conduct doctrine and ships none of it. A sentence about how a host should work can only become false if the HOST changed, which is exactly the measure that says it is not this kit's to hold: a framework that shipped a starter cardinal set would be installing an opinion on behalf of a party nobody asked. So this capability ships the CARRIER -- the shape of a distributed cardinal, the shape of a host's answer to one, and the page where the two are read side by side -- and no cardinal whatsoever. Doctrine arrives, if a host wants any, as a BUNDLE: an ordinary capability with an id, a semver and an `installs`, resolved by the same resolver as everything else, with no privileged plane, no second install grammar and no condition language -- a chapter that applies only in some environments is a `requires` on a profile fact, which keeps the condition in the declaration where a host can read it. A host never edits what a bundle publishes; it declares a STANCE in its own plane, naming `bundle@semver#id` and one word of a declared vocabulary, which is a different proposition from the cardinal and therefore not a second home for it. And a host that has taken no doctrine at all projects a page that SAYS SO, in those words: the doctrine in force is none. That is a complete and legal state, `check` stays green on it, and it is written down because a page that simply ended would read exactly like a host whose doctrine failed to render.

| path | class | mode |
| --- | --- | --- |
| `.agents/project/doctrine/norms.json` | binding | seed |
| `.agents/project/doctrine/doctrine.json` | binding | seed |
| `.agents/generated/DOCTRINE.md` | projection | projection |
| `.agents/generated/LAWS.md` | projection | projection |

Gates declared by this capability:

- **FF-NORMS** — `norms-coherent`
- **FF-LAWS** — `laws-one-source`

### enforcement 0.1.0

Declares the ENFORCEMENT LINE: a host's own edit gates, judged at the moment an edit is made, from whichever runtime the host serves. The host declares the gates -- which paths, which introduced text, why, and what instead -- and the kit ships only their grammar and ONE judge (the `judge` verb), vendored in the pinned kit and run by the hook a runtime adapter serves. The judge holds no policy and knows no product: how a product hands a hook its edit, and how it is told no, is declared by that product's surface (ADR-013/014). Every gate is calibrated before it is believed; `check` fails an uncalibrated one, and the judge names it as unjudged rather than refusing on its word.

| path | class | mode |
| --- | --- | --- |
| `.agents/project/enforcement/edit-gates.json` | binding | seed |
| `.agents/project/enforcement/known-violations.json` | binding | seed |

Gates declared by this capability:

- **FF-EDIT-GATE** — `edit-gates-calibrated`
- **FF-MESSAGE-RULE** — `message-rules-calibrated`
- **FF-TREE-AUDIT** — `tree-audited`

### hygiene 0.1.0

Declares RESIDENCE: the genres of document that have no home in an installed surface, why each has none, and where each belongs instead. It is a sensor and never a broom -- it names a resident and stops, because removing something is a decision with an author, and a machine cannot be that author. Every genre ships its own calibration, one path it must see and one lookalike it must tolerate, so the sensor proves what it sees before anything is believed on its word. The kit's genres are shipped and versioned with the kit; the host may declare more of its own and may exempt nothing, since a gate that names a defect and then permits it has already stopped being a gate.

| path | class | mode |
| --- | --- | --- |
| `.agents/project/hygiene/residence.json` | binding | seed |
| `.agents/generated/hygiene/RESIDENCE.md` | projection | projection |

Gates declared by this capability:

- **FF-RESIDENCE** — `residence-declared`

### knowledge 0.1.0

Grants a host the ability to hold knowledge with DECLARED AUTHORITY: a document's KIND decides whether it may declare a rule at all, and the gate catches a title claiming an authority its location cannot grant.

| path | class | mode |
| --- | --- | --- |
| `docs/decisions/ADR-0001-a-documents-kind-decides-its-authority.md` | binding | seed |
| `docs/reference/README.md` | binding | seed |
| `.agents/project/corpus/` | binding | space |
| `.agents/generated/corpus/CATALOG.md` | projection | projection |
| `.agents/generated/corpus/ROUTES.md` | projection | projection |

Gates declared by this capability:

- **FF-KIND-AUTHORITY** — `title-claim-within-authority`
- **FF-CORPUS-VOCABULARY** — `reference-declared-across`
- **FF-CORPUS-DECLARED** — `artifact-classified`
- **FF-AUTHORITY-DECLARED** — `authority-declared`
- **FF-OBLIGATION-ROUTED** — `obligation-reachable`
- **FF-CORPUS-OWNED** — `owned-places-resolve`
- **FF-CORPUS-RATCHET** — `budget-ratchet`
- **FF-INDEX-COMPLETE** — `index-complete`

### roles 0.1.0

Declares that a role DEFINITION is a PROJECTION and never a document anybody writes. The defect it was built to make unreachable is not a duplicated file -- it is two files that are BOTH RIGHT: one role with two homes, each internally correct, drifting apart while every reader standing at either one sees no contradiction. So the kit ships ARCHETYPES, which say what is true of a role as a KIND wherever the discipline is practised, the host authors OVERLAYS, which say only what it legitimately says about its own instance, and the definition is composed from the two. The line is drawn by a test anyone can apply: can the sentence be written without naming a repository? If it can, it belongs to the archetype. The overlay schema closes itself to the archetype's vocabulary, so a host cannot restate a binding body even by accident -- the drift is not a discipline anyone is asked to keep, it is a state the schema cannot express. It ships zero of any host's content: no roster, no private knowledge, no answers. A host that has hired nobody projects a roll that SAYS SO, in those words, and an archetype nobody instanced is counted rather than omitted -- because a shipped role with no takers and a role that was never shipped read identically to anyone who is only shown what exists.

| path | class | mode |
| --- | --- | --- |
| `.agents/project/role-archetypes.json` | binding | seed |
| `.agents/project/roles/` | binding | space |
| `.agents/generated/ROLES.md` | projection | projection |
| `.agents/generated/roles/` | projection | projection |

Gates declared by this capability:

- **FF-ROLE-BASE** — `reference-declared-across`

### runtimes 0.3.0

Declares that a RUNTIME -- the tool a host actually executes its agents on -- is a declared subject rather than a thing each surface hand-writes its own version of. The kit ships CLASSES, which say what is true of a runtime as a KIND: how an agent reaches it at all, and which translation sits in the gap. The host authors DESCRIPTORS, which say only what a host legitimately says about its own tool. No vendor's name appears in a class or in the interpreter, because the name of a product is the one thing about a runtime guaranteed not to be true of the kind. Where a product LOOKS for its instructions is true of the product everywhere and of no kind and no host, so it is declared in exactly one place -- a SURFACE, the one declaration allowed to carry a product's name (ADR-013), which this kit ships the GRAMMAR of and never an instance: every surface arrives in an ADAPTER, an ordinary capability a host takes through the provenance door, and is found by the contract its document keeps rather than by a list of publishers (ADR-014) -- and a host SERVES a surface by naming it from its own descriptor: the files that product reads at its fixed paths are then projections of what the host already declared, rebuilt on every render and recorded in the projection plane before a byte is written outside it. The reason this exists as a capability at all is a failure that has already happened here: a runtime's capabilities were WRITTEN DOWN and believed, an invocation shape among them was never measured, and a peer runtime later reported all eight of its claimed capabilities as unproven -- correctly. So the grammar refuses to let a belief become a fact by being written confidently: a descriptor has no field a proof can be written in, the capability vocabulary is declared so that what a runtime does NOT claim has a name instead of being silence, and every surface places every declared capability in exactly one of CLAIMED, PROVEN and ABSENT. It ships no roster of runtimes: a host that runs none says so in those words.

| path | class | mode |
| --- | --- | --- |
| `.agents/project/briefing.json` | binding | seed |
| `.agents/project/mcp-servers.json` | binding | seed |
| `.agents/project/owners.json` | binding | seed |
| `.agents/project/skills.json` | binding | seed |
| `.agents/project/skills/` | binding | space |
| `.agents/project/runtime-classes.json` | binding | seed |
| `.agents/project/runtimes/` | binding | space |
| `.agents/generated/RUNTIMES.md` | projection | projection |
| `.agents/generated/runtimes/` | projection | projection |
| `.agents/generated/SERVED.json` | projection | projection |
| `.agents/runtime/observations/` | ephemeral | space |

Gates declared by this capability:

- **FF-RUNTIME-SURFACE** — `reference-declared-across`
- **FF-RUNTIME-CLASS** — `reference-declared-across`
- **FF-RUNTIME-CLAIM** — `reference-declared-across`
- **FF-RUNTIME-ACTIVE** — `served-setting-active`
- **FF-CONTEXT** — `context-held`

### claude-code 1.3.1

A runtime ADAPTER for Claude Code: the one published declaration that carries this product's name, and nothing else. It is an ORDINARY capability (ADR-004, ADR-014) -- a host takes it through the provenance door (ADR-008) exactly as it takes a doctrine bundle, and no interpreter in the kit knows that it exists. Its single document keeps the runtime-surface contract, which is how the kit's served projection finds it: by the contract, never by a list of publishers. Remove it and the host serves this product nothing -- and says so.

| path | class | mode |
| --- | --- | --- |

Gates declared by this capability:


### codex 1.3.1

A runtime ADAPTER for Codex: the one published declaration that carries this product's name, and nothing else. It is an ORDINARY capability (ADR-004, ADR-014) -- a host takes it through the provenance door (ADR-008) exactly as it takes a doctrine bundle, and no interpreter in the kit knows that it exists. Its single document keeps the runtime-surface contract, which is how the kit's served projection finds it: by the contract, never by a list of publishers. Remove it and the host serves this product nothing -- and says so.

| path | class | mode |
| --- | --- | --- |

Gates declared by this capability:


### fitness 0.1.0

Declares the ARROW: a host's layers and the direction a dependency between them may run, enforced generically (the ArchUnit layered-rule / import-linter contract form). The host declares the layers, the rules and how a dependency is read in each kind of file; the kit ships only the grammar and one interpreter, applied over the tree by `check` and over the text an edit introduces by the enforcement line's ONE judge -- no second judge. Every reading and every rule is calibrated before it is believed. The gate ships at the declared default stance like every other gate; a host that must loosen it signs a stance row.

| path | class | mode |
| --- | --- | --- |
| `.agents/project/fitness/arrow.json` | binding | seed |

Gates declared by this capability:

- **FF-ARROW** — `arrow-held`

### git 1.1.0

A runtime ADAPTER for git's commit hooks: the one published declaration that carries this product's name. Git is not an agent runtime, and that is the point -- it is the RETURN POINT every runtime, every tool and every human shares: whatever wrote a change, the change is recorded through a commit. Served, it projects a pre-commit hook that hands the STAGED change, as a patch, to the same one judge and the same host-declared edit gates a runtime's write hook uses; activated (the `activate` door sets the setting git reads), an edit made where no pre-write hook exists is still refused before it is recorded. It publishes a second declaration for the same reason: a worker dispatched to another intelligence writes only inside a tree of its own (ADR-017 decision 5), and WHICH program makes such a tree is a product fact -- so `workspaces.json` says how git makes and withdraws one, and the dispatch port names no program. An ordinary capability, taken through the provenance door like any adapter; no interpreter in the kit knows that it exists.

| path | class | mode |
| --- | --- | --- |

Gates declared by this capability:


### github-actions 1.1.0

A runtime ADAPTER for GitHub Actions: the one published declaration that carries this product's name. A CI runner is not an agent runtime, and that is the point -- it is the one RETURN POINT nobody at the keyboard can skip: `git commit --no-verify` bypasses every local hook by git's design, but a push or pull request is checked out and judged where no local flag reaches. Served, it projects one workflow file that runs the kit this host CARRIES -- never a fetched one -- as `check` over the tree and as the same one judge, over the pushed or proposed diff, that a runtime's write hook and the commit hook use. An ordinary capability, taken through the provenance door like any adapter; no interpreter in the kit knows that it exists.

| path | class | mode |
| --- | --- | --- |

Gates declared by this capability:


## Facts this install was adapted to

- `ci.workflows` = true
- `ci.workflows.files` = ['tests.yml']
- `vcs.git` = true
