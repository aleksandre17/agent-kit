# ADR-015 — The whole line: from an upstream change to a host lesson and back

- **Status**: Accepted (owner-delegated, 2026-09-13: "see the full line from start to end, add what is missing, complete the system")
- **Date**: 2026-09-13
- **Amends**: ADR-001 (the blueprint), by declaring the END-TO-END chain the slices were built as parts of, and the order in which the remaining parts are finished
- **Sources**: both proposals read in full; ADR-001…ADR-014; the 2026-09-13 audit (92 rows); the first real migration map on host #2; a clean-host install listed against the blueprint's Part VI drawing

## The situation

Fourteen ADRs built the framework as PARTS, each green, each live-walked where it could be. What no
document states is the LINE the parts are links of — and a line is only as strong as the link nobody
drew. Measured today, three links of it were drawn in the blueprint and never built, and one was never
drawn at all:

- the blueprint's arrow ① says the payload crosses into a host as **vendor + lock**, and the host's
  `.agents/kit/` is a *pinned copy of the kit*. Installed on a clean host, `.agents/kit/` holds nine
  doctrine pages and **no interpreter** — a host can run nothing by itself: no `check` in CI, no edit-time
  hook, no offline upgrade;
- Part V says the ecosystem GENERATES from measured facts. Ten detectors measure; **no capability reads a
  single fact they emit** (`grep` of `kit/capabilities` and `kit/seeds` for `stack.|ci.|quality.|data.|legal.`
  finds nothing). The kit measures the repository it lands in and then adapts to nothing;
- the blueprint lists a `fitness` capability — the **abstract arrow**: a host declares its layers and the
  allowed direction, the kit enforces it generically. It is not among the nine capabilities;
- the drawing's arrow ④ — **a lesson returns upstream as TEXT, never as a dependency, once seen twice** —
  has no mechanism. Every lesson host #2 taught the kit this week crossed back by hand.

## Decision — the line, declared

```
 UPSTREAM (L0–L3, its own release)                         HOST (L4–L7, its own release)
 ─────────────────────────────────                         ─────────────────────────────
 1 author changes kit ──► fresh-repo + two-host tests ──► 2 RELEASE: version, changelog, signed digest
                                                                 │ ① vendor + lock (runnable copy)
                                                                 ▼
 3 init  P0 boundary ─► P1 probe ─► L4 profile (facts + moment)
         P2 resolve ─► P3 THE DOOR (L5 answers) ─► P4 seed ─► P5 shadow/estate
         P6 PROJECT from facts + answers:  roles · runtime surfaces · per-module laws ·
                                            doctrine (`when` = requires on a fact) · docs · CI
         P7/P9 gates at their declared stance ─► P8 check
 4 WORK  runtime reads its SERVED files ─► edits ─► served settings call the VENDORED hook ─►
         host-declared gates (laws, the ARROW) judge ─► receipt (L7 life)
         cards: intake → shaped(appetite) → bet(owner) → in-flight → verified(evidence) → landed → learned
         the continuity capsule externalises position before anything can be lost
 5 LEARN evaluation (L7 quality) · the ledger: a row seen twice is a rule already paid for
         ├─ host-true ─► promoted IN the host (binding / law / gate)
         └─ universal ─► ④ exported UPSTREAM as text (a proposal) ─► ADR ─► step 1
 6 UPGRADE fetch target release ─► three-way reconciliation ─► changelog delta ─► back to 3/P6
```

Every link is a declaration read by an interpreter that holds no policy; every crossing of the
upstream/host boundary is one of exactly three — ① payload, ③ contract (schemas + MANIFEST), ④ lesson as
text. Answers never leave the host (②).

## What is built, and what the line still lacks

Built and verified: P0–P5, P7–P9 (ADR-006), P6 for roles/doctrine/runtime entry files (ADR-004, ADR-013),
estate + three-way reconciliation (ADR-002), adoption (ADR-003), provenance (ADR-008), versions (ADR-009),
leaving (ADR-010), succession (ADR-011, ADR-012), the Shape-Up card lifecycle with WIP and age gates, run
receipts and journal (L7 life), evaluation grammar (L7 quality).

