---
kind: decision
authority: canonical
owns: work-classes
---

# ADR-025 — Work is weighed before it is walked: the change decides its own path, and only upward

- **Status:** accepted (2026-10-17, owner-delegated)
- **Deciders:** the owner's delegate, on the owner's instruction (2026-10-17) that the kit carry the
  ideal balance -- a simple change must not need three hundred confirmations, and nothing may slip --
  built from what a measured prior system did well, completed where it was missing, and founded on the
  international standards for change, risk and AI management, so that work never grows into a monster
  of files and permissions.
- **Builds on:** ADR-020 (the management spine: the card, computed criteria, appetite, doors),
  ADR-022 (the operating plane: task classes route WHO acts), ADR-024 (every token serves the result).

## The situation, measured

The prior system (`gs-serialized`, read 2026-10-17) had excellent mechanisms and one missing axis.

- **What it did well, and this ADR keeps:** one entry gate per phase, and a gate PASS that certifies
  only its own evidence; a claim never above its evidence class; the owner rules and an agent never
  does; a deferral carries the trigger that makes it due; a lesson carries the guard that prevents its
  recurrence; work modes that state what they may write and when they stop; a session-end test (*could
  a newcomer continue from the repository alone?*).
- **What it lacked: proportionality.** Every change walked the heaviest path. In four weeks it wrote
  104 intakes, 276 ledger events, 144 cards (125 superseded), 117 decisions (25 open), 3116 document
  changes against 127 product changes, and its 18-stage route stood at stage 0, blocked. A one-line
  documentation card carried twenty fields and 8 KB; the largest card was 174 KB; the current-state
  file reached 538 KB. Its own diagnosis named the constraint: the owner's decision queue. The process
  had become the product.
- **What this kit already had:** the card as the one home of work, computed criteria, appetite with a
  circuit breaker, the owner's door on `bet`, a pre-approved `standard` edge (ITIL) -- and an always-on
  floor (edit gates, tests, secrets, `check`). What it lacked is the same axis: nothing decides how
  heavy a piece of work's path is, so the `standard` edge still demanded a card, and nothing stopped
  heavy work from walking the light path.

## The principle

**Rigour is proportional to consequence and uncertainty; safety comes from the floor, never from the
number of approvals.** Every standard in the tables below converges on it, in change management
and in AI engineering alike: the path a piece of work walks is chosen by what a mistake would cost,
and an agent is trusted exactly as far as an independent check reaches.

## The standards it is aligned with

Alignment, never a compliance claim: each row names the practice a mechanism follows, so a reader can
check the mechanism against its source. Certification is an external auditor's act and nothing here
asserts it.

**Change, risk and delivery management**

| Mechanism here | Practice | Source |
|---|---|---|
| `standard` / `normal` / `emergency`; a standard change pre-approved by its class | standard, normal and emergency changes; no change board for the pre-approved | ITIL 4, Change Enablement |
| the floor of automated controls on every change; doors only where irreversible | heavyweight external approval slows delivery without improving stability | Forsgren, Humble, Kim, *Accelerate* (2018), DORA |
| the undo-cost scale; doors on irreversible acts | reversible and irreversible decisions | two-way and one-way doors (Amazon) |
| the class computed from consequence | rigour scaled to the consequence of failure | IEC 61508 (SIL), DO-178C (DAL), NASA NPR 7150.2 |
| the uncertainty scale on a card | clear, complicated, complex, chaotic domains | Snowden, Cynefin |
| areas tailor the path (`at_least`, `requires`) | the process is tailored to the work, and the tailoring is recorded | ISO 21502, PMBOK 7 |
| signals weighed before and during the work | risk identified, assessed and treated in proportion, continuously | ISO 31000, ISO/IEC 23894 |
| `after` and the computed entry gate | one entry gate per phase, lighter for smaller work | Cooper, Stage-Gate (and Lite / Xpress) |
| appetite and the circuit breaker (ADR-020) | a fixed budget the owner bets, not an estimate | Basecamp, *Shape Up* |
| `emergency` with its debt | an expedite class of service | Anderson, *Kanban* |
| a lesson's guard; an emergency's card | learning becomes an automated guard, blamelessly | Google, *Site Reliability Engineering* |

