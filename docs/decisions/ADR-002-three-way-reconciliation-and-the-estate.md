# ADR-002 — Three-way reconciliation, and the estate that makes it possible

- **Status**: Accepted
- **Date**: 2026-09-10
- **Supersedes**: nothing
- **Amends**: ADR-001 (the framework blueprint), by naming the second mutating door

## The situation

Everything this kit has proved was proved on a tree it created itself. `init` writes into a host
and then, on a second run, is by construction render + check: the create-once modes keep, the
vendor modes replace, and nothing has to be reconciled because nothing was ever supposed to have
moved. `upgrade` is the first verb that meets a tree it did not create, where a human has been
living and working, and where the kit that installed the tree is no longer on the machine.

Reconciliation needs three readings of every path, and each is a reading taken at its own moment:

| | reading | moment | where it comes from |
|---|---|---|---|
| **S** | what the kit SHIPPED into this host | T0, the last install | must be recorded — see below |
| **H** | what the host HAS now | T1, this run | measured from disk |
| **N** | what the NEW kit ships | T2, this run | computed from the new kit's declarations |

The first of the three is the whole problem. S is not on disk. A tree cannot state what it was
*given* — only what it *is*, and those two readings are indistinguishable from inside the tree.
Any attempt to recover S by looking at H is an inference from the tree about something a
declaration should have stated, which is the lesson this project has now paid for twice.

## Decision

### 1. The host keeps an ESTATE: the record of what it RECEIVED, at a stated moment

A new declared install, mode `estate`, class `binding`, target `.agents/project/estate.json`,
schema `estate`. It records, for every path the kit wrote: the path, its class, its install mode,
the capability that owns it, and the digest of the bytes as they were written — plus the kit
version and the moment the reading was taken, and the name of whoever approved the writes.

It is the host-side twin of `kit.lock.json` and it is the same idea applied to the other side of
the boundary: the lock says *what the kit is*, the estate says *what this host was given*. Both
are READINGS with a `taken_at`, never properties; both refuse rather than shrug; neither is ever
inferred from a walk of the tree.

The estate is written by `init` after render, and rewritten by `upgrade` after it applies. It is
declared by a capability like every other path, so `installs` remains the only write permission —
`upgrade` invents no authority `init` did not already have.

**A host with no estate cannot be upgraded.** Not "upgraded conservatively", not "upgraded by
assuming the disk is pristine": refused, by name, with the remedy stated. This is the cell most
likely to be quietly bridged, and bridging it would make every reconciliation below a fiction
dressed as a measurement.

### 2. Stewardship is DECLARED, and the reconciler reads it

`kit/stewardship.json` states, for each install mode, WHO OWNS the bytes after the install. The
reconciler holds no knowledge of any mode's name and no default:

| steward | modes | what it means |
|---|---|---|
| `kit` | `vendor` | the kit owns the bytes; the host is not supposed to edit them |
| `host` | `seed`, `reading`, `declaration` | created once; from then on the host's, and the kit never rewrites it |
| `derived` | `projection` | no history; deleted and rebuilt from its inputs, so there is nothing to reconcile |
| `host-space` | `space` | a root the host authors into; the kit accounts for the directory and never for its contents |

A mode with no stewardship row is a **refusal**, not a default. A default is how a new mode
arrives one day and is silently reconciled under whichever rule was cheapest to write.

### 3. The reconciliation table — every cell, including the refusals

`·` = absent. `=S` = present and equal to what was shipped. `≠S` = present and different.

| # | S | H | N | name | `kit` | `host` | `derived` | `host-space` |
|---|---|---|---|---|---|---|---|---|
| 1 | · | · | · | out-of-account | *no row* | *no row* | *no row* | *no row* |
| 2 | · | · | ✓ | `introduced` | create | create | create | create |
| 3 | · | ✓ | · | `unaccounted` | **REFUSE** | **REFUSE** | **REFUSE** | *out-of-account under a declared space root* |
| 4 | · | ✓ | ✓ | `collision` | **REFUSE** | **REFUSE** | **REFUSE** | n/a |
| 5 | ✓ | · | · | `forgotten` | forget | forget | forget | forget |
| 6 | ✓ | · | ✓ | `restored` | create | create | create | create |
| 7a | ✓ | =S | · | `retired` | orphan | orphan | forget | orphan |
| 7b | ✓ | ≠S | · | `retired-diverged` | orphan | orphan | forget | orphan |
| 8a | ✓ | =S | =S | `unchanged` | keep | keep | rebuild | keep |
| 8b | ✓ | =S | ≠S | `advanced` | replace | `available` (keep) | rebuild | keep |
| 8c | ✓ | ≠S | =S | `diverged-kept` | **keep + report, every run** | keep | rebuild | keep |
| 8d | ✓ | ≠S | ≠S, H≠N | `conflicted` | **REFUSE** | keep | rebuild | keep |
| 8e | ✓ | ≠S | ≠S, H=N | `converged` | keep (advance the record) | keep | rebuild | keep |

