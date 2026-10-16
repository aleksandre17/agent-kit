---
kind: decision
authority: canonical
owns: the-agentic-layer
---

# ADR-024 — The agentic layer: every token serves the result

- **Status:** accepted (2026-10-16, owner-delegated)
- **Deciders:** the owner's delegate, on the owner's instruction that agent-kit be a complete framework
  for AI engineering and agentic AI engineering -- context engineering first, schema-, contract- and
  meta-driven, open by declaration -- and on the binding rule that the result must outweigh the cost.
- **Builds on:** ADR-013 (serving a runtime), ADR-017 (one dispatch port), ADR-022 (the operating
  plane), ADR-023 (one door, open by declaration).

## The principle

**Every token serves the result.** What a script or a verb can do deterministically is done by it, at
zero tokens; intelligence is spent only where judgement is needed, at the highest standard; quality is
the floor, and a saving that lowers it is worthless. It is the engineering bundle's cardinal E5 and the
economy doctrine under it; every decision below is that principle applied to one mechanism, and each
mechanism is declaration-driven: a new product, skill, server, eval, route, norm or point is a
declaration, never a kit edit, proven by a fixture the kit does not ship.

## Decisions

1. **Skills** are the Agent Skills unit, declared once (`skills`): name and description in the row, prose
   in the body, deterministic steps as `scripts/` (executed, never loaded). Served per product
   (`.claude/skills/`, `.agents/skills/`). A host extends a published skill with chapters and stances
   (`extends`), so one served skill composes the publisher's chapters and the host's, one generated index.
   *Rejected:* a skill per product (two homes); front matter in the body file (a second copy of the name).
2. **MCP servers** are declared by trust (`mcp-servers`, `mcp-trust`), environment variable NAMES only --
   a secret has no field to live in. Untrusted servers' write and exec tools are denied where the product
   can say so. *Rejected:* a per-product MCP file the host writes (n copies); allowing values (a secret's
   field).
