# Walk a piece of work

The kit computes how heavy a change is; you judge only what it cannot compute. Run every verb below
through this skill's `scripts/kit.py <verb> ...` from the host root.

0. **A question, an explanation, a read changes nothing: answer it.** Open no card, weigh nothing.
1. **Before the first edit, weigh what you will touch:** `kit.py weigh --path <paths>`. Read its
   class, `requires`, doors, `feeds` (who moves with the change) and lessons. Do not re-derive them.
   Not sure which paths yet? Read until you are, then weigh those -- never a guessed one.
2. **Leave exactly what the class requires, nothing more:**
   - `standard` -- change, run the host's test command (the briefing's Commands), commit. No card.
     None declared: say "no test command declared -- not run".
   - `normal` -- a card with criteria, each with the proof that decides it; move it to `in-flight`;
     every commit carries `Card: <id>`.
   - `major` -- as `normal`, plus `origin` pointing at a decision (an ADR under `docs/decisions/`, front
     matter `kind: decision`, left `status: proposed`: the question, the alternatives and why they lost),
     an `appetite`, and a criterion that `needs: review`. The owner bets it (`move --to bet --approve`)
     and rules on the ADR before any commit of the work -- walk-a-door.
   - **Opening the card:** `kit.py capture --card <id> --title "<what>" --by <you>`, then add to its
     JSON only what the class requires -- for `normal` the first two fields, for `major` all four:

     ```json
     "class": "major",
     "criteria": [{"id": "green", "statement": "the suite passes", "needs": "tested",
                   "proof": {"kind": "test-report-passed", "ref": "<the JUnit or TRX report>"}},
                  {"id": "reviewed", "statement": "a peer approved it", "needs": "review",
                   "proof": {"kind": "review-approved", "ref": "docs/work/evidence/<id>/review.json"}}],
     "origin": {"kind": "artifact-present", "ref": "docs/decisions/ADR-<n>-<slug>.md"},
     "appetite": {"amount": 2, "unit": "day"}
     ```
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
6. **Proof follows the change** (Cardinal IX): run the tests of what you touched; `prove` (the
   pre-push) selects them from the areas and runs everything only where the change's weight asks.
   Never run a whole suite by hand for a standard change, and never re-run a green proof on the same
   bytes.
7. **Done is computed:** `kit.py move --card <id> --to verified --by <you>` passes only when every
   criterion holds at the evidence it needs. A test not run is reported as not run. Read the host's
   state with `kit.py check --brief` (what fails, and the summary) -- the full listing is for people.

Never yours to do: lower a card's class, declare `Work-Class: emergency` (a person declares it; a card
is never shaped `emergency`), or approve a door -- where the host declares `owner_signing`, a door
holds only in a commit the owner signs, so a mark you write opens nothing; never run `signer --setup`. Write trailers exactly `Card: <id>` in the last
paragraph, beside the other trailers. Report what you found and wait for the owner.
