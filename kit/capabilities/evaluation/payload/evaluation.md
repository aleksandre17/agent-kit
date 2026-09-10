# Evaluation — the grammar of judgement, and none of the judgement

> VENDOR. This file belongs to the kit. Edit it and an upgrade overwrites you; what is yours is
> the declaration in `.agents/project/evaluation/`.

A run's receipt proves that it **fired**. This capability is the other half — whether it **hit** —
and that question is not the framework's to answer. A good answer is a property of a domain, and
this framework has never met a domain. So it ships the **grammar**:

- the shape of a **rubric** — a question, broken into the criteria it is asked through;
- the shape of a **case** — a thing to be judged, naming the rubrics it must be judged against;
- the shape of a **judge** — who or what may put a verdict on a case, and why this host trusts it;
- the **verb** that evaluates, which opens a judgement for every pair that needs one;
- the **schema of a quality receipt** — one case, read against one rubric, by one judge, at a moment;
- the **vocabulary of a verdict** — `UNJUDGED · PASS · FAIL · INCONCLUSIVE`.

And it ships none of the content: no case, no criterion, no rubric, no threshold, no scale, no
default eval set. Not because they are hard, but because the only ones the framework could write
would be an opinion about a subject somebody else owns, arriving in a file written once and owned
by the host forever after — wrong in the way only someone who knows the domain would ever notice.

## The zero measure

A new host has declared no rubric, no case and no judge. That is a **ZERO MEASURE** — not a good
score, not a bad one, no measure at all — and every surface here is required to say so in those
words. An evaluation page that shows nothing because nothing was declared is indistinguishable
from one showing that everything is fine, and *that* is the exact lie this project exists to
prevent.

So the blank is **materialised**, never implied. `evaluate` opens a judgement for every pair of a
case and a rubric that has none, holding `verdict: UNJUDGED`. An absence cannot be counted; a blank
can. `never judged` becomes a record with a date on it, which is the only form in which anyone ever
chases one.

The order is the same as a run receipt's, and for the same reason: the record is written before the
judging, so that a judging which never happens is still visible afterwards.

## What is yours

- `.agents/project/evaluation/evaluation.json` — your rubrics, your cases, your roster of judges.
  Seeded empty. The first row is authored by whoever will live with it.
- `.agents/project/evaluation/readings.json` — your own dispositions over judgements: ways of
  reading a judgement that mean the record is not evidence. Seeded empty; the kit's own readings
  still hold.

## Who judges the judge

Nothing here measures a judge. `llm-rubric` and `llm-pairwise` are themselves declarations, and a
judge's agreement with a human sample — the one thing that would make its verdicts evidence rather
than testimony — is not measured anywhere in this kit. A judgement is therefore trusted exactly as
far as the host trusts its judge, and no further. That limit is stated here, and on the projection,
rather than left to be discovered: an unmeasured judge is not a defect, but an unmeasured judge
that reads as measured is.

## What is enforced, and what is not

The kit's readings ask one thing of a judgement: **can it be questioned?** A verdict that cannot say
who reached it, or when, is named. Whether a verdict was *deserved* is never read — that is the
domain, and the moment the kit had an opinion about it, it would have shipped a verdict.

There is no threshold and no tolerance field. A threshold would be a number; the number at which
observing becomes enforcing has never been declared anywhere in this framework, and a field nobody
filled in would read as enforced. The first crossing is a finding.

Nothing is ever removed. A judgement is evidence, and evidence is not swept up by the thing being
questioned.
