# Knowledge with declared authority

> VENDOR. This file is framework payload: it is replaced wholesale on upgrade and never edited
> downstream. What is true *for this host* belongs in the BINDING plane, not here.

## The rule this capability exists to hold

**A binding rule living in a kind that cannot declare has no authority, however true it is — and
the reader cannot tell, which is the harm.** The rule is obeyed by whoever happens to find it and
unknown to everyone else, and both of those readers are locally correct. The failure is not that
the rule is wrong; it is that the corpus speaks with confidence and cannot be contradicted.

So authority is not a property of a document's content, nor of its tone, nor of how true it is.
It is a property of **where it lives**. A kind either grants declaring authority or withholds it,
and a document inherits exactly what its kind grants — no more, and never by claiming it.

## Kinds

The taxonomy is Diátaxis (what a document is FOR) crossed with MADR (how a decision is recorded)
and the Kind Law (what a location may grant):

- **intent** — what we want. Durable, few, owner-blessed. States direction, not rules.
- **decisions** — ADRs. This is the only kind that **DECLARES**. Append-only; an accepted decision
  is immutable, and it is superseded by a later decision rather than edited. The path is MADR's
  canonical `docs/decisions/`, adopted rather than invented.
- **reference** — what is true now. Describes; never commands.
- **guides** — how to do a thing.
- **archive** — DEAD BY LOCATION. Nothing here binds anyone, whatever it says.

Which kinds exist, and which of them declare, is stated **once** — in this capability's own
declaration, as the parameters of its gate. This page explains the identity; it deliberately does
not restate the table, because a table with two homes drifts while both copies read as correct.

## What the gate catches

`FF-KIND-AUTHORITY` compares a document's **claim** with its location's **grant**. A file name is
a claim: `ADR-…`, `CANON-…`, `DESIGN-…`, `LAW-…` all announce to a reader that the thing inside
binds. If such a name sits in a kind that cannot declare — or in no declared kind at all — the
gate fails and names both the claim and the grant it lacks.

The cure is never to soften the gate. It is one of: promote the content to a decision, move it to
the kind that fits what it actually is, or rename it so it stops claiming what it never had.
