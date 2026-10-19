---
kind: decision
authority: canonical
owns: management-spine
---

# ADR-020 — The management spine: the card is the one home of work, and currency is never bought with the record

- **Status:** Accepted (2026-09-23; owner-delegated under ADR-015 amendment 5 — a design question
  inside the line is decided against one criterion and recorded with its rejected alternatives, not
  brought as a menu). **Design only.** Nothing below is built by this document.
- **Decides:** ADR-015 link **F**, the management spine: the continuity capsule promoted from host
  tooling into a kit capability; `evidence/<card>/` so `verified` has a referent; the card as the ONE
  home of work; appetite and the circuit breaker; expiry into the archive; and checklists whose status
  is COMPUTED, never typed.
- **Extends:** ADR-019 (the corpus plane) — this ADR declares cards, evidence and checklists THROUGH
  that plane and adds no second reader; it reuses ADR-019's `budget-monotonic` ratchet and its gate
  registry. ADR-006 (stance and maturation). ADR-001 point 4 (the kit ships the vocabulary, the host
  ships the number). ADR-017 keeps `REQUIRED_CONTEXT` on the dispatch packet; nothing here duplicates it.
- **Requires amending, and does NOT amend here** (an ADR that edits another ADR in passing is how a
  decision acquires clauses nobody can date): ADR-015's link **F** row and its amendment 10, and ADR-019's
  declared absences 1 and 4. Each is named exactly, with the wording it needs, in *What this requires
  amended elsewhere*.
- **Sources:** ADR-015 link F row and amendments 4, 6, 7, 8, 9, 10; ADR-019 decisions 8, 9, 10 and its
  absences 1, 3, 4; the live capsule writer and its section contract read from `--help` and from
  `prose_budget` / `budget_report`; `kit/capabilities/delivery/{capability,lifecycle}.json`;
  `kit/schemas/card.schema.json`; `kit/capabilities/governance/stances.json`. All readings dated in
  *Measured when*.

## The situation

The management spine exists in parts and each part is green. A capsule externalises position under a
compare-and-swap so two runtimes cannot silently overwrite one another. A lifecycle declares nine states
with the owner's door on `bet`. A board is a projection. A journal is append-only per runtime. Measured
against what the owner named as the failure — *work laid down, then never marked whether it was done;
mixed up, endless, lost* — the parts do not compose into a spine, and one of them actively destroys the
record it exists to protect.

**The failure that motivates this ADR was measured, not hypothesised.** On 2026-09-23, four writes were
attempted against the continuity capsule. **Three were refused** by the hot-prose ceiling — over by 403,
then 129, then 9 characters. Every refusal was correct: the ceiling is a real hygiene constraint and the
refusal even printed a per-section budget so the cut could be arithmetic instead of blind. And every cure
was the same act: **true, dated history was DELETED so that a newer truth could be recorded.** The
instrument's own remedy text says *"archive a colder section to the cold-history pointer first"* — and
the tool ships four verbs (`rev`, `get`, `set`, `claim`) and no mechanism to do it.

Read that for what it is. At capacity, the management spine **buys currency by destroying the record**,
and the destruction leaves **no trace at all**: the capsule after the write is internally perfect, the
validator passes, the journal records an accepted write, and nothing anywhere states that a paragraph of
dated history stopped existing. That is not a missing feature. It is the exact shape Cardinal V calls the
most dangerous lie — a system that reads as correct precisely where it lost something — and it is worse
than a crash, because a crash is noticed.

Three defects are structural rather than accidental, and each is a cardinal already in force, held only
by discipline:

- **One artifact holds two truths with opposite lifecycles.** POSITION (where the work stands now) is
  small, volatile, and read whole at every session start. RECORD (what happened, when, decided by whom)
  is append-only and grows without bound. They share one file and therefore one budget, so the only move
  a refusal leaves is deletion of the record (Cardinals III and VIII).
- **Three instruments describe the same work.** The capsule's *Active WIP*, *Exact next action*,
  *Evidence map* and *Open threads*; the board; and the roadmap all state work state, all authored by
  hand, all locally correct, and drifting from the day they were written (Cardinal III). ADR-015 link F
  already says the card is the one home of work. Nothing makes it so.