The line lacks, in the order the line itself imposes — each link is useless until the one before it holds:

| Order | Link | What is missing | Gaps it closes |
|---|---|---|---|
| A | runtime surfaces | adapters leave the kit core as bundles; open publisher set | owner's agnostic rule; R1 residue (ADR-014, in flight) |
| B | ① the host carries its kit | a RUNNABLE pinned copy of the kit in the host (interpreters + schemas + manifest), recorded in the estate; a release artifact (version, changelog, the kit's own signed digest) | H1; ADR-008 "signing the kit's own lock"; upgrade fetch + changelog delta |
| L | the layout is the drawing, at least | the tree's shape as ONE machine-readable declaration; the Part VI drawing and a both-sides FLOOR check (every drawn path exists, by its drawn name) are its projections; every path beyond the drawing is a declared row naming its improvement | owner's rule (amendment 1); upstream floor gaps; H3–H6 placement; drawn `eject`, `init.lock`, `kit.lock.json` |
| C | the enforcement line — **form decided in ADR-017, cut into slices C1–C4** | served settings → vendored hook → HOST-DECLARED gates; the abstract ARROW capability; per-directory served entry files; `core.hooksPath`; CI projection from the `ci.*` fact; ONE DISPATCH PORT: an orchestrator in either runtime starts a worker in either runtime (Claude Code ⇄ Codex, `claude -p` / `codex exec` behind the port), with one lease per path, one worktree per worker, one receipt stream, and both runtimes' hooks calling the same vendored interpreter: limbs of one body, never two nervous systems (owner, 2026-09-13) | E1; blueprint `fitness`; H7; O-7 per-module laws |
| D | facts drive projection | capabilities consume detector facts: `quality.tests.*` → a verification profile, or a DECLARED gap when no tests exist; `stack.*.workspaces` → per-module law blanks + arrow blank; `data.migrations` → a roster suggestion; `ci.workflows` → the CI projection. Profile drift: `check` compares the recorded reading with a fresh probe and reports, never overwrites | Part V; L4 drift |
| E | the knowledge plane | the BINDING plane `.agents/knowledge/` (private/<role> · shared), as drawn; preview checks exactly what the act checks. *Cut by amendment 2: `retained`, carry-into-seed and a lane for foreign formats are OVERTURNED* | K1/H2, V1 (S1, S2, X1 overturned) |
| F | the management spine | the continuity capsule as a kit capability (one CAS writer, a gate that says when the capsule no longer describes the tree); `evidence/<card>/` so `verified` has a referent; ARCHIVE dead by location; the intent documents (vision · roadmap · registry) seeded blank under the knowledge capability's Diátaxis form; ONE REAL EVALUATION run (amendment 4); THE CARD IS THE ONE HOME of work: board, roadmap and capsule become its projections, never parallel instruments; APPETITE on every bet and a CIRCUIT BREAKER, so a bet that overruns stops and returns to the owner and is never silently extended; a waiting idea EXPIRES into the archive, so nothing becomes a graveyard (owner, 2026-09-13: "mixed up, endless, lost, no logistics"); CHECKLISTS WITH COMPUTED STATUS: every card carries acceptance criteria (Definition of Done; Given/When/Then), each criterion names its PROOF (a gate id, a test name, an artifact path), and `check` COMPUTES each item as proved · failed · unproven. Nothing is ticked by hand, and the board shows N/M proved per card (owner, 2026-09-13: "it was laid down, then never marked whether it was done") | H3, H4, B1; L7-quality closed live; the owner's named failure: work laid down, never finished, lost |
| G | ④ the lesson returns | a `learned` card or a ledger row marked universal is EXPORTED as a proposal text addressed to upstream — never a dependency, never automatic; seen twice first | the framework cannot learn from its hosts without a human copying |

After G, the framework is complete for 1.0 and the migration runs (the map floors at zero undecided once
C and E hold). Honestly post-1.0, and recorded as such: OTel `gen_ai` naming, `--explain`/SARIF, TUF
freeze and transparency log, detector `any_of`, one home for the stance and status vocabularies, POSIX
no-clobber rename, the trust class for foreign content, judging the judge.

## One body — how the framework and its host are one organism (owner, 2026-09-13)

*Restated on the owner's instruction: "the two systems must be one body, with the natural structural
function of successfully established systems."*

Today they are two bodies. The host is driven from OUTSIDE — `python <framework>/kit/interpreters/cli.py
--root <host>` — and the framework repository manages its own development by hand, with none of the
instruments it installs into others. Successful systems are one organism with a membrane, never a tool
pointed at a project:

- **Genome and organism.** The upstream kit is the genome: it changes only by selection — a lesson seen
  twice, returned as text (④), accepted in an ADR, released. The host is the organism: it lives by its
  metabolism — cards, capsule, receipts. One body, two rates of change, and exactly three things cross
  the membrane (①③④). That is the structure; the drawing already had it.
- **One nervous system.** Every event a host produces — a runtime hook, a git hook, a CI run, an operator's
  command — reaches ONE interpreter (the host's own pinned copy, link B), is judged by ONE set of declared
  gates (link C), and leaves ONE receipt stream (L7). After a migration there is no second enforcement
  layer beside the kit's: a parallel old hook system is a second nervous system, and two nervous systems
  in one body is the Cardinal-III failure in its most expensive form.
- **SELF-HOSTING is the proof.** A compiler compiles itself; git is developed in git; the platforms that
  last run their own delivery on themselves. **The framework repository becomes host #0 of its own kit**,
  the first host link B lands in: its ADRs, ledger, cards and continuity run on the kit it ships. Then
  host #0 and host #2 are two installs of one kit, the lesson loop (④) runs between two living hosts
  instead of by hand, and "is the framework complete" gets its only honest answer — *it can run its own
  development*. Until it can, it is a library, not a framework.

Consequence for the order: link **B** lands first in the framework repository itself (host #0), then in
the clone of host #2. Every later link is walked live in BOTH.

## Amendments — the owner's rules, 2026-09-13 (restated on record)

**1. The drawing is the FLOOR, never the ceiling.** *Owner: "what is on the drawing must be at least
like that; what you improve, refine, add as mechanism, pattern, function — that is the question of
improvement."* Every path in the blueprint's Part VI drawing, on both sides, exists in its drawn place by
its drawn name. Anything beyond it is welcome when it improves, and says so in a declared row. Applied:
`adapters/` outside the kit stays (an ADDITION: the kit core names no product) · `kit/runtimes/` must
exist and holds the NEUTRAL runtime-class grammar, never a product · `estate.json` stays beside the drawn
`project/kit.lock.json` only because they are two truths (what the tree IS vs the lock it was GIVEN) ·
`host.lock` covers every mutating verb; the drawn `runtime/init.lock` still exists or is named as that
lock · `eject` exists as a verb. ADR-002/007/010 are amended to this extent. Link **L** carries it.
Measured floor gaps, 2026-09-13: UPSTREAM `kit/VERSION`, `kit/doctrine/`, `kit/roles/`,
`capabilities-lib/`, `playbooks/`, `kit/runtimes/`, `capabilities/fitness/`, `interpreters/hooks/`,
`tests/unit`, `examples/`; HOST H1–H7 and `docs/work/`, `docs/archive/` under `docs/`.

**2. The old system is conceded NOTHING; the old adapts to the new.** A migration is a triage with two
verbs, **re-declare in the new form | delete**, and the default for anything that does not fit is DELETE:
git history is the archive. OVERTURNED as concessions to a prior system: S1 `retained` (nothing stays on
the old's terms), S2 carry-into-seed (old content is RE-AUTHORED, never piped into seeds), X1 (a move in a
format the kit cannot read is refused at preview, with no lane for it), and the "705 moves" reading of K1
(a host's memory is distilled, never relocated wholesale). Kept, because the NEW system needs them on
their own merits: the knowledge plane (H2) and V1.

**3. Outcome objectives — the framework must prove it is not a bureaucracy.** The grammar is SRE's
SLI/SLO. The observability capability ships the SLI grammar BLANK: token share per work class, cost per
task (p90 peak), window, source = receipts, class carried by the card. The HOST declares its objectives;
the kit never knows a number. Host #2's baseline is governance **78%** of all tokens, p90 peak **118k**.
**The migration is DONE only when both are below baseline over the declared window.** A framework that
does not change that ratio is the best-designed bureaucracy, and that is now a measured gate, not a hope.

**4. The quality loop closes before 1.0.** Link F runs ONE real evaluation through Part VIII's grammar:
one suite on one role, accepted vs candidate on the same cases, verdict as a receipt, the promotion gate,
and the owner's signature. A grammar no one has run is an unverified claim.

**5. Standing delegation of design decisions.** *Owner: "I confirm that it must be whatever is the best
concept, the best pattern, the best structure, the best modern architecture, the best standard and
decision, agnostic — decide on that basis."* Inside the line, a design question is decided by the
orchestrator against ONE criterion — the best form known to the field, agnostic — and recorded with its
rejected alternatives. It is not brought to the owner as a menu. Still the owner's: the migration
(Consequences), real spend, key custody (signing), and anything irreversible outside this repository.
First application: host #0's install approval, signed `agent-linkB(owner-delegated:ADR-015)`, STANDS. An
approval that names its delegation and its ADR is the canonical delegated-authority form. Re-signing it
with the owner's name would claim a signature he never made (Cardinal V).

**6. Cheaper and better than a bare agent, BY CONSTRUCTION — not by a comparison ritual.** *Owner:
"we are building a modern system; why should the architecture not be arranged so the result is better
than alone?"* Measured on host #2: every call opens on ~12–15k tokens of prose rules (laws ~5k, charter,
role definitions) and 22 hooks, before any work is done. A bare agent pays none of that. It pays
instead for ARCHAEOLOGY: re-searching the repository every time (reads outnumber writes 125 to 1). The
kit wins only if it removes the bare agent's cost without adding its own. Design law for every link,
checked at review:
- **A rule the machine checks is never loaded as prose.** Enforcement lives in gates and hooks, which cost
  no context. The always-loaded entry is a short INDEX with a budget the kit gates, and everything else is
  pulled by task vocabulary (progressive disclosure, the Agent-Skills pattern).
- **Ground is precomputed and pulled, never re-searched.** The kit supplies detector facts, the knowledge
  plane and distillates, so a task starts from a map instead of a grep.
- **Verification is targeted.** A change runs the tests it affects (test-impact selection), and the full
  suite runs once at the gate.
- **Routing is part of the kit.** A task that needs no spawn gets none, and mechanical work goes to the
  cheapest capable model.
- **No double-running.** Amendment 3's objectives are read PASSIVELY from receipts. Nothing is run twice to
  prove it.

**7. The cure is deletion, never another rule.** *Owner, 2026-09-13: "put this in the right place, so a
new session carries it out."* The diagnosis of why a system built on the best patterns still never
became what was wanted:
1. every failure added a rule and none was ever deleted, so a model reading a hundred rules on every step
   spends its effort navigating them instead of working;
2. the orchestrator's own charter turns every sentence into a process (echo, ledger, capsule, packet,
   check), so a simple question costs minutes. That is how it was built, not the model's nature;
3. "done" was measured by process (green tests, an ADR written, the ledger updated), never by the
   outcome the owner wants: fast, correct, simple;
4. the same mind builds the system, judges it and uses it, so it cannot see the excess. The owner sees
   it, every time.
Therefore the framework is built with FEW, SHORT rules that a machine checks (amendment 6), ONE measure,
the outcome (amendment 3), and everything that does not serve that outcome is deleted. Every link is
reviewed against this, and a link that adds prose rules a machine could hold is not done. For the prior
ecosystem of host #2: **when the line reaches it, the FIRST step is deletion, not migration.** What does
not serve the outcome is removed before anything is carried, and whatever survives is re-declared
(amendment 2).

**8. A place for everything: the layout declaration becomes the RECORDS MAP.** *Owner, 2026-09-13: "a
structured, organised, logistical system where everything has its place, never chaos again; the path
work must travel, as the big management companies do; so that we know where and when to look for what."*
The field's answer is records management (ISO 15489) and information architecture: every KIND of
information has one declared home, one writer, a moment it is read, and a lifecycle. Link L's layout
declaration already names every place, so it is extended rather than doubled: each entry gains
`holds` (the truth that lives there), `writer`, `read_when` (the task trigger that pulls it into
context) and `lifecycle` (how it ages and where it goes). Consequences:
- the floor gate refuses a document in a place whose `holds` it does not match, and a write by a
  non-declared writer (Law 15, the Kind Law, made mechanical);
- context is retrieved through the map by `read_when`, never by searching the tree (amendment 6);
- every card state names the artifact it produces and that artifact's place, so the path of work is on
  the map too.
Built as link L3, right after L2, on the declaration L1 and L2 produced.

**9. Every agent receives exactly what it needs at that moment: nothing more, nothing less.** *Owner,
2026-09-13.* This is Cardinal VIII (no client depends on what it does not use) bound to CONTEXT. It is
the same identity as interface segregation in code, need-to-know and least privilege in security (NIST),
and context engineering and progressive disclosure for agents. It is a binding, not a new cardinal.
Mechanism:
- **A context compiler.** `role × task × stage → the exact set`: knowledge pulled through the records map
  by `read_when` (amendment 8), the narrowest tool loadout the task needs, memory by the task's vocabulary,
  and detector facts (link D). An agent never assembles its own context by searching.
- **Both directions measured, passively from receipts,** with the field's metrics for retrieval (RAGAS):
  context PRECISION falls when something was loaded and never used; context RECALL falls when an agent had
  to search for something the map already held. Both join amendment 3's objectives.
- **Correction by declaration.** A recall miss widens a `read_when`, a precision miss narrows it. Each is
  recorded and signed, never automatic, so the map learns and rules do not pile up.
Built with L3 (the map) and C (receipts that record what was loaded, and what was then searched).

## Why this order, and not the audit's

The audit ordered by RISK TO THE MIGRATION. The line orders by DEPENDENCY: the enforcement line (C) cannot
run in a host that cannot run the kit (B); facts cannot drive a CI projection (D) that has no served
surface to land in (A, C); the capsule (F) cannot be migrated into a plane that does not exist (E). A
walking skeleton is built along the dependency, thin, end to end — and then thickened. The migration risk
is retired by the same order, because every blocker the map found sits on this line.

## Rejected alternatives

**A. Keep closing the audit's list in risk order.** Rejected: it builds links whose predecessor does not
hold — a hook that no host can execute, a CI projection with no surface — green in isolation and dead on the
line. That is exactly how fourteen green ADRs produced a kit that could not serve the runtime it described.

**B. Declare the framework complete and let the migration discover the rest.** Rejected: the migration is
irreversible-in-spirit for a working product repository with live work in it; a host must never be the
place a framework is finished. The map already proved the kit was not ready; the line says why.

**C. Put the continuity capsule, the ledger and the lesson export into doctrine only.** Rejected: they are
the owner's named failure — work laid down and lost — and a failure that has cost real work is answered by
a mechanism, not by a paragraph (the doctrine existed; the loss happened anyway).

## Consequences

- The remaining work is the links A, B, L, C, D, E, F, G, finished one agent at a time, each walked live
  on host #0 and the clone of host #2 before it is called done.
- "How much is left" is answered by position on this line, never by a percentage of a list.
- **The migration is an OWNER DOOR (owner, 2026-09-13: "when you reach the migration, do not start it —
  say you are ready").** After G, the orchestrator STOPS and reports readiness; nothing moves in host #2
  until the owner says so.
- The migration of host #2 starts only after G and the owner's word; the map is re-run then, must read zero undecided, and
  the migration is done only when amendment 3's objectives hold over their window.
