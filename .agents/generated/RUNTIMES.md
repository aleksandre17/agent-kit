# Runtimes — what this host runs its agents on, and what it has only been told

> **Generated. Do not edit.** Recomputed from the classes declared and the descriptors this host
> authored. Kit 0.1.6.

A runtime descriptor is a PROJECTION. The kit ships classes — what is true of a runtime as a
KIND, in no vendor's vocabulary — and this host authors descriptors, which say only what a host
legitimately says about its own tool. No file anywhere holds a second body for a runtime, and
that is not a rule anybody keeps: the descriptor schema is closed to the class's vocabulary, so
the two-homes state cannot be written down.

The second closure is the one that matters more here, and it is a closure by absence. **There is
no field in a descriptor in which a proof can be written.** The strongest thing any authored file
in this repository can say about a runtime is *we believe it can do this*. Whether it ever did is
answered by a record of something that happened, and the two can never be confused, because they
are not the same document and are not written by the same hand.

## This host's runtimes

**This host has declared no runtime.** Not "none found" and not an empty page: the roster is the
set of descriptors in the binding plane, and this host has authored none, so nothing is projected
into `.agents/generated/runtimes/`. That is a complete and honest answer, and it is written here
because a page that simply ended would read exactly like a page whose runtimes failed to render.

## The capability vocabulary — every word that may be claimed

Declared so that an absence can be counted. A capability that has no name cannot be missing from
anything: a runtime that never claimed it and a runtime that has no need of it are the same
silence until somebody declares the word.

Each is a QUESTION — what would have to be observed — and never an answer about any particular
tool.

- **command-shape** — Work is handed over as an argument vector, so a value carrying a space, a quote or a backslash arrives at the far side with the bytes it left with.
  - observed by: a run in which a value carrying a space, a quote and a backslash is handed over and read back unchanged, with the reading recorded where a later reader can find it. This is the one that has already been wrong: it was assumed, and it was believed for as long as nothing happened to carry a space.
- **working-directory** — Relative names resolve against a directory the caller chose, rather than one the runtime inherited from whoever started it.
  - observed by: a run that writes to a relative name, and a later reading that finds the file where the caller said it would be and nowhere else.
- **line-ending** — Text authored through this runtime is written with the line ending the caller declared rather than the one the platform prefers.
  - observed by: a byte-level reading of a file this runtime authored -- never a reading of what it displayed, which is the same file after a second translation.
- **write-scope** — The runtime can be confined to a stated part of the workspace, and a write outside it is refused rather than performed and reported.
  - observed by: a run that attempts a write outside the stated scope, is refused, and leaves the refusal on record; a run that was simply never asked proves nothing.
- **delegation** — A run can start another run and receive its result, rather than only describing what another run should do.
  - observed by: a record naming the run that was started, and the started run's own record existing beside it.
- **interruption** — A run that is cut off mid-way is distinguishable afterwards from a run that finished, without anyone having to remember which it was.
  - observed by: a run stopped mid-way, followed by a reading that finds a record which opened and never declared an end.
- **refusal** — The runtime can decline an instruction and state why, rather than failing quietly or answering anyway.
  - observed by: a run handed something it must decline, and a record carrying both the declining and the reason it gave.

## Classes — the ones taken up, and a count of the ones that were not

**No class has been taken up by this host.**

**3 declared runtime class(es) are not used here.** Available, and this host runs none of
them.

They are not named on this page, deliberately. Which tools a host runs is the host's choice, and
a framework that printed a list of kinds into a host that has chosen none of them would have
taken a side in that choice before meeting it. The names are one file away, in the declarations
that legitimately hold them: the kit's own class registry, and this host's
`.agents/project/runtime-classes.json`. A count is a declared zero and a pointer; a roster is a
decision nobody made.
