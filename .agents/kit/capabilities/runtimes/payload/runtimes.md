# Runtimes — the doctrine

> VENDOR. This file is the kit's, it is replaced wholesale on upgrade, and nothing a host writes
> in it survives. What this host declares lives in `.agents/project/runtimes/` and
> `.agents/project/runtime-classes.json`.

## Why a runtime is a declared subject at all

A runtime is the tool a host executes its agents on. Every surface that mentions one — an
instruction file, a launcher, a piece of documentation — was previously free to state its own
version of what that tool can do, and every one of those statements was locally correct. That is
the condition under which a system speaks with confidence and lies: two homes for one truth, both
internally consistent, neither able to detect the other from where it stands.

So the runtime is declared once. The kit ships CLASSES, which state what is true of a runtime as
a KIND: how an agent reaches it at all, and which translation sits in the gap between it and the
work. A host authors DESCRIPTORS, which state what a host legitimately says about its own tool.
The descriptor is the composition of the two, and it is rendered, never written.

**No vendor's name appears anywhere in the kit.** The name of a product is the one thing about a
runtime that is guaranteed not to be true of the kind, and a registry that carried one would have
to be edited every time somebody shipped. A tool's proper name is data, in a descriptor a host
owns, where the choice is visible, revisable and reversible.

## The line, and the test for it

Can the sentence be written without naming a repository or a product?

- If it can, it is the runtime AS A KIND. It belongs to a class.
- If it cannot, it is this host's instance. It belongs to a descriptor.

A descriptor never OVERRIDES its class. A key carried by both sides is refused rather than
ordered, because precedence is exactly how the loser's declaration goes on reading as true while
the value came from somewhere else. Where a host must vary something a class states, the class
was wrong to state it: that thing was never true of the kind, and the cure is to move it.

## Claimed, proven, absent

This capability exists because of a failure that has already happened here. A runtime's
capabilities were written down and believed. One of them was an invocation shape — whether work
crosses the boundary as an argument vector or as a string to be re-parsed — and it had been
ASSUMED. A peer runtime later reported all eight of its claimed capabilities as unproven, and was
right.

**A runtime's capabilities are not known. They are proven.** So three states, and every declared
capability is placed in exactly one of them, for every runtime, always:

- **CLAIMED** — a host says it, and carries the reason it believes. Testimony, labelled as
  testimony. The reason is required, and required to be a sentence rather than a flag: `true`
  cannot be wrong out loud, and a belief that cannot be read cannot be contradicted.
- **PROVEN** — a record of something that HAPPENED names this runtime and this capability. There
  is no field in the descriptor schema in which a proof can be written, and none may be added,
  because the document is closed. A host cannot author a proof. That is the point.
- **ABSENT** — the vocabulary declares the capability and this host claims nothing about it. It
  is named, never omitted: a short list of claims and a runtime that genuinely needs nothing read
  identically to anyone shown only what is present.

The vocabulary is what makes the third state possible at all. A capability with no declared name
cannot be missing from anything.

## The zero that is not a measurement

Today no record in this repository names a runtime and a capability together. The PROVEN group is
therefore empty for every runtime, and the surface says WHY in those words rather than printing a
zero: a count taken where no instrument exists is an attribution that cannot fail, and an
attribution that cannot fail certifies rather than measures.

That absence is a declared gap and not an oversight. What would have to happen for each capability
is written beside it, in the vocabulary, as `observed_by` — declared there rather than left to
whoever gets around to checking, because a capability whose proof nobody specified is proven by
consensus, which is testimony wearing a lab coat.

## Settings are not capabilities

What a host CONFIGURED is not what a runtime DOES. A setting is projected as a setting however
confidently it was written — an invocation shape, a model, a working directory. The one that cost
most was a setting that read like a fact.
