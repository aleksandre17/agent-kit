# ADR-006 — Gate stance and maturation: what a failure DOES is declared, and it matures by declaration

- **Status**: Accepted
- **Date**: 2026-09-11
- **Amends**: ADR-001 (the framework blueprint), by ruling on P7 (gates ship in OBSERVE first) and
  P9 (observe⇄enforce matures on a threshold stated as a number), which ADR-001 left OPEN and the
  ledger narrowed to "absence declared on a surface". ADR-002 … ADR-005 are unaffected; ADR-005
  gains one code (`KIT0030`).
- **Rules on**: `kit/interpreters/verbs/check.py`, a new interpreter module
  `kit/interpreters/stance.py`, a new schema `kit/schemas/stance.schema.json` (registered in
  `kit/MANIFEST.json`), a new governance document `kit/capabilities/governance/stances.json`, the
  `stance` field of a gate in `kit/schemas/capability.schema.json`, and the `stances` field of the
  host's answers file in `kit/schemas/project.schema.json`.

## The situation

Fifteen gates across nine capabilities are declared as `{id, kind, params}`. `check` runs every
gate of every enabled capability and a single failure fails the verb. There is no stance: a host
adopting the kit on a real tree is met by every gate at full strength on day one, and the only
lever it has is to disable a whole capability — which removes the gate's VISIBILITY along with
its bite. The blueprint promised the opposite order (P7: watch first, then stop), and a maturation
from one to the other (P9), but neither was ever a mechanism.

Four precedents inside this system bound the answer:

- **ADR-001 ④ / L7-quality** — the kit ships the GRAMMAR and no case, rubric, threshold or scale.
  So a maturation threshold is not the kit's to state.
