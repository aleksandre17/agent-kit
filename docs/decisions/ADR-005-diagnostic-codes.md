# ADR-005 — Diagnostic codes: every refusal carries a stable code, meant in one append-only registry

- **Status**: Accepted
- **Date**: 2026-09-11
- **Amends**: ADR-001 (the framework blueprint), by ruling on §VII③ — stable machine-readable
  diagnostic codes over the exit-code contract. ADR-002, ADR-003 and ADR-004 are unaffected.
- **Rules on**: `kit/interpreters/errors.py` (`KitError` and its subclasses), the refusal line
  printed by `kit/interpreters/cli.py`, and a new declaration `kit/diagnostics.json`.

## The situation

The kit already refuses honestly: a situation it can name is a `KitError`, reaches the operator
as one line and an exit code, and anything else is a kit bug that crashes loudly. What the kit
cannot yet do is let a MACHINE tell refusals apart. The exit code carries a class (1 refused, 3
pending approval) and nothing finer; the only finer signal is the prose, and the prose is exactly
the part that is rewritten as the kit learns to explain itself better. A CI job, another runtime
or an agent that wants to react to "the lock is stale" as distinct from "the selection names a
capability nobody declares" can today only match a substring — and is broken by the next edit to
a sentence.

A published code is a **one-way door**. The day an outside consumer matches on `KIT0026`, its
meaning is fixed forever and the string can never be handed to a second situation. So the
numbering, the home of the meaning and the lifecycle are decided before the first code ships.

## What the field does with the same question

- **rustc** — `E0308`: a letter and four opaque digits, no class in the digits. The emission
  site names the code; the explanation lives once, in the `error_codes` registry, and
  `rustc --explain E0308` prints it. The registry is append-only: a code no longer emitted stays,
  marked as no longer emitted, and is never reissued. rustc's `tidy` gate refuses a code that is
  used without an explanation, or explained without being used.
- **TypeScript** — `TS2322`: prefix plus number. The thousands digit loosely groups categories,
  and in practice the grouping is not relied on; the number is the identity.
- **ESLint** — rule ids are NAMES (`no-unused-vars`). Readable, but a name is prose: renaming a
  rule is a breaking change, so ESLint keeps deprecated rules under their old name rather than
  reusing it. Named ids still pay the append-only price, and add the temptation to rename.
- **Python warnings** — a class HIERARCHY (`DeprecationWarning` ⊂ `Warning`) is the category;
  filters match the class. The class is the identity of the situation, not a string beside it.
- **HTTP status** — the counter-example: the first digit carries a CLASS (4xx client, 5xx
  server). This works because the classes are fixed forever; it fails wherever the class of a
  situation can change, because the digit then lies.
- **SARIF 2.1.0** — machine output carries `ruleId` (the stable code) and `level`
  (`error`/`warning`/`note`/`none`) separately, with the rule's text in a `rules` table keyed by id.

The questions they answer, and our answers: numbered, not named · the digits carry no class ·
retirement is a recorded row, never a deletion · explanation lives in one registry · machine output
leads with the code and keeps severity as a separate field.

## Decision

### ① The code is opaque, prefixed and sequential: `KIT` + four digits

`KIT0001`, `KIT0002`, … issued in order. The digits carry **no class**. Severity already has a home
— the exit code — and a family digit would lie the day a refusal moved between modules or families.
Four digits leave room for 9,999 codes. The prefix `KIT` is fixed for the life of the registry;
changing it would renumber every published code at once.

### ② The meaning of a code has exactly one home: `kit/diagnostics.json`

Each row is `{code, status, title, explanation}`. The title is one line in the host's terms; the
explanation says what the situation is, why the kit refuses rather than guesses, and what the
operator does next — it is the text a future `kit explain KIT0026` prints. The registry is a
DECLARATION: pure data, shipped in the payload (a `declaration` account in `MANIFEST.json`), so a
consumer in any runtime reads it without executing Python. Its shape is `kit/schemas/diagnostics.schema.json`.

### ③ The refusal CLASS names its code; the raise site does not

