# PROPOSAL — Agent framework layout: the four-class seam, the vendored-with-lockfile distribution, and the declared detector

> **Kind: PROPOSES (root Law 15).** This document lives under `docs/architecture/proposals/` and is therefore
> **NON-BINDING**. Nothing here is law until an ADR restates it under `docs/architecture/decisions/` and is
> Accepted. It contains ONE decided design, not a menu; the alternatives listed at the end are REJECTED,
> not offered.
> Date of the readings it rests on: 2026-09-09. Kit version measured: 1.9.0.
> Scope: structure only. No file is moved, renamed or created by this proposal.

## 0. The question, stated as the owner stated it

> *"core is agnostic, yet it still holds folders and files that keep it from BEING a framework."*

Both halves are true and not in tension — together they are the diagnosis. Agnosticism is a property of
**content**: a grep for project-domain literals across `.agents/core` is clean (measured this session).
Framework-hood is a property of **class**: whether every shipped file knows what it *is* — vendor payload,
host binding, generated projection, or ephemeral state — DECLARED, not implied by a folder name.

`.agents/core` is agnostic content in undeclared classes. One undifferentiated tree ships an interpreter
(`hooks/`, `tools/`), a doctrine (`CARDINALS.md`, `strategy/`), a knowledge genre (`feedback/`), one-time
seeds (`templates/`), a release ledger that grows forever in every host (`UPGRADE-NOTES.md`), text dead by
location (`archive/`), its own unit tests, and its own `__pycache__`. A framework is not a folder of good
files; it is a **declared payload with a declared install contract and declared upgrade semantics**.

### The live defect that proves the point

`.agents/core/agents/architect.md` and `.agents/system/agents/architect.md` both exist, both declare
`name: architect`, and they DISAGREE: the core copy declares `tier: apex` and `tools: Read, Grep, Glob,
Bash`; the system copy omits the tier and adds `Edit, Write`. Two homes for one truth. Neither is wrong
from where it stands — which is exactly the failure Cardinal III names: *both remain internally correct
while the system speaks with confidence and lies.* An agent dispatched today gets whichever one the
runtime resolved, and no participant can detect the contradiction locally.

This is not a bug to patch. It is the missing seam, showing itself. The design below exists to make that
duplication structurally impossible rather than periodically noticed.

## 1. The decision in one paragraph

**The framework is a vendored payload governed by a manifest, installed by a generic interpreter, adapted
by declared detectors, and upgraded by a three-way lockfile reconciliation.** Every path under the host's
`.agents/` belongs to exactly one of four CLASSES — VENDOR, BINDING, PROJECTION, EPHEMERAL — the class is
declared in the kit's `MANIFEST.json` and never inferred from a folder's name; upgrade replaces VENDOR,
regenerates PROJECTION, never touches BINDING, and never reads EPHEMERAL. Role definitions, doctrine
chapters, templates and runtime adapters all obey this one rule, so a host that has customised a role and
a host that has not survive the same upgrade by the same mechanism.

### The seam rule, in one sentence

> Every file under `.agents/` is exactly one of **VENDOR** (framework payload — never edited downstream,
> replaced wholesale on upgrade), **BINDING** (host truth — never written by an upgrade, only ever created
> once if absent), **PROJECTION** (derived from VENDOR + BINDING — never hand-edited, always reproducible
> by `render`), or **EPHEMERAL** (observed state — never committed, never upgraded, safely deletable), and
> that class is DECLARED in the kit manifest, not read off the path.

Corollary, load-bearing: **a projection is not a copy.** `.claude/agents/architect.md` must be output —
deletable at any moment, reconstructible byte-identically from `kit/roles/architect.md` + host overlay +
runtime descriptor. The moment a projection can be edited and survive, it is a second home and Cardinal
III is already lost.

## 2. Decided layout — the framework's OWN upstream repository

The framework is its own repo. Its root is not the payload; the payload is one subtree of it. This
separation is the single most common miss in home-grown kits: they ship their own test suite, their own
CI, and their own history into every consumer.

