# ADR-003 — Adoption, and the path that has no class

- **Status**: Accepted
- **Date**: 2026-09-10
- **Amended**: 2026-09-11 — §6, on first contact with a tree the kit did not create
- **Supersedes**: nothing
- **Amends**: ADR-001 (the framework blueprint), by settling the `foreign` question it left open;
  ADR-002 (three-way reconciliation), by naming the reading in which S is empty rather than absent

## The situation

`upgrade` met a tree the kit had created and a human had then edited. Adoption meets a tree the
kit has **never touched** — full of paths written by people and tools that never heard of this
kit, whose provenance is unknown and unknowable from inside the tree.

Two things about that host are different, and only two:

1. **There is no estate.** Not "an estate that might be stale": none. ADR-002 refuses an upgrade
   in that situation, and it is right to — an upgrade must tell *the host edited this* from
   *upstream changed this*, and with no record it can tell neither.
2. **There are paths.** Some of them sit exactly where this kit ships something. Some of them sit
   inside a plane this kit governs entirely. Neither was put there by the kit.

ADR-001's Part III put a foreign path on **HALTING** and recorded, explicitly, that the fifth
class was left undecided rather than settled unilaterally. That is the decision this ADR takes.

## Decision

### 1. `foreign` is NOT a fifth class. It is the DECLARED ABSENCE of a class, read at a moment.

A class in this kit is not a label. **A class is a write permission.** It is conferred in exactly
two ways, both of them declarations: a capability's `installs` entry states the class of the path
it writes, and a plane root states the class of everything the kit puts beneath it. ADR-002 §7a
settled the same identity from the other side — *a capability's `installs` IS its write
permission, so a path the new kit no longer declares is a path nothing gives it permission to
touch.*

A `foreign` class would therefore be a **write permission over bytes nobody declared**, granted
by no declaration — conferred instead by the *absence* of one, which means conferred by looking at
the tree. That is the precise inference this whole system exists to prevent, and this project has
paid for it twice.

It fails a second test just as hard. `path-class-total` is the gate that holds the four-class
seam: every file under a governed root must resolve to **exactly one** declared class. Add a fifth
class that means *no declaration explains this*, and every unexplained path resolves to it. The
gate can then never go red. An attribution that cannot fail certifies rather than measures.

So the four-class seam was never incomplete. **A foreign path simply HAS NO CLASS — and that is
the seam working, not a hole in it.** The question was mis-posed: `foreign` was named beside
`vendor | binding | projection | ephemeral` as though HALTING were a fifth column, when halting is
an *installation behaviour* and the blueprint's own words for it — *it does not get absorbed and
does not get overwritten: it HALTS with a list* — describe a **reading and a roster**, not a class.

### 2. Adoption is the SAME reconciliation, with S = ∅ — empty, not absent

An unadopted host has no record of what it received. There are two ways to say that, and they are
not the same statement:

- *the record is ABSENT* — nothing here can say what this host was given. This is `upgrade`'s
  situation, and it is refused.
- *the record is EMPTY* — this host was given **nothing**, and that is not a guess: it is true by
  construction of a host the kit has never installed into.

Adoption is the second. `S = ∅` is a **declared zero**, not an inferred one, and it makes adoption
the existing three-way reconciliation run with one reading known to be empty. `reconcile.survey`
is called unchanged, `stewardship.json` is unchanged, and **not one new cell is needed** — which
is the proof that the seam was right:

| what is on disk | what the kit ships | cell (already declared) | what happens |
|---|---|---|---|
| absent | ships it | `introduced` | create — the ordinary install |
| **present** | **ships it** | **`collision`** | **REFUSE** — the foreign path, halting |
| present in a governed plane | nothing ships it | `unaccounted` | **REFUSE** — the foreign path, halting |
| absent | nothing ships it | out-of-account | *no row* |
| present under a declared `space` root | — | out-of-account **by declaration** | *no row* |

`collision` and `unaccounted` were both already refusals, both already declared by stewards, both
already named with the path and the moment. Adoption did not need a new answer; it needed the
existing answer to be **reachable on a host that has never been installed into**.

### 3. The roster is PRODUCED BY THE MACHINE and never by judgement

Every row of the migration list exists because a **declaration** put it there:

- a `collision` row exists because some capability's `installs` states that the kit writes that
  exact path;
- an `unaccounted` row exists because a **plane root** states that the path is inside a plane this
  kit governs, and no install and no record explains it.

No filename is matched. No directory is guessed at. No heuristic decides that something *looks
like* a doctrine file. **A human decides what happens to each row; no human hand writes the
roster** — and no human hand can add a row to it either, which is the half of that requirement
that is easy to forget.

The roster is a **READING**, so it is re-taken and never edited. What a human does with a row is
not to *class* it — that would be a hand-written declaration, exactly what the requirement
forbids — but to do one of three things that change what a fresh reading measures:

- **move or remove** the path, and it stops colliding;
- **declare a capability** that legitimately ships it, and it becomes `introduced`;
- **disable** the capability that wants it, and the kit stops asking for that path.

Then adoption is run again and the reading says something different. A roster with no rows is the
statement *this host can be installed into*, and it is a counted zero like every other.