As in rustc, the emitting side names the code and the registry means it. Here the emitting side is
the class: every `KitError` subclass declares `code = "KIT00NN"` **on itself**. The binding is
class→code (a reference into the registry); the meaning is never restated on the class. The grain
is the class because the class is already the kit's unit of a named situation (Python's own model,
above). A finer distinction is made the same way the kit makes any: **declare a subclass and issue
it a code** — a new row, never a code argument threaded through raise sites.

`KitError.__init_subclass__` refuses, at import, any subclass that does not declare its own code:
an inherited code would be a second situation silently answering to the first one's code. The root
`KitError` itself carries `code = None`, and a bare `raise KitError(...)` is gated out (⑥).

### ④ The registry is APPEND-ONLY, and retirement is a recorded row

A code is never deleted, never reused, never re-meant. When no class raises it any longer, its row
stays with `status: retired` and `retired: {in: <kit version>, reason}`. `issued` is the
high-water mark and codes are **dense from 1 to `issued`**: a deleted row is a gap the gate sees
without consulting history. Changing a code's meaning is not an edit — it is a retirement plus a
new code.

### ⑤ The rendered line leads with the code, bracketed; the prose is untouched

    kit: [KIT0007] <the refusal's prose, unchanged>

A machine matches `^kit: \[(KIT\d{4})\] `; a person reads the prose. A refusal with no code renders
`kit: [uncoded] …` — an honest absence, never an invented code. Exit codes are unchanged. SARIF
output, when built, is a PROJECTION: `ruleId` = the code, the rule text from the registry, `level`
projected from the exit code (1 → `error`, 3 → `note`) — severity keeps its single home.

### ⑥ Fitness functions (each shown to deny)

`tests/acceptance/fresh-repo/test_diagnostics.py`, tests 178–185: every refusal class names an active
code · no two declarations share a code · the registry is unique and dense to `issued` · a retired
code states when and why and is raised by nothing · every active code has a raiser (else retire it)
· the registry honours its schema · no raise site raises the uncoded root · the operator's line
leads with the code. All expectations are read from the registry and the classes, never hardcoded.

## Rejected alternatives

1. **Named ids (ESLint-style `stale-lock`).** Readable, but a name is prose and prose is the thing
   that drifts; renames become breaking changes and the pressure to "improve" a name never stops.
   The readable part already has a home — `title`.
2. **Class digits (HTTP-style `KIT1xxx` = lock, `KIT2xxx` = composition).** The family of a refusal
   is an implementation fact that moves; the digit would then lie forever, because the code cannot.
   Severity, the only class consumers need, is already the exit code.
3. **Code per raise site (`raise X(msg, code="KIT0042")` at ~100 sites).** Finer, but it scatters
   the binding over every raise, lets two sites of one class claim different meanings with no
   typed seam between them, and makes a new distinction an edit of a call rather than a
   declaration. A subclass is the typed, OCP form of the same precision.
4. **The meaning on the class (docstring or `explanation` attribute), no registry.** One home
   for Python, none for any other runtime; and a deleted class takes its code's meaning with it,
   which is exactly the silent removal an append-only registry exists to prevent.
5. **A mutable registry with deletion allowed.** The failure every one of the field's registries
   is designed against: the next author takes the freed number, and every consumer still matching
   on it is silently told a different thing.

## Consequences

- A new refusal = a new row (`issued + 1`) plus `code = …` on the new class. The interpreter is not
  edited; `cli.py` renders whatever code the class names.
- The refusal record written by observation still carries only the prose; carrying the code there
  needs a field in `observation.schema.json` and is left open (below).

## Open gaps (declared, not routed around)

- **GAP-EXPLAIN-VERB** — `kit explain <code>` is not built. The registry already holds the text; the
  verb is a pure projection of it and requires no new decision.
- **GAP-RECORD-CODE** — the observation record and the run receipt should carry the code as a
  field, not inside the message.
- **GAP-SARIF** — no machine-output mode exists; ⑤ fixes its shape when it does.
- **GAP-DOUBLE-IMPORT** — `context.py` imports `ports.manifest`/`ports.probe`/`ports.workspace` by
  package path while every other module imports them by stem, so each of those modules exists
  twice and so does each refusal class it declares (two objects, one code). An `except` holding
  one of the two objects does not catch the other. Codes are unaffected (they attach to the
  declaration), but the defect is real and is outside this decision.
