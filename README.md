# agent-framework

The portable, host-agnostic agent framework. Its payload is `kit/`; nothing else in this
repository is ever installed into a host.

**Status: day one.** Nothing here is proven. The design it is built against lives, for now, in the
first host's repository as two NON-BINDING proposals:
`docs/architecture/proposals/PROPOSAL-agent-framework-layout.md` (the four-class seam, the
vendored-with-lockfile distribution, the five verbs) and
`PROPOSAL-agent-framework-blueprint.md` (seven levels, capability as the unit, initialization
P0–P9, the intelligence axis). Those proposals move here once this repository can stand on its own.

## The one rule that decides everything here

A framework born inside its first host cannot tell **universal** from **familiar** — everything
works there, so nothing is measured. Therefore this repository's first host is a scratch repo it
has never met, and `tests/acceptance/fresh-repo/` is the development loop, not a final exam.

## What may enter

Forms are rebuilt from scratch; no file is copied from any existing system. Findings — measured
lessons, declared gaps, the failures that produced the cardinals — are inherited in full. Rebuilding
a form is discipline; discarding a finding is amnesia.
