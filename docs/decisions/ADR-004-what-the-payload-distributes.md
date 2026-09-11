# ADR-004 — What the payload distributes: the carrier, the grammar, and no cardinal

- **Status**: Accepted
- **Date**: 2026-09-11
- **Amends**: ADR-001 (the framework blueprint), by settling for *doctrine* the same boundary ④
  settled for *judgement*; ADR-002 and ADR-003 are unaffected and are relied on, not changed.
- **Rules on**: both proposals' `kit/doctrine/` — `CARDINALS.md`, `protocol.md`, the economy and
  risk chapters, the environment chapters under `when:`, `capabilities-lib/` skills, `playbooks/`.
  Declared there as the payload's reason to exist; shipped by the kit at HEAD in no form at all.
  No ADR had ever ruled them in or out. This one does.

## The situation

The gap is not *a missing folder*. It is that the framework has never said **what kind of thing a
sentence of doctrine is** — and until it says so, every future answer is available: doctrine as
kit-owned truth, doctrine as a seed the host copies and owns, doctrine as a privileged plane with
its own loader. Each of those is a different framework. The folder was absent because the identity
was undecided, and building the folder first would have decided it by accident.

One precedent inside this system already answers the same question in an adjacent subject. Slice
L7-quality (ADR-001 ④) decided that **the kit ships the grammar of judgement and no case, rubric,
threshold or scale** — `evaluate` on a blank host prints *THE MEASURE IS ZERO*. A receipt proves it
fired, never that it hit. Doctrine is judgement with the verb removed: a cardinal is a standing
verdict about conduct. Anything decided here that is not consistent with ④ would have to overturn
it. Nothing here overturns it.

## What the field does with the same question

Every mature system of this class has answered *where does normative content live relative to the
engine that enforces it*, and they converge:

- **ESLint** — the engine ships zero enabled rules; `eslint-config-*` is an independently
  versioned package the consumer chooses, extends and overrides. The engine never has an opinion
  it did not receive.
- **OPA / Rego** — *policy is data*: signed, revisioned bundles distributed apart from the engine.
  The engine holds no policy whatsoever, which is exactly why it can be trusted with everyone's.
- **Semgrep** — engine versus registry rulesets (`p/…`), separate lifecycles, separate versions.
- **Terraform** — provider (mechanism), module (composition), Sentinel policy (norm): three
  artifacts, three release cadences, on purpose.
- **Kubernetes + Gatekeeper** — `CustomResourceDefinition` and `ConstraintTemplate` are the
  *grammar*; the `Constraint` is the cluster's own instance. The platform ships the shape of a
  rule and none of the rules.
- **Rust** — clippy lints travel *with* the toolchain because their meaning is the toolchain's;
  **editions** are opt-in, declared per crate, and an old edition stays legible forever.
- **cookiecutter / Yeoman / Backstage templates** — the counter-example: a one-shot imprint with
  no upstream. After generation the norm has as many divergent homes as there are projects, and
  nobody can ever speak about it again.

The convergent reading: **the engine ships the CARRIER and the GRAMMAR; the norm arrives as
separately versioned, host-chosen DATA — except where the norm is the meaning of the engine's own
mechanism, in which case it is version-locked to it.** That exception is the clippy/Rust half, and
it is the part a naive "mechanisms only" reading loses.

## Decision

### ① There are exactly two genres of normative text, told apart by one measure

The measure is ADR-001's T2 blank test, turned on a sentence:

> **Can this sentence become false without the kit changing?**

- **No** — it can only become false if a mechanism *this kit ships* changed. Then it is
  **MECHANISM DOCTRINE**: the meaning of a thing the kit owns. Its home is beside the mechanism,
  version-locked to it, and separating them would create a truth with two release cadences, which
  is a copy with extra steps.
