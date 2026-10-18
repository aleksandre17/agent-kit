# agent-kit

**Guide:** what the kit does, how, what it generates and how a host extends it -- [docs/guide/](docs/guide/README.md).

A framework that makes a repository ready for AI coding agents and keeps it that way. One command
installs, into any repository:

- **instructions the agents read** -- `CLAUDE.md` (and `AGENTS.md` for Codex): the project's laws,
  its build and test commands, its conduct doctrine and its roles, generated from declarations so
  they cannot drift from the tree;
- **guard rails that run** -- an edit hook in `.claude/settings.json` and a git pre-commit gate,
  both handing every change to one judge that applies the gates the project declares;
- **a delivery spine** -- cards, a board, registers and ADRs under `docs/`, with lifecycle states
  and an approval step on the transitions that need a person;
- **checks** -- `check` runs every declared fitness function and reports, never repairs;
- **an agentic layer** -- skills, MCP servers by trust, a normative tree of rules (RFC 2119), task
  classes and routes that pick the actor, model and effort, hooks with a declared posture, evals judged
  by oracles, and what every surface costs in context, measured.

**Every token serves the result.** What a script or a verb can do deterministically is done by it, at
zero tokens; a model is spent only where judgement is needed, and its result is accepted by oracles --
tests, gates, `check` -- never by itself. The always-loaded briefing carries laws and pointers only;
everything else is read on demand or loaded by description, and `check` reports the token cost of every
surface so the saving is visible.

The kit is vendored and pinned file by file (`.agents/kit/` + `kit.lock.json`), needs only
Python 3.10+ and git, and has no third-party dependency.

## Quick start

```sh
git submodule add https://github.com/aleksandre17/agent-kit.git kits/agent-kit
python kits/agent-kit/kit/interpreters/cli.py start --root . \
    --path kits/agent-kit/starters/standard.json --plan      # what it will do
python kits/agent-kit/kit/interpreters/cli.py start --root . \
    --path kits/agent-kit/starters/standard.json --approve "<your name>"
```

`start` walks a published **starter** (`starters/standard.json`: Claude Code, Codex/AGENTS.md and git served, the
cardinals, the conduct, the secrets and the declared-stopgaps policies taken, the commit gate active) and ends with `check` green. From then on
the repository runs its own pinned copy:

```sh
python .agents/kit/interpreters/cli.py check  --root .     # are the declared gates green?
python .agents/kit/interpreters/cli.py render --root .     # rebuild every generated file
python kits/agent-kit/kit/interpreters/cli.py upgrade --root . --plan   # take a newer kit
```

The whole pipeline, act by act, and the blueprint of every place the kit draws: [docs/guide/setup.md](docs/guide/setup.md).

### The first day: weighed by place, proved by what proves it

`start` drafts the host's **areas** -- where a change lands, what undoing it costs, and what proves it -- from
the modules its build tool declares (a module map its adapter publishes; stack-kit's does), plus its prose,
which `check` alone proves. A one-line change in a web module is then proved by that module's tests, a change to
the delivery declarations weighs heavier, and a push runs only what the change can affect (`prove`, the pre-push).
Where no area declares a proof yet, `prove` runs the test command the host declares. Either kit may come first:
after adding a build tool (or a module), re-read and re-draft, each a door you walk once:

```sh
python .agents/kit/interpreters/cli.py retake --root . --approve "<your name>"   # the reading sees the tool
python .agents/kit/interpreters/cli.py areas  --root .                           # the draft, nothing written
python .agents/kit/interpreters/cli.py areas  --root . --approve "<your name>"   # it only adds areas
```

A host that keeps the kit as a submodule need not carry a second copy of it: `python
kits/agent-kit/kit/interpreters/cli.py upgrade --root . --mode referenced --approve "<you>"` runs it
from the submodule at its pinned commit, and removes `.agents/kit/` once `check` is green.

A kit can also be read straight from where it is published, at an exact revision, instead of a
submodule: `--kit "git+https://github.com/aleksandre17/agent-kit.git@<tag>#subdirectory=kit"` (it is
cloned into a scratch outside the host, read with `git archive`, and refused unless it equals its lock).

Three things stay yours to write, because no framework can know them: the project's laws, as numbered rules
(`law: <n>` in `.agents/project/doctrine/norms.json`), a stance on each published cardinal
(`.agents/project/doctrine/doctrine.json`), and the build and test commands, declared where a
detector reads them (`stack-kit.json` `commands`, or `package.json` `scripts.test`).

## Words this kit uses

| here | in industry terms |
| --- | --- |
| door, `--approve <who>` | an approved command (human-in-the-loop approval), recorded with the approver's name |
| gate, `check` | a policy-as-code check / architecture fitness function, and running them all |
| edit gate, `judge` | a pre-commit / pre-write policy check, the hook that applies it |
| binding / projection / vendor / ephemeral plane | config the host owns / generated artifacts / the vendored, pinned dependency / runtime state, never committed |
| capability, take | a plugin (package) and installing it with a pinned digest |
| adapter | a driver for one product (Claude Code, Codex, git, CI) |
| bundle / policy / starter | a published content package / an enforced rule set / a project template |
| surface, render | an integration target and the code generation that writes it |
| reading, `retake` | discovered facts about the repository (detection), and re-detecting them |
| cardinal, doctrine, rule | a principle, a concern area, an RFC 2119 requirement (MUST / SHOULD / MAY) |
| stance | the project's conformance statement against a published principle (adopt, extend, narrow with an exception) |
| task class, route cell | a work classification and the routing policy that picks actor, model and effort |
| dispatch, packet | delegating a task to an agent worker, and its brief |
| trial | an agent eval judged by deterministic oracles |
| extension point, `extend` | a scaffolding generator for the project's own files |
| estate | the inventory of what the kit installed and who owns each path |
| conformance map | a standards traceability matrix with evidence |

## Where things are

| path | what |
| --- | --- |
| `kit/` | the payload: interpreters, capabilities, schemas, detectors -- [kit/README.md](kit/README.md), with the verb table |
| `adapters/` | runtime adapters published beside the kit (claude-code, codex, git, github-actions, ...) |
| `bundles/` | published content: doctrine (`cardinals`, `conduct`, `engineering`), skills (`kit-skills`, `engineering-standards`), opt-in mechanisms (`agent-evals`, `change-records`, `execution-graph`, `shared-tree`) |
| `policies/` | enforced rule sets: `secrets`, `untrusted-content`, `memory`, `recovery-points`, `spawn-packets` |
| `starters/` | the walks `start` takes a new repository through |
| `docs/decisions/` | ADRs -- why each mechanism is the way it is |
| `tests/` | unit tests and the fresh-repository acceptance suite, the development loop |

```sh
python -B -m pytest -p no:cacheprovider tests/unit -q
python -I -B tests/acceptance/fresh-repo/parallel.py
```

## Status

Version `0.2.0`, unreleased. Proven by the unit and acceptance suites on Windows and by its first
consumer; no signed release has been cut yet, so `release` reports authenticity as NOT
ESTABLISHED. No licence is declared yet.
