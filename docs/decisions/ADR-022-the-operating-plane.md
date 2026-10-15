---
kind: decision
authority: canonical
owns: operating-plane
---

# ADR-022 — The operating plane: how work moves between minds, priced, grounded and proven

- **Status:** Accepted (2026-10-15; owner-delegated under ADR-015 amendment 5). The owner's instruction:
  *"study the old architecture (national-accounts `.agents`, above all CORE; `work/` the management
  system; `ops/` later, for the stack kit) to its depth, see the invisible threads, and take from it
  whatever makes the kit a professional framework of modern AI engineering."*
- **Builds on:** ADR-004 (what the payload distributes — the T2 measure used throughout), ADR-006 (stance),
  ADR-011/012 (a prior system is triaged, never relocated), ADR-017 (the dispatch port), ADR-019 (the
  corpus plane and its budget ratchet), ADR-020 (the management spine), ADR-021 (the tree is the drawing).
- **Sources, all read in full on 2026-10-15:** `national-accounts/.agents/core/` — `INDEX.md`, `README.md`,
  `CARDINALS.md`, `B.md`, `strategy/00,01,02,03,06,07,08,09,11,13,15`, the 19 `feedback/*.md`, the 17
  `commands/*.md`, `skills/architecture-standards/SKILL.md`, every `tools/*.py` and `hooks/*.py` docstring,
  `hooks/hooks.map.json`; `.agents/system/{project.json, doctrine/authority.json, runtimes/}`;
  `.agents/knowledge/{shared/INDEX.md, shared/handoff.template.md, private/*/MEMORY.md}`;
  `.agents/runtime/telemetry/{token-log.md, route-decisions.jsonl}`; `work/{PROCESS.md, BOARD.md,
  CONTINUE-HERE.md, AUTONOMOUS-LEDGER.md, board/, items/0147}`; `docs/architecture/{GUARDRAILS.md,
  CANON-LEDGER.md, ARCHITECTURE-REGISTRY.md}`; `ops/{RUNBOOK.md, cli/, compose/catalog.json, config/}`.

## What was measured

The prior system is not a draft of this kit; it is the **field trial** the kit was distilled from. Over
two months it ran ~140 cards, two runtimes on one tree, and an owner who stepped away for days at a time,
and every one of its mechanisms carries a dated incident that produced it. The kit has already absorbed
its governance half — authority by kind (ADR-019 ← `authority.json`), neutral wiring (`runtime-surface`
`hands` ← `hooks.map.json`), receipts (observability ← `_receipt.py`), the board as a projection
(delivery ← `11-work-board`), the capsule and its one writer (ADR-020 ← `capsule.py`), the prior-system
triage (ADR-011/012).

**What it has not absorbed is the half that made the prior system work as a team: how work moves between
minds.** A packet with a named terminating artifact; a route chosen on two axes instead of a feeling; a
ground that states the instrument it came from and expires with its own evidence; a return that reports
its economy, its findings and whether the brief was any good; a capability believed only once a receipt
proves it; a claim that bites when two principals share a tree; a gate that has been seen red before it
is trusted, and is deleted when it never fires. In the kit today these are either *pending C* rows
(`runtime/ground`, `runtime/telemetry`, `runtime/guards`, `generated/skills`), a thin dispatch packet
(`route`, `instruction`, `branch`, `role`), or nothing.

The measure that sorts each concept into its home is ADR-004's, unchanged: **can this sentence become
false without the kit changing?** If not, it is a MECHANISM and its grammar ships here. If yes, it is
CONDUCT and it ships in a bundle a host may take (ADR-021 decision 2).

## The register — every concept of the prior system, and where it now lives

`present` = the kit already holds it · `decided here` = built by a slice below · `conduct` = published in a
bundle, never in `kit/` · `host` = the host's own declaration or knowledge · `refused` = with the reason.

