# Delivery — the lifecycle is a declaration, the board is a projection

**Kind: VENDOR.** Replaced wholesale on every install. Nothing you write here survives.

## Why this capability exists

It was not designed from a theory. It was measured. In the repository that commissioned it,
`proposals/` held **121 files** and `decisions/` held **74** — more proposed than decided, for
months. The diagnosis is the whole design:

> **A folder can never force a decision; a column can.**

A proposal is not a document genre. It is a card in the **shaped** state — and a state has an
owner, an age and an exit criterion, all three of which a folder lacks.

The second measurement was a skipped step: work that was shaped went straight into flight
because someone was asked to build instead of to decide. Nothing was broken, and that is the
point — **you cannot violate a transition that was never declared.** So the transitions are
declared, in `lifecycle.json`, as data.

## The four rules the machinery holds

1. **A card carries exactly one state, and its state lives in exactly one place** — the `state`
   field of the card. The board is derived from it. Two files claiming one card id are refused
   by name; a state the lifecycle does not declare is refused rather than quietly dropped from
   the board, because a column that silently loses a card is a surface that lies.
2. **`shaped → bet` is the owner's door and no machine may open it.** It is the same mechanism
   as an install approval: a machine drafts, a human accepts, and the acceptance is recorded
   with a name and a moment. Attempting the move without walking the door exits with the code
   that means *waiting for a human*, not the code that means *broken*.
3. **Capacity and staleness are the host's declarations**, in `.agents/project/delivery/policy.json`.
   The interpreter holds no number. A second card entering a full state is refused; a card that
   has sat too long in one fails a gate rather than being moved by a machine that no one named.
4. **Work is weighed before it is walked** (ADR-025). The host declares its areas -- paths and the
   cost of undoing a change to them -- in `.agents/project/delivery/areas.json`; `weigh` computes a
   change's class from the areas it touches. A `standard` change (reversible, inside the host's
   breadth) leaves only its commit; a `normal` one a card and its criteria; a `major` one a decision,
   an appetite and a review as well; a `program` a plan of cards. The computed class is a floor: a
   change may be declared heavier, never lighter, so low-risk work is light by computation and heavy
   work cannot pass as light. The floor of edit gates, tests and `check` holds for every class.

## Working with it

```
# author a card (it is data -- the kit interprets cards, it does not own your text)
docs/work/cards/<id>.json

# move it, and the move is recorded with who and when
kit move --root . --card <id> --to shaped --by <who>

# the owner's door
kit move --root . --card <id> --to bet --approve <who>

# how heavy is this change? (staged and untracked, a range, or paths not yet touched)
kit weigh --root . [--base <rev> --head <rev> | --path a,b] [--class <declared>]

# the board is never edited; it is rendered
kit render --root .
kit check  --root .
```
