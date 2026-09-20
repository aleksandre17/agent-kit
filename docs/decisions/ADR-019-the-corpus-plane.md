# ADR-019 — The corpus plane: an artifact declares what it is, and navigation is projected from that

- **Status:** Accepted (2026-09-21; owner-delegated under ADR-015 amendment 5 — the specification of
  2026-09-21 was handed over as a requirement, not as a design). Two facts it rests on were MEASURED
  rather than assumed; both are in *Measured when*.
- **Amends:** ADR-015, by deciding the FORM of links **E** (the knowledge plane) and **F** (the
  management spine) where the corpus is concerned. This ADR creates **no third instrument**: every
  mechanism below is delivered by a capability that already exists — `governance` (the words),
  `knowledge` (the classification, the index, the catalog) and `delivery` (the routing of
  obligations). It also settles, for documents only, one row of ADR-015's post-1.0 debt: *one home
  for the status vocabularies*.
- **Extends:** ADR-006 (gate stance and maturation) — the whole adoption path below is that
  mechanism used as designed, and nothing else. ADR-001 point 4 (the kit ships vocabulary, the host
  ships the number).
- **Sources:** the owner's Engineering-Project-Operating-System specification (2026-09-21, forty
  sections); `docs/architecture/audits/AUDIT-engineering-os-delta-2026-09-21.md` in host #2, which
  maps every section to the mechanism already running and names the six genuine gaps and the four
  things that must not be adopted; the corpus reading of 2026-09-21; the tree as it stands
  (`kit/interpreters/gatekinds.py`, `kit/capabilities/governance/record-keeping.json`,
  `kit/capabilities/knowledge/capability.json`, `kit/capabilities/hygiene/residence.json`,
  `kit/capabilities/governance/host-layout.json`).

## The situation

A corpus of two thousand documents had been reached without any document ever being asked to say
what it IS. Measured on 2026-09-21 over host #2: **2013 documents; 557 (28%) reachable from the
control plane; 1835 (91%) declaring no kind, authority or status at all; 352 documents carrying 815
live obligation markers; and 213 documents carrying 506 live obligations that no route from the
control plane reaches.**

Read that last number for what it is. Five hundred and six open obligations are correct, are owned
by somebody, and cannot be reached from where the work is steered. **The defect is not loss — it is
routing.** A document that cannot be reached from the control plane is not tracked; it is
*remembered*, and memory is precisely what ends at a session boundary.

Three things in that reading are structural rather than accidental, and each is a cardinal already
in force, held only by discipline:

- **Law 15 / the Kind Law is doctrine with no mechanism.** A folder has a kind; a kind confers or
  withholds authority. Ninety-one per cent of the corpus never says which kind it is, so the only
  reading available to a machine — and, in practice, to a reader in a hurry — is the PATH and the
  FILENAME. Cardinal VII says a name is not a referent. The corpus currently has nothing else.
- **There is no NAVIGATION plane.** There is no artifact that answers *what exists and where is the
  thing that answers my question*, and the moment one is written by hand it becomes a second home
  for "what exists" and starts to drift (Cardinal III). The owner's other project lost two accepted
  decisions to exactly this: an index that answered the question WRONGLY, which is worse than no
  index, because a wrong index is consulted and believed.
- **Nothing forbids the corpus getting worse.** Every reading we have is a snapshot. A count with no
  ratchet is a lament.

The specification handed over on 2026-09-21 is right about all three. It is also, in the main, a
restatement in another vocabulary of mechanisms this framework already runs — which is the danger,
not the value: *an adopted requirement that already has an owner must reference that owner, never
spawn a rival.* This ADR therefore decides in OUR vocabulary wherever one exists, and says plainly,
in three places, where ours LOSES.

## Decision

### 1. An artifact's CLASS and AUTHORITY are read from a DECLARATION, and from two declaration sites only

An artifact's class and authority are resolved by exactly two readings, in this order:

