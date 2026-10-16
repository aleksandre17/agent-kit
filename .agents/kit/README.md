# The kit — the payload

Exactly this directory is what lands in a host. Nothing above it travels: not the tests, not the
CI, not this repository's history. That is the Helm-chart and Terraform-module convention — the
unit of distribution is a directory with a manifest at its head — and it is what lets the
acceptance test be honest, because the test may read only from here.

**Where you are reading this decides what you may do here.** At the publisher, in `kit/`, this is
the source: it is edited, locked (`lock`) and released. In a host, at `.agents/kit/`, it is the
PINNED copy of a release, held byte for byte to `.agents/project/kit.lock.json` by
`FF-KIT-PINNED`: it is never edited there — a change is made at the publisher and arrives by
`upgrade`. The framework's own repository is both (ADR-016 decision 8, host #0): its `kit/` is the
source and its `.agents/kit/` is the release it runs on, so a broken edit to the source can never
switch off the gates that judge it.

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

<!-- verbs:begin -- derived from each verb's SUMMARY and MUTATES -->
| verb | does | writes |
| --- | --- | --- |
| `activate` | point a setting outside the tree at what a served surface serves -- or withdraw it -- through a door | yes -- `--plan` prints the writes first |
| `adopt` | read a host this kit has never touched and name every path that has no class | nothing |
| `capsule` | show the continuity capsule, or replace one revision of it by compare-and-swap | yes -- `--plan` prints the writes first |
| `check` | run the declared fitness functions and report | nothing |
| `claim` | take, list, release or break by name a claim on paths, which the judge holds other writers to | nothing |
| `dispatch` | hand one act to the dispatch port: start a worker for a task, or carry an operator's answer back into one that asked | yes -- `--plan` prints the writes first |
| `doctor` | prove every served hook refuses a throwaway violation, and read what each product fired | nothing |
| `eject` | hand a path the kit shipped to the host, through a signed door | yes -- `--plan` prints the writes first |
| `evaluate` | open a judgement for every declared pair that has none, and state the measure | yes -- `--plan` prints the writes first |
| `extend` | scaffold a host extension from its declared point, list the points, or merge a newer template | yes -- `--plan` prints the writes first |
| `ground` | record a measured fact with its instrument and paths, or read one back while it still holds | nothing |
| `guard` | before a command a runtime runs: a destructive one gets a recovery point first (advisory) | nothing |
| `inherit` | read a host's prior agent system and state what becomes of every path of it | nothing |
| `init` | measure, choose, draft the answer, seed, vendor, render, check | yes -- `--plan` prints the writes first |
| `judge` | judge one edit a runtime hook hands over, against this host's declared edit gates | nothing |
| `ledger` | after a product's sub-agent stops: requested vs verified model and tokens, one ledger row (advisory) | nothing |
| `lock` | enumerate what the kit is, measure it, and record the reading | yes -- `--plan` prints the writes first |
| `message` | before a change is recorded: its message must take the form the host's message rules declare (blocking) | nothing |
| `move` | move one card across one declared transition | yes -- `--plan` prints the writes first |
| `propose` | state what this host learned that it says is not its own, as text a person carries | nothing |
| `release` | state what this kit is as a release, or refuse to call a working tree one | nothing |
| `render` | recompute every projection from VENDOR + BINDING | yes -- `--plan` prints the writes first |
| `retake` | take this host's reading again, through a door, when its reality has legitimately moved | yes -- `--plan` prints the writes first |
| `review` | check that a review range is covered by verified change records (tri-state JSON report) | nothing |
| `session` | at a session's start: one context line -- the kit, how a change is proven, the capsule's handoff (advisory) | nothing |
| `spawn` | before a runtime starts a sub-agent: the brief must be a packet under its ceiling (blocking) | nothing |
| `start` | carry a host from nothing to a served, checked install in one door, by a published starter | yes -- `--plan` prints the writes first |
| `stop` | before a session ends: the continuity capsule it leaves must keep its contract (blocking) | nothing |
| `take` | take a published capability into this host's take plane, beside the pinned kit | yes -- `--plan` prints the writes first |
| `takeover` | carry out the host's signed migration map, through a door that accepts its roster digest | yes -- `--plan` prints the writes first |
| `trial` | run an agent eval on a fixture host, judged by the host's gates and check, recorded with its cost | yes -- `--plan` prints the writes first |
| `upgrade` | reconcile what was shipped, what the host has, and what this kit ships -- then install | yes -- `--plan` prints the writes first |
<!-- verbs:end -->

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