Notes on the cells that are not obvious:

- **3 `unaccounted`** — a file inside a governed plane that no reading explains. It is not deleted
  (the kit did not put it there and may not take it away) and not ignored (an unexplained path in
  a governed plane is exactly the defect `kit.lock.json` exists to make impossible). It is a
  refusal that names the path. Under a declared `host-space` root it is not a row at all — because
  a *declaration* said so, not because a folder looked like the kind of place a host writes in.
- **4 `collision`** — the new kit wants a path the host authored independently. No class permits
  overwriting bytes the kit never wrote. Refused, both moments named.
- **6 `restored`** — the host deleted a file the kit shipped and the new kit still ships. It is
  recreated. This is the same create-once rule `init` has always applied on a re-run, and the
  alternative — treating a deletion as a silent decision — would give a decision a home nobody
  can read. Taken knowingly: a host that means to be rid of a shipped path disables the capability
  that declares it.
- **7a/7b `retired`** — the first draft of this table had the kit DELETE a withdrawn file it owned,
  and refuse where the host had edited it. Building it settled the question without anyone
  choosing: **a capability's `installs` IS its write permission, so a path the new kit no longer
  declares is a path nothing gives it permission to touch.** The kit cannot delete there, and the
  cell collapses to `orphan` for every steward whose plane the kit does not rebuild wholesale.
  `derived` is the exception and not an exception to the law: `render` already tears its whole
  plane down and rebuilds it under an authority the projection plane grants, so a withdrawn
  projection is `forget` — the row goes, and render removes the file.
- **7a/7b `orphan`** — the file STAYS and the estate KEEPS the row, marked
  orphaned with the version that withdrew it. The path therefore remains accounted for by a
  declaration rather than becoming, at the next run, an unexplained file in a governed plane. The
  kit stops shipping it; it does not stop knowing about it.
- **8b `available`** for `host` — the create-once contract is not suspended by an upgrade. The new
  content is REPORTED as available and never written. A kit that "just updates" a seed is a kit
  that edits the host's own words.
- **8e `converged`** — the host had already made precisely the change upstream now ships. A naive
  implementation reports this as a conflict; it is agreement, and the estate simply advances.

### 3b. `upgrade` is a GATE IN FRONT OF THE INSTALLER, not a second installer

`init` already carries out every install mode correctly. A second write path in `upgrade` would be
a second home for the one thing that must never have two, and it would drift from the first the
week after it was written. What was missing was never the writing — it was the judgement of
whether the writing is safe. So `upgrade` reconciles, refuses or passes, and then calls `init`.

That leaves one hazard, and it is the one this design nearly shipped: `vendor` replaces wholesale.
That rule is correct for a foresight with **no record to read** — nothing could tell it whether
the host had touched the file. The reconciliation HAS read one, so its verdict is handed to `init`
as data, and the mode's own foresight yields to it. It is not a precedence ladder and not an
override: it is the same question answered with more evidence, arriving as a value, so that
foresee and apply remain ONE decision *across two verbs*. A test compares the plan of an upgrade
with what the upgrade did, and a smoke run caught the silent overwrite before any test existed.

### 4. The state of a legitimately locally-modified shipped file

Cells **8c** and **8d**. The recorded open question named three failures, and they are three:

- *silently overwrite* — destroys work the kit has no way to know was wrong;
- *silently keep* — worse, because it is also a decision and it leaves no trace: the host then
  believes it is on the new version while carrying the old bytes at that path. Two readings, both
  internally correct, and neither able to detect the other. That is Cardinal III's fatal stage,
  not its visible one;
- *ask a human every time* — a prompt leaves no artefact, cannot be re-read, cannot be diffed,
  and answers differently on Tuesday. It is a decision with no home.

The fourth answer, and the one taken:

1. The divergence is a **named state with two moments**, computed in the PLAN, before a byte moves.
   `--plan` and apply are one decision, so what the operator reads is what would happen.
2. `diverged-kept` (8c) is **kept and reported at every single upgrade**, forever, until it is
   resolved. It never becomes invisible, which is the whole failure of silently keeping.
3. `conflicted` (8d) **refuses the upgrade as a whole**, naming the path, the moment the kit shipped
   it and the moment this reading was taken. Not the path skipped and the rest applied: a partial
   upgrade is a host in a state no version describes.