1. **The artifact's own front matter** — `kind`, `authority`, and optionally `owns`, `supersedes`,
   `superseded_by`, `indexes`, `read_when`. This is the artifact's self-declaration and the ONLY
   site that can grant an authority above the place's ceiling.
2. **The host's CORPUS MAP** — a declaration of PLACES (`.agents/project/corpus/*.json`, validated
   against a new `corpus-map` schema declared by the `knowledge` capability), modelled row-for-row
   on `governance/host-layout.json`: `path`, `holds` (a class), `authority_ceiling`, `entry`,
   `read_when`, `indexed_by`. A row states, once and with an author, what an entire place holds.

**A place declaration may CONFER a class. It may never RAISE authority.** A place's
`authority_ceiling` caps what an artifact resident there may declare; it never supplies authority
that the artifact did not declare itself. The ceiling for every place defaults to `SUPPORTING`.
CANONICAL is therefore unreachable except by an artifact that says so in its own front matter, and
`kind` is never inferred from a filename by anything.

This is the difference the specification is reaching for and states imprecisely. The forbidden thing
is not *path-correlated classification*; it is **inference**. A place row is a declaration a human
wrote, reviewable in one diff, with one author — it is Cardinal IV-clean. A filename pattern
evaluated inside an interpreter is the interpreter deciding policy, which is the same cardinal
violated. The rule that survives both: **an interpreter reads declarations and never infers; and no
declaration that a human did not author about THIS place may ever raise authority.**

*Rejected — one declaration site, the artifact only (the specification's literal reading).* It is
correct and it is unreachable: it prices the mechanism at 2013 file edits before the first gate can
run, which Cardinal I forbids us to use as an excuse and arithmetic forbids us to pretend away. A
mechanism that cannot start is not a stronger mechanism.
*Rejected — a single central registry file listing every artifact.* That is a hand-maintained
catalog wearing a schema: a second home for "what exists", drifting from the day after it is
written (Cardinal III), and unmergeable by two sessions at once.
*Rejected — extend `hygiene/residence.json` with classification genres.* Residence is a sensor for
what has NO home; classification is a statement of what a thing IS. One reason to change each
(Cardinal VIII); folding them makes a fat seam whose two halves fail together.

### 2. An artifact that declares nothing is UNCLASSIFIED — a declared state, counted, never refused and never authoritative

`UNCLASSIFIED` is a first-class value of the authority vocabulary, not an error and not an absence.
An unclassified artifact is: named in the catalog projection as unclassified, counted against a
declared budget (decision 9), forbidden to be cited as authority by any gate, and left exactly where
it is. Nothing deletes it, nothing moves it, and `check` does not fail merely because it exists.

This is Cardinal V bound to the corpus: unbound, empty and unclassified are DECLARED STATES the
system can name and render. The alternative — treating silence as a failure — makes the first run of
the gate produce 1835 failures, which is not a signal, and the alternative to THAT — treating
silence as "probably fine" — is the fabricated zero the cardinal forbids.

*Rejected — refuse the unclassified (fail `check`).* 1835 simultaneous failures is noise with a
severity field; the gate would be switched off within a day and the mechanism would die at birth.
*Rejected — default the undeclared to the place's class silently.* Then the corpus reads as fully
classified while 91% of it was classified by nobody, and the surface lies (Cardinal V). A place
default applies only where the corpus map declares a place; everything else stays honestly
unclassified, and the two are distinguishable in the catalog.

### 3. The vocabularies have ONE home each, and that home already exists

| Vocabulary | The one home | How it grows |
|---|---|---|
| **Document / record CLASSES** | `governance/record-keeping.json` → `kinds[]` (already 27 rows: `decision`, `reference`, `guide`, `intent`, `work-card`, `work-evidence`, `run-evidence`, `projection`, `retired-record`, …) | a new class is a ROW; a host adds its own rows |
| **PLANES** | `governance/record-keeping.json` → `planes[]`, and `kinds[].plane` | a plane is a row; a kind names its plane |
| **AUTHORITY states** | `governance/record-keeping.json` → `authorities[]` | a row |
| **WRITERS / LIFECYCLES of a place** | `governance/record-keeping.json` → `writers[]`, `lifecycles[]` (already there) | a row |
| **Gate STANCES** | `governance/stances.json` | a row (ADR-006) |
| **WORK statuses** | `delivery/lifecycle.json` — the card lifecycle | a row (ADR-015 link F) |
| **OBLIGATION markers** | the corpus map's `obligation_markers[]`, kit-shipped defaults, host-extensible | a row, each carrying its calibration (decision 5) |

The specification's taxonomy (CONTROL / ARCHITECTURE / DECISION / CONTRACT / REFERENCE / GUIDE /
WORK / EVIDENCE / REGISTER / REPORT / HISTORICAL) is **adopted as rows of the existing `kinds[]`
list, not as a rival list.** Where a row is missing (`contract`, `register`, `report`, `historical`
as distinct from `retired-record`) it is added there. Where our word differs from the
specification's, **our word wins and the specification's is recorded as its alias in the row's
summary**, because a second vocabulary for one truth is the Cardinal-III failure at its fatal stage:
both lists stay internally correct while the system speaks with confidence and lies.