```
agent-framework/                     # upstream repo — NOT what lands in a host
├── kit/                             # THE PAYLOAD. Exactly this subtree is vendored into a host.
│   ├── MANIFEST.json                #   ★ the one declaration: every shipped item, its class, its
│   │                                #     install path, its applicability condition. Data only.
│   ├── VERSION                      #   semantic version of the payload
│   ├── doctrine/                    #   portable identities and protocol — text, no project vocabulary
│   │   ├── CARDINALS.md             #     the eight identities (canonical declaration)
│   │   ├── protocol.md              #     ← today's B.md, under a name that states its contract
│   │   ├── economy.md, risk.md, …   #     today's strategy/ chapters, one concern per file
│   │   └── environment/             #     chapters that apply ONLY under a detected fact
│   │       ├── windows-worktrees.md #       gated by `when: {os: windows}`
│   │       └── posix-shell.md
│   ├── roles/                       #   role ARCHETYPES — the base layer of the role overlay
│   │   ├── architect.md             #     declares capabilities + duty order; no host vocabulary
│   │   └── …
│   ├── capabilities/                #   skills — reference bodies loaded on demand
│   │   └── architecture-standards/
│   ├── playbooks/                   #   command bodies (today's commands/)
│   ├── interpreters/                #   ★ the only executable payload
│   │   ├── hooks/                   #     runtime-invoked enforcement
│   │   ├── verbs/                   #     init · render · check · upgrade · eject
│   │   └── ports/                   #     Manifest, Workspace, Runtime, Probe — the abstract seams
│   ├── detectors/                   #   ★ declared environment probes (data, not code)
│   │   ├── node-workspace.json
│   │   ├── python-project.json
│   │   └── …
│   ├── runtimes/                    #   adapter DESCRIPTORS: how a runtime wants its projection shaped
│   │   ├── claude-code.json
│   │   └── codex-cli.json
│   ├── schemas/                     #   project.schema.json · profile.schema.json · manifest.schema.json
│   │                                #     · role.schema.json · detector.schema.json
│   └── seeds/                       #   ONE-TIME copies into the host's BINDING plane (never re-applied)
│       ├── project.json.template
│       ├── laws.md.template
│       └── work/…
├── tests/                           # the framework's own suite — NEVER vendored
│   ├── unit/                        #   today's hooks/test_*.py, tools/test_*.py
│   └── acceptance/
│       └── fresh-repo/              #   ★ installs kit into an empty scratch repo, end to end
├── examples/                        # reference installs, illustrative only (Law 15 kind: ILLUSTRATE)
├── docs/                            # framework docs, ADRs about the framework itself
├── CHANGELOG.md                     # ← today's UPGRADE-NOTES.md, upstream only
└── README.md
```

**Why `kit/` is a subtree, not the repo root.** A vendoring installer must be able to say "copy exactly
this directory"; if the payload were the root, every consumer would inherit the framework's CI, tests,
`.gitignore` and `docs/`. This is the Terraform-module and Helm-chart convention (the unit of distribution
is a directory with a manifest at its head), and it makes the acceptance test honest — it may read only
from `kit/`.

## 3. Decided layout — what the framework INSTALLS into a host repo

```
<host-repo>/
├── .agents/
│   ├── kit/                    [VENDOR]      verbatim copy of upstream kit/ at a pinned version.
│   │                                         Committed. Read-only by convention AND by gate.
│   │                                         Deleting it and re-vendoring is always safe.
│   ├── project/                [BINDING]     the host's own truth. Upgrades never write here.
│   │   ├── project.json                      the manifest the interpreter reads (schema-validated)
│   │   ├── profile.json                      ★ measured environment facts + the timestamp of the reading
│   │   ├── kit.lock.json                     ★ every vendored path → source, version, sha256
│   │   ├── roles/                            OVERLAYS ONLY — the delta over kit/roles/<id>.md
│   │   │   ├── architect.md                    (front-matter delta + host-specific appendix)
│   │   │   └── react-specialist.md             (host-only role: full body, no base)
│   │   ├── doctrine/                         host laws + bindings (ROOT-LAWS, ARCHITECTURE-BINDINGS,
│   │   │                                     authority.json) — the concrete bindings of the cardinals
│   │   └── roster.json                       which roles exist in THIS project
│   ├── knowledge/              [BINDING]     durable host knowledge. The framework ships ZERO content.
│   │   ├── private/<role>/
│   │   └── shared/
│   ├── generated/              [PROJECTION]  everything derived. Deletable; `render` rebuilds it.
│   │   ├── roles/<id>.md                     kit archetype + host overlay, composed
│   │   ├── skills/<id>/                      neutral capability projection
│   │   └── runtimes/<runtime-id>/…           the material each adapter needs
│   └── runtime/                [EPHEMERAL]   gitignored. telemetry · receipts · ground · guards · runs
├── .claude/                    [PROJECTION]  thin locators into .agents/generated + settings
├── .codex/                     [PROJECTION]  same, per its own adapter descriptor
└── CLAUDE.md                   [BINDING with GENERATED BLOCKS]  host-authored law; the cardinals block
                                              between BEGIN/END markers is projection and is diffed by check
```

