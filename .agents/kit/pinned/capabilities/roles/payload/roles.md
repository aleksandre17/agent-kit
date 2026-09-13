# Roles — archetype, overlay, and the line between them

> **Kind: VENDOR.** Framework payload. Replaced wholesale on upgrade; never edited in a host.

## The defect this exists to make unreachable

Not a duplicated file. **Two files that are both right.**

One role, two homes — a definition in the framework and a definition in the host — and each is
internally correct. They drift, and the drift is invisible from either side, because a reader
standing at one of them sees no contradiction: there is nothing there to contradict. By the time
anybody notices, both have been obeyed, by different people, for months.

Synchronisation by discipline is not a mechanism. A single declaration is.

## The shape

A role definition is a **projection**, composed from two declarations and written by neither.

| | Declares | Lives | Answers |
|---|---|---|---|
| **Archetype** | what is true of the role as a KIND | the kit, or the host's own registry | *what is this role, anywhere?* |
| **Overlay** | what is true of THIS host's instance | the host's binding plane | *what does this repository do with one?* |
| **Definition** | neither — it is the composition | the projection plane | *what does this agent read?* |

## Where the line falls, and the test that decides it

**Can the sentence be written without naming a repository?**

If it can, it is true of the role as a kind and belongs to the **archetype**: its seam (the one
reason it changes), its duty order (what wins when its duties compete), its reference class (the
proven exemplars it is measured against).

If it cannot — because it names a package, a path, a stack, a model, a directory — it is this
host's instance and belongs to the **overlay**: which runtime settings it is given, which parts
of this repository it owns, what prose this host appends.

Two consequences, and they are the whole design:

**An overlay is closed to the archetype's vocabulary.** Its schema declares no `seam`, no `duty`,
no `reference_class`, and refuses properties it did not declare. A host therefore *cannot* write
a second body for a role that has one — not "should not". The divergence is not a discipline
anybody is asked to keep; it is a state that cannot be written down.

**An overlay never overrides. It only adds.** A key carried by both sides is refused, never
resolved. Overriding is precedence, and precedence is exactly how the losing declaration goes on
reading as true while the value came from somewhere else. If a host must vary something the
archetype states, *the archetype was wrong to state it* — that thing was never true of the role
as a kind, and the cure is to move it, not to let one side win an argument at render time.

## What the framework does not ship

**Any host's content.** No roster, no answers, no remembered facts, no role-private knowledge.
Knowledge is append-only and host-owned: it fits neither VENDOR (replaced on upgrade) nor
PROJECTION (regenerated), so it is BINDING, and the framework's whole duty toward it is to
declare where it lives and what a record must contain.

A host that has hired nobody gets a roll that **says so, in those words**, and no definitions.

## Roles with no shipped ancestor

They are not an exception to the grammar. A host declares an archetype of its own — in exactly
the same shape, in its own registry — and an overlay that names it. Two sources for bases, one
grammar, and neither source outranks the other. An id declared by both is refused rather than
ordered, for the reason everything else here is refused rather than ordered.

## The zeros, and why each occupies space

- A host with **no overlays** projects a roll saying it has declared no role. A page that simply
  ended would read exactly like a page whose roles failed to render.
- An archetype **nobody instanced** is listed and counted as shipped-and-never-instanced. Omitted,
  it would be indistinguishable from an archetype that was never shipped — and those are two very
  different questions, asked of two different people.
- An overlay naming an archetype **nobody declares** renders a definition that says UNBOUND. It is
  not skipped and it is not a traceback: an overlay alone reads exactly like a complete role to
  anyone who only opens the file. `check` says the same thing with an exit code, under
  `FF-ROLE-BASE`. The surface and the gate know it independently, and neither is allowed to be the
  only one that does.