The authority vocabulary is adopted whole and extended by one: `CANONICAL`, `SUPPORTING`,
`HISTORICAL`, `SUPERSEDED`, `MIGRATION_ONLY`, **`UNCLASSIFIED`**.

The seven planes are adopted as a GROUPING ATTRIBUTE OF A KIND, never as a field on a document and
never as a directory. A document declares its `kind`; its plane is DERIVED (`plane(doc) =
plane(kind(doc))`). One declaration, everything else projected.

**A document carries no `status` field.** This is the settlement of ADR-015's debt row for
documents, and it is a deletion rather than a new vocabulary: an ADR that is Proposed is
`SUPPORTING`; Accepted is `CANONICAL`; superseded is `SUPERSEDED` and names its successor. The
states a document was going to carry in a third field are ALREADY the authority states. Work status
lives on the card (link F). Gate status is a stance. Three vocabularies, three owners, no fourth.

*Rejected — a new `taxonomy.json` in a new `corpus` capability.* A second home for the words, and a
third instrument beside E and F — forbidden by the brief and by Cardinal III.
*Rejected — per-document `status` alongside `authority`.* Two fields whose value sets overlap is the
drift generator; within a month a document is `status: current, authority: SUPERSEDED` and both
readings are locally correct.
*Rejected — planes as seven directories.* §33 of the specification forbids the move, Law 7 has no
patience for it, and it would relocate 2013 files to make a classification visible that a
projection shows for free. The planes are a CLASSIFICATION, not a filesystem.

### 4. NAVIGATION is a projection, and its sources are the declarations already being read

Two generated surfaces, both `class: projection`, both written by `render` only, both drift-checked
by the existing `FF-KIT-PROJECTION`. No new gate, no new writer, no hand-kept file:

- **`.agents/generated/corpus/CATALOG.md`** — what exists, by plane and class: one section per
  plane, one row per declared PLACE (its class, ceiling, writer, lifecycle, index), plus per-place
  counts, plus the NAMED exceptions — every `CANONICAL` artifact by name, every index, every
  supersession, every unrouted obligation, every unclassified place. It does **not** list 2013 rows.
- **`.agents/generated/corpus/ROUTES.md`** — question → place. Projected from the `read_when` field
  that `host-layout.json` rows ALREADY carry, and from the same field on corpus-map rows and on
  artifact front matter. The vocabulary is reused verbatim; no `answers` field is invented.

Materializing every artifact as a row is refused (lazy materialization, §34, and the kit's own
stance: *a count is a declared zero and a pointer; a cast is a decision nobody made*). The per-file
index is computed at gate time, in memory, and never committed — a 2013-row generated file changes
on every commit, is reviewed by no one, and becomes the most authoritative-looking unread document
in the repository.

