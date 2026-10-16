---
kind: decision
authority: canonical
owns: drawing-conformance
---

# ADR-021 — The tree is the drawing: every drawn path is present, pending, or realised by a decision

- **Status:** Accepted (2026-10-15; owner-delegated under ADR-015 amendment 5). The owner's instruction:
  *"agent-kit must be able to carry out exactly the architecture the proposals draw — one structured whole,
  no gaps, no logical breaks, no incompatibility, every part working as one body; change only to make the
  architecture, structure, mechanisms and functions better, never worse."*
- **Amends:** ADR-015 amendment 1 (the drawing is the floor) by giving the floor a third legal state;
  ADR-004 (doctrine) and ADR-018 (taken capabilities) by naming where their decided forms sit on the drawing.
- **Sources:** blueprint Part VI (both boxes), layout proposal §2–§3, `docs/reference/UPSTREAM-LAYOUT.json`,
  `kit/capabilities/governance/host-layout.json`, and a measurement of three trees on 2026-10-15 at `4bf492d`
  + `dotnet-project`: this repository (upstream side), this repository's own `.agents` (host #0), and a second
  host (`geostat_in_out`, kit 0.1.6).

## The measurement

**Upstream, against the left box — 12 drawn paths absent, 12 present paths undrawn.** Absent: `kit/doctrine/`
with `CARDINALS.md`, `protocol.md`, `lifecycle.md`, `economy.md`, `risk.md`, `verification.md`, `environment/`;
`kit/capabilities-lib/`, `kit/playbooks/`, `kit/interpreters/hooks/`, `examples/`. Undrawn and undeclared:
`.agents/`, `.claude/`, `.codex/`, `.githooks/`, `AGENTS.md`, `CLAUDE.md` (host #0's own tree), `adapters/`.

**Host, against the right box — the same shape on both hosts measured.** 19–22 drawn paths absent; and:

| Drawn | Installed instead | Defect |
|---|---|---|
| `docs/work/cards/<id>`, `docs/work/BOARD.md` | `.agents/project/delivery/cards/`, `.agents/generated/delivery/BOARD.md` | the kit's own `host-layout.json` declares `docs/work/cards/` (pending F) while `delivery` installs elsewhere: **one place, two homes** |
| `.agents/project/doctrine/` — the host's numbered laws | `laws.md` + `laws/` + `law-scopes.json` + `doctrine/doctrine.json` | `host-layout.json` declares both `doctrine/` and `laws/` as `host-law`: **one kind, two places** |
| `CLAUDE.md` [BINDING with GENERATED BLOCKS] — host-authored law, a marked generated region | the whole file a projection, 6.6 KB of framework explanation, no host content | the host cannot author its own entry file; the always-loaded part breaks the kit's own L0 ≤ 3k budget (context engineering) |
| `.agents/project/roster.json` | none; the roles page says "the roster IS the set of overlays" | a drawn place the kit has already decided against, still reported as *pending F* |
| `.agents/generated/INDEX.md` | that, plus `.agents/generated/governance/INDEX.md` | one name, two referents (Cardinal VII) |

**The doctrine row is the sharpest.** ADR-004 decided that the kit ships **no** cardinal — conduct doctrine
arrives as a doctrine BUNDLE, mechanism doctrine is carried by the capability that explains it — and
`UPSTREAM-LAYOUT.json` nonetheless lists all seven `kit/doctrine/` paths as *pending F*: a promise to build
what an accepted decision forbids. The surface lies (Cardinal V). And because no bundle is published anywhere,
a host that wants its owner's cardinals cannot take them: the second host reads **"THE DOCTRINE IN FORCE IS
NONE"** while its owner's eight cardinals exist only in the prior system of host #2.

## Decision

1. **A drawn path has exactly three legal states.** *Present* at its drawn place; *pending* a named link that
   will build it; or **realised** — its truth lives at another declared place, by a named decision that says
   why that form is better. `realised_as: {"path": …, "decision": …}` is an optional field of a layout entry
   (expand-only, schema v1). The floor gate checks the realised path exists, prints the row, and refuses a row
   that is both pending and realised. "Pending" for a path an accepted decision forbids is a defect. Where the
   decision is taken and its form is not yet built, the *replacement* carries the link
   (`realised_as.pending`): the row prints PENDING with both the link and the decided place, so the drawn form
   is never promised and the undecided build is never shown green.
2. **Doctrine sits where ADR-004 put it, and the drawing says so.** `kit/doctrine/` and its mechanism pages
   are *realised* in each capability's payload (ADR-004 ②, L3a decision 1). `CARDINALS.md` and the conduct
   chapters are *realised* as doctrine bundles **published beside the kit at `bundles/<id>/`**, the same
   publication form as `adapters/` (ADR-014): one complete capability per directory, never inside `kit/`,
   taken by a host through `take` (ADR-018). The first bundle is **`bundles/cardinals/`** — the owner's eight
   cardinals, one sentence each as `says`, the full statement in the bundle document. The kit still supplies
   no default norm: a host holds the cardinals only by taking them. This narrows ADR-004 ③'s "the kit's own
   repository ships no bundle" to what that sentence protects — the **issued manifest** ships none, so the
   carrier is still proven on a host that declared none (`test_145`–`147`). The conduct chapters the drawing
   places beside the cardinals (protocol, economy, risk) are realised as a `bundles/conduct/` bundle pending
   link F; environment chapters are any bundle's `requires` on a profile fact; skills and playbooks are
   bundle genres pending link C. Mechanism pages (`lifecycle`, `verification`) are realised in the
   capability that owns the mechanism.
3. **The work plane lives in `docs/work/`, as drawn.** `delivery` installs its cards space at
   `docs/work/cards/`, its board projection at `docs/work/BOARD.md` and its evidence space at
   `docs/work/evidence/`; `docs/work/CONTINUE-HERE.md` is the capsule's place (ADR-020). An existing host is
   moved as one planned act — the generalisation of the act L3a decision 2 performed once by hand — read
   from a `relocations` list **declared by the capability beside the install it moved** (`from`, `to`,
   `decision`, optional `referenced_by`). Per capability rather than one manifest list: the capability owns
   its write scope, so the old name of a place has its home with the place. `to` must be one of that
   capability's own install targets — a relocation never declares a place. `upgrade` reconciles the host
   *as if* the moves had happened (so `--plan` is the plan carried out and writes nothing); `init` carries
   them out as its own phases (`relocations` reads and refuses, `relocate` renames) under the run's one hold
   and journal, before the write set is foreseen — so even a plain `init` can never seed a blank at the new
   name beside the host's bytes at the old one. A move is a rename, verified by an h1 measured at both
   names; the estate's rows are carried to the new name and the move is appended to the estate's
   `relocated` record. It never rewrites content: where a host document named in `referenced_by` still
   points into `from`, the run is refused whole (KIT0068) with the exact restatement printed, the owner
   edits their own file, and the move then proceeds. Both places holding something is two homes: refused.
4. **Host law has one home: `.agents/project/doctrine/`.** The records map already names stances and
   numbered laws as one kind, `host-law` (binding doctrine the host adds), so the drawing's single rule
   directory is the better form. The law page, the law scopes and the scoped law pages move under it by the
   same relocation, beside the doctrine stances; two capabilities write there, each its own files (the
   one-owner rule is per path, held by the resolver). `law-scopes.json` names its pages by path, so its
   relocation declares `referenced_by` and the owner restates them.
5. **Entry files are binding with one kit span, inside a budget the host writes.** `CLAUDE.md` and
   `AGENTS.md` (and every scoped one) are host-owned: a surface render row names a `span` and a `seed`; the
   file is written once from the seed and the kit owns only the text between `kit:begin <span>` /
   `kit:end <span>` — the one marker grammar the kit already had (`derivation`, ADR-020), now with a public
   `span`/`spliced`/`withdrawn`, never a second one. Reproduction (`check`) and the anti-clobber rule judge
   the span only: the serve record carries the span's digest and the seed's, so the host's text around the
   span is never in question, a stale span beside host edits is still served, an edit inside the span is
   refused, a file the kit last served whole is converted once, and a surface that stops being served
   withdraws only its span (an untouched seed goes with it). The span carries what binds on every turn —
   the laws — and POINTS to the pages a runtime reads when a question arises (doctrine, roles: section
   field `points`) instead of inlining them. Its size is the published measure `served_span_bytes`, held
   by the corpus plane's ordinary budget (ADR-019 decision 9): the host writes the number; the kit ships no
   default ceiling, because a budget is a number a human writes about their own corpus.
6. **The roster is the overlays.** `.agents/project/roster.json` is *realised* as `.agents/project/roles/`
   (the decision the roles capability already states). `.agents/generated/governance/INDEX.md` is renamed
   `CAPABILITIES.md`, so `INDEX.md` names one thing.
7. **What exists beyond the drawing is declared, or it is a defect.** Host #0's own tree (`.agents/`,
   `.claude/`, `.codex/`, `.githooks/`, `AGENTS.md`, `CLAUDE.md`), `adapters/` and `bundles/` get upstream
   rows naming their decision (ADR-015 "one body", ADR-016 decision 8, ADR-014, decision 2 here), in the
   optional field `declared_by`. A drawing names the directories where it is **exhaustive** (`closed`; upstream:
   the root and `kit/`), and every *tracked* child of a closed directory is covered by a row or it fails by
   name — without that check a `declared_by` row would be decoration. The capability-namespaced binding and
   projection directories on a host (`project/<capability>/…`) are kept: a capability's directory is its
   write scope, a better form than one undivided plane. They are **already declared, once**: by the
   capability's own `installs`, which `FF-KIT-CLASS` holds total over the tree. A host-layout row for each
   would be a second home for the same declaration (Cardinal III), so none is added.
