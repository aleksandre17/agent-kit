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

16. **Review owners are declared once** (`owners`: pattern -> owners), an extension point the CI adapter
    seeds and serves into a span of the host's own `.github/CODEOWNERS` through a generic `declared`
    resolver (a view of any contract's rows). What only a person can set outside the tree -- branch
    protection -- is a surface `controls` row: `doctor` names it NOT ASSERTED with the exact command, and
    the kit never runs it. *Rejected:* a CODEOWNERS file the kit owns whole (a host's own owners would be
    shadowed); setting protection through the API (a credential and a remote, irreversible act); a
    resolver per contract.

17. **A commit message is judged like an edit**, by declaration and opt-in: contract `message-rules` (a
    pattern the message must match from its first character, why, instead, and its calibration -- one
    message it must refuse, one it must admit), gate `FF-MESSAGE-RULE` in `check`, verb `message` (blocking)
    run by the git adapter's `commit-msg` hook; the policy `conventional-commits` is the published rule.
    A host that takes no rule is held to nothing; an uncalibrated rule is named and never applied.
    *Rejected:* a message check in the edit judge (a message is not an edit and has no path); a hard-wired
    Conventional Commits regex in the hook (a policy, not a mechanism).

## Cuts (the result did not outweigh the cost)

Operating modes; a separate knowledge store; a growth-ladder ceremony beyond the lesson schema; a
defense-in-depth document kind (the conformance map carries it); an OTel exporter; ISO/IEC 42001 and
NIST AI RMF rows beyond one `mapping` row (organisational standards). Each is a `non-goal` row.

## Owed

- Signed releases and a licence (the owner's decisions).
- Codex's session-start, stop and subagent-stop hooks: the event names are a claim (codex-cli 0.154.0 by
  inspection), their payloads and exit semantics unmeasured, so none is served; a session-end token log.
- Branch protection (an external control a person sets; a conformance `gap` row, `doctor` prints the command).
- More procedure skills (verify, refactor) beyond kit-skills and the record/review procedures.
- Codex memory home and Codex hook coverage for pre-exec and pre-spawn (no measured product fact yet).
- One full acceptance run after the last commit: the last full run was 412/415, the three failures
  fixed in it and their modules green when run alone.
