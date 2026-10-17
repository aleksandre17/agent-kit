# agent-kit guide

agent-kit answers one question for a repository: *how do AI agents (Claude Code, Codex, and the next
one) work here, and what are they held to?* It is a framework. The kit holds the mechanism, the
defaults, the schemas and the templates; a host repository only declares its own answers.

Read in this order:

| Page | What it explains |
|---|---|
| [setup.md](setup.md) | the setup pipeline, act by act; the daily loop; alone and with stack-kit; the host blueprint |
| [overview.md](overview.md) | capabilities, the take plane, vendored and referenced installs, the CLI |
| [hooks.md](hooks.md) | what runs on every agent action: writes, shell commands, sub-agents, sessions, commits, pushes |
| [norms-and-laws.md](norms-and-laws.md) | the normative tree, a host's laws, edit gates, the whole-tree audit |
| [context-and-skills.md](context-and-skills.md) | what an agent loads always and what on demand; skills and their host chapters; MCP, memory, untrusted content |
| [generated-files.md](generated-files.md) | every file the kit writes into a host, and what it is computed from |
| [extending.md](extending.md) | extension points: how a host adds its own without editing the kit |
| [doors.md](doors.md) | decisions only a person makes, and how they are recorded |
| [refusals.md](refusals.md) | what each refusal means and what to do |
| [developing-the-kit.md](developing-the-kit.md) | how to change the kit itself, how versions work, how a host takes a change |

The decisions behind each mechanism, with their rejected alternatives, are in
[`docs/decisions/`](../decisions/); ADR-024 covers the agentic layer. The full verb list is the
CLI's own help: `python kit/interpreters/cli.py --help`.
