# Context and skills

Every token an agent spends should serve the result, so context is layered and measured:

| Layer | What | Loaded |
|---|---|---|
| always | the briefing (`CLAUDE.md`, `AGENTS.md`): the host's laws, how a change is built and proven, pointers | at every session |
| on demand | the pages under `.agents/generated/` (doctrine, roles, runtimes, corpus) | when a pointer is followed |
| by description | skills | when their description matches the task |

- `check` reports each served surface's size per layer against its budget (FF-CONTEXT).
- The always-loaded text is ordered stable-first, so a product's prompt cache can reuse it.
- A task router (the generated index) names, for each kind of task, the one page to read.

## Skills

A skill follows the Agent Skills standard: a `SKILL.md` with `name` and `description`, and
optionally `scripts/` and `references/`.

**Published by bundles:**

- `kit-skills`: propose a law, take a capability, walk a door.
- `engineering-standards`: the architecture and engineering reference, with chapters loaded on
  demand.

**Declared by the host:** in `.agents/project/skills.json`. A host can also extend a published
skill with its own chapters. For the standards skill these live in
`.agents/project/skills/standards/<name>.md` and hold the host's stack, its profile, and the line a
change travels in that system.

The served skill is the published chapters plus the host's, under one generated index.

## MCP servers, memory, untrusted content

- **MCP servers.** A host declares each one once, with its trust, in
  `.agents/project/mcp-servers.json`. Each adapter projects them into its product (`.mcp.json`,
  `.codex/config.toml`). An untrusted server's tools are denied write and exec by default.
- **Memory.** The `memory` policy says a product's persistent memory points to a fact's home; it
  never copies the fact.
- **Untrusted content.** The `untrusted-content` policy says content from tools, MCP servers, the
  web and unauthored files is data, never instructions.
