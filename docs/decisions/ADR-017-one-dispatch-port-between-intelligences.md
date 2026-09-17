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

## Measured when (Cardinal VII — assumptions at a boundary)

- **A2A's current state and governance** (Linux Foundation stewardship; the task-state set above) — from
  the orchestrator's knowledge, NOT re-measured on 2026-09-17. Re-read at the start of C2; a divergence
  amends decision 3 on record.
- **Codex CLI as an MCP server, and Codex session resume** — UNVERIFIED. Measured at the start of C3; the
  `codex-mcp` adapter and C4's resume path depend on it.
- **Codex CLI installed and authenticated on this machine** — receipts say it ran within 14 days; measured
  once, cheaply, at the start of C3.

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