Five planes, five single responsibilities, each answering a different question: `kit/` = *what the field
knows*; `project/` = *what is true here*; `knowledge/` = *what we have learned here*; `generated/` = *what
follows from the first two*; `runtime/` = *what we observed just now*.

**Root `CLAUDE.md` is deliberately mixed** — the one place classes meet, tolerable only because the mixing
is marked: generated regions are delimited and `check` fails on drift inside them. Everywhere else,
mixing classes in one file is refused.

### Strangler path from today's shape (a migration, not a rename)

| Today | Becomes | Class |
|---|---|---|
| `.agents/core/` | `.agents/kit/` | VENDOR |
| `.agents/system/` | `.agents/project/` | BINDING |
| `.agents/knowledge/` | unchanged | BINDING |
| `.agents/skills/` (generated) | `.agents/generated/skills/` | PROJECTION |
| `.agents/runtime/` | unchanged | EPHEMERAL |
| `.claude/agent-memory` junction | replaced by an adapter descriptor + projection | PROJECTION |

The rename `core → kit` is not cosmetic: "core" names *importance*, "kit" names *provenance*. Under a
four-class seam the only thing a top-level name must tell a reader is which class they are standing in,
and "core" answers a question nobody asked (Cardinal VII — an unresolved name is resolved by assumption).

## 4. What is ruled OUT of the framework, item by item

The owner's complaint is specific, so the ruling is specific. Each item below is ruled either OUT of the
payload with a named new home, or IN with its class declared.

### `archive/` — **OUT, entirely. Deleted from the payload, not relocated.**
Two files of superseded doctrine. Root Law 15 already calls `archive/` dead by location; a framework that
vendors dead text ships it into every host forever, where a future reader will find it, be unable to date
it, and obey it. Superseded doctrine's one home is the upstream repo's **git history**, indexed by
`CHANGELOG.md`. If a chapter is worth keeping it is not archived — it is current. If it is not current, no
host needs a copy.

### `feedback/` (19 files) — **OUT as a folder. The genre is a lifecycle stage, not a home.**
"Feedback" records *how a rule was learned*, not *what it governs*. Cardinal VI is explicit that a register
whose rows never leave it has become a graveyard; a folder named after the intake is a permanent graveyard
by construction. The 19 files split three ways by one test — *what does this govern?*

- **Portable identity** (`primacy_of_the_idea`, `growth_oriented_open_mechanisms`, `verification_doctrine`,
  `construction_over_convention`) → doctrine already promoted; they belong in `kit/doctrine/` under the
  concern they govern — and several are restatements of Cardinals I, II and V, where the correct action is
  deletion, not relocation. A cardinal restated in a second file is exactly the two-home failure.
- **Environment-conditional** (`powershell_sandbox`, `windows_worktree_pitfalls`, `worktree_isolation`) →
  `kit/doctrine/environment/`, each declaring `when: {os: windows}` / `when: {vcs.worktrees: true}`. True,
  portable, and *inapplicable to most hosts*; projecting them unconditionally is how a framework teaches a
  Linux team about PowerShell quoting. Cardinal VII made structural — the chapter loads because the
  boundary was measured, not assumed.