*Rejected — a hand-maintained `CATALOG.md`.* Named by the audit as the artifact to refuse while
adopting the concept.
*Rejected — a full generated index of every file.* Diff noise that hides the twelve rows that
matter; and it invites the reader to treat a regenerable listing as the register.

### 5. REACHABILITY is a closure over a declared root set, and an unreachable obligation is a counted defect before it is a failing one

**Reachable** means: there is a path in the ROUTE GRAPH from a declared ENTRY to the artifact.
Nodes are corpus paths. Edges are (a) a resolvable link from one corpus document to another, and
(b) `indexed_by` on a corpus-map row — a place reached through its index reaches its residents.
ENTRIES are the corpus-map rows declaring `entry: true`; on host #2 that is the capsule, the laws,
the registry and the ledger. Depth from the entry is COMPUTED AND REPORTED — it is the honest
referent for the specification's L0–L4 progressive disclosure — and is **not** gated (decision 11).

**A live obligation must be reachable.** An obligation marker is a row of the declared
`obligation_markers[]` vocabulary, and — copying the calibration discipline that
`hygiene/residence.json` already ships for every genre — **each marker row carries one path it must
match and one lookalike it must tolerate.** A marker vocabulary with no calibration is a regex
somebody believed; the owner's other project met exactly this as a parser bug.

`FF-OBLIGATION-ROUTED` fails when the number of documents carrying live obligations and reachable
from no entry EXCEEDS the declared budget. On the day of adoption that budget is 213 (decision 9),
so the gate is green and truthful on the first run, reports the 213 by name every time `check`
runs, and cannot be made worse.

*Rejected — reachability by hop limit (≤3 from the capsule).* A number nobody can justify, failing
correctly-routed documents for being deep and passing badly-routed ones for being shallow. Depth is
a report, not a verdict.
*Rejected — reachability defined over the filesystem (a file in a known tree is reachable).* That is
the status quo, and 506 obligations prove it false: they are all in known trees.
*Rejected — gate every document for reachability, not only those carrying obligations.* A reference
document nobody links is inert; an OBLIGATION nobody can reach is a promise the system has quietly
stopped keeping. The invariant is about obligations.

### 6. INDEX COMPLETENESS is decided in both directions, or it is not decided

An artifact declares `indexes: <place id>` (optionally with a class scope). `FF-INDEX-COMPLETE`
refuses, for each such artifact:

- **a missing row** — a resident of that place, in scope, that the index does not link;
- **a dangling row** — a link in the index that resolves to nothing;
- **a mis-stated row** — a link whose target declares an authority the index contradicts.

Both directions are the decision. A one-directional check (every link resolves) passes an index that
is missing half its subject, which is precisely how two accepted decisions were lost. This is fully
machine-decidable and is declared at `enforce` from the first day for every place that declares an
index, because unlike the corpus-wide invariants it starts at zero: a place with no index declared
is simply not checked.

*Rejected — link validity only.* Passes the exact failure mode the invariant exists for.
*Rejected — generate every index, so completeness is structural.* Correct for the catalog and wrong
for a curated register: an index with prose, ordering and judgement is a `reference` document with
an author, and generating it would delete the curation. Generate the CATALOG; gate the INDEX.

### 7. Authority can never be read out of a path or a filename — the three bindings

1. **The ceiling rule** (decision 1): a place may cap authority; it may never confer it.
2. **`FF-KIND-AUTHORITY`, already built and now reframed.** The `knowledge` capability's existing
   gate refuses a TITLE that claims an authority its location cannot grant (`CANON-*`, `DESIGN-*`,
   `ADR-*` outside a declaring place). It was the only reading of authority we had; it is now
   demoted to what it always should have been — **a detector of the filename-as-authority defect**,
   never a source of authority. The gate's code is unchanged; its meaning in this ADR is.
