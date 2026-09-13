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
| C | the enforcement line | served settings → vendored hook → HOST-DECLARED gates; the abstract ARROW capability; per-directory served entry files; `core.hooksPath`; CI projection from the `ci.*` fact | E1; blueprint `fitness`; H7; O-7 per-module laws |
| D | facts drive projection | capabilities consume detector facts: `quality.tests.*` → a verification profile, or a DECLARED gap when no tests exist; `stack.*.workspaces` → per-module law blanks + arrow blank; `data.migrations` → a roster suggestion; `ci.workflows` → the CI projection. Profile drift: `check` compares the recorded reading with a fresh probe and reports, never overwrites | Part V; L4 drift |
| E | knowledge + migration plumbing | a receiving BINDING plane for host knowledge (`.agents/knowledge/`, as drawn); `retained`; carry-into-seed; preview checks exactly what the act checks | K1/H2, S1, S2, X1, V1 |
| F | the management spine | the continuity capsule as a kit capability (one CAS writer, a gate that says when the capsule no longer describes the tree); `evidence/<card>/` so `verified` has a referent; ARCHIVE dead by location; the intent documents (vision · roadmap · registry) seeded blank under the knowledge capability's Diátaxis form | H3, H4, B1; the owner's named failure: work laid down, never finished, lost |
| G | ④ the lesson returns | a `learned` card or a ledger row marked universal is EXPORTED as a proposal text addressed to upstream — never a dependency, never automatic; seen twice first | the framework cannot learn from its hosts without a human copying |

After G, the framework is complete for 1.0 and the migration runs (the map floors at zero undecided once
C and E hold). Honestly post-1.0, and recorded as such: OTel `gen_ai` naming, `--explain`/SARIF, TUF
freeze and transparency log, detector `any_of`, one home for the stance and status vocabularies, POSIX
no-clobber rename, the trust class for foreign content, judging the judge.

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

- The remaining work is seven links, A–G, finished one agent at a time, each walked live on the clone of
  host #2 before it is called done.
- "How much is left" is answered by position on this line, never by a percentage of a list.
- The migration of host #2 starts only after G; the map is re-run then, and must read zero undecided.
