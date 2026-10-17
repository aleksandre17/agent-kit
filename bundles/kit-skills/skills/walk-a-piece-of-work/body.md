# Walk a piece of work

The kit computes how heavy a change is; you judge only what it cannot compute. Run every verb below
through this skill's `scripts/kit.py <verb> ...` from the host root.

0. **A question, an explanation, a read changes nothing: answer it.** Open no card, weigh nothing.
1. **Before the first edit, weigh what you will touch:** `kit.py weigh --path <paths>`. Read its
   class, `requires`, doors, `feeds` (who moves with the change) and lessons. Do not re-derive them.
2. **Leave exactly what the class requires, nothing more:**
   - `standard` -- change, run the host's test command, commit. No card.
   - `normal` -- a card in `docs/work/cards/` with criteria, each with the proof that decides it
     (`needs: tested` or `review` where the claim must be one); move it to `in-flight`; every commit
     carries `Card: <id>`.
   - `major` -- as `normal`, plus `origin` pointing at a decision (an ADR with `kind: decision`: the
     question, the alternatives and why they lost), an `appetite`, and a criterion that `needs: review`.
     The owner bets it (`move --to bet --approve`) before any commit; the ruling is theirs -- walk-a-door.
   - An area may owe more than its class (a review where identity lives): `weigh` lists it; the card holds it.
   - `program` -- the parts as child cards (`parent`) in order (`after`); each part walks its own
     class.
3. **Judge what is not computed, and say it honestly:** the card's `uncertainty` (clear, complicated,
   complex, chaotic) -- it can only raise the class; the criteria and their proofs; the alternatives.
   A proof is independent of the card: never a gate that reads cards or the board (`FF-WORK-*`,
   `FF-DELIVERY-*`, `FF-KIT-PROJECTION`) -- that is the card vouching for itself.
4. **While working, keep weighing:** run `kit.py weigh` when the change grows. A finding outside the
   card is `kit.py capture --card <id> --title "<what>" --from <card> --by <you>` -- then return to the
   work. Never do it on the side.
5. **A lesson `weigh` shows applies now.** Follow it, or say in the card why it does not.
6. **Done is computed:** `kit.py move --card <id> --to verified --by <you>` passes only when every
   criterion holds at the evidence it needs. A test not run is reported as not run.

Never yours to do: lower a card's class, declare `Work-Class: emergency` (a person declares it; a card
is never shaped `emergency`), or approve a door -- where the host declares `owner_signing`, a door
holds only in a commit the owner signs, so a mark you write opens nothing; never run `signer --setup`. Write trailers exactly `Card: <id>` in the last
paragraph, beside the other trailers. Report what you found and wait for the owner.