| Prior concept (source) | Home | Note |
|---|---|---|
| Authority classes IDENTITY/BINDING/CAPABILITY/STATUS (`authority.json`) | present | ADR-019 kinds and authority |
| Neutral events × tool classes, declared gap per runtime (`hooks.map.json`) | present, **extended** (S6) | `hands` covers the write class; `exec` and session events are not served yet |
| Receipt on every exit path (`_receipt.py`) | present | observability `run-disposition` |
| Board as projection; status in the card; reject with a reason (`11`) | present | delivery |
| Capsule: CAS writer, ceiling, per-runtime journal (`capsule.py`) | present | ADR-020; eviction keeps the before-image |
| Render one source / `--check` drift (`render.py`) · doctor (`doctor.py`) | present | `render`, `check` |
| Prior system migrated, never relocated (`upgrade.md`, archive) | present | ADR-011/012, `takeover` |
| **Packet** MISSION · GROUND · BOUNDARIES · RETURN · BUDGET + terminating ARTIFACT (`06` §2,§5,§6) | **decided here** (S1) | the dispatch packet grows these fields |
| **Route on D × R**, proof depth from R, verification profile by name (`06` §4, `route.py`) | **decided here** (S1) | the host declares the table; the kit ships the grammar |
| **Return packet**: artifact, ECONOMY line, findings, brief-quality, growth note, refusal (`06` §3, `03`, `13`, `01`) | **decided here** (S1) | one schema, read by the port at completion |
| **Spawn gate**: an incomplete or oversize packet is refused (`context-budget-gate.py`) | **decided here** (S1) | a gate kind over the packet, at the port |
| **Ground ledger**: fact + instrument + paths, expires with its own evidence (`ground.py`, `06` §8) | **decided here** (S2) | through `ports/vcs.py` (ADR-021) |
| **Telemetry** stream; the four numbers; CTX-BURN alarm (`06` §7, `session-end-tokenlog.py`) | **decided here** (S3) | OpenTelemetry GenAI conventions; measures budgeted by the corpus ratchet |
| **Sunset sensor**: a mechanism with no firing is named for deletion (`06` §8, `gate-firings.log`) | **decided here** (S3) | named, never deleted by a machine (hygiene is a sensor, not a broom) |
| **Attestation**: a runtime's capability is DERIVED from receipts, never declared (`attest.py`) | **decided here** (S4) | declared-unproven is a printed gap |
| **Claims that bite** + receipt-backed optimistic concurrency (`_claimguard.py`, `_arbitration.py`) | **decided here** (S5) | the judge refuses a write under another principal's live claim |
| **Gate posture** blocking/advisory; undeclared fails closed; crash follows posture (`08`) | **decided here** (S6) | Saltzer–Schroeder fail-safe defaults |
| **Bite-proof**: a gate ships only after it was seen red; guard-of-guards self-test (`02` Gate-2, `GUARDRAILS` R2) | **decided here** (S6) | generalises the specimen/lookalike calibration hygiene and boundary already carry |
| **Four rings** Prevention · Detection · Containment · Recovery, honest gaps (`GUARDRAILS.md`) | **decided here** (S6) | a projection of the gates' declared ring — never a hand-kept page |
| **Destructive-exec guard** with a recovery point (`pre-bash-guard.py`, `_worktree.py`) | **decided here** (S6) | the `exec` hand class |
| **Session events**: start injects the capsule locator, stop gates it (`session-start.py`, `continuity-gate.py`) | **decided here** (S6) | served settings for the session hands |
| **Registers** beside the cards: findings (triaged), vision registry, standards ledger with GAP (`01`, leadership, `CANON-LEDGER`, `ARCHITECTURE-REGISTRY`) | **decided here** (S7) | one collection grammar, N collections — never a second board |
| **Handoff** with its measurement point (`measured_at_head`, `tree_state`) (`handoff.template.md`) | **decided here** (S7) | a record kind of the shared knowledge plane |
| Knowledge planes `private/<role>`, `shared` with an admission rule (`INDEX.md`) | **decided here** (S7) | the host floor's `knowledge/` rows, pending E, are built |
| Growth ladder, DEF-DELTA proposed, never self-applied (`13`) | present in part, **completed** (S1, S7) | link G exports a twice-seen lesson; the growth note becomes a return field and a role-overlay proposal |
| Class-M surfaces → the risk protocol first (`01`, `09` §B, `class_m_triggers`) | **decided here** (S6) | an edit gate with posture `remind`, naming a door |
| Bloat ceilings, memory guard (`hygiene.bloat_limits`, `memory_guard`) | **decided here** (S3) | a size measure per KIND under the corpus ratchet, never a number in the kit |
| Mediator A–E, verbatim directive, amplify vs distort (`01`) | conduct | `bundles/conduct` chapter *protocol* |
| Authority vs orchestration, principled refusal, depth = 1 (`01`) | conduct + mechanism | the refusal's SHAPE is a return field (S1); who may overrule is conduct |
| Mission command and the four freedoms (`feedback_lead_logistics` §6, leadership) | conduct | chapter *protocol* |
| Economy price list, done = artifact, loadout, greedy rule (`06`, logistics) | conduct + mechanism | the artifact and the budget are packet fields (S1); the prices are conduct |
| Risk §A parallel spawn, §B degradation, erosion vectors (`09`) | conduct + mechanism | the §A collision check is the port's write-set map (S1); the questions are conduct |
| Delivery gates (WIP = 1, parity pre-gate, gesture DoD, felt sweep, side-by-side) | conduct | chapter *delivery* |
| Verification doctrine; instrument matrix; evidence rules (pipe exit, denominator, mutation-control) | conduct + mechanism | the denominator and the bite-proof are mechanisms (S6); choosing the instrument is conduct |
| Construction over convention; Generality Law; architecture craft; leadership doctrine | conduct | the cardinals already state III, II, I; the chapters carry the applications |
| Journeys and playbooks; the architecture-standards skill catalog (`11`, `commands/`, `skills/`) | conduct, genre `skill`/`playbook` | the pending-C rows: bundle genres with progressive disclosure (catalog preloaded, chapters on demand) |
| Learning notes for the owner's education (`07`) | host | a host's own practice; not every host has a learner |
| Tier names apex/senior/middle/junior and model mapping at the edge (`00`) | present in form | archetypes + runtime classes; tier is a host vocabulary in the routing table (S1) |
| Windows, PowerShell and worktree pitfalls (feedback) | host | knowledge of one machine |
| `ops/`: validate-local stages with value anchors, structure-only migrations vs seed, secrets the human supplies, compose catalog | **stack-kit** | its proposals S1–S6 (ADR-0003 of the second host); out of this kit by its boundary |

