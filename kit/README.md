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
| `upgrade` | reconcile kit, lock and host three ways; a cell no steward answers is refused | only cells a steward declared, and nothing at all if any path refuses |
| `adopt` | read a host this kit never installed into; class every path or name it unaccounted | nothing — adoption reads |
| `inherit` | read a host's PRIOR agent system inside a declared boundary, measure each path, and print the disposition its migration map (`--map`) assigns; every state counted, an unanswered path `undecided` (ADR-011) | nothing — a roster is carried out at a door, never by this verb |
| `evaluate` | report the measure this host declared; with none declared, say the measure is zero | nothing |
| `lock` | re-take `kit.lock.json` from the manifest's own declaration closure | the lock |
| `move` | move a card to a declared state, recorded by who moved it | the card |
| `eject` | hand paths the kit shipped to the host, through a door signed by name; the kit never writes them again and every reading names them | the estate row, and nothing at all if any asked path cannot change hands |
| `takeover` | carry out the migration map at its declared residence: rename each relocated path into a kit space and each removed path aside into the observed plane, at a door that accepts the roster BY ITS DIGEST, re-read at the act; a killed act is reconciled and finished by the next run (ADR-012) | the prior paths the signed roster names, the act record, the estate's account -- and nothing at all if any path is undecided or the roster moved |

`eject` is granular, one path at a time (ADR-010 rejected the all-or-nothing CRA/`ng eject` shape
and named this verb `cede`; ADR-015 amendment 1 draws the verb list with the name `eject`, and one
verb carries the act -- never two for one act). A capability is left with `--disable`, and the
whole kit by no longer running it. A verb is a file in `interpreters/verbs/`; the
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