**AI engineering and agentic systems**

| Mechanism here | Practice | Source |
|---|---|---|
| what is computable is a verb or a script; a model is spent only on judgement | start from the simplest deterministic workflow; add agentic complexity only when it earns its cost | Anthropic, *Building Effective Agents* (2024) |
| a lesson or a rule reaches the agent when its area is touched, and nowhere else | context is a finite resource, retrieved just in time | Anthropic, *Effective Context Engineering for AI Agents* (2025) |
| the owner decides only irreversible or accountable acts | human oversight in proportion to risk | NIST AI RMF 1.0 and its GenAI Profile (AI 600-1), ISO/IEC 42001, EU AI Act art. 14 |
| an agent's autonomy is bounded by declared areas, gates and doors | no excessive agency; least privilege | OWASP Top 10 for LLM Applications (LLM06) |
| an agent's result is accepted by a test, a gate or a review -- never by the agent | verification by an independent oracle; evaluations | agentic evaluation practice (ADR-024 `trial`) |
| a review by the work's author proves nothing | separation of duties; a model does not grade its own output | ISO/IEC 27001 A.5.3 |
| a claim never exceeds its evidence class | an assurance case: a claim is as strong as its evidence | ISO/IEC/IEEE 15026 |
| the AI system's process is a declared lifecycle | AI system life-cycle processes | ISO/IEC 5338 |

## Decisions

0. **A question changes nothing and walks nothing.** Answering, explaining, reading and read-only
   discovery write no record, open no card and pass no door: there is no change to weigh. The prior
   system's `READ_ONLY_DISCOVERY` mode, kept and made the default -- the pipeline begins only where a
   byte of the repository would change.

1. **The floor is the same for every change and costs no judgement.** Edit gates, the host's declared
   test command, the secrets policy and `check` run on every change of every class. *Nothing slips* is
   a property of the floor; a class never removes a floor control, it only adds records and doors.

2. **A work class is a row of one catalogue.** The kit ships the rows (`delivery/work-classes.json`):
   `standard`, `normal`, `major`, `program`, `emergency`. Each row says when it applies, the records it
   requires (from a closed vocabulary: `commit`, `card`, `criteria`, `decision`, `appetite`, `review`,
   `card-tree`), the acts that need the owner's door, and the standards it is aligned with. No
   interpreter names a class. A host TAILORS by declaring areas, never by editing the rows: an area
   sets its undo cost, may ask a minimum class (`at_least`) and may owe records beyond its class
   (`requires`) -- a review where security lives, a decision where a public contract does.

3. **The class is computed from the change, never chosen by its author.** A host declares its AREAS
   (`.agents/project/delivery/areas.json`): an area is a set of paths, its undo cost
   (`reversible` < `costly` < `irreversible`) and why. The kit computes a change's SIGNALS -- the areas
   it touches, the highest undo cost among them, how many it spans -- and the smallest class whose
   envelope admits them. The envelopes' numbers are the host's (ADR-001 point 4). Uncertainty is the one
   signal no diff carries; it is declared on the card at shaping (its Cynefin domain) and can only raise
   the class.