## Decision

1. **The operating plane is a capability family, not a doctrine.** It ships grammars, ports, gate kinds
   and measures; it ships no price, no tier name, no threshold and no route — every number and every word
   a host would argue about is the host's declaration (ADR-001 point 4). A host that declares nothing
   gets the declared zero, stated as such, and `check` stays green.
2. **A packet names what ends the run.** The dispatch packet (ADR-017) gains `deliverable` (the one
   thing that will exist — named so because the port already provides `artifact` for the worker's
   answer file, and one word must not carry two referents), `ground[]` (each `{fact, instrument, paths?}` — a reading carries the instrument it
   came from, so the recipient can see whether it answers the question), `boundaries` (write set and
   one-way stops), `return` (the declared return shape), `budget` (`calls`, `peak`), and the two routing
   facts `decision_density` and `reversibility`. A packet without a `deliverable` is not dispatchable —
   the port refuses it before a worker starts. Requiring it is a breaking change, so the packet kind
   moves to version 2 (ADR-009); the kind is TRANSIENT — a caller hands it over and the task record
   carries it opaquely — so no host stores one and a version-1 packet is refused by `KIT0034` and
   re-authored, with no migration to declare. The **return** is one schema: the artifact's referent, an
   `economy` record (`calls`, `peak`, `not_read` with the reason), `findings[]` beyond scope, a
   `brief_quality` grade, an optional `growth` note `{lesson, evidence, ladder, delta?}`, and a `refusal`
   `{argument, alternatives[], escalate_to}` that is a complete answer, never a failure.
