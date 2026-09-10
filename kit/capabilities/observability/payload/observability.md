# Observation — the life of a run

> VENDOR. Shipped with the kit, replaced wholesale on upgrade. Nothing here is yours to edit;
> what is yours is the declaration in the binding plane beside it.

## The one sentence

**A receipt proves that a run fired. It never proves that the run hit.**

Observation has two halves and they answer different questions. *Life* asks: did it run, did it
finish, did it leave a trace. *Quality* asks: was it any good. Only the first is the kit's business.
The second is about this host's own subject matter — it is judged against cases and standards a host
declares, and a host that has declared none legitimately starts with no measure at all. The kit
ships the grammar of that judgement and never the verdict.

## State it before you can lose it

A receipt is written the moment a run begins, holding a status that means *nothing has been
concluded yet*, and rewritten exactly once when the run reports its end.

The order is not a detail; it is the entire guarantee. A record written only at the end says nothing
about a run that never reached the end — and a run that dies mid-way is precisely the case that
needs recording, because everything it left on disk reads exactly like the output of a run that
finished. Half-built state is not partial success. It is unverified state, and without a receipt
nothing on the disk can tell you which one you are looking at.

So a process that is killed leaves its record holding the unset status forever. That is the record
working, not failing.

## What is recorded, and in whose words

Where the field already has a word, the receipt uses it: a run carries a name, a status of unset, ok
or error, and a message when it ended badly. That vocabulary is not this kit's invention and is not
re-invented here. Two places where this kit's own contract wins are stated in the schema rather than
left to be discovered: the identity of a record is `id`, because that is what a member of a
collection is identified by everywhere in this kit; and moments are stated the way the clock port
states them.

A collector is not built, not shipped, and not implied. A receipt is a JSON record in the ephemeral
plane, which is never committed and is always safe to delete once you have read it.

## What is not recorded

- **Anything about a run that had nowhere to write.** Observation is declared by a capability, and a
  capability is only enabled once this host has answered which capabilities it wants. A run against a
  host that has not answered yet leaves no receipt — there is no declaration under which one could be
  written, and the kit would be writing into a host that has approved nothing.
- **Runs that write nothing.** A run that cannot change the host cannot leave it half-built, so the
  record would measure only itself. A plan is the same case: it promises to touch no byte, and a
  receipt would be a byte.
- **A verdict.** A status of ok records that the run reported success. Nothing more.

## Reading the record

The gate over these records is a sensor and never a broom. It names a run whose record says
something is wrong, says how to read it, and removes nothing — a run's record is evidence, and
evidence is not swept up by the thing being questioned. Clearing one is a human act.

Which readings exist is a declaration: the kit ships its own, this host may add more of its own in
the binding plane, and neither the gate nor any other machinery in the kit knows a single one of
them by name.
