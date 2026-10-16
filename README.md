# agent-kit

A framework that makes a repository ready for AI coding agents and keeps it that way. One command
installs, into any repository:

- **instructions the agents read** -- `CLAUDE.md` (and `AGENTS.md` for Codex): the project's laws,
  its build and test commands, its conduct doctrine and its roles, generated from declarations so
  they cannot drift from the tree;
- **guard rails that run** -- an edit hook in `.claude/settings.json` and a git pre-commit gate,
  both handing every change to one judge that applies the gates the project declares;
- **a delivery spine** -- cards, a board, registers and ADRs under `docs/`, with lifecycle states
  and an approval step on the transitions that need a person;
- **checks** -- `check` runs every declared fitness function and reports, never repairs.

The kit is vendored and pinned file by file (`.agents/kit/` + `kit.lock.json`), needs only
Python 3.10+ and git, and has no third-party dependency.

## Quick start

```sh
git submodule add https://github.com/aleksandre17/agent-kit.git platform/kits/agent-kit
python platform/kits/agent-kit/kit/interpreters/cli.py start --root . \
    --path platform/kits/agent-kit/starters/standard.json --plan      # what it will do
python platform/kits/agent-kit/kit/interpreters/cli.py start --root . \
    --path platform/kits/agent-kit/starters/standard.json --approve "<your name>"
```

`start` walks a published **starter** (`starters/standard.json`: Claude Code, Codex/AGENTS.md and git served, the
cardinals, the conduct and the secrets policy taken, the commit gate active) and ends with `check` green. From then on
the repository runs its own pinned copy:

```sh
python .agents/kit/interpreters/cli.py check  --root .     # are the declared gates green?
python .agents/kit/interpreters/cli.py render --root .     # rebuild every generated file
python platform/kits/agent-kit/kit/interpreters/cli.py upgrade --root . --plan   # take a newer kit
```

A kit can also be read straight from where it is published, at an exact revision, instead of a
submodule: `--kit "git+https://github.com/aleksandre17/agent-kit.git@<tag>#subdirectory=kit"` (it is
cloned into a scratch outside the host, read with `git archive`, and refused unless it equals its lock).

Three things stay yours to write, because no framework can know them: the project's laws
(`.agents/project/doctrine/laws.md`), a stance on each published cardinal
(`.agents/project/doctrine/doctrine.json`), and the build and test commands, declared where a
detector reads them (`stack-kit.json` `commands`, or `package.json` `scripts.test`).

## Words this kit uses

| here | in common terms |
| --- | --- |
| door, `--approve <who>` | an approval step, recorded with the approver's name |
| binding / projection / vendor / ephemeral plane | config the host owns / generated files / the pinned kit / runtime state, never committed |
| take, taken capability | install an add-on (adapter or bundle) beside the pinned kit |
| reading, `retake` | the measured facts about the repository, and re-measuring them |
| cardinal, stance | a published principle, and this project's answer to it |
| gate, `check` | a fitness function, and running them all |
| estate | the record of what the kit installed and who owns each path |

## Where things are

| path | what |
| --- | --- |
| `kit/` | the payload: interpreters, capabilities, schemas, detectors -- [kit/README.md](kit/README.md), with the verb table |
| `adapters/` | runtime adapters published beside the kit (claude-code, codex, git, github-actions, ...) |
| `bundles/` | doctrine bundles: `cardinals`, `conduct` |
| `policies/` | edit gates every host holds once taken: `secrets` |
| `starters/` | the walks `start` takes a new repository through |
| `docs/decisions/` | ADRs -- why each mechanism is the way it is |
| `tests/` | unit tests and the fresh-repository acceptance suite, the development loop |

```sh
python -B -m pytest -p no:cacheprovider tests/unit -q
python -I -B tests/acceptance/fresh-repo/parallel.py
```

## Status

Version `0.1.6`, unreleased. Proven by the unit and acceptance suites on Windows and by its first
consumer; no signed release has been cut yet, so `release` reports authenticity as NOT
ESTABLISHED. No licence is declared yet.