3. **`FF-AUTHORITY-DECLARED`** refuses: an authority above the place ceiling that the artifact did
   not declare; a `CANONICAL` artifact that declares no `owns` topic id; **two `CANONICAL` artifacts
   declaring the same `owns` id** — one fact, one owner, machine-enforced, which is the
   specification's §2 and §19 anti-parallelism rule made decidable without inventing a topic
   vocabulary; a `supersedes` or `superseded_by` that dangles; and a supersession declared in one
   direction only.

Here **ours loses and says so**: the specification is right that a filename must never determine
authority, and until this ADR the filename and the path were the only determinants we had.
Doctrine held it (Cardinal VII, Law 15); no mechanism did; and a doctrine held by discipline is not
a mechanism.

*Rejected — keep path-derived authority and gate the exceptions.* Inverts the burden: every future
reorganisation silently re-authorises documents.
*Rejected — a new gate for the filename rule.* One exists. Adding a second would be two gates for
one invariant.

### 8. This is delivered as ADR-015 links E and F, by capabilities that already exist

| Owner | What it delivers here | Why it, and not a new capability |
|---|---|---|
| `governance` | the vocabularies: `planes[]`, `authorities[]`, `kinds[].plane`, the new class rows | it is already "the words the records map is written in" |
| `knowledge` — **link E** | the artifact front-matter contract, the `corpus-map` schema, `FF-CORPUS-DECLARED`, `FF-AUTHORITY-DECLARED`, `FF-INDEX-COMPLETE`, the CATALOG and ROUTES projections; `FF-KIND-AUTHORITY` reframed | its declared purpose is already *"hold knowledge with DECLARED AUTHORITY"*. This ADR is that sentence finally holding for the whole corpus |
| `delivery` — **link F** | `FF-OBLIGATION-ROUTED` and the entry-root declaration; the capsule as a kit capability is F's own work and is the primary entry | routing an obligation to where work is steered IS the management spine; the card is the one home of work |
| the existing gate registry | every gate above is a module in `kit/interpreters/gates/` plus a `gates[]` declaration in a capability document | a new gate kind is a module and a declaration, never an edit to a switch (`gatekinds.py`) |

Three gate kinds are new modules: `artifact-classified`, `authority-declared`, `index-complete`,
`obligation-reachable`, `budget-monotonic`. Each is discovered; none edits an interpreter; none adds
a verb. **There is no `corpus` capability, no `corpus` verb and no validator script.**

*Rejected — a new `corpus` capability.* It would be the third instrument the brief forbids, and it
would split "documents have declared authority" across two owners the week after it shipped.
*Rejected — `ops/validation/project-verify.*` as the specification asks.* Named by the audit: an
invariant belongs in the gate registry, where it runs at the edit, at the commit and in CI — not
only when somebody remembers a script. Here ours is stronger and the specification loses.

### 9. Monotonic quality is a BUDGET that can only fall, and it is the engine of adoption

The host declares, in its corpus map, one budget per corpus-wide invariant:

```
unclassified_documents: 1835      # measured 2026-09-21
unrouted_obligation_docs: 213     # measured 2026-09-21
```

`FF-CORPUS-RATCHET` is declared at **`enforce` from day one** and refuses exactly one thing: a
budget row whose value is higher than the value recorded in the previous accepted state, or a
measured count above its declared budget. Lowering a budget is an ordinary edit. Raising one is a
refusal with no override.

This inverts the usual adoption order on purpose: **the substantive gates start at `observe` and the
ratchet starts at `enforce`.** Nothing fails on the first run; nothing can get worse from the first
run. When a budget reaches zero, its gate matures to `enforce` under ADR-006 and the zero becomes
unraisable. That is the specification's §29 monotonic architectural quality, machine-decidable,
with no judgement call in it.

*Rejected — a percentage or a trend.* A ratio improves when the denominator grows; a corpus can
"improve" by adding documents.
*Rejected — a deadline ("classified by date X").* A date is not a mechanism; it expires and the rule
with it.

### 10. The adoption sequence for 2013 documents — and the four things it refuses to do

