---
kind: decision
authority: canonical
owns: starting-a-host
---

# ADR-023 — A new host starts in one door, and is served to the field's standards

- **Status:** accepted (2026-10-16, owner-delegated)
- **Deciders:** the owner's delegate, on the owner's instruction that the kit be a working framework a
  new project receives whole, judged against current practice from outside and not by its own rules.
- **Amends:** ADR-013 (serving a runtime): what the briefing carries and how a hook fails.

## Context

Each new project needed seven acts and two hand-written JSON declarations before `check` went
green: `init` twice, `take` per adapter and bundle, editing the answer to enable them, writing a
runtime descriptor per surface, `render`, and `activate`. An external audit then held the kit
against current practice (AGENTS.md, Agent Skills, OWASP LLM06, OpenSSF Scorecard, Diátaxis) and
found, among other things:

- the served briefing told an agent nothing about how to build or test the project, and on a fresh
  host it served the laws seed's own authoring instruction ("Delete the sentence you are reading")
  as if it were a law;
- the Claude Code and Codex hooks ran a bare `python`, so a machine without it ran no judge at all:
  in Claude Code a non-2 exit does not block, so the gate failed open;
- nothing stopped an interactive session from hand-editing the pinned kit or a generated page; it
  was caught only later, by `check`;
- the kit's own suites ran in no CI, and the one workflow template pinned its action by tag;
- the verb table in `kit/README.md` listed 11 of 21 verbs, and the README said "day one".

## Decision

1. **Starters.** A starter is a document published beside the kit (`starters/<id>.json`, schema
   `starter`) declaring what a new host takes, which runtimes it serves and which surfaces it
   activates. Verb `start --path <starter> --approve <who>` walks it as the verbs a person would
   run, each a separate run of the same kit, printed with its exit; the first failure stops the walk
   (`KIT0073`), and what landed stays because each act is safe to repeat. One door, one name on
   every act. Activation precedes the attesting `init`, whose closing `check` must not meet a served
   setting not yet pointed at what it serves. A starter decides what a host RUNS, never what it
   HOLDS: laws and stances stay unanswered and are named as such. `standard` serves Claude Code,
   Codex (AGENTS.md, which most other agents also read) and git, takes the cardinals and the
   conduct, and activates the commit gate.
2. **Commands in the briefing.** Projection `.agents/generated/evaluation/COMMANDS.md`, one line per
   consumed reading (`build-command`, `test-command`), inlined in the briefing. Detector
   `stack-kit-commands` reads `stack-kit.json` `commands.test` / `commands.build` as the host
   spelled them; an undeclared command is named as undeclared, never invented. The laws seed no
   longer serves authoring prose: an HTML comment and "No project law is declared yet."
3. **A plane is written by its writer.** Gate kind `plane-held-by-its-writer` (`FF-PLANE-WRITER`,
   floor enforce) refuses an edit inside the `vendor` and `projection` planes from the runtime
   classes it names (`an-interactive-session`), with the verb to run instead. The judge learns the
   writer's class from the runtimes served through the surface (`attestation.classes_through`). A
   batch writer (a commit, CI) carries what the plane's own verb wrote and is judged by `check`; a
   writer of unknown class is judged, never exempt.
4. **Hooks fail closed.** The Claude Code and Codex hook commands probe `python3`, `python`, `py`
   as the git hook does, and refuse with the surface's refusal exit when none runs.
5. **Pinned by commit.** The github-actions template pins `actions/checkout` by full SHA (v6.1.0,
   verified with `git ls-remote`). The kit's own suites run on Ubuntu and Windows, Python 3.10 and
   3.13 (`.github/workflows/tests.yml`, owner-authored).
6. **The verb table is derived.** `kit/README.md` carries the table between markers, built from
   each verb's `SUMMARY` and `MUTATES`; `test_verb_reference` fails when it drifts. The README
   is rewritten: what the kit gives, a quick start through `start`, a glossary of the kit's words
   in common terms, and an honest status.

## Considered options

- *A bootstrap script outside the kit* — rejected: a second home for what each verb already owns,
  and nothing would hold it to the verbs' doors.
- *`start` calling the verbs in-process* — rejected: the composition changes after each `take`, and
  a run holding one manifest would be judging a host that moved under it. A separate run per act is
  exactly what a person runs.
- *A starter that also writes stances* — rejected: a stance is the host's own word (doctrine
  schema), and a published default answer reads as one the host gave.
- *A detector that guesses build and test commands from a `.sln` or `angular.json`* — rejected:
  the verification page has always refused to invent a way of proving a change; the cure is a
  declaration a detector reads.
- *Refusing every edit to a kit plane, including commits* — rejected: it refuses the commit of every
  `upgrade`. The writer's class is what distinguishes a hand edit from a verb's output.
- *A separate `agents-md` adapter* — rejected for now: AGENTS.md is already the codex adapter's
  render, and two adapters rendering one target would be two homes. `CLAUDE.md` importing
  `@AGENTS.md` is the remaining step if the two briefings ever need to diverge.

## Not decided here (the owner's)

- A licence: until one is declared the kit cannot legally be adopted outside the owner's work.
- Signed releases and a signed lock (`release` still reports authenticity NOT ESTABLISHED).
- Whether `--approve <who>` must be backed by a signature: today it records a name, and an agent the
  owner delegated to can give it. The judge could refuse `--approve` from an interactive session
  unless the host declares the delegation.

## Proof

Acceptance `test_start` 407–409, `test_commands` 412, `test_enforcement` 289c–289d; unit
`test_verb_reference`. Each mutation-checked: door removed, capability check removed, plane gate
emptied, bare-python hook restored.
