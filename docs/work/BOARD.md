# Delivery board

> **PROJECTION — do not edit.** Every column below is computed from the cards in
> `docs/work/cards/` and the lifecycle those cards move through. Delete this file
> and run `render`: it comes back byte-identical. Edit it and run `check`: the edit is caught,
> because a projection that survives editing has become a second home for a state.
>
> The two numbers on each card are COMPUTED here and now, by resolving the reference each
> criterion names: how many were proved, out of how many the card declares. Nothing is ticked and
> nothing is typed. A card that declares no criterion reads `0/0`, which is the honest state of
> work nobody has shaped yet, and a criterion whose reference could not be read at all is not
> among the proved -- it is not claimed in either direction.

kit 0.4.1

## Intake — 0 card(s), limit -

*owner: anyone* — A request as it arrived, in the words it arrived in. Nothing is promised here.

_empty_

## Shaped — 0 card(s), limit -

*owner: shaper* — The problem, the appetite and the exit criterion are written down. This is the state a folder of proposals is really in -- and a state has an owner, an age and an exit.

_empty_

## Bet — 0 card(s), limit -

*owner: owner* — The owner has accepted this work. Nothing reaches this column without a human passing the door.

_empty_

## In flight — 0 card(s), limit -

*owner: doer* — Being built right now, inside the capacity this host declared.

_empty_

## Verified — 0 card(s), limit -

*owner: verifier* — Evidence exists that the exit criterion is met. A claim of green is not green.

_empty_

## Landed — 0 card(s), limit -

*owner: doer* — In the trunk, reachable by everyone.

_empty_

## Learned — 0 card(s), limit -

*owner: owner* — What this taught is recorded where it will be read, or it was not learned.

_empty_

## Parked — 0 card(s), limit -

*owner: owner* — Deliberately not now, said out loud. An honest declared state, never a silent drawer.

_empty_

## Blocked — 0 card(s), limit -

*owner: doer* — Waiting on something outside this board, named.

_empty_

## The transitions, as declared

- `intake` → `shaped` · owner **shaper**
  - exit: the card states a problem, an appetite and the criterion that will end it
- `shaped` → `bet` · owner **owner** · DOOR: only the owner may open it
  - exit: the owner has accepted this work into the cycle -- no machine may make this move
- `shaped` → `in-flight` · owner **doer** · only when `class` = `standard`
  - exit: a pre-approved standard change that was written as a card anyway: its class computed, not claimed (ADR-025) -- a standard change needs no card at all, its commit is its record
- `shaped` → `in-flight` · owner **doer** · only when `class` = `normal`
  - exit: a normal change (ADR-025): costly to undo but not irreversible, so it is assessed by its criteria and its owner's peers rather than bet by the owner -- the owner's door stands where consequence is irreversible
- `bet` → `in-flight` · owner **doer**
  - exit: the work has started and the host had a free slot for it
- `in-flight` → `verified` · owner **verifier**
  - exit: evidence, not testimony: every criterion the card declares resolved to a proof that held, and the machine refuses the passage until they do
- `verified` → `landed` · owner **doer**
  - exit: the change is in the trunk and reachable by everyone -- and so is everything decomposed out of it: every card hanging under this one, at any depth, has every criterion it declares resolved to a proof that held. A card that was broken into parts is read from its parts, so nothing lands by saying so while a piece of it is still open
- `landed` → `learned` · owner **owner**
  - exit: what it taught is recorded where it will be read
- `shaped` → `parked` · owner **owner**
  - exit: the owner has said not now, out loud, with a reason
- `in-flight` → `parked` · owner **owner**
  - exit: work stopped on purpose, and the board says so rather than showing it as active
- `parked` → `shaped` · owner **shaper**
  - exit: the card is shaped again against what has changed since it was parked
- `in-flight` → `blocked` · owner **doer**
  - exit: the thing being waited on is named on the card
- `blocked` → `in-flight` · owner **doer**
  - exit: what blocked it is gone, and the card says what it was
