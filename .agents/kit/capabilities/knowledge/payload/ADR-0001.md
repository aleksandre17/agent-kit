# ADR-0001 — A document's kind decides its authority

- Status: accepted
- Date: seeded at install
- Deciders: this host

> SEED. Created once, then owned by this host. The kit will never rewrite or diff this file.
> It is here because a corpus with no first decision has no place to put its second one.

## Context and problem statement

Rules accumulate wherever they are first written down: in a proposal, in a review comment, in a
README that happened to be open. Each is true where it was written and invisible everywhere else.
A reader who finds one cannot tell whether it binds; a reader who does not find it cannot tell
that it exists. The corpus is then never wrong in any single place and is unreliable as a whole.

## Decision

A document's **kind** — the directory it lives in — decides whether it may declare a rule.
`docs/decisions/` declares; `intent`, `reference`, `guides` and `archive` do not. A rule that
binds is recorded here, as a decision, or it does not bind. This is enforced mechanically by the
`FF-KIND-AUTHORITY` gate, which refuses a file whose name claims an authority its location cannot
grant.

Decisions are append-only. An accepted decision is not edited into a new opinion; it is
superseded by a later decision that says so, so that the reasoning stays readable in the order it
actually happened.

## Consequences

- A rule can be located by looking in exactly one place.
- Moving a document changes what it is allowed to say — which is the point, and is why the gate
  reads the location and not the prose.
- Writing down a binding rule now costs an ADR. That cost is deliberate.
