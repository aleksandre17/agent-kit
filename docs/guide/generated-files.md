# Generated files

The kit writes these files into a host. None of them is edited by hand: change the source and run
`render`, and `check` fails on drift. The host's estate (`.agents/project/estate.json`) lists every
file, its class, and the capability that owns it.

| File | Computed from |
|---|---|
| `CLAUDE.md`, `AGENTS.md` (the kit's spans) | the host's laws (its numbered rules), the build and test commands an adapter reads, and the doctrine and roles pointers |
| `.agents/generated/` (`DOCTRINE.md`, `LAWS.md`, `ROLES.md`, `RUNTIMES.md`, `INDEX.md`, the corpus, evaluation and governance pages) | the taken bundles and the host's declarations |
| `.claude/settings.json`, `.claude/skills/`, `.claude/agents/` | the claude-code adapter, the skills and the roles |
| `.codex/*`, `.agents/skills/` | the codex adapter and the skills |
| `.mcp.json` | `mcp-servers.json` |
| `.githooks/*` | the git adapter (activated with `activate --surface git-commit`) |
| `CODEOWNERS` | the github-actions adapter and the host's `owners.json` |
| the board of the host's cards | the cards (`delivery` capability) |

A **seed** is different. It is written once as a starting answer (for example
`.agents/project/doctrine/norms.json`), and from then on it belongs to the host.
