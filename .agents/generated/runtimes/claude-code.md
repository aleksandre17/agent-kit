# claude-code

> **Generated. Do not edit.** This descriptor is composed from a runtime class and this host's
> own declaration, and it is rebuilt from scratch on every render. An edit here is a change the
> next render discards without asking.
> Class: `an-interactive-session` · kit 0.4.2

## Reach — how an agent gets to this runtime at all

An operator and the agent take turns inside a session that stays open between them, so work arrives as a turn and everything the run knows accumulates in the session rather than in the request.

## The boundary — the translation that sits in the gap

The session inherits a working directory, an environment, a locale and a line-ending convention from whoever opened it, and a turn states none of them. Every one of those is a name both sides will read confidently and may resolve differently, and the failure arrives as a thing that is simply not where it was put.

## Reference class — what this kind of boundary is measured against

- the Language Server Protocol's initialize handshake, which states the root once and assumes it never again
- POSIX process environment inheritance, where what a child gets is what the parent happened to hold
- terminal encoding negotiation, where both ends agree on a name and not on a byte

## Capabilities — claimed, proven, absent

Every capability any vocabulary declares is placed below, in exactly one of three groups. None is
omitted, and that is the whole mechanism: a list of what a runtime can do reads identically to a
list of what somebody once believed it could do, and both read identically to a short list
belonging to a tool that genuinely needs nothing.

### Proven — 0 of 7

Nothing has been observed of this runtime. The records that would say otherwise are read from
`runtime_observations`, and none of them names this runtime and a declared capability. That is a
measurement with an instrument behind it, and it says: nothing, yet.

### Claimed — 0 of 7

Testimony. This host believes each of these; nothing here has been observed.

This host claims nothing of this runtime. Every declared capability is therefore absent below,
and that is a complete answer rather than an empty one.

### Absent — 7 of 7

Declared, and not claimed. Named rather than omitted: a runtime that was never asked about
something and a runtime that cannot do it are the same silence, and only one of them is a
decision anyone made.

- **command-shape** — Work is handed over as an argument vector, so a value carrying a space, a quote or a backslash arrives at the far side with the bytes it left with.
- **working-directory** — Relative names resolve against a directory the caller chose, rather than one the runtime inherited from whoever started it.
- **line-ending** — Text authored through this runtime is written with the line ending the caller declared rather than the one the platform prefers.
- **write-scope** — The runtime can be confined to a stated part of the workspace, and a write outside it is refused rather than performed and reported.
- **delegation** — A run can start another run and receive its result, rather than only describing what another run should do.
- **interruption** — A run that is cut off mid-way is distinguishable afterwards from a run that finished, without anyone having to remember which it was.
- **refusal** — The runtime can decline an instruction and state why, rather than failing quietly or answering anyway.

## Binding protocol

Declared once, for every runtime, and rendered into each. Not a link and not a reference: a
reference can be left unfollowed.

- **a-claim-is-not-a-proof** — Everything a descriptor says about this runtime is a stated belief with an author. It is written as CLAIMED and it stays CLAIMED until a record of something that actually happened says otherwise -- and no document a host can author is such a record.
- **an-absence-has-a-name** — A capability this runtime does not claim is ABSENT, and it is named. A short list of claims and a runtime that genuinely needs nothing read identically to anyone who is only shown what is present.
- **a-setting-is-not-a-capability** — What this host CONFIGURED is not what the runtime DOES. A setting is carried as a setting, however confidently it was written: the one that cost most was an invocation shape recorded once and never measured.
- **the-boundary-is-measured-before-it-is-trusted** — Two components can agree perfectly on a NAME and disagree completely on what it points at, and when they do each behaves correctly while the work lands somewhere nobody chose. The translation in the gap -- paths, quoting, encodings, clocks, line endings -- is measured once at the boundary, cheaply, and never inferred from the fact that a name looked familiar.
- **when-a-run-is-cut-off-the-record-is-what-remains** — A run that dies mid-way leaves work that reads exactly like finished work. Whatever this runtime is asked to do, the record that it STARTED is written before the work, so that its silence is legible as a death rather than as a success nobody checked.

## This host's instance

Everything above the settings is true of the runtime as a kind, or is a belief this host has
stated as one. Everything below is what THIS repository configured, and nothing else may be said
here.

### Settings

What this host's tooling was TOLD. Never what the runtime does: the setting that cost most was an
invocation shape written down once, believed, and never measured.

This host declares no settings for this runtime.

### Used for

No part of this repository is declared as this runtime's. A declared state and not an oversight:
the descriptor is where a scope would be written.

### Appendix

This host adds nothing beyond what is declared above.