- **Host incident** (`commit_attribution`, `lead_logistics`, anything naming this project's workflow) →
  `.agents/knowledge/shared/` in the host. Not framework payload at all.

### `UPGRADE-NOTES.md` — **OUT of the payload. Upstream `CHANGELOG.md`.**
An append-only release record is unbounded and monotonically increasing. Vendoring it means every host
carries the full history of versions it never ran, and the file's size grows with the framework's age
rather than the host's needs. The host's legitimate need is narrower and different: *what changed between
the version I have and the version I am moving to*. That is answered by the `upgrade` verb reading the
upstream changelog for the version range in `kit.lock.json` and printing the delta — a projection at the
moment of need, not a vendored artifact. Debian's model: the changelog ships as documentation upstream;
the *decision* a maintainer faces is computed at upgrade time.

### `B.md` — **IN, as `kit/doctrine/protocol.md`.**
The content is framework-essential — it is the binding protocol every agent obeys at its boundary. The
*name* is the defect. `B.md` is a nickname: it is unresolvable by anyone who was not present when it was
chosen, it sorts meaninglessly, and it cannot be searched for. Cardinal VII again — a name is not a
referent. A framework's file names are part of its public contract; single letters are private vocabulary
escaping into a public surface.

### Role-specific knowledge (`knowledge/private/<role>`, 13 roles) — **OUT. Host BINDING, always.**
The framework ships the **topology** (the directory contract, the record template, the retrieval protocol)
and **zero content**. A framework that ships remembered facts ships one project's experience as another
project's premise. It also cannot be upgraded: knowledge is append-only and host-owned, so it fits neither
VENDOR (replaced) nor PROJECTION (regenerated). It is BINDING, and the framework's only duty is to declare
where it lives and what a record must contain.

### The 13/14 named roles — **the real cut, and the resolution of the live defect.**
Rule: **the kit ships role ARCHETYPES; the host declares its ROSTER; the projection composes them.**

- `kit/roles/` holds archetypes true of the discipline anywhere — architect, debugger, explorer,
  orchestrator, project-manager, senior-*-developer, junior-executor — each declaring capabilities, duty
  order and reference class, in no repository's vocabulary.
- `project/roles/` holds **overlays only**: the *delta* over an archetype (front-matter overrides plus an
  appendix), never a full second body. A host-only role (`engine-specialist`, `plugins-specialist`,
  `react-specialist`) holds a full body, because it has no base to overlay.
- `project/roster.json` declares which roles exist — **open by declaration** (Cardinal II): a new role is a
  file plus a roster row, never an edit to any mechanism.
- `generated/roles/<id>.md` is the composition, and the ONLY file any runtime reads.

Kustomize base + overlay, exactly. It dissolves the measured `architect.md` duplication: the two divergent
bodies become structurally impossible, because the host plane cannot hold a full body for a role with a
base — stated as an invariant in §8, FF-KIT-OVERLAY.

### Also ruled out, less contentiously
- `hooks/test_*.py`, `tools/test_*.py` → upstream `tests/unit/`. A host runs `check`, not our suite.
- `__pycache__/` → EPHEMERAL, and it currently sits inside what we call the portable kit. The manifest
  enumerates what ships, so anything unlisted simply cannot travel.
- `settings.template.json` → into `kit/runtimes/claude-code.json`. A template named after one runtime's
  settings file is that runtime's concern, not the doctrine's.

### Ruled IN, with class
`CARDINALS.md`, `strategy/` (→ `doctrine/`), `commands/` (→ `playbooks/`), `skills/` (→ `capabilities/`),
`hooks/` + `tools/` (→ `interpreters/`), `*.schema.json`, `githooks/`, `templates/` (→ `seeds/`, with
**seed semantics**: created once if absent, never re-applied, never diffed — the host owns its
`project.json` the moment it exists). `INDEX.md` stays the task router but becomes a PROJECTION: its rows
point at paths whose existence depends on roster and profile, so a hand-maintained index drifts within two
releases.

## 5. Distribution and upgrade — DECIDED: vendored copy, manifest-driven, lockfile-reconciled

**The framework is copied into the host and committed there. Every copied path is recorded in
`project/kit.lock.json` with its upstream path, the payload version, and a sha256. Upgrade is a
three-way reconciliation against that lock.**

This is copier's answers-file model plus Debian's conffile semantics plus Terraform's lockfile, and each
contributes exactly one idea:

- **copier / cruft** — the host keeps an *answers file*, so a re-run is an UPDATE, not a re-generation.
  Ours is `project.json` + `profile.json`. *Breaks:* copier merges template output; we never merge VENDOR.
- **Debian conffile** — a vendor file the local admin modified is a DECLARED state; the upgrade reports
  rather than silently clobbering or keeping. Ours: sha ≠ lock → `locally-modified`, halt. *Breaks:*
  Debian blesses local edits as normal; we treat them as a defect to be lifted into an overlay.
- **Terraform lockfile** — provenance of every dependency is committed and reviewable in a diff.
  *Breaks:* Terraform locks remote artifacts; ours locks present files, so it is also a drift detector.
- **XDG / FHS** — vendor-default (`/usr/share`) vs local-override (`/etc`) vs mutable-state (`/var`) is a
  fifty-year-old answer to three of our four classes. *Breaks:* FHS is system-global, not repo-local, and
  has no PROJECTION class — it has no renderer, so it needs no fourth.
- **Rails / Django convention-over-configuration** — layout carries meaning; Django's project-vs-app split
  is the same instinct as our kit-vs-project split. *Breaks:* their conventions are enforced by a run-time
  loader; markdown doctrine has no loader, so ours must be gate-enforced or they are mere suggestion.
- **Helm values / Kustomize overlay** — the base is never edited; variation is a declared delta. Adopted
  wholesale for roles and doctrine. *Breaks:* Helm renders at deploy time into a target that never sees the
  chart; our host commits its projection, so we need drift detection Helm does not.
- **oh-my-zsh `custom/`, chezmoi source-vs-target** — one declared extension dir upgrades never touch, and
  a rendered target never edited in place. Adopted as `project/` and `generated/`. *Breaks:* oh-my-zsh has
  no upgrade contract for the base beyond `git pull` — the submodule failure mode rejected below.

**Upgrade algorithm** (the `upgrade` verb, stated as behaviour so an ADR can bind it):
1. Fetch the target payload version; read its `MANIFEST.json`.
2. For every VENDOR path in the current lock: if sha matches → replace freely. If not → record
   `locally-modified`, do not write, continue collecting.
3. Paths present in the old manifest and absent from the new → delete (this is how `archive/` ever leaves
   a host; without manifest-driven deletion, vendored kits accumulate forever).
4. Paths in the new manifest with class SEED → create only if absent.
5. BINDING → never read for writing, only validated against the new schemas; a schema field added upstream
   surfaces as a named, actionable failure (this already works today via `bootstrap --check`).
6. PROJECTION → delete and re-render from scratch. Never merged, never diffed against its old self.
7. Emit the changelog delta for the version range, then run `check`. Halt non-zero if any
   `locally-modified` path remains.

The host survives an upgrade without drift because after step 6 **no projection has a history** — it is a
pure function of VENDOR + BINDING, so there is nothing for it to drift *from*.

## 6. The lifecycle verbs and their ports

**Decided set: `init` · `render` · `check` · `upgrade` · `eject`.** Five, not six.

| Verb | Does | Reads | Writes |
|---|---|---|---|
| `init` | measure the host, draft bindings, seed once, render, check | VENDOR, host filesystem | BINDING (create-if-absent), PROJECTION |
| `render` | recompute every projection from scratch | VENDOR + BINDING | PROJECTION only |
| `check` | run the fitness functions; report, never repair | all four classes | EPHEMERAL (the reading) |
| `upgrade` | re-vendor per §5 and re-render | upstream payload + lock | VENDOR, PROJECTION, lock |
| `eject` | dissolve the seam: reclassify all VENDOR as BINDING, drop the lock, record the decision | VENDOR + lock | BINDING |

**`adapt` is deliberately NOT a verb.** Detection is a *phase* of `init` and `upgrade`, and its output is
`profile.json`. Making it a separate verb would create a second occasion on which the environment is
measured, and two readings of one reality is precisely the observational form of Cardinal III — each
reading locally correct, the contradiction undetectable from either. One reading, one home, one timestamp.

**`eject` is kept** though rarely used: a framework that cannot be left cannot honestly be adopted, and the
alternative to a declared exit is an undeclared one — a host that quietly edits VENDOR files and stops
upgrading. Eject makes leaving a *declared state* (Cardinal V) instead of a decay nobody dated.

**Ports** (Cardinal IV — the verbs are the interpreter and hold no policy):
- `Manifest` — reads the payload declaration and the host bindings. The ONLY source of "what is true here".
- `Workspace` — filesystem effects, root-resolved once at the boundary (today's `hooks/_root.py` already
  does this correctly and is the model to generalise).
- `Probe` — executes a detector declaration against the workspace and returns facts. Generic; knows no
  stack.
- `Runtime` — projects generated material into an adapter's expected shape, per its descriptor.

No verb contains a project name, a stack name, a role name, or a runtime name. Every one of those arrives
as data. That is the test for whether this design is real: **grep the interpreters for any proper noun; a
hit is a defect.** (Today's core passes the domain-literal form of this test — measured clean — which is
why the fix is structural, not a cleanup.)

## 7. "Adapt to the repo it lands in" — the detector, and why it stays open

A **detector is a declaration, not a function.** `kit/detectors/*.json`, schema-validated:

```jsonc
{
  "id": "node-workspace",
  "evidence": [ {"file_exists": "package.json"},
                {"json_path": {"file": "package.json", "path": "workspaces"}} ],
  "emits": { "stack.node": true, "stack.node.workspaces": "$1" }
}
```

It contains no branch, no closure, no fetch — it states what would be true and what that would mean. The
`Probe` port is the single generic evaluator. **Output goes to exactly one place**: `project/profile.json`,
which carries every emitted fact *and the timestamp of the reading* — because a measured environment is a
reading of reality, and a reading that does not state when it was taken cannot be contradicted, only
believed (Cardinals III and VII).

Consumers — doctrine chapters, roles, seeds, playbooks — declare applicability as `when: {fact: value}` in
front-matter; the renderer evaluates that generically. Therefore a new stack is a **new detector file**, a
new conditional chapter is a **new front-matter line**, and nowhere in the system is there a list of known
stacks or a switch on one — Cardinal II by construction, not by vigilance. The foreclosed failure is the
one every home-grown scaffolder hits: a `detect_stack()` if-ladder, a closed enumeration each new
ecosystem must be granted permission to join. Today's `bootstrap.py` detects architecture with exactly
such an inline ladder (hardcoded build-file and extension lists); here that becomes six detector
declarations, and the code reading them contains none of those names.

**Honest limit:** detectors answer *what is present*, not *what is intended* — a monorepo about to go
polyglot detects as whatever it is today. So `profile.json` is BINDING, not PROJECTION: the host may
correct a measured fact by hand, and `check` reports divergence between the recorded reading and a fresh
probe rather than overwriting the human's correction. Measurement informs; it does not rule.

## 8. Fitness functions — each with the measured failure it prevents

Proposed only where a failure has actually been observed or is structurally guaranteed. No gate is proposed
speculatively.

- **FF-KIT-CLASS** — every `.agents/` path resolves to exactly one manifest-declared class; unclassed paths
  fail. *Prevents:* the current condition — `__pycache__`, tests and an append-only ledger sitting inside
  the "portable kit" because nothing declares what the kit is.
- **FF-KIT-OVERLAY** — no `project/roles/<id>.md` may carry a full body for an id present in `kit/roles/`.
  *Prevents:* the measured divergence between `core/agents/architect.md` and `system/agents/architect.md`
  (same `name`, different `tools`, different `tier`).
- **FF-KIT-LOCK** — every VENDOR path's sha256 matches `kit.lock.json`. *Prevents:* silent downstream edits
  to vendor files, invisible today because there is no lock and no second install to compare against.
- **FF-KIT-PURE** — no proper noun (project, stack, role, runtime) in `kit/interpreters/`. *Prevents:*
  policy leaking into the interpreter (Cardinal IV). Today's clean grep is the baseline it ratchets.
- **FF-KIT-SECOND-HOST** — CI installs `kit/` into an empty scratch repo and runs `init` then `check`.
  *Prevents:* the stated gap — **the kit has never been installed into a second repository, so portability
  is claimed and not measured.** The highest-value gate here: the only one testing the central claim.

## 9. Rejected alternatives

1. **Git submodule for `.agents/core`** (today's assumed distribution, printed by `bootstrap.py`) —
   rejected: a commit pointer means a fresh clone yields an EMPTY `.agents/` and every hook silently no-ops
   until someone runs `--recurse-submodules`; no per-file drift detection, no manifest-driven deletion of
   retired files, and it cannot install *adapted* content — the whole point of a starter kit.
2. **Publish as an npm/pip package** — rejected: imposes a host toolchain the framework must not assume (a
   Go or Java repo gains `node_modules`), hides doctrine in a dependency directory where it is unreviewable
   in a diff, and hooks must run before any install step has ever executed.
3. **Generator-with-eject, CRA-style one-shot scaffold** — rejected: no upgrade path by design. Kit 1.9.0
   with an append-only release record proves upgrades are the normal case; this strands every host at its
   install date.
4. **One flat `core/`, seam enforced by discipline** — rejected under Cardinal III: synchronisation by
   discipline is not a mechanism. The divergent `architect.md` is proof the discipline already failed while
   everyone believed it held.
5. **Ship a fixed set of 12–14 named roles** — rejected under Cardinal II: a closed roster makes a new role
   a framework release. `engine-specialist` and `plugins-specialist` are this project's vocabulary and were
   never payload candidates.
6. **Three-way text merge of VENDOR into locally-modified files** — rejected: a merged doctrine file is one
   nobody authored and nobody can date, and a conflict marker inside a law is worse than a halt.

## 10. GAPS met — declared per Cardinal VI, not improvised around

Two questions arose that our doctrine does not answer. They are declared here and belong in the GAP
register of `docs/architecture/CANON-LEDGER.md`.

- **GAP — doctrine has no versioning semantics for ITSELF.** If a host pins kit 1.9.0 and the framework
  amends a Cardinal at 2.0.0, then `upgrade` rewrites the generated cardinals block inside the host's own
  law document. The host's law silently changes text it never authored. Cardinal VI says the law set grows
  by declaration and is amended only by restatement on record — but it does not say *whose* record when the
  declaring authority is upstream of the project. Unanswered: does a host consent to a doctrine amendment,
  and if so, through what artifact?
- **GAP — no declared status exists for a legitimately locally-modified VENDOR file.** §5 halts on it and
  §8 gates it, but doctrine offers no vocabulary for the emergency case where a host must patch vendor code
  to unblock itself. Cardinal V demands declared states rather than silent ones; there is currently no
  declared state to put it in. Improvising a `# KIT-PATCH:` comment convention would be exactly the silent
  improvisation Cardinal VI forbids, so it is declared as a gap instead.

## 11. CANON — standards' concepts that surfaced this session

Status per root Law 13, declaration site = this proposal (non-binding until an ADR restates it).

- **Kustomize base + overlay** — *proposed, not built.* The role/doctrine composition mechanism.
- **copier/cruft answers-file update** — *proposed, not built.* The re-runnable-install mechanism.
- **Debian conffile three-way handling** — *partial, named deviation:* we halt on a locally modified vendor
  file where Debian prompts and permits.
- **Terraform dependency lockfile** — *proposed, not built.* Repurposed as a drift detector over present files.
- **FHS / XDG vendor-vs-override-vs-state split** — *adopted as the class model,* plus a fourth class
  (PROJECTION) FHS has no analogue for.
- **Helm chart directory as the unit of distribution** — *adopted whole* as the `kit/`-subtree decision.
- **Django project-vs-app split** — *adopted in spirit* as the kit-vs-project plane split.
- **Rails convention-over-configuration** — *deliberate partial:* layout carries meaning, but with no
  run-time loader the convention must be gate-enforced.
- **Ports & Adapters (Manifest/Workspace/Probe/Runtime)** — *adopted whole* for the verb boundary.