3. **The route is a declared table, not a judgement the kit makes.** A host declares, per
   `(decision_density, reversibility)` cell, the archetype or tier and the proof depth; a verification
   profile is a NAMED argv in the host's declaration and the port runs only a named one — no command
   text from a prompt ever executes. The kit ships the grammar, the port that reads it, and nothing in
   any cell.
4. **A ground is a reading with an expiry, not a fact.** The ground ledger stores `{key, fact, instrument,
   paths, digest}` where the digest folds the working-tree content of only the declared paths (through
   `ports/vcs.py`); a read is a HIT or a declared MISS that names what moved and hands back the
   instrument. It lives in the observed plane (`.agents/runtime/ground/`) — it is a cache, and a clone
   that has none is correct.
5. **What a run cost is measured, and only measured.** The telemetry stream is normalised to the
   OpenTelemetry GenAI semantic conventions (`gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`,
   operation and agent attributes), written by the served session hands into the observed plane. The
   measures are published by a gate module exactly as `served_span_bytes` is, so a host budgets them
   through the corpus ratchet it already has: `meta_ratio`, `calls_per_artifact`, `peak_context`,
   `input_output_ratio`. The **sunset** measure counts, per declared gate and per served hook, the
   firings in a window; one with none is NAMED as a deletion candidate. No machine deletes it — removal
   is a decision with an author (the hygiene stance).
6. **A capability is believed once it is proven.** A runtime's attested capability set is derived from
   receipts in a declared window — a receipt whose decision is a real verdict, from a hook implementing
   that capability, attributable to that runtime. Declared-but-unproven is printed as an UNPROVEN GAP;
   proven-but-undeclared is printed too. Routing may honour only the attested set. This is the in-toto
   attestation shape (a statement about a subject, by evidence), applied to the kit's own seams.
7. **Two principals on one tree are arbitrated by a claim that bites.** A claim `{principal, paths,
   reason, taken_at}` lives in the observed plane of the one working tree the principals share. It has
   NO time-to-live: ADR-007 holds that no amount of elapsed time breaks a hold, only a person by name,
   and a claim is a hold — so it stands until released or broken by name, the break recorded on it,
   and its age is printed with every refusal it causes; the one judge refuses a write under another principal's live
   claim, and a receipt of a peer's successful write to the same path inside a declared window refuses
   too — unless my own lease on that path predates it (optimistic concurrency, the etcd/HTTP `If-Match`
   form). The host lock (ADR-007) stays the hold on the HOST; this is the hold on a PATH, and it reuses
   `hostlock.take(..., registers=False)` rather than a second lease.
8. **A gate is trusted only after it bit, and it says how it fails.** Every gate kind declares a
   `posture` (`blocking` | `advisory`); an undeclared one fails closed; a blocking gate that crashes
   DENIES with its remedy, an advisory one degrades to silence with a stderr line (Saltzer–Schroeder,
   fail-safe defaults). Every gate kind ships calibration — one specimen it must flag, one lookalike it
   must admit — the form hygiene and the boundary already carry, generalised; a meta-gate fails the
   suite for a kind with no calibration or whose specimen does not go red. Every gate declares its
   `ring` (prevention · detection · containment · recovery) and the four-rings page is a projection of
   those declarations with the honest gaps — the rings no gate occupies — named.