8. **The floor holds on a fresh clone.** A drawn place inside the OBSERVED plane is named and never
   judged (`floor.observed`): it holds what a run left behind, which no version control carries — this
   generalises the rule that applied only to a surface whose clone is declared ephemeral. An empty
   declared space already carried its marker (`space`). Probes match their patterns against what the
   repository CARRIES — tracked plus untracked-not-ignored, `Workspace.carried()` — never the raw
   filesystem, so a reading cannot depend on a dependency directory and the match is bounded by the
   repository rather than by a walk (measured: a third-party `.sln` under `node_modules` was a host fact).
   One port asks version control anything (`ports/vcs.py`; the ratchet's reader moved into it). And a
   clone must receive the bytes that were committed: governance seeds `.agents/.gitattributes` (`* -text`)
   beside `.agents/.gitignore`, because a checkout translating line endings turned every pinned file into
   a lock failure on a fresh Windows clone (measured by `test_350`).

## Order of slices

| Slice | Lands | Proof |
|---|---|---|
| S1 | `realised_as` (+ its `pending`), `declared_by` and `closed` in the layout grammar and the floor gate; every upstream row restated, the roster row realised | upstream floor green, 0 undeclared tracked children of `.` and `kit/`; a row both pending and realised is refused (negative test) |
| S2 | `bundles/cardinals/`; take on both hosts | `test_bundles`: a fresh pinned host takes it, its roll names all eight cardinals UNANSWERED, `check` green |
| S3 | capability `relocations` + the `relocations`/`relocate` init phases + the reconciliation's moved view; delivery, law and capability-index targets moved; KIT0068 | `test_relocation` 330–333: an ancestor host's `--plan` names every move and writes nothing; upgraded, each place is the same bytes at its new name, the estate re-keyed and recording each h1, `check` green; a scope page still named at the old place refuses until restated; two homes refused |
| S4 | surface `span`/`seed`; span-aware serve record, admission, withdrawal; derivation's public span grammar; pointer sections; measure `served_span_bytes`; both adapters 1.1.0 | `test_entry_files` 340–346: seeded with the markers; host text outside survives render and `check`; an edit inside is reported and refused; a file served whole is converted through `upgrade`; doctrine and roles pointed to, not inlined; a withdrawn surface leaves only the host's text; a budget below the span fails `check` |
| S5 | `floor.observed`; `ports/vcs.py` + `Workspace.carried()`; probes over what the repository carries; seed `.agents/.gitattributes` | `test_fresh_clone` 350–351: an installed host, committed and cloned, checks green on the clone; a project file in an ignored directory is never a fact, one the repository carries is; unit host #0 floor green |

## Rejected alternatives

- **Restore `kit/doctrine/CARDINALS.md` inside the kit** to satisfy the drawing literally. Reverses ADR-004:
  the kit would install an opinion in every host, and a cardinal could no longer be answered by stance.
- **Delete the undrawn rows of the drawing** (`roster.json`, `kit/doctrine/`). Loses the record of what was
  drawn and why it changed; the drawing is the floor, and a realised row keeps both.
- **Leave the work plane in `.agents/project/delivery/`** and edit the drawing to match. The cards are host
  knowledge read by people as much as by agents, and the corpus plane (ADR-019) reaches `docs/`; a card hidden
  in the binding plane is outside every reachability, index and evidence route that ADR-019 and ADR-020 built.
- **Move binding files by a one-off script per host.** A migration nobody can replay; the relocation list is
  a declaration the next host gets for free.
- **One `relocations[]` list in the manifest.** A second home for each install's old name, kept by a party
  that does not own the place; the capability that moved an install is the one that can say where it was.
- **Rewrite a host document's references during the move.** The document is binding — the host's words,
  which no upgrade reads for writing (ADR-002); a rewrite would be the kit authoring them.
- **A second marker pair for entry files (`BEGIN/END GENERATED`).** Two grammars for one idea — where a
  computed span stands — and the day one changed, the other would go on finding nothing.
- **A kit default budget of 3 kB.** A ceiling is a number a human writes about their own corpus; a
  default would be the kit's opinion of every host's context, unanswerable by stance.
- **Leave law in governance's places and relabel the doctrine row.** Keeps four places for one kind the
  records map already unifies, against the drawing, to avoid a one-time declared move.

## Amendment 1 — a space is there when a clone receives it (2026-10-16, owner-delegated)

S5 held the floor on a fresh clone of a host the kit had just installed. The second host, upgraded,
still failed it on every clone: `.agents/project/roles/` was opened before spaces carried a marker, so
the working tree held a bare directory and the clone held nothing. Both doors that install decided
`keep` from the directory alone -- `init` because a space was install-once, `upgrade` because a
directory has no digest and its reconciliation therefore reads UNCHANGED. Host #0 had two such
spaces itself (`corpus/`, `doctrine/laws/`).

**Decided:** a space is present when its directory and its marker are (`space.carried`), and that
one rule is read by both doors: `init`'s foresight for the space modes (`space.MODES`), and the
reconciliation's presence for them, so a marker-less space is RESTORED and its steward answers
`create`. The marker is the only write; nothing the host put in the space is read or touched.

*Rejected:* a check-time exemption for an empty space, which would make the floor accept a place
no clone has; and a one-off repair per host, which the next host would need again.

Proof: `test_fresh_clone` 352 (both doors, then clone and `check`), mutation-checked on each half.


## Amendment 2 — a reading is replaced through a door (2026-10-16, owner-delegated)

The second host's tree moved on purpose: a test project was added, and `node_modules` stopped being
evidence. `reading-current` then failed on every `check` and named no remedy, and the only way out was
to move `.agents/project/profile.json` aside and let `upgrade` take a new reading, unsigned. The same
host is a monorepo whose Angular client lives at `platform/apps/inout/frontend/web/`, and
`node-workspace` read `package.json` at the root only, so a Node host read as having no Node.

**Decided:**
- Verb `retake`: a fresh reading compared fact by fact with the recorded one. A reading that holds is
  not retaken. `--plan` prints each moved fact (`+`, `-`, `~`); without `--approve <who>` it is a door
  (`doors.refuse`) and writes nothing; approved, it writes the fresh reading with `retaken`
  (`signed_by`, `signed_at`, `replaces`: the moment of the reading it replaced). That is an optional
  property, so `profile` stays at version 1 (ADR-009 decision 5). `KIT0072` refuses a retake on a host
  holding no reading, or one that would not honour its schema. What the new facts admit stays the
  answer's: `upgrade --plan` names it.
- `reading-current` names the remedy in its failure.
- `node-workspace` matches `**/package.json` in what the repository carries (ADR-021 decision 8, so a
  dependency directory is never evidence), and still emits the root's `workspaces` when declared.
- A take records its `source` relative to the host when it lies inside it (a submodule, a vendored
  kit), so every clone reads the same row; absolute only when it lies outside.
- A served entry's pointer section ends its line, so the next heading opens its own paragraph.

*Rejected:* re-taking the reading inside `upgrade` (it would impose a new composition basis nobody
stated); keeping the replaced reading beside the new one (two readings in the tree are two answers to
one question, and git already holds the old bytes); a `**/*migrat*` migrations pattern alongside the
node change (it matches the kit's own `migration-map` files, a detector that fires on a lookalike).

Proof: acceptance `test_retake` 404–406, unit `test_entry_sections`; each mutation-checked (door
removed, remedy removed, absolute source, pointer newline removed).