- **A checklist cannot be computed because the field does not exist.** Measured: `card.schema.json`
  carries eight properties with `additionalProperties: false` — no criteria, no proof, no evidence, no
  parent, no appetite. The owner's *"it was laid down, then never marked whether it was done"* is
  therefore not a discipline failure at all. There was nothing to mark, and a hand-ticked box would have
  been testimony rather than proof in any case (Cardinal V).

## Decision

### 1. POSITION and RECORD are different truths with opposite lifecycles, and one artifact may hold only one of them

A bounded artifact that holds the current position may hold **only** the current position. The record —
what was true earlier, and when — is append-only, unbounded, and lives elsewhere. This is not a size
policy; it is an identity. The instant a ceiling is placed over an artifact that carries both, the two
compete for one budget, and the system has been designed so that **currency is purchasable with the
record** — an exchange no one ever chose, made at the moment of most pressure, by whoever hit the limit.

The ceiling stays exactly where it is and is never relaxed (ADR-015 amendment 6: every call pays for
what the hot surface holds). The capsule remains ONE file. What changes is what it is allowed to contain:
position, and pointers into the record.

*Rejected — raise or remove the hot limit.* It converts the one artifact every session reads whole into a
second corpus, and pays for it on every call of every session forever. It also does not solve the problem:
a larger ceiling is reached later, by a session with more to lose.
*Rejected — a cold-history file the capsule points at (the remedy text's literal reading).* A document
whose only purpose is to receive what nothing reads is a graveyard, and ADR-015's link F row forbids
creating one in the same sentence that asks for expiry. Work prose already has a home — the card — and a
parallel prose drawer would be a second home for it (Cardinal III).

### 2. Nothing leaves the bounded artifact without being written down first: eviction is WRITE-AHEAD, and a removal with no landing is a counted, ratcheted state

Every accepted mutation of the capsule computes what it REMOVED, and the removed text — the text itself,
not a digest of it — is appended to the journal **before** the new capsule is written, in the same
transaction the writer already runs under its lock. A write whose journal append fails is refused. The
journal is the write-ahead log; the capsule is a materialized view of position over it.

Therefore **deletion becomes a MOVE by construction**, and the destructive act measured tonight becomes
impossible to perform rather than merely discouraged. Two further properties follow, and both are the
point:

- **A removal states where it landed.** The journal event carries `removed_chars`, the removed text, and
  a `landed` reference — a record kind and its address (a card, a decision, the ledger) — or `null`.
  `null` is legal and honest: it means the text is preserved in the log and was curated nowhere.
- **Unlanded removals are COUNTED, and the count is a budget that can only fall.** The count is a field
  of the capsule's own front matter, rendered on the surface that shows position, and gated by ADR-019's
  existing `budget-monotonic` kind. No new ratchet, no second engine.

*Rejected — record only a digest of what was removed.* A digest proves that something changed and returns
nothing. It makes the loss detectable and still permanent, which answers half of a cardinal.
*Rejected — refuse every removal that names no landing.* It converts a pure-editorial cut (a typo, a
re-word) into a bureaucratic act, and a gate that fires on ordinary work is switched off within a week
(ADR-019 decision 2's reasoning, applied here). Preservation is unconditional; curation is optional and
counted.
*Rejected — trust git history as the record.* Measured: three of tonight's capsule writes were never
committed as separate revisions, and the deleted spans crossed no commit boundary. A record that exists
only if someone commits at the right moment is not a mechanism. (Git remains the archive of what WAS
committed — ADR-015 amendment 2 — and that is a different claim.)

### 3. The bounded artifact's SHAPE is a declaration, and every section declares what it holds and where it cools

The capsule's sections are not knowledge of the interpreter. They are rows of a declaration the capability
ships and the host may extend, and each row states: `holds` (the truth that lives there), `source`
(`authored` or `projected` — decision 4), `cools_to` (the record KIND a cold span of this section belongs
to, from `governance/record-keeping.json`'s `kinds[]`), and `audience`. Cooling is then ONE generic
passage — *evict this span, land it at the destination its section declares, journal both halves* — held
by an interpreter that knows no section name and no privileged case (Cardinals II and IV).

A new section is a ROW. A new destination kind is a ROW. Neither is an edit to a writer, and no section
is ever special-cased in code.

*Rejected — keep the section set inside the tool, as today.* It is a closed enumeration in an interpreter:
every host that needs a different position surface must edit the one writer, and every destination decision
is then a `switch` somewhere. Cardinal II names this a defect in the kit's own instrument.
*Rejected — let the author choose the destination at each eviction.* That is discipline wearing the name of
a mechanism: it answers correctly on a rested session and improvises under pressure — exactly the condition
under which tonight's three deletions happened.

### 4. The CARD is the one home of work; every other work surface is a PROJECTION of it, and an authored surface that restates a card field is a defect the gate names

The board, the roadmap and the capsule's work sections are generated from cards and regenerated at will.
Deleting any of them and re-rendering returns them byte-identical (ADR-019's consequence, applied to the
work plane). An authored section survives only where it is the ONE home of something no card can own —
governing intent, a session's handoff, a standing caution — and that is the test the gate applies: an
authored surface carrying a fact a card field already holds is refused as a second home, not tolerated as
a convenience.

This is what makes decision 1 affordable in practice. The projected half of the position surface costs
its author nothing to maintain, cannot go stale, and shrinks the hot artifact structurally rather than by
someone cutting paragraphs at a ceiling.

*Rejected — keep the capsule authored and reconcile it with the board by discipline.* Synchronisation by
discipline is not a mechanism (Cardinal III); both copies stay internally correct while the system speaks
with confidence and lies. This is the defect that has already cost two accepted decisions in the owner's
other project.
*Rejected — delete the capsule once the board projects work.* Rejected on measurement, not on principle:
the capsule holds three things no card owns — the governing intent, the session handoff and the
must-not-forget — and a session that opens on a board alone opens on a list of work with no standing.

### 5. Work has ONE root and typed lineage: a record knows what it came from and what it produced, and an orphan is counted before it is refused

A card may name a `parent` card. The parent's state is COMPUTED from its children and their proofs and is
never set by hand. Decomposition is therefore a TREE of one kind, recursive to any depth, and not a fixed
ladder of named levels — a card is a card whether it is a bet or the third slice of one, and the only
difference is where it sits.

Lineage is typed and two-way-readable: every work record declares its `origin` (the idea, proposal or
decision that justifies it) and, on completion, what it `produced` (evidence, a decision, a ledger row).
An orphan — a decision no card realises, a card no decision justifies — is a counted state under the same
ratchet as decision 2, and a refusal only once its budget reaches zero.

*Rejected — a fixed hierarchy INITIATIVE → PHASE → WORK PACKAGE → TASK* (ADR-019 absence 4, now decided).
Four named levels are a closed enumeration: work that needs a fifth level either lies about its depth or
forces a schema change, and three of the four levels are empty on most work. A recursive parent edge
carries every arrangement the ladder can express and does not privilege a rung (Cardinal II).
*Rejected — a manifest artifact that lists a work item's parts* (the specification's single lifecycle
MANIFEST, already refused by ADR-019 for documents). It is a second board with a different name.

### 6. EVIDENCE is a place a card owns, and it is declared THROUGH the corpus plane rather than beside it

`evidence/<card>/` is the place where a card's proofs live. It is declared as a PLACE ROW in the host's
corpus map (ADR-019 decision 1): `holds: work-evidence`, `authority_ceiling: SUPPORTING`, its `read_when`
being the verification of that card. Evidence is append-only: a proof is added, never rewritten, because a
proof that can be edited after the fact proves the editor's belief rather than the run.

The card, its evidence and its checklist are artifacts of a corpus that can already be read. The delivery
capability therefore contributes **rows and gate modules**, and contributes **no reader**: classes,
authorities, roots, indexes and obligation markers stay with the corpus interpreter, and reachability of a
card from a control root is the reachability invariant ADR-019 already ships, not a new one.

*Rejected — a delivery-owned scanner over `evidence/` and `cards/`.* It is a second reading of the same
tree, correct on the day it is written and divergent afterwards, and it would make "what exists" answerable
from two places (Cardinal III). Where the work plane needs a fact about artifacts, it asks the plane whose
one job that is (Cardinal VIII, direction).
*Rejected — evidence as a list of links inside the card document.* A link is a claim about a file; a place
that holds the artifact is the file. Links rot silently, and a rotted link reads exactly like a good one.

### 7. A criterion's status is COMPUTED by RESOLVING its proof, through an OPEN resolver registry, and what does not resolve is `unproven` — never `proved`

Every card carries acceptance criteria (Definition of Done, stated as Given/When/Then). **Each criterion
names its PROOF as a typed reference** — a gate id, a test name, an artifact path, a receipt, a walked
journey — and `check` COMPUTES each criterion as exactly one of `proved · failed · unproven`. Nothing is
ticked, and no status field is writable by anyone: a human or a machine that could type `proved` has been
handed the power to make the surface lie.

The reference kinds are an OPEN registry: each kind is a resolver module discovered exactly as gate kinds
are discovered, declaring the prefix it answers and returning a verdict plus the reading it made. A new
kind of proof is a module plus a row; it is never a branch in a checker. A reference that names nothing,
or names something the resolver cannot read, is `unproven` — a declared, counted, honest absence, never a
failure and never a pass. The board shows **N/M proved per card**, and `verified` is unreachable while any
criterion is not `proved` (decision 8).

*Rejected — a boolean `done` on each item.* That is the mechanism that produced the owner's named failure;
a box is testimony, and testimony is outranked by evidence in every case where the two differ.
*Rejected — a closed enum of proof kinds (`gate | test | file`) resolved by a switch.* The first proof kind
that does not fit — a walked journey, an owner's signature, a receipt — is either forced into a wrong kind
or costs an interpreter change. Cardinal II, and the same open-registry form the kit already uses for gates.
*Rejected — treat an unresolvable proof as failing.* A missing referent and a refuted criterion are
different facts about the world; collapsing them makes a broken path read as broken work and trains the
reader to ignore both.

### 8. A state that is machine-decidable is never set by hand; a state that is a judgement is never set by a machine

Both halves are one identity, and each half alone is a defect. `verified` is machine-decidable — it means
every criterion resolved `proved` — so no principal may declare it; the state is computed and the machine
may refuse to enter it, which is what makes `verified` mean anything. `bet` is a judgement — the owner
accepting the work — so no computation may enter it, and the door stays a door forever, unratchetable and
unmaturable (the lifecycle already declares `door: owner`; this decision forbids ever removing it).

Each transition therefore declares which it is: `computed` (with the condition that decides it) or `door`
(with the principal who holds it). A transition that declares neither is an unowned passage, and an unowned
passage is how work silently advances.

*Rejected — compute every state, including acceptance.* It automates away the only decision the owner
actually keeps, and makes the board a report of activity rather than of commitment.
*Rejected — leave every state hand-set, as today.* `verified` then means "somebody said so", and the
evidence place of decision 6 becomes decoration beside it.

### 9. An appetite is a declared limit, overrun STOPS the line at a door, and a waiting idea EXPIRES by a declared passage into the archive

A bet declares an APPETITE — a budget for the work, in a unit the HOST declares (the kit ships the
vocabulary and never a number, ADR-001 point 4). Consumption is read PASSIVELY from receipts the system
already writes; nothing is run twice to measure it (ADR-015 amendment 6). At exhaustion the card moves, by
a computed transition, into `blocked` with the declared reason `appetite-exhausted`: the line STOPS and the
exit is an owner's door. **An appetite is never extended by the principal doing the work** — extension is
the owner re-betting, on the record, which is a different act from continuing.

Symmetrically, a card that waits beyond the host's declared age expires by a declared PASSAGE — to `parked`
(said out loud, dated) and from `parked` into the ARCHIVE, which is dead by location (Law 15 / ADR-019).
An archived card is not deleted: it stops being routed. That is what keeps a waiting list from becoming a
graveyard, and it is a passage in the lifecycle grammar `move` already interprets — not a cron, not a
cleanup task, and not a discretionary tidy-up.

*Rejected — a warning at the appetite line, with work continuing.* A warning that does not stop anything is
a silent extension with a paper trail; the measured failure mode of every budget that does not bind.
*Rejected — auto-cancel an overrunning card.* The machine would be deciding that the work is not worth
finishing, which is the owner's judgement and no one else's (decision 8).

### 10. This is delivered by capabilities that already exist; the kit ships gates and vocabulary, and the HOST answers the stance

| Owner | What it delivers here | Why it, and not a new capability |
|---|---|---|
| `delivery` | the capsule as a kit capability and its one writer; the capsule shape declaration; the card's criteria, proof references, parent, origin, appetite; the board's N/M projection; the lifecycle's `computed` / `door` transition kinds and the expiry passage | its declared purpose is already the task lifecycle as data, with the board as a projection of it |
| `governance` | the words: criterion-status values, proof-reference kinds, appetite units, the `work-evidence` and eviction record kinds | it is already the home of the vocabularies the records map is written in |
| `knowledge` | nothing new — the corpus map's place rows for `cards/` and `evidence/<card>/`, and the reachability and catalog projections that already exist | ADR-019 decision 8; this ADR adds rows to that plane, not a reader beside it |
| the gate registry | every gate here is a module in the existing registry plus a `gates[]` row; the ratchet is ADR-019's `budget-monotonic` kind, unchanged | a new invariant is a module and a declaration, never an edit to a switch |

**There is no new capability, no new verb and no new validator script.**

**Stance is the host's answer, and the kit spells none.** Measured: `governance/stances.json` declares
exactly `observe` and `enforce`, and answers an UNANSWERED gate at `enforce`. Two consequences bind the
adoption order below and are the reason it is shaped as it is. First, a gate id shipped before its budget
row exists binds at `enforce` on the host's next run, so **no gate id lands in a slice that does not also
land the reading that seeds its budget.** Second, what a host would answer, and why, differs by gate kind:
the *record-safety* gates (unlanded-removal, capsule staleness) are the ones a host should answer `enforce`
from the first day, because on a healthy tree they refuse nothing at all and the only act they refuse is
the destruction of a record; the *substantive* gates (criteria present, proofs resolving, lineage complete)
are the ones a host should answer `observe` until their budgets reach zero and then mature under ADR-006.
The kit ships neither answer, because a capability that ships a stance row for its own gates is the kit
setting a host's policy — a defect this line has already deleted twice.

*Rejected — a `continuity` capability of its own.* It would split "where the work stands" across two owners
the week after it shipped, and every field of the capsule is a projection of the work plane.
*Rejected — leave the capsule as host tooling, vendored per host.* It is the instrument that failed
tonight; a mechanism that no release governs cannot be fixed once for everyone, and every host repeats the
loss privately.

### 11. The adoption sequence — record safety first — and the six things it refuses to do

| Slice | What lands | What it refuses to do |
|---|---|---|
| **S0** | the words only: criterion statuses, proof-reference kinds, appetite units, eviction and `work-evidence` record kinds, `computed` / `door` on transitions | touch a single card, a schema field or the writer |
| **S1** | **the bleeding stops.** Write-ahead eviction in the one writer: every accepted write journals the text it removed, before the write; `removed_chars` / `landed` on the event; the unlanded-removal counter in the capsule's front matter; the budget row seeded at the reading below | relax the ceiling · move the capsule · add a section · touch cards |
| **S2** | the capsule shape declaration (`holds`, `source`, `cools_to`, `audience`) and the generic `cool` passage to the destination a section declares | generate any section yet · invent a cold-history file |
| **S3** | the card grows: criteria with typed proof references, `parent`, `origin`, `produced`, `appetite`; the resolver registry; `check` computes `proved / failed / unproven`; the evidence place rows in the corpus map; the board shows N/M; every substantive gate lands with its budget row | write any status field · back-fill criteria onto existing cards |
| **S4** | the capsule's work sections become PROJECTIONS of cards; the authored-duplicate gate reports; the expiry and circuit-breaker passages become computed transitions | delete the authored sections no card owns · auto-extend an appetite |
| **S5** | each budget that reaches zero matures its gate to `enforce` under ADR-006 | mature a DOOR — `bet` is never computed, at any budget |

It refuses, by name:

- **a cold-history file, or any other artifact whose purpose is to receive what nothing reads.** A
  graveyard is what link F was told to prevent.
- **relaxing the hot ceiling, now or as a later concession.** The ceiling is not the defect; the shared
  budget was.
- **back-filling criteria or evidence onto historical cards.** A criterion nobody chose and a proof nobody
  ran are fabricated declarations that pass the gate forever (ADR-019 decision 10, same reasoning).
- **a second board, roadmap or manifest artifact**, however convenient the view.
- **a writable status field anywhere in the work plane.** If it can be typed, it will be typed under
  pressure, and it will be typed wrong exactly when it matters.
- **a campaign slice.** Criteria arrive on the work that touches the card; WIP=1 stands.

## What is NOT decided here — declared absences, each with its reason

1. **The ONE REAL EVALUATION run** (ADR-015 amendment 4). Named, not decided: it is an execution of a
   grammar that already exists, and a design document cannot discharge it. It remains part of F's close.
2. **The intent documents (vision · roadmap · registry), seeded blank in the Diátaxis form.** They belong
   to `knowledge` (link E), not here. This ADR contributes one binding constraint to whoever builds them:
   a roadmap that states work STATE is a second board and is refused by decision 4; a roadmap that states
   INTENT is a different kind and is welcome.
3. **The adversarial verification matrix** (ADR-019 absence 1). Still absent, for its original reason.
   This ADR adds one forbidden state to the list it must attack when it is built: *a record destroyed to
   buy currency in a bounded artifact* — whose classification after S1 should be PREVENTED, and which is
   UNCONTROLLED today.
4. **Every number.** Ceilings, appetite units, age limits, WIP and each budget's opening value are the
   host's, declared in its own project plane. The kit ships vocabulary and gates and never a number.
5. **Journal retention and compaction.** Not decided, and named because its absence is the same defect at
   a longer timescale: a compaction that dropped spans with no landing would re-create tonight's loss in
   slow motion. Until a retention passage is declared, the journal is append-only and is never compacted.
6. **`REQUIRED_CONTEXT` / L0–L4 on the card.** Remains with ADR-017's dispatch packet (ADR-019 absence 3
   is unchanged by this ADR).
7. **Cross-host work identity.** Whether a card can be referenced, or a board merged, across two hosts.
   No measured case needs it; YAGNI, and a wrong answer here would leak a host's private work into the
   kit's vocabulary.
8. **Progress as a percentage, and the hill chart.** The only progress reading decided here is N/M criteria
   proved, which is countable and cannot be estimated optimistically.
9. **Recovery of the three spans deleted on 2026-09-23.** They are gone. Recorded here because the record
   of a loss is the only thing that remains when the content does not, and because a budget seeded at zero
   would otherwise imply this never happened.

## Where the field's practice wins, and where ours loses

**Adopted, in our form:** write-ahead logging — the durable record precedes the mutation, and the bounded
artifact is a materialized view over an append-only log (ARIES; event sourcing). Retention and disposition
as a declared property of a record kind rather than an act of tidying (ISO 15489, which ADR-015 amendment 8
already began as the records map). Acceptance criteria bound to executable proof and traceable in both
directions (ISO/IEC/IEEE 29148; Definition of Done). Appetite and the circuit breaker (Shape Up), stopping
the line at a door rather than warning past it (the andon cord). Monotone budgets as the engine of adoption
(ADR-019 decision 9).

**We lose, and it is written down:** the kit shipped an instrument whose documented remedy — *archive the
cold history* — has no mechanism anywhere in the system, and it shipped that sentence instead of the
mechanism. Every record kind we declare has a home and a writer, and **not one of them has ever had a
disposition**: nothing in the framework said what becomes of a record when its home is full, so the answer
was improvised, three times, by deletion. That is Cardinal VI's second direction — a gap met and silently
filled — and it was filled by the mind that also built the instrument, which is why nobody saw it (ADR-015
amendment 7, point 4).

## Measured when (Cardinal VII — assumptions at a boundary)

- **The capsule refusals.** 2026-09-23, in the session that authored this ADR, on host #2: four `set`
  writes, three refused over the 9000-character hot limit by **403, 129 and 9** characters; the cure each
  time was the deletion of true, dated prose. The position artifact measured **9037 characters across ten
  sections** at `capsule_rev` 4910. These are the numbers decision 1 rests on; no later reading replaces
  them silently.
- **The writer's contract, read rather than assumed.** From `--help` and the module's own contract:
  sub-commands `rev`, `get`, `set`, `claim`; `set` is a compare-and-swap on `capsule_rev` addressed to one
  named section; validation runs on the CANDIDATE text before any write; exit 3 is a CAS conflict; the
  journal is per-runtime at `work/continuity/journal/<date>.<runtime>.jsonl`. **There is no archive verb**
  — verified by reading the verb list, which is why decision 2 adds a passage rather than a tool.
- **The remedy text without a mechanism.** `budget_report` prints *"archive a colder section to the
  cold-history pointer first, then retry"*; no such pointer, file, verb or destination exists in the tree.
- **The card schema.** 2026-09-23: eight properties, `additionalProperties: false`, required
  `schema_version, id, title, state, created_at`. No criteria, proof, evidence, parent or appetite field
  exists today — so decision 7 creates a field, it does not repair a habit.
- **The lifecycle.** Nine states; `shaped → bet` already carries `door: owner`; the only delivery gates are
  `FF-DELIVERY-WIP` and `FF-DELIVERY-AGE` — so the expiry passage of decision 9 extends a gate that exists
  rather than adding a rival.
- **The stance vocabulary.** `governance/stances.json` declares exactly `observe` and `enforce`, with
  `unanswered: enforce`. That reading, not a preference, is why decision 10 forbids shipping a gate id
  ahead of its budget row, and why the kit spells no stance.
- **The corpus plane is already the reader.** `kit/interpreters/corpus.py` resolves places, classes,
  authorities, roots, indexes and obligation markers, and the gate modules publish the measures. Decision 6
  contributes rows to it; verified by reading the interpreter's published surface.

## Consequences

- **A record can no longer be destroyed to make room for a newer one.** After S1 the act measured tonight
  is not refused by judgement; it is not expressible. What an author deletes is preserved before the
  deletion lands, and what was curated nowhere is counted on the surface everyone reads first.
- A new capsule section, destination, proof kind, appetite unit or record class is a **ROW**; a new
  invariant is a **module plus a declaration**. Nothing in this ADR can be extended by editing an
  interpreter.
- `verified` acquires a meaning for the first time: every criterion resolved `proved` against a referent
  that exists. A card that cannot state a criterion is visible as a counted absence rather than passing
  quietly.
- The board, the roadmap and the capsule stop being three instruments. Delete the projected surfaces and
  the next render returns them byte-identical; what survives by hand is exactly what no card can own.
- A bet that overruns stops at a door, and an idea that waits ages out of the routed corpus into the
  archive. Neither is discretionary, and neither deletes anything.
- The framework acquires, for the first time, a **disposition** for a record kind whose home is full —
  which is the general lesson tonight's failure taught, and it binds every bounded artifact this kit ever
  ships, not only this one.

## What this requires amended elsewhere (not done in this ADR)

1. **ADR-015, link F row.** It should record that F's FORM is decided by this ADR, and that two items of
   the row are carried forward rather than delivered: the ONE REAL EVALUATION run (amendment 4) and the
   blank intent documents, which belong to `knowledge`. Suggested addition to the row: *"Form decided by
   ADR-020; the evaluation run and the intent documents remain open and are named as its absences 1–2."*
2. **ADR-015, amendment 10.** Its three requirements are now decided — the parent card as the one root
   (decision 5), typed traceability (decision 5), and one lifecycle grammar per record kind (decisions 3,
   8 and 9) — but it names a levelled hierarchy by illustration ("initiative → epic → story"). It should
   record that the decided form is a recursive parent edge, and that the named ladder is an illustration
   rather than a schema. GAP-F1 in the host's ledger is answered by decision 5 and should be marked so by
   the run that owns the ledger.
3. **ADR-019, declared absence 4** (INITIATIVE → PHASE → WORK PACKAGE → TASK, "not decided here — link F").
   Decided by decision 5, and rejected in its four-level form. The absence should be marked resolved with
   that reference.
4. **ADR-019, declared absence 1** (the adversarial verification matrix). Its list of forbidden states
   should gain *a record destroyed to buy currency in a bounded artifact*, classified UNCONTROLLED until
   S1 lands.

## Amendment 1 — two things this ADR said twice, restated once (2026-09-23, on building S0+S1)

Both were found by the slice that implements this decision, which is where a contradiction in a
declaration is supposed to surface: the builder had to choose, and a builder choosing between two
sentences of its own specification is the defect, not the choice.

**1. The kind is `budget-ratchet`.** Decision 2 and the slice table call the ratchet
`budget-monotonic`. No such gate kind exists anywhere in this kit; the kind published by ADR-019 and
running today is **`budget-ratchet`**, and S1 reused it whole, as instructed. The name in this ADR
was wrong on arrival. A second spelling of a live kind is not a synonym — it is a second home for a
name, and the first reader to trust it would go looking for a mechanism that is not there.

**2. Proof-reference kinds are a REGISTRY, not a vocabulary row.** The S0 row of the slice table
lists "proof-ref kinds" among the words to be declared; decision 7 declares them an OPEN registry of
resolver modules, discovered exactly as gate kinds are. Both cannot hold: rows would be a second
home for a set the registry owns, and every new resolver would then cost a vocabulary edit — the
closed enumeration Cardinal II refuses. **Decision 7 stands; the table cell was a summary that
over-reached.** S0 therefore declared no proof-reference words, correctly, and S3 lands the registry.

*The rule this amendment follows:* where a numbered decision and a table summarising it disagree,
the DECISION governs and the table is corrected — a summary never legislates. Recorded here rather
than edited into the table above, because an amendment that rewrote the sentence it amends leaves a
doctrine whose clauses nobody can date (Cardinal VI).

## Amendment 2 — an appetite is spent while the work is, and the lifecycle says when that is (2026-10-20)

**Context.** Decision 9 declares a limit and reads its spend; it never said which stretch of a record's
life the spend covers. The reading took the only window it could name without naming a state -- from
the record's capture to now -- and said so in its own docstring. In use that window was wrong at both
ends. A card captured days before it was bet began over its limit (a host had to declare 7 days for 3
of work, because 3.3 had already passed in intake). And a card that finished went on spending forever:
one that landed five minutes after it was captured, inside a one-day limit, held the gate red from the
next day on, which taught the host that the board's one red light could be explained away.

**Decision.** The window is the lifecycle's to declare, as a property of its states. A state that
carries `spends: true` is one in which work consumes its appetite; the spend of a record is the sum of
its stays in such states, read from the passages it already records. The stay a record is in now runs
to the moment of the reading. The delivery lifecycle marks `bet`, `in-flight`, `verified` and
`blocked`: the bet is where Shape Up starts the clock, blocked time still burns the cycle, and neither
`parked` nor a closed state spends. A lifecycle that marks none keeps the whole-life reading, and every
reading names the window it used.

**Rejected.** *From the first spending passage to the first closing one* -- simpler, but it charges a
card for every day it stood parked between, and parked is the one state whose meaning is "not now".
*Naming the states in the reading module* -- the module would then know the delivery vocabulary, which
is exactly what the registry of units exists to keep it out of; a host with its own lifecycle could not
use it. *A field on the record saying when its clock started* -- a second home for a moment the history
already holds, and one a principal under pressure could edit. *Subtracting blocked time* -- a blocked
cycle is still a cycle spent; the appetite is a limit on calendar the host is willing to give, not on
effort.

**Consequence.** No host has to re-declare a limit: the same amount now measures what it was always
meant to. A host whose own lifecycle marks no spending state sees no change at all, and is told so in
every reading.
