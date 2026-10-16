# Propose a law

A law is a sentence every agent and every commit is held to. Judgement is needed in exactly two places:
whether the rule is true of this repository everywhere, and how its violation shows in text.

1. Write the law as one rule in `.agents/project/doctrine/norms.json` carrying `law: <n>` (the next number),
   its `title`, what it `says`, its `enforced_by` and, if useful, an `enforcement_note`; give it its
   `derives_from`, `modality` and `subject`. Keep it short: the rendered law list is loaded on every turn.
2. Where a violation shows in text, run this skill's `scripts/gate.py <id>` and fill the
   printed gate (`paths`, `forbids`, `because`, `instead`, `proves`, `admits`) into
   `.agents/project/enforcement/edit-gates.json`. `proves` must be refused and `admits` admitted.
3. Run the kit's `render` and `check`. A gate that `check` reports uncalibrated is not done.
