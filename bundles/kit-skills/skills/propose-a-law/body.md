# Propose a law

A law is a sentence every agent and every commit is held to. Judgement is needed in exactly two places:
whether the rule is true of this repository everywhere, and how its violation shows in text.

1. Write the law as one numbered sentence in `.agents/project/doctrine/laws.md`, ending with where it is
   enforced. Keep it short: the law page is loaded on every turn.
2. Where a violation shows in text, run this skill's `scripts/gate.py <id>` and fill the
   printed gate (`paths`, `forbids`, `because`, `instead`, `proves`, `admits`) into
   `.agents/project/enforcement/edit-gates.json`. `proves` must be refused and `admits` admitted.
3. Run the kit's `render` and `check`. A gate that `check` reports uncalibrated is not done.