| Step | What lands | File moves | Front matter written |
|---|---|---|---|
| S0 | vocabulary rows in `governance/record-keeping.json`: `planes[]`, `authorities[]`, `kinds[].plane`, the missing class rows | 0 | 0 |
| S1 | the host's corpus map: its places, their classes, their ceilings, its entry roots, its indexes, its obligation markers with calibration — tens of rows for thousands of files | 0 | 0 |
| S2 | the four substantive gates declared at `observe`; `check` reports every count and every named exception on every run | 0 | 0 |
| S3 | `FF-CORPUS-RATCHET` at `enforce`, budgets seeded from the 2026-09-21 reading | 0 | 0 |
| S4 | front matter arrives **only** where an artifact CLAIMS authority, IS an index, or CARRIES an obligation — and only as part of work that already touches the file | 0 | hundreds, authored |
| S5 | each budget that reaches zero matures its gate to `enforce` (ADR-006) | 0 | — |

It refuses, by name:

- **a mass front-matter injection by script.** A `kind:` no human chose is testimony, not a
  declaration — and it is worse than silence, because it passes the gate forever and the surface
  then lies with confidence (Cardinals IV and V).
- **moving files into plane directories.** The planes are a classification.
- **back-filling `history/` and `archive/`.** Dead by location; classifying the dead is work that
  produces a more convincing corpse.
- **a big-bang classification campaign as a work item.** Classification rides on work that touches
  the file. A campaign competes with WIP=1 and finishes as a half-classified corpus in which the
  unclassified remainder looks deliberate.

*Rejected — classify by LLM pass over 2013 documents.* Fast, plausible, and it produces exactly the
fabricated declarations the previous paragraph refuses; an agent's guess about a document's
authority is a guess wearing a field name.
*Rejected — freeze the corpus until it is classified.* Cost-of-change as a hostage; Cardinal I
forbids the argument in both directions.

## What is NOT decided here — declared absences, each with its reason

1. **The adversarial verification matrix.** NAMED, not built (a later slice of link F). It must
   prove, per forbidden state, an outcome classified PREVENTED / DETECTED / RECOVERABLE /
   UNCONTROLLED, each with a receipt rather than a claim, and UNCONTROLLED driven to zero wherever
   the state is machine-decidable. The states to attack are already known: a second CURRENT beside
   the capsule; two `CANONICAL` artifacts owning one fact; authority claimed by a filename; an
   obligation routed to nothing; an index that LOOKS complete and is not; a capsule that no longer
   describes the tree; a gate declared at a stance that makes it decorative. It is not decided here
   because a verification matrix over gates that do not yet exist would verify a design.
2. **The fresh-session test.** NAMED, not built. A cold agent, repository state only, answering the
   specification's thirteen questions. What it must prove is **ROUTING, not recall**: for each
   question, that the answer was reached from an ENTRY through the generated ROUTES projection, in
   a recorded number of reads, and that removing the agent's prior memory does not change the
   answer. A test a warm agent passes measures nothing. Our continuity design has never been
   measured this way; it has only ever been believed.
3. **REQUIRED_CONTEXT / L0–L4 as a durable field on a work item.** Deliberately left to ADR-017's
   dispatch packet and link F's card. The context vocabulary has an owner; a second one on the
   document would be Cardinal III committed in the act of obeying the specification.
4. **INITIATIVE → PHASE → WORK PACKAGE → TASK.** Not decided here. It is a change to the card
   schema (link F), and a hierarchy declared in the corpus plane would be a second home for work
   structure.
5. **Per-file classification of code and non-markdown artifacts.** Place-level only, permanently as
   far as this ADR goes: source files declare their contracts in code, and front matter in a `.py`
   is a comment a machine believes.
6. **Depth / progressive-disclosure as a gate.** Computed and reported; not gated. The number that
   would make it a verdict does not exist yet.
7. **Host #2's own migration.** This ADR is kit doctrine. Host #2 adopts it as a host, through its
   own ledger and its own cards; the counts above are its opening budget, not the kit's.