- **ADR-003 §6** — a stance toward a situation is DECLARED as data where the thing is declared,
  never derived by the interpreter (the plane's `unaccounted: refuse|report`).
- **ADR-004 ④** — a host qualifies a vendored declaration by declaring a STANCE against its
  address, dated and authored, never by editing it; an unanswered item is a named silence.
- **ADR-005** — refusals carry opaque codes in an append-only registry.

## The field

| System | Stance vocabulary | Who owns it | Can it be lowered | Unanswered default |
|---|---|---|---|---|
| Rust lints | `allow · warn · deny · forbid` | the lint DECLARES a default level; the crate/scope overrides | yes, **except `forbid`: an inner scope may not lower it — trying is itself an error (E0453)** | the lint's declared default level |
| ESLint | `off · warn · error` per rule | the consumer's config | yes, every rule | off unless a shared config says otherwise |
| Kubernetes PSA | `enforce · audit · warn` per namespace | the namespace label (consumer) | yes | the cluster's declared default |
| OPA Gatekeeper | `enforcementAction: deny · dryrun · warn` | the constraint's author | yes; `dryrun` results are still recorded in the audit | `deny` |
| SonarQube | quality gate on new code; legacy observed | the project | by scoping, not by lowering | the declared gate |
| Progressive rollout | percentage / cohort | the operator | yes | off |

What the field agrees on: (a) the stance vocabulary is small and **ordered**; (b) the **publisher**
of a check declares its default and the **consumer** overrides it; (c) a non-blocking stance still
**records** its findings (Gatekeeper dryrun audit, PSA audit, Rust `warn`); (d) exactly one of
them — Rust — has a **floor the consumer cannot lower**, and it refuses the attempt rather than
silently clamping it. Rust is the closest fit on every axis and is the model taken.

## The decision

1. **The stance VOCABULARY is one declared document**, `stances.json`, shipped by `governance`
   (never disabled) and FOUND by the schema it honours (`stance`), never by path or owner. Each row
   is `{id, rank, fails, says}`; the document names `unanswered`, the stance of a gate nobody has
   answered for. The kit ships two rows — `observe` (rank 0, does not fail) and `enforce` (rank 1,
   fails). A new stance (e.g. a Rust-like `warn` channel) is a ROW; the interpreter reads only
   `fails` and `rank`, and spells no stance by name (Cardinal II, IV).
2. **A gate's PUBLISHER declares on the gate** an optional `stance: {ships?, floor?}`. `ships` is
   the stance the gate stands in until the host answers — this is P7 made concrete: a NEW gate
   that must enter watched declares `ships: observe`. `floor` is the lowest stance any host may
   declare — Rust's `forbid`.
3. **The HOST declares** in its answers file a `stances` array of `{gate, stance, by, at, because?}`
   — dated and authored, the ADR-004 ④ shape. It is read through the approval door like every other
   host choice.
4. **Resolution is three declared rungs and nothing else**: host row → publisher's `ships` → the
   vocabulary's `unanswered`. Every gate line on `check` prints its stance AND its source
   (`declared by X at T` · `shipped so by capability C` · `unanswered -- the vocabulary's declared
   default`). An unanswered gate is therefore a declared state on the surface, never a guess.
5. **Visibility is independent of stance.** Every gate runs and every failure prints, whatever its
   stance. A failure under a non-failing stance is counted and named on its own summary line; a
   non-failing gate that is clean is named as such ("no failure stands between them and a stance
   that fails"). The stance decides one thing: whether the failure fails `check`.
6. **Refusals, not clamps** (`KIT0030`): a stance no vocabulary row names; a host stance ranked
   below the gate's floor; one gate answered twice; a host stance naming a gate id two capabilities
   declare; a gate shipping below its own floor; zero or two vocabularies. A host row naming a gate
   no enabled capability runs is NOT refused — it is printed as `STANCE … binds nothing`, because a
   host may keep a stance for a capability it has switched off, and a refusal there would punish a
   reversible choice.
7. **Maturation is a human DECLARATION.** Raising observe → enforce is the host restating its row,
   by a named person on a date (or deleting it, reverting to what the publisher ships). The NUMBER
   P9 asked for is the one the kit can honestly supply: the count of failures observed, printed on
   every run — evidence gathered by this run and nothing else. The kit ships no threshold
   (ADR-001 ④), and no machine promotes a gate on its own.

### The default for an unanswered gate — UNCHANGED

`unanswered` is `enforce`. With no host declaration, today's behaviour is exactly reachable: every
failing gate fails `check`. This is deliberately NOT the P7 reading "every gate observes first":
P7 is about a gate's *introduction*, and it is honoured per gate by `ships: observe` on the gate
that is new. A global default of `observe` would silently disarm the fifteen gates every current
host relies on, on an upgrade nobody accepted — the one change a surface cannot announce after the
fact. Gatekeeper and Rust's `deny`-by-default for correctness lints make the same call: fail
closed unless the publisher or consumer declares otherwise. Changing `unanswered` is a one-way
door for every host at once and requires an ADR.

### Which gates are a floor, and why

The test: **a gate is a floor iff, when it fails, the KIT can no longer truthfully state something
about itself or about the bytes it reads and writes** — as opposed to judging the host's own work.
Four gates pass it and declare `floor: enforce`:

| Gate | Why the kit's own promise depends on it |
|---|---|
| `FF-KIT-CLASS` | the four-class seam: every governed path has exactly one class. Without it, upgrade and adoption cannot say whose a byte is. |
| `FF-KIT-PROJECTION` | projections are byte-reproducible from declarations; observed-drift would make every projection a possible hand edit. |
| `FF-BINDING-SCHEMA-PROJECT` | the answers file honours its schema — the file that now carries the stances themselves. A lowerable version would let a host observe the invalidity of the document that lowered it. |
| `FF-BINDING-SCHEMA-PROFILE` | the reading honours its schema; the kit decides on that reading and may not decide on evidence it cannot read. |

Not floors, because they judge the host's own work or its freshness, which the host may reasonably
watch before it is ready to be stopped by: `FF-DELIVERY-WIP`, `FF-DELIVERY-AGE`,
`FF-QUALITY-JUDGEMENT`, `FF-QUALITY-REFERENT`, `FF-READING-FRESH`, `FF-RESIDENCE`,
`FF-KIND-AUTHORITY`, `FF-RUN-RECEIPT`, `FF-ROLE-BASE`, `FF-RUNTIME-CLASS`, `FF-RUNTIME-CLAIM`.
The floor is a declaration on the gate — this table is its reasoning, not its home; the
interpreter holds no list, and an acceptance test proves no gate id is spelled in it.

## Rejected alternatives

- **A. A privileged list of "integrity gates" in `check`, and a hardcoded `observe|enforce` switch.**
  The fastest build; it makes the floor the interpreter's policy and every new floor or stance a
  code change — the exact defect Cardinals II and IV forbid.
- **B. A kit-shipped maturation threshold (e.g. "N clean runs → enforce") evaluated automatically.**
  Contradicts ADR-001 ④ (the kit ships no threshold), and it is a machine deciding on evidence
  the host never declared it would accept; it also needs run history no gate reads today.
- **C. A host-declared measured trigger (`mature_when: {clean_runs: N}`) now.** The honest form of
  B, and the field's progressive-rollout analogue; deferred, not refused: it needs a recorded run
  history (observability receipts) and its FIRING recorded as a dated event, or the stance on the
  surface would change without an author. Named as the open gap below.
- **D. An ESLint-style `off` stance.** A gate that runs and prints nothing is a silent green
  (Cardinal V); a host that wants a gate gone disables its capability, which is visible on the
  selection.
- **E. Clamp a lowered floor silently back to `enforce`.** The surface would then show a stance
  the host declared as honoured when it was not. Rust refuses (E0453); so does this kit.
- **F. Global default `observe` (P7 read literally).** See "The default" above.

## Consequences

- A host adopting on a real tree can watch a gate before it is stopped by it, without losing the
  gate's findings — P7 is reachable per gate, by publisher or host.
- `check` output gains a stance label on every gate line; the verdict line `check: N gate(s)
  failed` is unchanged and counts only failures under a failing stance.
- `KIT0030` is issued (ADR-005, append-only).
- **Open (named, not improvised):** (i) a host-declared measured trigger whose firing is recorded
  (alternative C); (ii) SonarQube's new-code scoping — enforcing a gate on changed paths only — is
  a question of a gate KIND's params, not of stance, and is not addressed here; (iii) whether
  `init --approve` preserves a `stances` array written before approval is untested.

## Fitness functions

`tests/acceptance/fresh-repo/test_gate_stance.py`, tests 187–193: the unanswered stance fails and
is named on every line; an observed failure is printed, named and counted without failing; every
declared floor refuses a lowering host with `KIT0030`; no gate id or stance name is spelled in the
interpreter; an unknown stance and a doubly-answered gate are refused; a stance binding no running
gate is shown; maturation by restatement bites on the next run.
