# Norms, laws, gates and the audit

## The normative tree

Everything an agent is held to is one tree of documents of the `cardinal` contract, told apart by
genre (ADR-024):

```text
L0 cardinal     a principle, never waived
L1 doctrine     a concern area (architecture, contract, data, security, testing, delivery, ...)
L2 rule         an RFC 2119 modality: MUST (needs an enforcer), SHOULD (deviation needs a recorded reason), MAY
L3 enforcement  an edit gate, a gate, a verb, or an adapter's enforcer that holds a MUST (`enforced_by`)
L4 procedure    a skill that says how to apply a doctrine
```

Every norm below a cardinal derives from exactly one parent (`derives_from`), so the tree stays a
tree. `check` (gate FF-NORMS) refuses:

- an orphan;
- a cycle;
- two rules on one subject with opposite modalities;
- a MUST with no enforcer the host has;
- a host stance that loosens a rule without an exception (ADR, owner, expiry, compensating control);
- an expired exception.

The `engineering` bundle publishes the generic tree: cardinals E1-E6 and their doctrines and rules.
The cardinals are:

- E1: one case never defines the system.
- E2: source facts are immutable.
- E3: under uncertainty, refuse.
- E4: proven, not claimed.
- E5: one owner per concept.
- E6: whole-system integrity.

Addresses carry the release, for example `engineering@1.1.0#fail-closed`.

## Enforcers a MUST may name

| Form | Accepted when |
|---|---|
| `gate:<id>` | a gate of an enabled capability has that id |
| `edit-gate:<id>` | an edit gate in force has that id |
| `verb:<name>` | the kit has that verb |
| `<prefix>:<name>` | a taken adapter vouches for it, and the host declares it |

An adapter vouches by shipping a document of contract `enforcers`: a `prefix`, a host JSON file
(`path`) and a `pointer` into it. Each key under the pointer with a non-empty value is an enforcer.
The stack-kit adapter vouches for every command in the host's `stack-kit.json` `commands` block:
`stack-kit:test`, `stack-kit:build`, `stack-kit:validate`. A host whose manifest does not declare
`commands.test` gets NT-UNENFORCED for a MUST that names only `stack-kit:test`. The core names no
product (ADR-024 decision 23).

## A host's laws

A host adds its own rules in `.agents/project/doctrine/norms.json`.

- A rule that carries `law: <n>` is one of the host's numbered laws.
- The briefing's law list (`CLAUDE.md`, `AGENTS.md`) is rendered from those rules, in order, so the
  laws have one source. FF-LAWS refuses a host that has both a `laws.md` and numbered rules.
- `upgrade --mode laws` migrates an older host's `laws.md` into rules.

## Edit gates

A text rule that a diff can show is an **edit gate**. A gate declares:

- an id and the paths it holds;
- the pattern it `forbids`;
- why, and what to do instead;
- a calibration: a text it must refuse (`proves`) and a lookalike it must admit (`admits`). An
  uncalibrated gate is not believed.

A host's own gates live in `.agents/project/enforcement/edit-gates.json`; the policies ship theirs.
One rule has one home: a gate id declared twice is refused (KIT0005).

## The whole-tree audit

`judge` sees only what a change introduces. `audit` runs every gate over every tracked file.

A violation already in the tree is acknowledged in
`.agents/project/enforcement/known-violations.json` (`gate`, `path`, `tracking`, optional
`until`), never by switching a gate off.

- An expired acknowledgement becomes a finding again.
- An acknowledgement that matches nothing is reported stale.
- `check` shows the counts (gate FF-TREE-AUDIT). It stays `observe` unless the host raises it.