## Where the specification wins, where we win, and where we lose

**The specification wins** (adopted, in our form): the authority classification as a first-class
declared field; the artifact catalog as a generated surface; explicit two-way supersession;
reachability as an invariant; index completeness as an invariant; monotonic quality as a ratchet;
adversarial verification; the fresh-session test; anti-parallelism enforced by a duplicate-owner
refusal.

**We win** (its request is REJECTED, with the reason): the hand-maintained catalog (generated —
Cardinal III); `docs/project/CURRENT.md` (the capsule is CAS-written, rev-guarded, size-gated and
staleness-gated — a second CURRENT would commit the specification's own §35 failure while adopting
the specification that forbids it); the standalone validator script (the open gate registry runs at
edit, commit and CI); seven physical directories (a classification, not a filesystem); a new
document taxonomy (rows of `record-keeping.kinds[]`); a per-document lifecycle `status` field
(authority + card lifecycle already hold it); and the single lifecycle MANIFEST as an ARTIFACT — its
controlled vocabulary is adopted, its file is refused, because the card is the one home of work
(link F) and a manifest would be a second board.

**We lose, and it is written down:** we had no artifact-level declaration at all, so Law 15 bound
9% of the corpus and was decoration over the rest; our only reading of authority was the path and
the filename, which Cardinal VII forbids and which we nonetheless shipped as a gate; and the
specification's §26 invariant list is genuinely richer than ours — index completeness and
reachability are invariants we had never named.

## Measured when (Cardinal VII — assumptions at a boundary)

- **The corpus reading.** `corpus_probe.py`, scratchpad, over host #2 on **2026-09-21**, every
  `*.md` except `history/`, `archive/`, `node_modules/` and the `kits/` submodules. Reachability
  computed as transitive link closure from the control surface in use that day. 2013 / 557 / 1835 /
  352 documents with 815 markers / 213 documents with 506 markers. Every budget in decision 9 is
  this reading and no other; a later reading replaces it by lowering a budget, never by silently
  re-measuring.
- **The gate registry is open.** Read in the tree on 2026-09-21: `kit/interpreters/gatekinds.py`
  discovers `KINDS` from every module in `kit/interpreters/gates/` and refuses a kind claimed twice.
  The five gate kinds this ADR declares therefore need no edit to any interpreter. This was verified,
  not assumed.
- **`read_when` already exists.** `governance/host-layout.json` carries it on every row. The ROUTES
  projection reuses that field rather than inventing one; verified by reading the document.
- **The calibration pattern already exists.** `hygiene/residence.json` ships `proves` and `admits`
  per genre. The obligation-marker vocabulary copies it; verified by reading the document.
- **Two gates on host #2's capsule fired and were obeyed on 2026-09-21** (hot-prose size, staleness
  against the working tree). That is why decision 8 makes the capsule an entry root rather than
  designing a new control surface.

## Consequences

- A new document class, plane, authority state, obligation marker or place is a ROW. A new invariant
  is a module plus a declaration. Nothing in this ADR can be extended by editing an interpreter
  (Cardinal II).
- `check` gains five gate ids and, on host #2's first run, fails none of them — while reporting 1835
  unclassified artifacts, 213 unrouted obligation documents by name, and a ratchet that from that
  moment forbids either number rising.
- The Kind Law stops being doctrine and becomes a mechanism, for the first time since it was written.
- Two surfaces appear that nobody maintains: `CATALOG.md` and `ROUTES.md`. Delete either and the next
  `render` returns it byte-identical.
- ADR-015's post-1.0 debt row *"one home for the stance and status vocabularies"* is settled for
  documents (decision 3) and remains open for gates and cards, which already have one home each and
  need only to be named together.
- The corpus can no longer get worse without a refusal. It can still be wrong; it can no longer be
  wrong in a way nobody can see.

## Amendments

*(none yet — appended on record, in the form of ADR-015 and ADR-017)*