3. **Context is measured per layer** (always, indexed, on-demand) on every `check`, against the kit's
   tight defaults, each product's own limits, and the host's own budget rows (the ratchet's one home for
   a host's number). Stable sections come first for prompt caches. *Rejected:* a ceiling in an
   interpreter; budgets in a second document beside the corpus map.
4. **Guardrails** against prompt injection are a published policy (`untrusted-content`): one always-loaded
   rule, calibrated gates against invisible controls (Trojan Source) and override text. *Rejected:* an
   LLM classifier (non-deterministic, paid on every edit).
5. **Memory points, never copies** (`memory` policy): a product's memory home, declared on its surface, is
   read on every working-clone `check`; a secret or a copied repository line is refused.
6. **Task classes and routes** (`task-classes`: mechanical, assisted, judgement, explicit, decision, with
   the decision procedure and the nine preconditions of automation). A route cell names the actor, model,
   effort, caps and escalation; mechanical work is refused at the port; a run past its wall time fails on
   the record and escalates without a retry. Adapters say how their product is told (`options`).
   *Rejected:* a model id in any kit file; an LLM routing classifier.
7. **Evals** (`trial`, `eval`): a fixture started from the host's own takes, a one-sentence temptation,
   the cheapest sufficient model, a hard cap; accepted by oracles only (the port's admission, this host's
   gates re-judging the tree, the fixture's check). Re-run only when a declared input's digest moves. Two
   real runs measured (claude-subagent 0.0034 USD, codex-exec 33178/182 tokens); no product has a distinct
   needs-input ending, so `asks` stays undeclared, now measured. *Rejected:* re-running on every commit;
   an LLM judge.
8. **Hooks** declare a posture: blocking fails closed with the surface's refusal even on a crash, advisory
   lets the act through; every invocation leaves a receipt. `guard` takes a recovery point before a
   destructive command; `spawn` holds a sub-agent brief to the five packet fields under a ceiling; the git
   pre-push runs `check`; `doctor` proves each served chain refuses a canary.
9. **Run records** carry OpenTelemetry GenAI attribute names (names only, no exporter -- owner's cut); the
   frontier (`FF-FRONTIER`) reports runs, first-pass acceptance and tokens per accepted change per task
   class, and names repeated work as a script candidate.
10. **The normative tree**: cardinals -> doctrines -> rules (RFC 2119) -> enforcement -> procedures, in the
    doctrine grammar (`derives_from`, `modality`, `subject`, `enforced_by`); a host tightens by stance and
    loosens only with an expiring exception; `FF-NORMS` refuses an orphan, a cycle, a contradiction, an
    unenforced MUST, an unexcepted loosening and an expired exception. The engineering bundle carries the
    generic content of the first host's quality doctrine.
11. **Extension points**: an install declares the points it opens; `extend` scaffolds a member from its
    template on demand, pending answers visible in `check`, newer templates merged three ways, the kit's
    copy never edited. The registry prints in the shared shape `kit/schemas/extension-points.schema.json`.
12. **Roles are profiles** (tools, what may change, context, task class), never personas; the host's
    runtime strings reach each product's definition verbatim.
13. **Opt-in bundles for what some hosts rely on**: change records over a review range (`review`), the
    execution graph (obligations derived from a registry), the shared-tree continuity capsule (CAS).
14. **The conformance map** (`conformance`, `FF-CONFORMANCE`): every standard clause is a row with evidence
    and a status; a conformant row without existing evidence is refused; gaps and non-goals are rows.

15. **A product's own session lifecycle** is three more hook verbs on the same posture and receipts:
    `session` (session-start, advisory) hands one context line -- the kit, how a change is proven, the
    capsule's handoff -- in the form the surface declares (`hands.context`); `stop` (blocking) refuses a
    stop over a continuity capsule that breaks its contract, served only where the host takes one (the
    `contracts` resolver lets a setting test what the host installs); `ledger` (subagent-stop, advisory)
    reads the finished sub-agent's own transcript through `hands.ledger` -- one turn per declared key,
    the last line winning -- into one row of requested vs verified model and tokens, a mismatch named.
    Claude Code's events are from its documentation, its transcript shape measured on this machine;
    Codex's are a claim and not served. *Rejected:* a stop hook served to every host (a process per turn
    for nothing to hold); reading the model from the event (the product puts none there); estimating
    tokens from text.

16. **Review owners are declared once** (`owners`: pattern -> owners), an extension point the core seeds
    (beside `mcp-servers`) and the CI adapter serves into a span of the host's own `.github/CODEOWNERS` through a generic `declared`
    resolver (a view of any contract's rows). What only a person can set outside the tree -- branch
    protection -- is a surface `controls` row: `doctor` names it NOT ASSERTED with the exact command, and
    the kit never runs it. *Rejected:* the adapter seeding the list (a taken adapter's seed is absent until its `init`, and a second
    forge would seed it twice); a CODEOWNERS file the kit owns whole (a host's own owners would be
    shadowed); setting protection through the API (a credential and a remote, irreversible act); a
    resolver per contract.

17. **A commit message is judged like an edit**, by declaration and opt-in: contract `message-rules` (a
    pattern the message must match from its first character, why, instead, and its calibration -- one
    message it must refuse, one it must admit), gate `FF-MESSAGE-RULE` in `check`, verb `message` (blocking)
    run by the git adapter's `commit-msg` hook; the policy `conventional-commits` is the published rule.
    A host that takes no rule is held to nothing; an uncalibrated rule is named and never applied.
    *Rejected:* a message check in the edit judge (a message is not an edit and has no path); a hard-wired
    Conventional Commits regex in the hook (a policy, not a mechanism).

18. **A host that holds the kit in its own tree is REFERENCED, never given a copy** (owner's request: no
    duplicated sources). Its lock keeps `files` -- the digest of every kit path -- and gains `reference`:
    the payload's path, the repository holding it (a submodule) and the commit pinned, and where each
    take is read from (a take's digest keeps its one home, the provenance pin). Served settings run the
    kit from that path; `check` holds it present, at the commit and byte for byte the lock; the entry
    point refuses a referenced kit that differs from the lock before any verb runs (KIT0083), save the
    verbs that pin a new state (`upgrade`, `lock`); a missing kit fails closed with `git submodule update
    --init <repo>`, in `check` and in every served hook (which now also refuses an absent kit instead of
    letting a product read a missing file as a non-blocking error). `upgrade --mode referenced` migrates
    a vendored host -- refused for a kit outside the host, with uncommitted changes, or a take whose source
    is not the pinned bytes -- and removes the copies only after the referenced host checks green.
    Vendored stays the default. *Rejected:* copying the take digests into the lock (two homes); a symlink
    from `.agents/kit` (a second path to one tree, unportable on Windows); trusting the submodule's commit
    alone (a working tree can differ from its commit).

19. **One secrets catalogue** (owner's request: no duplicated sources). The secrets policy's calibrated
    edit-gate document is the list every judge reads -- the edit hook and the commit gate here, a
    tree-and-history scanner by path. Its README publishes the path and the contract (`edit-gate`: paths,
    forbids, proves, admits, with the calibration a reader must apply first); the bridge to stack-kit's
    `scan` (`security.secretPatterns`) is declared by the stack-kit adapter alone, and the core names no
    scanner. *Rejected:* a second pattern list in the scanner (two judges of one question); the kit
    importing the scanner (a dependency on a tool it does not need).

20. **The tree is audited by the gates that judge its edits** (owner's request: a violation already in the
    tree was never seen). An edit gate judges what a change introduces -- a ratchet -- so a line older than
    the gate, or one that reached the tree past every hook, stood unseen. Verb `audit` runs every calibrated
    edit gate in force (the host's and every taken policy's, the `edit-gate` contract) over the FULL text of
    every TRACKED file its `paths` reach, with the judge's own reach (a gate's declaration and the
    publisher's pinned planes are not read), and prints `path:line`, the gate and its `because` -- never the
    matched text, so a secret is located and not repeated. A known violation is acknowledged by
    declaration, never by silencing the gate: the extension point `known-violations` (contract
    `known-violations`: gate, exact path, tracking, `until?`) prints it KNOWN with its tracking; an `until`
    that has passed makes it a finding again (EXPIRED); an acknowledgement matching nothing is STALE.
    Exit 1 on an unacknowledged finding; KIT0084 where no repository says what is tracked or one violation
    is acknowledged twice. `check` runs it as `FF-TREE-AUDIT` (kind `tree-audited`, calibrated), which
    SHIPS `observe` and prints its counts on every run (a gate kind's `REPORTS` entry): blocking only when
    the host raises its stance to `enforce`. *Rejected:* `judge --tree` (the judge's stdout and exit code
    belong to the product whose hook ran it, and a tree is not an event); an acknowledgement by path
    pattern (one row could cover a file nobody looked at); narrowing the gate's `paths` to exempt a file
    (the file's next edit would no longer be judged); every untracked file (not what a clone receives).

21. **A host's laws have one source: its numbered rules** (owner's request: two homes for one law). A
    host rule in the normative tree may carry `law: <n>` (its number in the served list) and an
    `enforcement_note`; the briefing's project laws are RENDERED from those rules in law order -- bold
    title, what it says, the note and the enforcers it names (`.agents/generated/LAWS.md`, resolver
    `numbered`). The prose law page is DEPRECATED: no longer seeded (a host that has one keeps it, its
    record orphaned, never deleted by an upgrade), and served in place of the rendered list while it
    exists (`deprecated_from` on the section). `FF-LAWS` (kind `laws-one-source`, calibrated) fails a host
    that authors both, or numbers that do not run 1..n in declared order, and reports which source is in
    force on every check. `upgrade --mode laws --approve <who>` moves each numbered law into a rule
    (`host@1.0.0#law-<n>`, its title, says and note), removes the page and renders; the host then
    completes `derives_from`, `modality` and `subject` where FF-NORMS names them. *Rejected:* rendering
    the page from prose (a parser as the source of truth); keeping the page authoritative and the rules
    derived (the tree `check` holds coherent would follow the prose, not the reverse); deleting the page
    in an ordinary upgrade (an upgrade cannot delete what the host wrote).

22. **A referenced host stays referenced, and its submodule's re-releases are taken in the same walk**
    (found on a real host: a plain `upgrade` rewrote the lock without its `reference` block and vendored
    the kit again, and the host broke with KIT0015). An `upgrade` with no `--mode` on a host whose lock
    carries `reference` IS `upgrade --mode referenced`: the same door, the same pin. Only `--mode
    vendored`, asked for by name and approved, returns it to copies -- each referenced take copied into
    the take plane, the block dropped, and the ordinary upgrade then delivers the kit. When the submodule
    advanced and a taken capability's referenced source now declares a NEWER version, `upgrade --mode
    referenced --approve <who>` takes it again in that walk: the provenance pin is re-written (its
    `supersedes` naming the old version and digest, attested by the approver at arrival, a refuted
    signature refused) and the take statement's row re-stamped -- what `take` writes, less the copy a
    referenced host never keeps. The same version with other bytes, or an older version, stays refused by
    the one judge of a pin (KIT0032, `provenance.arrival`), and no name opens it; a take with no pin at
    all stays KIT0083. *Rejected:* keeping the refusal and sending the host to `take --path` (it vendors a
    copy beside the reference -- two sources for one pin -- and `start` is blocked meanwhile by the
    kit/lock mismatch); a plain upgrade that silently vendors (a host's choice of where it runs the kit,
    reversed by a verb that did not say so); re-pinning on any changed digest (a drift could then be
    walked through a door, and a pin that can be re-taken pins nothing).

23. **A MUST may name an enforcer a taken adapter vouches for in the host** (found on a real host: a law
    held by its own build tool -- its test suite run by another kit -- could only be a SHOULD). An adapter
    ships a document of contract `enforcers` (`prefix`, `path`, `pointer`): every key of the object at
    `pointer` in the host's JSON file `path` whose value is not empty is an enforcer `<prefix>:<key>`.
    The stack-kit adapter (1.2.0) declares `stack-kit` over `stack-kit.json` / `commands`, so a host that
    declares `commands.test` may hold a MUST with `stack-kit:test` (likewise `stack-kit:build`,
    `stack-kit:validate`). FF-NORMS reads every `enforcers` document of the enabled capabilities by its
    contract; the core names no product, and an enforcer the host does not declare (the command absent,
    the file absent or unreadable) is not accepted -- NT-UNENFORCED, as before. The `cardinal` contract's
    `enforced_by` pattern widens from `gate|edit-gate|verb` to any `<prefix>:<name>`. *Rejected:* a
    `stack-kit:` (or `command:`) word in the norms gate (product knowledge in the core); accepting every
    `<prefix>:` a taken adapter names whatever the host declares (an enforcer the host does not run would
    hold a MUST on paper); running the command from `check` to prove it (the build tool's run is its own
    gate, and a check that runs a host's suite is a second runner of it).

## Cuts (the result did not outweigh the cost)

Operating modes; a separate knowledge store; a growth-ladder ceremony beyond the lesson schema; a
defense-in-depth document kind (the conformance map carries it); an OTel exporter; ISO/IEC 42001 and
NIST AI RMF rows beyond one `mapping` row (organisational standards). Each is a `non-goal` row.

## Owed

- Signed releases and a licence (the owner's decisions).
- Branch protection: an external control only a person with the rights sets; a conformance `gap` row,
  and `doctor` prints the exact `gh api` command.
- Codex's session-start, stop and subagent-stop hooks: the event names are a claim (codex-cli 0.154.0 by
  inspection), their payloads and exit semantics unmeasured, so none is served; a session-end token log.
- Codex memory home and Codex hook coverage for pre-exec and pre-spawn (no measured product fact yet).
- Observed receipts of Claude Code's SessionStart, Stop and SubagentStop hooks firing (served from the
  documentation; the sub-agent transcript shape is measured) and of stack-kit's `scan` reading the
  secrets catalogue through `security.secretPatterns` (a claim in the stack-kit adapter).
- More procedure skills (verify, refactor) beyond kit-skills and the record/review procedures.
