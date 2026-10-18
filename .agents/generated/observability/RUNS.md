# Runs — what a run leaves behind, and how its record is read

> PROJECTION. Do not edit: delete this whole plane and run `render`, and it comes back byte-identical.
> Kit version 0.4.0 · project status accepted.

**No run is listed on this page, and that is deliberate.** A receipt changes after it is written —
it begins holding a status that means *nothing has been concluded yet*, and is closed once when the
run reports its end. A page that listed runs would therefore be stale in the instant it was correct,
and this plane is rebuilt only when `render` is asked to rebuild it. The live reading of the runs
this host holds is `check`, which takes it at the moment you ask and says so.

What is on this page is the GRAMMAR: what a receipt is for, and every way a run's record can be
read as saying that something went wrong.

## What a receipt claims

A receipt claims that a run **fired**. It never claims that the run **hit**. Whether the work was
any good is a question about this host's own subject matter, answered by cases and standards this
host owns, and nothing in the kit has an opinion about it.

The order is the whole mechanism. The record is written **before** the work, holding an unset
status, and rewritten **once** when the run declares its end. A record written only at the end
would prove nothing about the runs that matter most — the ones that never reach an end.

## The one record a reading may not treat as a corpse

A run cannot judge its own liveness. While `check` runs, the run that started it is holding an
open record of its own — legitimately unclosed, because it has not finished — and a reading that
could not tell that from a run that died would report every healthy run as one.

That is not an exemption hidden in the machinery. The reading of a record carries one field no
record can hold, `in_flight`, which is true only of the run doing the reading, and the kit's own
disposition below NAMES it. A host may declare a reading that does not exclude it. The exclusion
is data, it is on this page, and it is yours to tighten.

## Enforcement, and the number that has never been declared

This gate names a crossing the **first** time it sees one. It does not observe for a while and
enforce later, because the threshold at which observing becomes enforcing must be a number and no
number has ever been declared anywhere in this framework. Rather than hold an unread field that
would read as enforced, this capability declares none and states the absence here: **there is no
observe-then-enforce period; the first crossing is a finding.**

Nothing here is ever removed by the kit. A disposition NAMES a run's record and says how to read
it; removing evidence is a human act, recorded as such.

## Declared by the kit

### a-run-that-never-declared-its-end

- because the run opened this record, wrote that it had begun, and was gone before it could write what became of it. Its work is therefore UNVERIFIED STATE and not partial success -- whatever it left behind reads exactly like the output of a run that finished, and nothing on disk can tell the two apart except this receipt.
- instead read what the run touched, decide whether that half is sound, and remove this record by hand once you have. Nothing removes it for you: a run's record is evidence, and evidence is not swept up by the thing being questioned.
- calibrated on the receipt it must match, `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa1`, and the lookalike it must tolerate, `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa2`

### a-run-that-claims-an-end-it-never-dated

- because the record says the run finished well and cannot say when. A reading that carries no moment cannot be contradicted, only believed -- so this one will go on certifying a success nobody can place in time, and it will do it most convincingly the longer it sits there.
- instead written by a closing that states its moment in the same act as its status. If this receipt came from outside this kit, the writer is the defect and this record is the symptom.
- calibrated on the receipt it must match, `bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb1`, and the lookalike it must tolerate, `bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb2`

### a-failure-that-cannot-be-placed-in-time

- because a failure with no moment is worse than an unrecorded one. It is read as current by every reader who finds it, for as long as it sits there, and the run it belongs to may have been fixed the same afternoon -- so the surface reports a fault the host no longer has, which is the same lie as reporting none it does.
- instead written by a closing that states its moment in the same act as its status, so that a failure can be dated, compared and eventually left behind.
- calibrated on the receipt it must match, `ccccccccccccccccccccccccccccccc1`, and the lookalike it must tolerate, `ccccccccccccccccccccccccccccccc2`

## Declared by this host

_This host has declared no dispositions of its own. That is a state, not a gap: the kit's readings
still hold, and a host adds one by declaring it._