- **Yes** — it is a claim about the host's conduct, and only the host can notice it is wrong. Then
  it is **CONDUCT DOCTRINE** — cardinals, protocol, economy, risk, environment chapters,
  playbooks, skills. **The kit ships none of it.** It ships the carrier by which a host receives
  some, the grammar by which the host answers it, and the surface that states which it has.

This is ④ restated exactly: the grammar, never the verdict. A cardinal is a verdict.

### ② Mechanism doctrine is VENDOR, carried by the capability whose mechanism it explains

Already true in the tree and hereby declared: each capability vendors one `<id>.md` to
`.agents/kit/doctrine/<id>.md`. Vendor is the right class and the only right one — replaced
wholesale, never merged, editable upstream or not at all — because the page and the mechanism are
one truth. This is the ONLY normative text the framework itself distributes, and it is bounded by
construction: a capability may explain what it ships and may not say a word about how a host
should work. The bound is testable by T1/T2 and belongs in the `fitness` slice.

### ③ Conduct doctrine arrives as a DOCTRINE BUNDLE — an ordinary capability, nothing privileged

A doctrine bundle is a capability. It has an id, a semver, `requires`, `provides: ["doctrine"]`,
`installs` and `gates`, and it is resolved by the same resolver as everything else. It may be
published by this framework's authors, by a company, or by one team for itself; the kit's own
repository ships **no** bundle, so that the carrier is proven on a host that declared none.

There is no `doctrine/` plane with its own loader, no `when:` engine, and no second installation
grammar. `installs` is the write permission (ADR-002 §7a, ADR-003 §1) and doctrine gets no
exemption from it. An environment chapter that the proposals wanted gated by `when:` is instead a
`requires` on a profile fact — the mechanism that already exists for exactly that, and the one
that keeps the condition in the *declaration* rather than in the interpreter (Cardinal IV).

Classes, per artifact:

| artifact | class | why |
|---|---|---|
| a distributed cardinal / chapter / playbook / skill | **vendor** (of its bundle) | it has ONE home, upstream; replaced wholesale; the host never edits it, so it can never fork |
| the host's own law page and its stances | **binding** (seed-once, `seeds/laws.md`) | it is the host's authorship; no upgrade may read it for writing |
| the roll of doctrine in force, cardinal-by-cardinal with each stance | **projection** | deleted and re-rendered; it is a reading of the two above, never a third copy |
| a bundle fetched but not installed | **ephemeral** | observed, never owned |

A distributed cardinal is **never binding class**. Binding means *host-owned after first write* —
which is precisely a fork, taken silently.

### ④ A host amends without forking, by DECLARING A STANCE

A host never edits a vendored cardinal. In its own binding law page it declares, per cardinal it
has something to say about, a row naming `bundle@version#cardinal-id` and one member of a stance
vocabulary — *adopts · narrows (with the narrowing) · extends (with the extension) · declares a
gap · refuses (with the reason)*. The vocabulary is itself a declared document, so a new stance is
a row and not a code change (Cardinal II). The stance carries a date and an author.

This does not create a second home for the cardinal, because the stance is **a different
proposition**: the cardinal states what its publisher holds true; the stance states what this host
does with it. Each has exactly one home. There is nothing to synchronize, therefore nothing that
can drift (Cardinal III — remove the copy, do not sync it).

The projection renders cardinal and stance side by side, each with its source and its date. A
cardinal with **no** stance is rendered as such — a named silence, not an omission — because a
surface that printed only the answered ones would read identically to a host that had answered
everything (Cardinal V).

### ⑤ Two hosts on different doctrine versions are legible by CITATION, not by text

Every doctrine document is addressed as `bundle@semver#id` and its installed content carries a
digest recorded in the estate. A claim, a review, a gate result cites the address, never the
prose. Two hosts that disagree therefore produce a **version delta that can be printed** —
`ethics@2.1.0` against `ethics@1.4.0`, with the ids that moved — instead of two texts that differ
in wording and cannot be compared. Old bundles stay legible forever and are never rewritten; this
is Rust's edition model and it is adopted whole. A withdrawn bundle orphans its documents
(ADR-002) and does not delete them, so a stance that cites a withdrawn cardinal still resolves —
to an orphan, declared as one.

