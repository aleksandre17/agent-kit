# Overview

## Capabilities

Everything the kit does is a **capability**: a directory with a `capability.json` that declares its
documents, seeds, projections and gates. There are four kinds:

| Kind | Where | Examples |
|---|---|---|
| core | `kit/capabilities/` | governance, doctrine, enforcement, knowledge, runtimes, roles, evaluation |
| adapters | `adapters/<product>/` | `claude-code`, `codex`, `git`, `github-actions`, `stack-kit`, and the ecosystem detectors (`dotnet`, `node`, `pnpm`, `python`, `go`) |
| bundles | `bundles/<id>/` | `cardinals`, `conduct`, `engineering`, `engineering-standards`, `kit-skills`, `memory`, `shared-tree`, `change-records`, `execution-graph` |
| policies | `policies/<id>/` | `secrets`, `untrusted-content`, `recovery-points`, `spawn-packets`, `conventional-commits` |

Only adapters name a product. The core reads products only through the contracts the adapters
keep, so a new product is a new adapter directory and never a core edit.

## Taking

A host **takes** a capability with `take --path <dir> --approve <who>`. The take is pinned by digest
and version in the host's provenance.

A **starter** (`starters/standard.json`) declares a whole walk: which capabilities to take, which
runtimes to serve, which surfaces to activate. `start` walks it under one name.

If a capability's bytes change upstream without a new version, the host refuses the change as
drift. A publisher who changes bytes releases a new version.

## Installs: vendored or referenced

- **Vendored** (the default). The kit is copied into the host under `.agents/kit/`, and taken
  capabilities under `.agents/taken/`.
- **Referenced**. A host that holds the kit in its own tree at a pinned commit (a git submodule)
  runs it from there, with no copy. The lock records the kit's path, commit and tree. Every hook and
  `check` refuse a kit that is missing, at another commit, or edited (KIT0083).
  `upgrade --mode referenced` moves a vendored host to referenced, and re-pins a referenced host
  after its submodule moves. On a referenced host a plain `upgrade` does the same: the host stays
  referenced. Only `upgrade --mode vendored --approve <who>` returns it to copies.
- **A take re-released in the submodule.** When the submodule advanced and a taken capability now
  has a newer version at its referenced source, `upgrade --mode referenced --approve <who>` takes it
  again in the same walk: the pin moves to the new version, and no copy is made. Bytes changed under
  the same version stay refused as drift (KIT0032) (ADR-024 decision 22).

## The CLI

```text
python <kit>/kit/interpreters/cli.py <verb> --root <host> [--plan] [--approve <who>]
```

| Verb or flag | What it does |
|---|---|
| `--plan` | prints the exact writes and touches nothing |
| `check` | runs every declared fitness function |
| `render` | recomputes every projection |
| `audit` | runs every edit gate over the whole tree |
| `doctor` | proves each served hook actually refuses a throwaway violation |
