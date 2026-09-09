# `kit/` — the payload

Exactly this directory is what lands in a host. Nothing above it travels: not the tests, not the
CI, not this repository's history. That is the Helm-chart and Terraform-module convention — the
unit of distribution is a directory with a manifest at its head — and it is what lets the
acceptance test be honest, because the test may read only from here.

## The one seam

Every path the kit produces in a host belongs to exactly one **class**, and the class is
**declared**, never read off a folder name:

| class | plane | who writes it | on re-run |
| --- | --- | --- | --- |
| `vendor` | `.agents/kit/` | the framework | replaced wholesale |
| `binding` | `.agents/project/` | the host | created once if absent, then never written |
| `projection` | `.agents/generated/` | `render` | deleted and rebuilt from scratch |
| `ephemeral` | `.agents/runtime/` | whatever observed it | never committed, never upgraded |

A projection is not a copy. Delete the whole projection plane, run `render`, and the bytes come
back identical — that is gate `FF-KIT-PROJECTION`, and it is what makes the plane safe to own.

## Verbs

```
python kit/interpreters/cli.py <verb> --root <host-repo> [--kit <kit-dir>]
```

| verb | does | writes |
| --- | --- | --- |
| `init` | measure the host, resolve what it chose, draft the answer, seed once, vendor, render, check | the answer first; everything else only once it is approved |
| `render` | recompute every projection from vendor + binding | projection only |
| `check` | run the declared gates; report, never repair | nothing |

`upgrade` and `eject` are designed and not built. A verb is a file in `interpreters/verbs/`; the
entry point discovers it and knows no verb's name.

### Choosing, and approving

```
init --root <host> --enable governance      # this host's set is exactly these
init --root <host> --disable knowledge      # ... or everything available except these
init --root <host> --plan                   # print every write, touch nothing
init --root <host> --approve <who>          # accept the drafted answer; only now does it install
```

The set is chosen ONCE. Before the host has answered, the flags author `.agents/project/project.json`;
afterwards that file **is** the answer and a flag that contradicts it is refused — edit the file.

`init` on a fresh host writes the draft and stops with **exit 3**: an install nobody approved is a
dated state on disk, not a hung process and not a silent proceed. `render` and `check` refuse while
it stands. `--plan` is available on every verb that writes, and it is not a preview: the verb
decides once, `--plan` prints that decision and the apply carries out the same one.

## What is a declaration here

Four kinds, each schema-validated the moment it is read, each carrying no behaviour whatsoever:

- **`MANIFEST.json`** — the planes, the capabilities, the detectors, the schema registry.
- **`capabilities/<id>/capability.json`** — what a capability requires, installs, and gates. Its
  `installs` list is also its **write scope**: the interpreter physically cannot write a path the
  capability did not declare.
- **`detectors/*.json`** — evidence that would be true, and what it would mean. There is no list of
  known stacks anywhere in the interpreter; a new ecosystem is a new file.
- **`schemas/*.schema.json`** — the JSON Schema subset the kit interprets itself, so a host needs
  nothing installed. `interpreters/validation.py` refuses a keyword it cannot honour rather than
  ignoring it.

## The rule this kit is built to survive

A framework born inside its first host cannot tell universal from familiar. So the kit is never
judged by working here; it is judged by `tests/acceptance/fresh-repo/`, which installs it into a
repository it has never met.
