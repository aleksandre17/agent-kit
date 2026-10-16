# Hooks: what runs on every agent action

The product adapters write the kit's hooks into each product's own settings:

- Claude Code: `.claude/settings.json`
- Codex: `.codex/`
- git: `.githooks/`, activated by setting `core.hooksPath`

Each hook calls one verb:

| When | Verb | Posture | What happens |
|---|---|---|---|
| an agent writes or edits a file | `judge` | blocking | the edit is judged against every edit gate in force; a violation is refused before the bytes land |
| an agent runs a shell command | `guard` | advisory | a whole-tree destructive command (`rm -rf`, `reset --hard`, `clean`, `worktree remove`) gets a recovery point first |
| an agent starts a sub-agent | `spawn` | blocking | the brief must be a packet (MISSION, GROUND, BOUNDARIES, RETURN, BUDGET) under its size ceiling |
| a session starts | `session` | advisory | one context line: the kit, how a change is proven, the handoff |
| a session stops | `stop` | blocking | the continuity capsule must keep its contract (served only with the `shared-tree` bundle) |
| a sub-agent stops | `ledger` | advisory | one row: requested vs verified model, and tokens |
| a commit | `judge` (pre-commit), `message` (commit-msg) | blocking | the same gates at commit time; the message form too, if a message policy is taken |
| a push | `check` (pre-push) | blocking | a red check blocks the push |

Every hook declares its posture. A blocking hook that crashes fails closed (exit 2).

Every invocation leaves a receipt under `.agents/runtime/receipts/`. "Configured" and "ran" are
therefore different facts, and both can be proven. `doctor` fires each hook with a throwaway
violation and reads its receipt.

What a product's hook event looks like is a fact the adapter owns. A payload that has not been
measured on the real product is written in the adapter as a claim, never served as fact.