9. **The session has hands too.** Runtime surfaces may serve the `exec` class (a destructive whole-tree
   command is met with a recovery point — `git stash create` — and a reminder, never a silent pass) and
   the session events (`start` injects the capsule locator and the routes; `stop` refuses a close whose
   capsule is invalid; `subagent_stop` writes the return into the port's record). A product that lacks an
   event prints a DECLARED GAP with its compensating control.
10. **One collection grammar holds every register.** Findings (triage: `fix-now · fold · debt ·
    owner-door`), the vision registry (`vision → designed → building → built → verified · deferred ·
    superseded · rejected`), the standards ledger (`adopted-whole · partial · not-built · non-goal ·
    unverified`, with `declared_at` — `—` is itself the finding — and the GAP register) are COLLECTIONS
    declared through delivery's existing collection-and-lifecycle grammar, generalised from one governed
    collection to N. A second board, a second lifecycle engine or a register kept in prose would be a
    fork (the unity axiom); a promotion out of a register is recorded at both ends.
11. **The conduct is published, not installed.** `bundles/conduct/` (pending F since ADR-021) is written
    from the prior system's chapters, each re-authored in no repository's vocabulary (ADR-011: re-declare,
    never pipe): *protocol* (intake echo, verbatim directive, mission command and its four freedoms,
    authority and principled refusal), *economy* (context is rent, done is an artifact, the greedy rule),
    *risk* (parallel-spawn and degradation checks, erosion vectors), *delivery* (the nine delivery gates),
    *verification* (ground truth over proxies, the instrument matrix), *craft* (construction over
    convention, the Generality Law, the highest applicable standard). Skills and playbooks become bundle
    genres with progressive disclosure: a catalog preloaded, a chapter on demand.

## Order of slices

| Slice | Lands | Proof |
|---|---|---|
| S1 | packet v2 (`deliverable`, `decision_density`, `reversibility`, `ground`, `boundaries`, `budget`, `profile`); `dispatch-return`; `route-table` and the `operating` capability that seeds an empty one; the port's route judgement, the carried return, the named profile run with its timeout; `minimum` in the schema subset | `test_routing` 360–364: a v1 packet refused by the reader rule; no cell declared is carried and said so; a packet off its cell, past its ceiling or naming an undeclared profile is refused before a worker starts; a failing profile closes the task by name; a return missing its economy closes it by name |
| S2 | `readings` module + `ground` verb + `ground-reading` kind (KIT0069 refused, KIT0070 declared miss, exit 4); a packet's ground row may cite a ledger `key`, checked at acceptance; verbs declare their own `ARGUMENTS`, merged by the entry point | `test_ground` 370–373 and `test_routing` 365: a fact expires with its own paths and only those; a MISS names what moved and returns the instrument; an ignored file never moves a reading; a packet citing a moved ground is refused before a worker starts |
| S3 | measures `peak_context` and `calls_per_delivery`, read from the returns S1 records (gate module `economy`) | `test_routing` 366: a host budget below the reported peak fails `check`; no return is `None`, never 0 |
| S3b | the telemetry stream from the served session hands, in OpenTelemetry GenAI attributes; `meta_ratio`, `input_output_ratio` | named and NOT built: reading usage out of a product's transcript is a claim about that product until an adapter declares where it lives and a run proves it — the measures it feeds wait for that declaration |
| S4 | `runtime-observation` records in the observed plane, written by the interpreter on an event it PROVIDES (`attestation.EVENTS`); the class vocabulary names the event each capability is observed on (`observed_on`); the runtimes composition reads them as its `proven` source; the judge's refusal is the first event (`write-scope`) | `test_attestation` 380–382: a claim stays claimed until a refusal through that runtime proves it, then the runtime's page reads PROVEN; an admitted write proves nothing and leaves nothing; the capability is found by its event and never spelled. NOT built here, named: routing on the attested set, and events for the other capabilities (each needs an interpreter that provides its event) |
| S5 | module `claims`, verb `claim` (take, list, `--release`, break by name), kinds `claim` and `arbitration` (the window, seeded 0 = off), KIT0071; the judge refuses a path under another principal's standing claim or written by a peer inside the window unless my later claim supersedes it, and records each admitted write per principal | `test_claims` 390–394 |
| S6 | a crashing gate kind FAILS under its own stance and `check` judges every other gate; `CALIBRATIONS` beside `KINDS` (specimen it must flag, lookalike it must admit), the unit meta-gate holding each, and the measure `uncalibrated_gate_kinds` a host budgets so the count only falls; first calibrations: `schema-valid`, `path-class-total` | `test_gate_calibration` (unit) and `test_gate_crash` 398 |
| S6b | `exec` and session hands; the four-rings projection; the sunset reading of calibrated, quiet gates | named and NOT built: the rings belong to MECHANISMS (the judge, scoped writes, verified moves), which declare no ring yet, and a page drawn from gates alone would show almost only detection and read as a gap that is not there |
| S7 | N collections; findings, vision registry, standards ledger; handoff record; knowledge planes | a register is a collection with its own lifecycle and no second engine; a promotion missing its far end fails |
| S8 | `bundles/conduct` chapters; skill and playbook genres | taken by a fresh host, its roll names every chapter UNANSWERED; a skill's catalog loads alone |

Each slice is one card on the kit's own board and lands with its acceptance test, its CHANGELOG entry and
a re-taken lock, as ADR-021's did.

## The standards it stands on

OpenTelemetry Semantic Conventions for GenAI (telemetry) · in-toto / SLSA attestation (capability by
evidence) · Saltzer & Schroeder 1975, fail-safe defaults and complete mediation (posture) · optimistic
concurrency with version tokens, etcd leases, HTTP `If-Match` (claims) · Evolutionary Architecture fitness
functions and ArchUnit-style calibration (bite-proof) · defence in depth (rings) · Auftragstaktik /
mission command (the four freedoms, as conduct) · Kanban WIP limits and Shape Up appetite and betting
(already in delivery) · A2A task states (already in the dispatch port) · progressive disclosure of
context (skills) · ADR (Nygard/MADR) and Diátaxis-style document kinds (already in the corpus plane).

## Rejected alternatives

- **Copy `.agents/core` into the kit.** It names its own repository, its tiers, its numbers and its owner on
  nearly every page; installing it would install one host's opinions in every host (ADR-004) and would be
  the relocation ADR-011 forbids.
- **Ship the prior system's numbers as defaults** (`≤1:4` meta ratio, `≤45` calls, `p90 ≤90k`, `WIP ≤2`,
  `window 15 min`). A default is an opinion nobody asked for; each is a host's budget row, and the kit
  ships the measure.