### 4. `adopt` READS and writes nothing; `init` at first contact REFUSES on the same reading

`adopt` is a non-mutating verb. It surveys and prints the roster, and it touches no byte — a verb
whose whole subject is *paths this kit has no permission to touch* may not begin by writing into
the host it is surveying.

That alone would make it advisory decoration, so the decision has a second half: **an `init` on a
host at FIRST CONTACT takes the same reading and refuses on it**, before a byte moves. Adoption
cannot be bypassed by simply running `init`, and the refusal is one decision computed once, in
the same module, printed the same way — the rule `upgrade` already follows.

**First contact is read from a DECLARATION, never from the shape of the tree.** A host is at first
contact when it has no answers file: the answers file is this host's own statement that it has
answered this kit, and its absence is that statement's absence. The kit does not decide *this tree
looks untouched*; it reads *this host has never answered*.

The refusal is **whole**, never partial. A host where three paths of forty collide is not
forty-minus-three adopted: it is refused entire, with all forty surveyed and all three named. A
partial adoption leaves a tree in a state no version describes.

### 5. The nested host — the refusal is CLOSED, the grammar is DECLARED open

The ledger records that *a host is assumed to be a whole repository, and nobody ever declared
that*, and that **nothing refuses a nested install**. Adoption is where that assumption first
becomes load-bearing: a real repository is exactly where a monorepo part with its own law is met.

**Closed here:** at first contact the kit measures its own boundary upward. If any ancestor
directory of `--root` holds a host declaration of this kit, the install is **refused by name**,
naming both roots. It is measured — the ancestor is looked for at the paths the *declarations*
state, never at a path constant held in an interpreter — and it is measured once, at the boundary,
before anything is trusted.

**Declared open — `GAP-NESTED-HOST-GRAMMAR`:** *what a nested host INHERITS and what it may
CONTRADICT* is not answered here, and refusing is not answering it. It is the same grammar
question as archetype ⊕ overlay, one level up, and it is a slice. What has changed is that the
silent case is gone: nesting is now a named refusal with a remedy, not two hosts each internally
right.

### 6. AMENDMENT, 2026-09-11 — whether an unaccounted path REFUSES is a property of its PLANE, declared as data

*Stated on record rather than adjusted in place, because a law is amended only by restatement
(Cardinal VI). What follows changes §1–§5 in exactly one respect and leaves the rest standing.*

**What was measured.** HOST #2 — `national-accounts`, the first tree this kit has ever met that it
did not create — refused. `init --plan` halted at exit 1 before a byte moved, over 82 paths: ONE
`collision` and EIGHTY-ONE `unaccounted`, and **every one of the eighty-one lay in the `ephemeral`
plane**: session receipts, probes, archives, a ledger. Precisely the droppings that a repository
which has ever been *run in* accumulates.

**The defect this exposed.** The surface said of each of them, in the kit's own words, *"The kit did
not put it here and will not take it away"* — and in the same breath demanded the path be moved or
removed before anything could proceed. Those two sentences cannot both be honoured. The `ephemeral`
class is DEFINED as observed state the kit never owns, never upgrades, and treats as safely
deletable; the kit even seeds `runtime/` into the host's `.agents/.gitignore` as its first act. So
the doctrine was already present and already correct — it simply had never been carried into the
halting rule, which was written over THE TREE when every other rule in this design is written over
A DECLARATION. One truth, two homes, and the second home was the one nobody could date (Cardinal
III). The consequence was not a cosmetic one: **it made every real repository unadoptable, for the
one class of path the kit explicitly disclaims.**

**Why it could only be found here.** Everything before this was proved on a clean tree, where the
ephemeral plane is empty and the rule is unfalsifiable. This is the entire reason Host #2 exists,
and it returned its finding on first contact.

**The decision.** An unaccounted path's verdict is **declared by the PLANE it lies in**, as data in
`MANIFEST.planes`, and never decided by the interpreter. `vendor`, `binding` and `projection`
declare that an unaccounted path REFUSES the whole operation, exactly as §4 states. `ephemeral`
declares that an unaccounted path is **REPORTED and never refuses** — it is counted, named and
printed, so the surface still states everything it found (Cardinal V); it simply is not an
obstacle, because nothing in a plane the kit disclaims can obstruct a write the kit was never going
to make. The refusal, where it applies, stays WHOLE: a single refusing path in a governed plane
still refuses the entire operation, in the plan, before a byte moves.

**Why declared and not derived.** The tempting derivation — *a plane no `installs` entry writes
into cannot obstruct* — is FALSE here and was measured false: `evaluation` and `observability` both
install with `class: ephemeral`. Worse, it would be action at a distance: one capability adding one
ephemeral seed would silently flip the halting behaviour of eighty-one unrelated paths, and nothing
on any surface would say why. A plane's stance toward what it does not account for is a property of
the plane, so it is stated where the plane is declared.

