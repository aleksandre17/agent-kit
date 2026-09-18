# ADR-017 — One dispatch port: agnostic collaboration between different intelligences

- **Status:** Accepted (2026-09-17; owner-delegated under ADR-015 amendment 5). Two facts it rests on
  are UNVERIFIED and are measured as the first act of C2/C3 (see *Measured when*).
- **Decides:** the design of ADR-015 link C's dispatch half, and how link C is cut into slices.
- **Relates:** ADR-007 (one writer per host) · ADR-009 (schema versions) · ADR-013/014 (runtimes and
  adapters) · ADR-015 (the whole line; "one body"; link C) · ADR-016 (the host carries its kit)

## Context

The owner asked (2026-09-17) whether an orchestrator in one runtime can dispatch work to agents of a
DIFFERENT intelligence — Claude Code ⇄ Codex — see that work running as it sees its own subagents, and
whether Codex could itself be the orchestrator. ADR-015 already declared the intent in link C ("ONE
DISPATCH PORT … limbs of one body, never two nervous systems"); it did not declare the FORM, and it did
not measure the field.

What is measured today (national-accounts, route decision `d7a23391`, attestation window 14 days):
- `claude-code` has proven `pre_exec_block`, `spawn_gate`, `subagent_ledger`, `pre_write_context`,
  `post_write_block`, `session_start_context`, `session_end`, `stop_gate`.
- `codex-cli` has proven `cli_broker_dispatch`, `pre_write_context`, `post_write_block`,
  `session_start_context`, `stop_gate` — and NOT `pre_exec_block`, `spawn_gate`, `subagent_ledger`.
- The packet gate blocked four malformed dispatches in one Claude session. In a Codex orchestrator the
  same gate would not fire: its enforcement lives in a hook that runtime has not proven.
- Claude Code's agent panel shows only subagents started by its own Agent tool, which starts only Claude
  models. A Codex process started by shell appears as a background task, not an agent.

## Decision

**1. The dispatch PORT is the one place a worker is started — enforcement lives in the port, not in a
runtime hook.** The port refuses a task without a routed `DISPATCH-ID` and a complete packet, takes the
path lease, creates the worker's worktree, and writes the receipt — itself. Whether the orchestrator's
runtime has a `spawn_gate` then stops mattering: the gate has one home, independent of who calls it
(Cardinal III, VIII). A runtime hook may CALL the port; it never replaces it.

**2. Hexagonal: the port knows no runtime; a runtime is an ADAPTER, and an adapter is a declaration.**
Adapters planned: `claude-subagent`, `codex-exec`, `codex-mcp` (if measured viable), `a2a-remote`
(future). A new intelligence is a new adapter row — the port is never edited (Cardinal II).

**3. The task model is A2A's, adopted whole — the MODEL, not the transport.** States `submitted ·
working · input-required · completed · failed · canceled`; results return as ARTIFACTS; a worker that
cannot proceed returns `input-required` with its question instead of guessing (Cardinal V). The kit
invents no vocabulary of its own for this. The HTTP/SSE transport is NOT built: for local CLI peers it is
cost without a consumer (YAGNI); the `a2a-remote` adapter is the declaration that would add it.

**4. Capability discovery is by RECEIPT, not by claim.** A2A's Agent Card is a declaration an agent
makes about itself; routing here selects a runtime by capabilities PROVEN in receipts (the existing
attestation table). A declared-but-unproven capability is shown as such and never routed on.

**5. Asymmetry is declared, and closed by isolation.** A runtime without `pre_exec_block` cannot be
stopped mid-command, so its worker writes only inside its own worktree, under a lease, and its change is
admitted to the host only after `check` passes on return. Verification at return replaces prevention at
write — stated, never implied equal.

**6. Shared state is a blackboard under compare-and-swap.** The continuity capsule, leases and the
journal are the only shared state; one writer per path; one orchestrator per host at a time (ADR-007,
WIP=1). Claude and Codex SUCCEED each other as orchestrator — never run concurrently; the CAS refuses the
stale one mechanically.

**7. Observability speaks one language.** Receipts from every adapter use OpenTelemetry `gen_ai` semantic
conventions, so a Claude run and a Codex run are comparable in one stream.

**8. Visibility in a runtime's own UI is an adapter concern, never the architecture.** In Claude Code, a
thin `codex-worker` subagent (cheapest model, Bash only) invokes the port's `codex-exec` adapter and
relays the artifact unchanged, so the work appears as an agent row. Streaming Codex's `--json` events
step by step is a refinement, not a requirement.

**9. Codex as orchestrator is supported in CODEX'S OWN environment, not inside Claude Code's window.**
Claude Code's CLI and IDE plugin run Claude models; the orchestrator's continuity is in FILES (capsule,
route, receipts), not in a window. Codex opens the same repository, reads `AGENTS.md`, resumes from the
same capsule, and dispatches through the same port.

## Slices — link C, in order, each walked live on host #0 before the next begins (WIP=1)

| Slice | Artifact | Done when |
|---|---|---|
| **C1** | the enforcement line: served settings → vendored hook → HOST-DECLARED gates; the abstract ARROW capability; per-directory entry files; `core.hooksPath`; CI projection from `ci.*` | an edit in host #0 is judged by the host's declared gates through the pinned kit, from both runtimes' hooks |
| **C2** | the dispatch port + `claude-subagent` adapter; packet gate, lease, worktree and receipt INSIDE the port | a malformed dispatch is refused by the port itself, whatever runtime calls it; a good one runs and receipts |
| **C3** | `codex-exec` adapter + the `codex-worker` visibility wrapper; both directions | a Claude orchestrator runs a Codex worker visible as an agent row, AND a Codex orchestrator runs a Claude worker; both receipts in one stream; `check` admits or refuses the returned change |
| **C4** | `input-required` round-trip + OTel `gen_ai` receipts | a worker's question returns to the orchestrator and the task resumes; a Claude run and a Codex run compare in one report |

**When:** C begins after L3b is verified and committed. C1 → C2 → C3 → C4, then ADR-015's D.

## Amendment 1 — one judge, entries by registry (2026-09-17, found building C1c's ARROW)

An edit is judged by ONE verb (`judge`, served to every runtime's hook). A gate module offers an edit
entry (`EDITS`) beside its tree entry (`KINDS`); `check.registry(entry)` finds both the same way, and
`judge` runs every enabled gate's `EDITS`. A new edit-time judgement is a gate module declaring `EDITS`
— never a second verb, never a new hook row per runtime. Rejected: an "arrow judge" verb (a second
judge; every adapter would need a new hook) and a second rule shape inside `edit-gate` (two jobs under
one schema; a text pattern cannot express an edge's direction). A kit-shipped gate stands at the
declared default stance (ADR-006); a real violation found on a host is cured, not frozen.

## Amendment 2 — the commit is the return point every writer passes (2026-09-17, C1c part 3)

**Decision.** Git is a surface ADAPTER like any runtime (`adapters/git`, surface `git-commit`): it serves
`.githooks/pre-commit`, which pipes the staged patch into the ONE `judge` over the same host gates. This
is decision 5 made concrete: whatever wrote the change — a human, a runtime without a pre-write block,
any tool — the commit is judged. `hands.carries: patch` and `hands.nothing` (an admitted empty patch
must be DECLARED; the default refuses) extend the event grammar, not the judge.

**A setting outside the tree** (`core.hooksPath`) is declared by the surface's `activation` block,
changed only through a door (`activate --plan/--approve/--to inactive`), and READ FRESH on every `check`
(`FF-RUNTIME-ACTIVE`: ACTIVE · INACTIVE · ELSEWHERE · UNREADABLE, with the moment of reading) — never
stored, so a hand-run `git config` cannot make a copy lie. The kit never overwrites or withdraws a value
it did not set, nor activates over live host hooks (KIT0047).

**Cardinal IV, stated honestly.** The activation block names argv arrays the kit executes. They are DATA
— fixed argv with declared placeholders, no shell, run only by a door or a read-only gate — the same class
as a hook command a product runs. The interpreter holds no product knowledge; the declaration holds no
branch, loop or condition. A declaration that needed one would be refused.

**Rejected:** a git branch inside `judge` (product name in the interpreter); adopting pre-commit.com /
husky / lefthook (a second config home for the host's gates); recording the setting in the estate (a
copy that drifts on the first hand edit). **Known limits:** `--no-verify` skips a hook by git's design
— CI (C1c part 4) is the projection that cannot be skipped; who activated lives only in the run journal
(GAP-A1).

## Amendment 3 — CI is the projection nobody skips (2026-09-17, C1c part 4)

**Decision.** A CI provider is a surface adapter (`adapters/github-actions`) serving a workflow that runs
the host's PINNED kit — `check` and the one `judge` over the pushed/PR diff — never a fetched kit. It
closes what `--no-verify` leaves open.
1. **The provider is DECLARED, not measured.** A runtime descriptor names the surface. A `ci.*` fact
   cannot choose: a host with no workflows would never be served, and the projection would create the
   evidence that enables it (a circle).
2. **Clone-local state is not repository state.** A surface declares `clone: working|ephemeral`;
   `check --surface <id>` reads through that clone, and what an ephemeral clone cannot carry
   (clone-local settings, the observed runtime plane) prints NOT MEASURED with its moment — never a
   fabricated pass, never a structural red on every push.
3. **A served path is never evidence about the host.** The probe ignores every path the served record
   names; the kit does not measure its own output.
4. **Ownership in an owner-written directory:** the directory is the owner's; the kit owns exactly the
   paths its record names; a host file at such a path is refused (KIT0039), a file beside it is untouched.

**Decided, not built:** `check --surface <ephemeral>` on a working clone would hide an inactive hook
(Cardinal V). The adapter declares the environment marker its runner sets; the interpreter refuses an
ephemeral reading when the declared marker is absent — generic presence test, no product name. And the
patch grammar now repeated in `git` and `github-actions` gets one home (a shared unified-diff grammar
both reference).

**Rejected:** provider chosen from `ci.workflows` (the circle above); the workflow running `activate` or
`git config` before `check` (fakes an approval or a reading); letting CI fail honestly on clone-local
state (a signal red on every push is read by nobody); a helper script under `.github/` (a second file in
the owner's directory).

**Unverified until a real push:** runner reads the file; event field shapes; `actions/checkout@v4`
(fetched, not SHA-pinned); fork PRs; force-push with unreachable base (fails closed).

## Amendment 5 — the Codex boundary, MEASURED (2026-09-18, first act of C3)

Cardinal VII: an environment is an assumption until measured, and it is measured once, cheaply, at the
boundary. Taken on this machine on 2026-09-18 by the orchestrator, with `codex --version`,
`codex exec --help`, `codex mcp --help` and `codex doctor` — read-only probes, nothing written.

- **Installed and authenticated: YES.** `codex-cli 0.154.0`; `doctor` reports auth mode `chatgpt`,
  provider endpoints reachable, `22 ok · 1 warn · 0 fail`. The receipt-based belief is now a reading.
- **Codex CLI as an MCP SERVER: NO, in this version.** `codex mcp` manages *external* MCP servers that
  Codex consumes (`list/get/add/remove/login/logout`); there is no server subcommand. The nearest thing
  is `codex app-server` (marked experimental), currently `not running (ephemeral mode)`. **Therefore the
  `codex-mcp` adapter of decision 2 is NOT built in C3** — it stays a declared, unbuilt row, and
  `app-server` is the path it would take if it is ever needed. Decision 2 is unharmed: this is exactly an
  adapter failing to be viable while the port is untouched.
- **Session resume: YES.** `codex exec resume <id> | --last` and `codex fork` exist, so **C4's
  `input-required` round-trip has a real resume path** rather than a re-prompt from the top.
- **What `codex-exec` can be declared with** (all flags verified in `--help`, none yet exercised):
  `-C/--cd <DIR>` to run inside the tree the PORT placed (never `--worktree`, which would make Codex
  place its own tree and give isolation a second home — Cardinal III) · `-s/--sandbox
  read-only|workspace-write|danger-full-access`, the declared form of decision 5's isolation ·
  `--json` JSONL events, the stream C4's OTel receipts read · `-o/--output-last-message <FILE>` and
  `--output-schema <FILE>`, which carry the worker's ARTIFACT back as a file with a declared shape
  instead of a parsed transcript.

**Still unverified:** every one of those flags' actual behaviour under this port; a real Codex run has
not been made through it. Measured presence is not measured behaviour, and C3 is where it becomes one.

## Amendment 4 — what C2 decided where this ADR had not (2026-09-18, building C2)

**The A2A re-read decision 3 asked for, as a DECLARED READING and not as a measurement.** Taken
2026-09-18 by the orchestrating agent; basis: that agent's own knowledge at model cutoff 2026-05; NOT a
fresh reading of the specification, and no network access was attempted. On that basis the task states
`submitted · working · input-required · completed · failed · canceled` and results-as-artifacts are
unchanged, so decision 3 stands unamended. This is testimony about a standard, dated and attributed,
and it is written here rather than left in a transcript — a reading whose moment is unstated goes on
certifying forever (Cardinal V). The reading is superseded, not repeated, when the specification is
actually measured; that measurement is still owed and is declared as such in the canon ledger.

**A packet does not name a path; the port places the tree.** Where a worker's isolated tree lives is a
property of the HOST's layout, not of the task, so the packet declares only its branch and the port
places every task's lease, record and tree together under its DISPATCH-ID inside the plane that already
holds what a run leaves behind. *Rejected:* the packet naming its own workspace path — it would make the
one door every worker passes through the one way to write anywhere in the host, and it puts a second
home for the host's layout into every orchestrator that writes a packet.

**How a tree is MADE is a product fact, so it is an adapter too** (`workspace-provider`, published by
the `git` adapter as `git worktree`). The dispatch port names no program. Exactly one provider may be
enabled: zero is refused rather than defaulted, because a worker with nowhere of its own would write
into the host, which is what the isolation exists to prevent. *Rejected:* `git worktree` called directly
from the port (amendment 2 already holds that git is a surface adapter like any runtime — the port would
have become the one interpreter carrying a product name); *rejected:* declaring it as another field on
`runtime-surface` (two jobs under one schema, and a host that wants isolation without being served).

**Routed means the route RESOLVES here.** The port holds an id routed when some capability this host has
enabled declares an adapter under exactly that id, and refuses it otherwise as a name with no referent.
Routing on capabilities PROVEN in receipts (decision 4) is the ROUTER's half and travels with the packet
as `routed_by` testimony the port records and does not judge. *Rejected:* the port consulting the
attestation table itself — the gate would then hold a routing policy, and the interpreter that decides
is the one that cannot be handed a subject it has never seen (Cardinal IV).

**The lease is the host hold's own mechanism with another path** (`hostlock.take(..., registers=False)`):
one document shape, one refusal, one break-by-name door, and a per-path hold that deliberately does not
register as the hold on the host. *Rejected:* a lease of its own for dispatch — two answers to *is
anyone already in there*, agreeing until one of them is fixed.

**`input-required` is declared and unwritten.** The `task` schema carries A2A's six states whole; the
port names the four it can produce and refuses at the first write if the two have parted. The round-trip
that produces the fifth is C4, and a vocabulary narrowed to what is built today would have to be widened
by a schema edit the first time a worker asked a question.

## Measured when (Cardinal VII — assumptions at a boundary)

- **A2A's current state and governance** (Linux Foundation stewardship; the task-state set above) — from
  the orchestrator's knowledge, NOT re-measured on 2026-09-17. Re-read at the start of C2 — and that
  re-read was itself a DECLARED READING from the same kind of basis, not a measurement (amendment 4).
  A real reading of the specification is still owed.
- **Codex CLI as an MCP server, Codex session resume, and Codex installed/authenticated here** — all three
  MEASURED on 2026-09-18; the readings, and what they change, live in **amendment 5** (one home).

## Rejected alternatives

**A. Enforcement in each runtime's hooks.** Rejected: two homes for one gate, and a runtime lacking the
hook silently bypasses it — measured: Codex has no proven `spawn_gate`.

**B. A thin wrapper subagent AS the architecture.** Rejected: it makes Claude Code a permanent dependency
of every collaboration and couples the design to one vendor's UI. It survives only as an adapter (8).

**C. A relay — Claude forwarding every owner message to Codex.** Rejected: two models billed per turn,
the owner reads Codex through a filter, and faithful relay becomes a risk the architecture created.

**D. Routing Claude Code to OpenAI models through an unofficial API proxy.** Rejected: that is a GPT model
inside Claude's tooling, not the Codex agent; unofficial, fragile, and our hooks are calibrated to the
runtime they serve.

**E. Build A2A's HTTP transport now.** Rejected: no remote consumer exists; the task MODEL gives every
benefit of the standard to local peers, and the transport is one adapter declaration away.

**F. An invented task vocabulary.** Rejected: A2A already names these states; a private vocabulary is a
second home for a solved concept (Cardinal I, III).

## Consequences

- Link C becomes four slices with one artifact each; "how much is left" stays a position on the line.
- The port becomes the single point every worker passes — a failure there stops all dispatch, which is
  the intended property (fail closed), and is covered by C2's refusal test.
- An intelligence the kit has never seen joins by one adapter declaration and a receipt that proves its
  capabilities.