4. The only way past is the door this kit already has: `upgrade --approve <who>`, a named human
   accepting the exact plan they have read. The adoption is then RECORDED in the estate on the row
   itself — `adopted_by`, `adopted_at`, and the digest that was superseded. The decision outlives
   the terminal session, can be read a year later, and can be contradicted.

The kit does not archive the superseded bytes. It refuses BEFORE the write, so the host still has
its own file at the moment it decides, and the host's version control is the archive. That
assumption is stated here rather than relied on quietly: the kit requires `vcs.git` to install at
all, so it is a measured fact and not a hope.

### 5. Doctrine self-versioning — partially closed, residual gap DECLARED

The recorded gap: upstream changes a cardinal, text in the host's law changes that the host never
wrote, and no artefact records the host's consent.

**Closed:** doctrine ships as `vendor`, steward `kit`, so an upstream change reaches a host as cell
8b, appears in the plan **path by path** before anything is written, and is applied only under
`upgrade --approve <who>` — which writes the approver's name and moment, and the new `kit_version`,
into the estate. The artefact recording the host's consent now exists and is dated.

**Not closed, and declared rather than implied — `GAP-DOCTRINE-SEMANTICS`:** consent is recorded
against a PATH and a VERSION, not against a CHANGE. The plan says *this doctrine file will be
replaced*; it does not say *this cardinal now says something else*. A host that has locally amended
its doctrine is protected (8c/8d), but a host that has not is consenting to bytes it has not read.
Closing it needs doctrine to carry its own versioned identity independent of the kit's, which is a
different slice and is recorded as a gap, not improvised around here.

## Rejected alternatives

**A. Recompute S from the new kit's payload — "what an install would have produced".**
Cheap, needs no estate, and wrong at the one moment it matters. It can only ever reconstruct what
the *current* kit would ship, so a file that upstream changed between versions reads as
locally-modified in every host that never touched it: cell 8b is misreported as 8d, and every
clean upgrade becomes a conflict. Worse, the failure is silent in the other direction too — a host
whose file happens to match the new payload reads as pristine whatever it did in between.
Rejected because it is an inference from the tree standing in for a declaration, and because a
reconciliation built on it can never distinguish "unchanged" from "changed twice".

**B. Trust the host's version control as the record of S — diff against the install commit.**
Attractive: the history is already there, and it is exactly a record of what arrived and when.
Rejected on the boundary. It makes the kit's core correctness depend on somebody else's
bookkeeping — a rebase, a squash, a shallow clone, a subtree merge, a host that installed on a
branch since deleted, or a `.agents/` that was never committed, and the record is gone or means
something else. It also cannot answer for a path at all: git knows what the *commit* contained,
not what the *kit* claimed to ship, and the two differ exactly where a human edited before
committing. A name is not a referent, and "the install commit" is a name nobody can measure.

**C. Ship the whole previous kit inside the host and diff kit-to-kit.**
Honest — the old kit could state what it shipped, using the lock it already carries. Rejected as
an over-materialisation: it vendors ~98 files of a *previous version* into every host to answer a
question a 100-line reading answers, it makes every host carry a second copy of an interpreter
that must never run, and it still does not record WHO approved anything or WHEN. It also creates
a tree inside the host that the host's own class-total gate would then have to be taught to
ignore — a new exemption to protect an artefact whose only job is bookkeeping.

**D. `upgrade` as a second installer, with its own write path.**
The obvious shape, and the one every "upgrade command" in the wild has. Rejected because the two
installers would then hold the same knowledge — which mode writes what, in which order, under
which scope — and would be correct together only for as long as somebody kept them in step.
Synchronisation by discipline is not a mechanism. It would also have hidden the defect that
actually mattered: with one installer, the vendor mode's unconditional replace was visible as a
contradiction with the reconciliation's verdict, and had to be resolved. With two, both would have
been internally correct and the host's edits would have vanished quietly.

**E. Interactive per-file prompting (the `dpkg` conffile experience).**
Proven prior art, and deliberately not taken. Its record is a terminal session; the resolution
lives in the operator's memory and in `.dpkg-dist` files that accumulate unread. This kit already
owns a better instrument — a door, with a name and a moment, recorded in a declaration — and
using two different mechanisms for one kind of decision would be a second home for it.

## Consequences

- `upgrade` is a mutating verb with a plan, a door, and refusals; its default when the three
  readings cannot be reconciled is REFUSAL, never a best effort.
- A host installed before the estate existed must take a first estate reading through `init`
  before it can be upgraded. That reading ASSERTS that what is on disk is what was shipped, so it
  is itself an approved act, recorded by name.
- Every zero the reconciliation prints is a counted zero: the number of paths surveyed, the number
  in each state, and the states with none of them are printed by name.
- `GAP-DOCTRINE-SEMANTICS` is open and recorded.