4. **The computed class is a floor: a change may declare a higher class, never a lower one.** At commit
   and on a review range, a change that declares less than it computes is refused, naming the signal
   and the record it now owes ("touches `migrations` (irreversible): a `major` change -- name its card
   and its decision"). Escalation mid-work is therefore automatic: it is a computation over the current
   change. Lowering a card's class is an owner's door; silent demotion does not exist.

5. **A standard change leaves exactly one record: its commit.** No card, no file, no door. The commit
   message is the record and the floor is the proof. This supersedes delivery rule 4's *"and a card is
   still written"*: that clause made the smallest work pay the record cost of the largest.

6. **An emergency is a debt with a clock.** It may land with its reason in the commit and no card. It
   owes a card that names it within the host's declared days; an unfollowed emergency is counted, and
   the count is a budget that can only fall (ADR-019 `budget-monotonic`). Kanban's expedite class, with
   the bill attached.

7. **A claim never exceeds its evidence.** Every proof kind declares the evidence class its reading
   yields (`static` < `tested` < `runtime` < `production`; and `owner`, `review` beside them). A criterion
   may name the class it needs; a weaker reading leaves it `unproven`, never `proved`.

8. **A deferral carries its trigger.** A parked card may name `due_when`, a typed proof reference in the
   grammar criteria already use. When it holds, the card is reported due. A parked card with no trigger
   is counted: a deferral without a trigger is an abandonment that has not admitted it yet.

9. **A program is a card tree with an order, not a second system.** A card may name the sibling cards it
   comes `after`; it cannot enter `in-flight` before they have landed -- the phase entry gate, computed.
   Because a criterion's status is computed, a landed card whose proof stops holding is reported
   REGRESSED with every card after it named: invalidation needs no ledger.

10. **A finding met on the way is captured in one act and never done on the side.** `capture` writes a
    card in the lifecycle's initial state with its origin and returns. Doing it inside unrelated work is what decision 4
    catches: the change touches an area its card does not, and its class rises.

11. **The monster is prevented by construction.** A class requires the smallest record set that answers
    its risk; a record kind with no declared reader is not created; a card holds position and criteria,
    never narrative (that is evidence's and the decision's); landed work expires into the archive
    (ADR-020 decision 9); and the ceremony each class costs -- records written, doors walked, tokens --
    is measured per accepted change (FF-FRONTIER), so a class whose cost grows while change-failure does
    not fall is a finding, not a habit.

12. **The areas are the architecture map, and the one place impact is read from.** An area may name
    its `owner` and the areas it `feeds` (its downstream consumers); weighing a change names every
    area downstream of what it touches, so impact analysis is a reading, not a preflight essay. A
    lesson whose `subject` is an area id is shown when a change touches that area -- the lesson
    reaches the work at the moment it applies, and costs no context anywhere else.

13. **The project's scale never grows the working surface.** What a person or an agent reads to
    work stays the same size however long the project lives: a card's schema is closed and carries no
    narrative (narrative is evidence's and a decision's); the board shows open work whole and closed
    work as a count and its most recent few, by the host's number; closed cards leave for the archive
    after the host's declared age and are not read again (ADR-020 decision 9, dead by location); every
    hot surface keeps its ceiling (FF-CONTEXT); one decision is one file, one card's evidence is one
    place. Growth goes into the record, which is append-only and never read whole.

14. **The machinery keeps to a time budget, and the budget does not grow with the project.** A
    question runs nothing. A commit runs one weighing -- the staged paths against the areas, no
    network, no history -- held under a second by a test over ten thousand paths and fifty areas
    (measured on the kit's own host: the message hook 0.4 s, `weigh` 0.5 s). Everything that reads
    across the history or across all cards runs at push and in CI (`check`, 3.5 s on the kit's own
    host), and what it reads is bounded by the archive (decision 13). Fast path and slow path, as an
    SLO-minded system splits them: the hot path is cheap by construction, never by hoping.

15. **The floor has no side door.** Four ways around it were found by a pre-mortem and closed:
    - *a skipped hook* (`--no-verify`, a commit made where no hook runs): CI weighs every pushed commit
      one at a time (`weigh --base --head --each`), by the areas its parent held and its card as the
      commit holds it;
    - *a card shaped lighter after the bet*: raising a class is anyone's act, lowering one is the
      owner's door (`reshape --approve`), and a commit that lightens a card without that record on it
      is refused;
    - *loosening the scale in the same change it weighs*: a change is weighed by the areas that stood
      before it, and a change that loosens them -- an area removed, a cost lowered, paths changed, a
      requirement dropped, a limit raised -- owes a card; tightening them costs nothing;
    - *an emergency declared to escape*: the debt is reported on every check and fails past the host's
      days, and the agents' skill (S9) leaves the declaration of an emergency to a person.

16. **A card's proof is independent of the card.** Met on the first real host: a finished card proved by
    FF-KIT-PROJECTION -- the gate that renders the board showing that very proof's status -- read
    differently at each depth and reported itself REGRESSED. ISO/IEC/IEEE 15026's rule applies as
    written: evidence for a claim may not be the claim. `declared-rule-holds` never follows a rule
    into its own evaluation, and the agents' skill names the gates that read cards or the board as
    unfit to prove one.

## What the prior system's control plane becomes here

Its `docs/project/` was the best part of it: one entry point, a small current-state file, a
lifecycle with gates, a catalog with *read when*, a capability map, an evidence index and a lessons
register. Each concern is kept; none is copied as a second file beside a mechanism that already
owns it.

| Its artifact | Concern | Here |
|---|---|---|
| `README.md` (start here) | one entry, a short required-read set | `CLAUDE.md` / `AGENTS.md` projections and the session line; progressive disclosure through the corpus map's `read_when` (ADR-019) |
| `CURRENT.md` | where the work stands, next action | the board (a projection of cards) and the position capsule -- bounded, with the record kept apart (ADR-020 decision 1) |
| `MANIFEST.md` | phases, entry gates, standing obligations, deferrals with triggers | a `program` card tree with `after` (decision 9); obligations are the host's laws and norms; deferrals carry `due_when` (decision 8) |
| `CATALOG.md` | what exists, its authority, when to read it | the corpus catalog, generated (ADR-019) -- never hand-kept |
| `ADOPTION.md` | mapping what existed before | `adopt` and the migration map (ADR-011) |
| `DELIVERY-PLAYBOOK.md` | practice, task modes, retrieval order | the work classes (this ADR), the task classes (ADR-022), the conduct bundles and skills |
| `PROJECT-OPERATING-CONTEXT.md` | repositories, runtime map, prohibitions | the host's laws (`norms.json`), stack-kit's declared targets and layout |
| `capability-map.json` | owners, upstream/downstream, impact | the areas, with `owner` and `feeds` (decision 12) |
| `evidence-index.json` | volatile verified facts and their invalidation | `ground` readings: a fact with its instrument and paths, invalid the moment those paths change -- computed, not reviewed |
| `lessons-register.json` | a failure, its guard, the paths that trigger it | a lesson on a card, surfaced by area (decision 12); its guard is a gate or a test, as there |

**Where it lives.** Work has one home per repository: `docs/work/` -- `cards/`, `evidence/<card>/`
and the generated `BOARD.md` (ADR-021 decision 3); the host's tailoring lives with its other
declarations in `.agents/project/delivery/` (`policy.json`, `areas.json`). There is no
`docs/project/` and no `docs/work/project/`: every concern such a directory held already has an
owner (the table above), and a directory beside them would be the second home ADR-020 refuses. A
repository with several applications (an API, a web client, a worker) keeps ONE card collection --
the areas say which application a change touches, and a card's scope is read from them. Splitting
the collection per application (`docs/work/<app>/`) was rejected: work that crosses two
applications -- the work that most needs one view -- would belong to neither, and two boards are two
answers to *what are we doing*.

**Folders follow only what never changes** (the owner asked whether cards should be grouped into
folders). A working card's area, application, state and even parent change while it is worked; a
folder by any of them would move the file each time -- its links, its history and every `after` that
names it would move with it. So the working set is one flat folder, as every issue tracker keeps one
store (Jira, GitHub Issues, Linear: a project, a label, an epic are views over it), and grouping is
the board's: in each column a program's parts follow their program, each line saying whose part it
is. The one axis that never changes is when a card closed, and the archive is foldered by it
(`docs/work/archive/<year>/`): bounded folders however many years the project runs, as logs rotate.
*Rejected:* folders by area or application (a card crossing two belongs to neither), by state (every
move a rename), a program's parts inside its folder (a part can be re-parented; an epic links its
stories, it does not contain them); areas on the board's lines (a card holds no paths -- its areas
are its commits', and a board that read git on every render would be a reading, not a projection).

## The prior system's failures, and the guard each has here

Balance has two failure directions, and each guard below is aimed at one of them.

| Failure measured there | Direction | Guard here |
|---|---|---|
| every change walked the heaviest path | too strict | decision 3: the class is computed, and most changes compute `standard` -- one commit |
| a one-line card of twenty fields | too strict | decision 2: a class requires only its record set; a card holds position and criteria, never narrative (decision 11) |
| a 538 KB current-state file | too strict | ADR-020 decision 1, kept: position is bounded, the record is append-only, and nothing is deleted to make room |
| two continuity files, five bootstrap orders | duplicate truth | the card is the one home of work; the board and the capsule's work sections are projections (ADR-020 decision 4) |
| 117 decisions queued on one owner | too strict | decision 4 and the doors: the owner decides only irreversible or accountable acts, the computed class decides the rest |
| hand-edited registers that broke on a round-trip | fragile | every register here is data a machine writes and reads; no state is typed by hand (ADR-020 decision 8) |
| validators that checked a field exists, not that it is true | too loose | decision 7: a criterion is proved by resolving its proof, at the evidence class it needs |
| *(the opposite risk)* a light path that lets an irreversible change through | too loose | decision 1, the floor on every change; decision 4, the computed class can only rise |

A host that has declared no area weighs everything `standard` and pays nothing; each area it declares
adds weight exactly where undoing is costly. A gate added by this ADR answers `observe` until the host
has declared its areas, and matures under ADR-006 -- it never binds a host on a declaration the host
has not made.

## Rejected alternatives

- **The author declares the class.** Under pressure every change is small. A declared class is
  testimony; a computed one is evidence (ADR-020 decision 8).
- **One heavy path for everything** (the prior system). Measured above: the process became the product.
- **No process for small work at all.** Small work is where an irreversible path hides; the computed
  floor of decision 4 is what lets small work be light without letting heavy work pass as small.
- **A model classifies the change.** Non-deterministic where a computation exists (task class
  `mechanical`); a model may propose the uncertainty domain at shaping, a person binds it.
- **Size estimates, story points or line counts as the class.** They measure effort, not consequence: a
  one-line migration is irreversible, a thousand-line test file is not.
- **A fixed hierarchy (initiative → phase → package → task).** Refused in ADR-020 decision 5; a program
  is the existing card tree plus `after`.
- **A ledger beside the cards for invalidation.** A second home for state the criteria already compute.

## Slices

| Slice | Lands |
|---|---|
| S1 | the work-class catalogue, the areas seed, signals, the computed class, and the `weigh` verb (staged or `--base/--head`) |
| S2 | the class floor at commit (message hook): an under-declared change, or one owing a card it does not name, refused; tailoring by area (`at_least`, `requires`); the uncertainty scale on cards; `normal` cards pass without the owner's bet; FF-WORK-CLASSES |
| S3 | evidence classes on proof kinds and the criterion's `needs` |
| S4 | `due_when` on parked cards; the `capture` verb |
| S5 | `after` edges, the computed entry gate, REGRESSED |
| S6 | the emergency debt and the ceremony measure per class |
| S7 | areas as the architecture map: `owner`, `feeds`, the downstream named on weighing, lessons by area |
| S8 | the bounded board: closed states as a count and the most recent few; the archive passage by declared age |
| S8b | the side doors closed (decision 15): `weigh --each` in CI, `reshape`, loosening owes a card |
| S9 | the agents' skill: how an agent walks a piece of work -- weigh first, judge only what is not computed, capture what it meets, leave doors and emergencies to people |

Each slice is proven by a fixture the kit does not ship, and the first host to adopt it declares its
areas before any gate binds.

## Consequences

- The smallest work costs one commit and the floor; the largest walks phases, decisions and review --
  and the change itself, not its author, decides which.
- `standard` no longer requires a card. Hosts that wrote cards for standard work keep them; nothing is
  back-filled or deleted.
- The owner's door stays exactly where consequence is irreversible or accountable, and nowhere else.

## Amendment 1 — an independent audit found decision 15 false, and what closed it (2026-10-17)

Two independent auditors read this ADR against its code before it shipped. Decision 15 said the floor
had no side door; it had several, and the auditors reproduced them. Each is closed below, with a test
that fails without the fix.

| Found | Closed by |
|---|---|
| `Work-Class : emergency` (a space before the colon) passed the hook and CI as expedite, and the debt search never found it | one trailer parser for every reader; a declared trailer written any other way than `Key: value` is refused; the debt search reads every spelling |
| a card reshaped to `emergency` admitted any weight and owed nothing | an expedite class is admitted only from a commit's trailer, never as a card's class; `reshape` refuses it; moving to or from it is the owner's door |
| a `major` card could skip the bet (shaped `normal`, moved into flight, then raised) | a class with doors needs a signed passage through a door, at commit and in FF-WORK-CLASSES |
| an area's `requires` (identity's review) was shown and never held | the commit floor holds every record the change owes -- its class's and every touched area's -- on the named card |
| any non-empty `origin` counted as the decision | `decision` is held by an `origin` pointing at a document whose front matter says `kind: decision` |
| CI weighed every commit of a first push by today's areas | a commit made before the host declared areas is not weighed, and is counted as such |
| a local merge of a heavy branch was refused; CI saw a merge as changing nothing | a merge is weighed by what differs from every parent (`--cc`, `MERGE_HEAD`) |
| the hook read cards and areas from the working tree, not the index | the hook reads what the commit records (the index); demotions are matched by path, and removing an unfinished classed card is one |
| a new area cheaper than the old default loosened the scale unseen | an added area cheaper than the default it claims from is loosening |
| `chaotic` lowered work to `emergency` | `chaotic` asks at least `major`; an expedite class is refused as any floor |
| a report whose every test was skipped proved `tested` | skipped is not executed; a run that executed nothing proves nothing (JUnit `skipped`, TRX `executed`) |
| archiving broke paid debts and orders after 90 days | the archive keeps any card a staying card names, to a fixed point, and `repays` is read from the archive too |
| a single-owner host could never review a major card | a passage through a door is the owner deciding, not authoring; the owner who bet the work may review it |