**The field already settled this.** Git refuses to overwrite an **untracked** file and proceeds
over an **ignored** one — not because ignored files are less real, but because the repository has
already DECLARED them outside its universe of discourse, and a thing outside the discourse cannot
be evidence within it. `rsync --exclude`, Terraform's `.terraform/`, Bazel's `bazel-out/` and
`node_modules` are all the same shape: a region the tool writes into freely, owns nothing in, and
never reasons about when deciding whether it may proceed. What every one of them makes explicit is
that the excluded region is DECLARED, never inferred from the shape of the tree.

**What this does NOT change.** `collision` still refuses everywhere, including in `ephemeral` — a
path some capability's `installs` names is a path the kit intends to WRITE, and the host holding
unaccounted bytes there is a genuine obstacle whatever plane it sits in. `adopt` still writes
nothing. `init` at first contact still refuses on the same reading. The roster is still produced by
the machine and never by judgement, and a row may still never be classed by hand.

**Consequence for HOST #2.** The refusal reduces from 82 paths to ONE: the `collision` at
`.agents/.gitignore`, where the host authored its own rules and the `governance` capability seeds
the plane rule. That is a real obstacle, correctly named, and it is cured by a declaration rather
than by a judgement.

## Rejected alternatives

**A. `foreign` as a fifth class in `MANIFEST.classes`, with a plane of its own.**
The literal reading of the open question, and the shape a reader expects. Rejected on two
independent grounds, either of which is fatal. First, a class is a *write permission* conferred by
a declaration, and this one would be conferred by the absence of a declaration — a class inferred
from the tree, which is the defect the estate exists to prevent, reintroduced one layer up.
Second, it would make `path-class-total` unfalsifiable: every unexplained path would resolve to
`foreign`, exactly one class, and the gate that holds the whole seam would pass forever. A gate
that cannot go red is not a gate, and a class that cannot be wrong is not a measurement. It also
needs a plane ROOT to be declared at, and foreign paths have no root — they are everywhere the
host is.

**B. `foreign` as a STATE a path occupies until a human classes it, recorded on an estate row.**
The most attractive alternative, and the closest to right — it keeps the decision, gives it a
name and a moment, and it is the shape ADR-002 used for `diverged-kept`. Rejected because the
estate records **what this host RECEIVED from the kit**, and a path the kit never gave it can have
no row there without the record beginning to state things that never happened. The record would
then carry two kinds of row that read identically and mean opposite things, and the next reader —
human or interpreter — could not tell them apart from where it stands. Worse, "a human classes
the path" is a hand-written declaration about provenance, which is precisely the roster-by-
judgement the owner's requirement forbids: the machine would produce the list and a human would
write the answer INTO the machine's own record. The three remedies in §3 achieve everything this
would, and each of them changes what a fresh reading MEASURES rather than what a human ASSERTED.

**C. Adopt by absorbing: take every existing path at a declared target as though the kit had
shipped it, and write the estate to say so.**
Cheap, one command, and it makes adoption of a real repository instant. It is also a lie written
into the one document whose entire job is to be true. The estate would state that the kit shipped
bytes it never shipped, and from the very next `upgrade` every reading built on it is a fiction
dressed as a measurement — a host edit reads as pristine, an upstream change reads as a conflict,
and nothing in the system can ever detect the contradiction because the record is internally
correct. This is ADR-002's rejected alternative A, arriving by a different road, and it is worse
here: there, S was recomputed and wrong; here, S is fabricated and signed.

**D. A separate adoption reconciler, with its own table for the S-is-empty case.**
The obvious shape: adoption is a different situation, so give it its own logic. Rejected for
exactly the reason ADR-002 rejected a second installer. The two reconcilers would hold the same
knowledge — which cell three readings fall in, what each steward says about it — and would be
correct together only for as long as somebody kept them in step. Synchronisation by discipline is
not a mechanism. Building it the other way proved the stronger point: with one reconciler, the
fact that adoption needed **zero new cells** became visible, and that is the evidence that the
four-class seam was complete all along.

**E. Ignore what the kit does not declare — adopt quietly and let `check` complain later.**
The path of least friction, and the one most tools take. Rejected because it inverts the order of
cause and consequence: the operator would see a gate failure about an unclassed path days after
the install that could not have avoided it, with no record of what was there beforehand. And it
would silently write into a tree whose contents nobody had accounted for, which is the one thing
a kit meeting an unknown repository must not do.

## Consequences

- `adopt` is a non-mutating verb: it takes a reading, prints the roster, and refuses with exit 1
  where any path stands foreign. A host with an empty roster is adoptable, and the zero is
  printed as a counted zero.
- `init` at first contact refuses on the same reading, so adoption is unbypassable.
- An already-installed host is not adopted and never re-adopted: it has answered, and its road
  forward is `upgrade` against its estate.
- A nested install is refused by name. `GAP-NESTED-HOST-GRAMMAR` is open and recorded.
- `foreign` is closed as a question: it is a reading, it appears in the roster, and it will never
  appear in `MANIFEST.classes`.
- **(2026-09-11)** An unaccounted path in the `ephemeral` plane is REPORTED and does not refuse;
  in `vendor`, `binding` and `projection` it refuses the whole operation. The stance is declared
  in `MANIFEST.planes`, so a new plane states its own and the interpreter learns nothing new.