### ⑥ A host that declared no doctrine is a DECLARED ZERO, never a supplied default

`check` is **green**. Declaring no doctrine is a legal, complete state, and a gate that failed on
it would be the kit smuggling in a requirement to accept its opinions.

The doctrine surface prints, in the register ④ already established for the blank host:

> **THE DOCTRINE IN FORCE IS NONE.** No bundle is installed. No cardinal binds this host through
> this kit. (read: `<timestamp>`)

`evaluate` reports no doctrine-derived judgement and says why — absence of an instrument, not a
score of zero. Under no circumstance does the kit supply a starter cardinal set "to be helpful": a
default norm is an opinion installed by a party that was never asked, and a zero taken against no
instrument certifies rather than measures.

### ⑦ Why this cannot become the two-divergent-`architect.md` failure

That failure had a precise shape: **one text, two writable homes, no upstream, no record of which
was authoritative** — and both halves stayed internally correct while the system spoke with
confidence and lied. Every one of its preconditions is now unreachable:

- there is no second writable copy — a vendored cardinal is replaced wholesale and digest-checked;
- the host's own text is a *different proposition* in its own home, not a copy of the first;
- the surface where both are read is a projection, reproducible from the two, owned by neither;
- the authority is addressed (`bundle@version#id`), so "which one binds" is answerable from any
  standing point rather than from whoever happened to open which file.

## Rejected alternatives

1. **Ship `CARDINALS.md` / `protocol.md` as kit-owned vendor payload (the proposals' L0).** Fails
   ADR-001 ④ head-on — it ships verdicts, not the grammar of verdicts — and fails T2: the file
   already says something about the host on a blank install. It also hardcodes one publisher's
   ethics into the engine, the closed set Cardinal II forbids.
2. **Ship cardinals as a SEED the host copies and owns (binding class).** This *is* the
   two-divergent-`architect.md` failure, industrialised: N editable copies, no upstream, no
   amendment record, and an upgrade that can never speak about them again. It is the
   cookiecutter/Yeoman outcome the field has already paid for.
3. **A privileged `doctrine/` plane with its own loader and `when:` conditions.** A second
   installation grammar beside `installs` (Cardinal VIII), a second versioning story, and a
   condition language evaluated inside the interpreter — policy in the one place the host cannot
   reach (Cardinal IV). `requires` on a profile fact does the whole job with the grammar that
   already exists.
4. **Mechanisms only — no normative text of any kind in the payload.** Loses the clippy half. The
   meaning of `path-class-total` or of a residence genre can only become false if the kit changed;
   exiling it recreates the copy problem in reverse, leaving a gate that binds whoever finds it and
   is unknown to everyone else (Law 15's exact harm).

## Open gaps (declared, not routed around)

- **Provenance and trust of a third-party bundle.** OPA signs bundles; this kit has no signature
  story and no fetch story. Until it does, a bundle is a path a human placed.
- **Two bundles declaring the same cardinal id.** ADR-001 says ambiguity resolves to nothing and
  the owner chooses; whether a doctrine id collision is *ambiguity* or *conflict* is unruled.
- **Whether the stance vocabulary is kit-shipped or host-declared.** ⑤ needs a shared vocabulary to
  make stances comparable across hosts; ① says the kit ships no conduct norm. The vocabulary is
  arguably grammar and not norm — but that is asserted here, not proven.
- **Stance coverage as a measure.** "How much of the doctrine in force has this host answered" is a
  number the surface could carry; it inherits ADR-001's unclosed `observe → enforce` threshold and
  must not acquire one by default.
- **Skills and playbooks specifically.** Classified here as conduct doctrine and therefore
  bundle-borne; whether an executable playbook is doctrine at all, or a capability with a verb, is
  not settled by this ADR.