**What this amendment does not claim.** Decision 6's count is reported and fails past the host's days;
it is not yet a `budget-monotonic` ratchet. Decision 11's ceremony reading measures cards, criteria and
lead time per class -- not records written, doors walked or tokens, and not standard changes. The
`owner`, `runtime` and `production` evidence classes have no proof kind that yields them yet, so a
criterion needing one stays unproven. A reviewer's name and an `--approve` name are recorded, not
verified (the kit ledger's *approval is a moment, not an identity*). Decision 16 is enforced against a
rule evaluating itself; a card proved by a gate that reads cards is otherwise refused only by the
agents' skill. The FF-WORK-* gates enforce from the first day -- the "observe until areas are
declared" sentence of the guard table is withdrawn: on a host with no areas they refuse nothing but a
real defect.

## Amendment 2 — a second independent audit, and what it closed (2026-10-17)

A second auditor read the code after Amendment 1 and reproduced two more side doors on live hooks and
in CI: loosening the scale cheaply, then committing irreversible work as `standard`; and an emergency
"repaid" by a stub card. Each row below is closed by a test that fails without its fix, or is named
as a limit this release does not close.

| Found | Closed by, or the limit |
|---|---|
| removing or cheapening an irreversible area cost one `normal` card; the next migration landed `standard` | a loosening is weighed as each area it loosens, AS IT STOOD: removing the migrations area is itself `major` (decision, bet, review), and so is cheapening it; a lowered default and a loosened breadth limit stand as areas of their own (`loosened_areas`) |
| an emergency debt was paid by any card naming its sha, in any state, holding nothing | the debt is the class the emergency commit weighs by its parent's areas; a card pays it only when it is shaped at least that class, holds every record that weight owes and passed the owner's door where the class has one |
| a new branch's first push weighed the whole history by today's rules | `weigh --each --published-as <remote ref>` weighs only the commits no other remote-tracking ref carries (github-actions 1.6.0) |
| an area's `requires` (review, decision) was owed by a `standard` change and refused nothing | a record held on a card raises the change to the lightest class that keeps a card |
| a classless `chaotic` card was read as `normal` | a card stands at the heavier of its class and what its uncertainty asks, at commit and in FF-WORK-CLASSES |
| a JUnit root without `skipped` outvoted children that skipped everything; per-case `<skipped/>` and TRX timeouts passed | the report is read the way that proves the least: cases counted, a root only lowers what ran; TRX holds only when every executed test passed |
| archiving a program's finished parts left it with no card tree | a part of a staying card stays with it |
| an old lowering approval could be replayed | the approving `reshaped` entry must be new in the change |
| whoever carried a card through a door stopped being its author | only the signer is spared; the carrier stays an author |
| decision 16's guard made a card-reading gate's inner reading unreadable and the outer one HELD | a gate kind that reads the governed records says so (`READS_THE_RECORDS`), and `declared-rule-holds` refuses it as the proof of a record |
| hook and CI split paragraphs differently; a declared trailer written twice was read once | one paragraph split for every reader (a line of blanks is blank, as git's cleanup reads it); a declared trailer written twice is refused |
| an undo cost changed to an undeclared word was not loosening, and locked every later commit out | an undeclared word reads as the cheapest; the hook checks the areas a commit records before it records them |
| `decision` was held by a `kind: decision` line anywhere in a document's head | only the front matter, between its fences, says what a document is |
| `prove` printed "nothing to run" and passed when a MUST's command could not be read | a MUST whose vouched command cannot be read is refused |
| `no-committed-config-secret` missed `API_KEY`, `api_key`, `apikey`, `JWT_SECRET`, `Pwd`, `launchSettings.json` and YAML / properties files | secrets 1.4.2: snake and short names, launch settings, and `no-committed-config-secret-in-properties` |

**The limits this amendment names and does not close.**
- `decision` is held by a decision document anywhere in the tree -- a vendored kit's ADRs count -- and
  the hook reads it from the working tree, CI from today's checkout.
- `git commit --amend` is weighed by its new delta only; CI's `--each` weighs the whole commit.
- A dropped `feeds` is not read as loosening.
- `appetite` is held by any non-empty value; FF-DELIVERY-APPETITE reports a unit nothing reads.
- `weigh --base --head` without `--each` weighs by today's areas.
- A bet passage and a reshape approval are plain JSON: their names are recorded, not verified, and
  nothing checks that the history at HEAD is a prefix of the staged one.
- A card with neither class nor uncertainty is still passed over by FF-WORK-CLASSES (ADR-020
  decision 11); its commits are held by the floor.
- `PublicKeyToken` is admitted on purpose: it is public by definition.
- A reading records the absolute root it was taken at (`boundary.root`), so a tracked reading carries a
  local path. It stays: the boundary's decisive test traces a host's own path to that measured fact, and
  a reading without it would leave that difference with no ancestor. A host that minds re-takes its
  reading where it lives.

## Amendment 3 — an owner's mark is a signature, not a name (2026-10-17, owner-decided)

**Context.** Amendment 2 left one limit standing that an outside reading ranks first: an owner's
mark -- a door's passage (`signed_by`), a lowering (`approved_by`) -- is text in a card, and whatever
can write the card can write it, an agent included. Human oversight that an overseen agent can forge
is oversight in name only: the EU AI Act (art. 14) asks that oversight be effective, OWASP's LLM06
(excessive agency) names an agent that can grant itself what a person must grant, and NIST AI RMF and
ISO/IEC 42001 ask that accountability be attributable. The owner decided it is closed now.

**Decision.**
1. *Where a host declares `owner_signing`, a mark holds only in a commit the owner signed* (FF-WORK-
   SIGNED). git verifies the signature -- SSH signing, against the host's allowed-signers file in
   OpenSSH's format (`gpg.ssh.allowedSignersFile`); the kit holds no key and verifies nothing itself.
   The principal a signature names is the name the mark carries. A door is held when one of its marks
   is signed: an agent may PREPARE a mark, and it opens nothing until the owner signs a commit that
   carries it; a door whose only mark is unsigned is walked again in a signed commit -- history is
   never rewritten. A mark not yet committed is reported, never failed; marks that stood before
   signing was set up hold as they were.
2. *Who may sign changes only by a signature.* Every commit after the first that changes the
   allowed-signers file holds only if an allowed signer signed it. A key is retired, keeping what it
   signed, with OpenSSH's own `valid-before`.
3. *The setup is the owner's own act* (`signer --setup`, the delivery capability seeding the file):
   refused without an interactive terminal; the passphrase asked by `ssh-keygen` itself, never seen,
   stored or passed by the kit; a key that opens with an empty passphrase refused; git's config told
   the format, the file and the key, and never `commit.gpgsign` -- an agent's commits go on unsigned,
   and only the owner's carry marks; a round trip (sign, then verify against the file) before anything
   leans on it; the fingerprint printed to compare once. It declares `owner_signing` in the host's
   policy itself: the opt-in is the owner's act, and from then on the gate is the setup rule -- a host
   that declares it and names no key is told the exact command.
4. *The commit floor does not judge signatures*: git signs a commit after its message hook runs, so
   the mark is judged where it can be -- `check`, which the pre-push hook and CI run.
5. *Every acceptance a record carries, not only a card's.* The gate reads every JSON record in the
   binding places (the binding plane and the binding spaces): a door's passage, a lowering, a host's
   install, upgrade or takeover (`signed_by`), and a review whose reviewer is a name an allowed signer
   signs as -- so no record speaks in the owner's name unsigned. A reviewer who signs nothing (an
   auditor agent) stays a name, judged as before by separation of duties.
6. *A shallow clone is not measured*: the commits that carry the marks are not in it, and a reading
   that found no history would hold every mark as one that stood before the setup. It fails, saying
   so (`fetch-depth: 0`; the kit's CI template already fetches the whole history).
7. *A decision is the host's own* (closes NEW-8 of Amendment 2): a card's `origin` holds `decision`
   only when the document stands in a place the host's layout declares holds decisions (`holds:
   decision`) -- a vendored kit's ADR is the kit's, and a card that bet on it bet on nobody's ruling
   here -- and only its front matter, between the two fences, says what it is.

**Limits, said.** The first registration is trusted on first use, as an SSH host key is: the printed
fingerprint is the owner's one check. The terminal test guards against accident, not against an agent
that fakes a terminal -- what an agent cannot fake is the passphrase only the owner knows (a hardware
key that asks for a touch is stronger still, and works the same way). A machine where the agent runs
as the owner's user can read the key file: it cannot open it.

**Rejected.** *Sign every commit* (`commit.gpgsign`): every agent commit would stop at a passphrase,
or the key would be left open for it. *A token or a password the kit checks*: a second credential
store, held where the agent runs. *GPG*: a second toolchain where SSH keys already are. *Verify in the
commit-msg hook*: the signature does not exist yet. *A kit-made key*: whatever made it knows it.

## Amendment 4 — proof is weighed as the work is (2026-10-17, owner-decided)

**Context.** The owner: a one-line change must not run every suite the repository has; the system must
not hold its users hostage to their own process. The work was weighed (a standard change is one
commit), and its proof was not: `prove`, on every push, ran every command a MUST names.

**Decision.** An area declares what proves it (`proved_by`: commands a vouching declaration runs;
`default_proved_by` for paths no area claims). `prove` weighs what the push carries -- through `weigh`,
the one weigher -- and runs what the touched areas declare: the web app's tests for the web app, `check`
alone for prose. Everything runs when the change owes a decision (major and heavier), when an area it
touches declares no proof (the safe default, said by name), when the host weighs nothing, or on `--full`;
CI and a release run everything as they did. It aligns with change-based test selection (test impact
analysis, as Google's TAP and the affected-target builds of Bazel and Nx run it), risk-based testing
(ISO/IEC/IEEE 29119) and DORA's fast feedback.

**Rejected.** *The agent picks the tests*: a judgement where a computation exists, and an agent wrong
once is a push unproved. *Coverage-derived impact maps* (a test is selected by the lines it ran): a
second tool, a cache to keep honest, and a map that is wrong after every refactor; the areas are the
map the host already keeps. *Skip a test whose declared inputs did not change* (a digest over the files
a test is said to read): a declaration of dependencies is a guess that goes stale after a refactor, and
a cache that lies is a red change pushed green.

**Decision 2 -- nothing is proved twice on the same bytes** (Cardinal IX). A command that went green on
a clean tree is remembered in the observed plane by that tree's id and its own command string, and is
not run again while both are the same: a second push of what was proved, a retry after a refused push.
The key is the exact bytes -- any change at all, a dirty tree, a command that wrote into the tree, or
`--full` runs it again -- so the cache cannot be wrong where the command is deterministic, and a red run
is never remembered.