- **Encode routing as a kit policy** (apex for high-D/expensive-R). The two axes are a mechanism; the
  answer in each cell is the host's — two hosts with two teams route differently and both are right.
- **One telemetry schema of our own.** OpenTelemetry's GenAI conventions exist and are what every
  observability backend reads; a private schema would be a fork of a standard.
- **Delete a dormant gate automatically.** The sunset rule's purpose is to put a decision in front of an
  author; a machine that removed a guard would be the author, and a guard that fires rarely may be the
  one that matters most.
- **A second board for findings and visions.** Two engines for one grammar is the fork the unity axiom
  names; the registers are collections of the one delivery grammar.
- **Leave the operating plane as conduct.** The prior system learned the opposite at cost: *doctrine you
  might recall is not a gate*. Every part above that a machine can hold is held by a machine; only the
  judgement stays in prose.

## Amendment 1 — what S3 measured on the way in (2026-10-15)

Building S3 measured two things the decision text assumed. **(a)** The corpus ratchet hands every measure
the gate's params, never the budget row — so a ceiling *per document kind* (the bloat ceiling as a
property of the kind, which the prior system's capsule recommended) needs a budget row that names its
subject. That is a grammar change of the corpus map and is recorded here as owed, not improvised.
**(b)** The SUNSET measure only means something for a gate already proven to bite: "this gate never
fired" reads the same for a guard with nothing to catch and a guard that cannot catch anything. It
therefore moves to S6, behind the calibration meta-gate, where *quiet and calibrated* is a real reading.
S3 ships the two economy measures a host can take today from the returns S1 records, and S3b names the
transcript telemetry it does not yet build.

## Amendment 2 — posture already had a home (2026-10-15, found building S6)

Decision 8 asked every gate kind to declare a `posture` (blocking | advisory). The kit already decides
exactly that per gate, with its author and its moment: the gate's STANCE (ADR-006) says whether a failure
fails `check`. A second field would be a second home for one decision (Cardinal III), so none is added.
What was missing was the CRASH: a kind that raised took `check` down whole. It now fails under its own
stance — the fail-safe default — and every other gate is still judged.
