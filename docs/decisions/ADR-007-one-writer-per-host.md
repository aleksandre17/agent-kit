# ADR-007 — One writer per host: every verb that writes the host holds it, and both run records have one shape

- **Status**: Accepted
- **Date**: 2026-09-11
- **Amends**: nothing in ADR-001 … ADR-006. ADR-005 gains one code (`KIT0031`); `KIT0010` (the
  hold) keeps its meaning and now also covers a hold that does not honour its schema.
- **Rules on**: `kit/interpreters/hostlock.py`, `kit/interpreters/journal.py`, every verb in
  `kit/interpreters/verbs/` that declares `MUTATES`, two new schemas `kit/schemas/hold.schema.json`
  and `kit/schemas/journal.schema.json` (registered in `kit/MANIFEST.json`), and the name of the
  hold document in the observed-state plane (`init.lock` becomes `host.lock`).

## The situation

The init slice built two mechanisms for the inside of an install: a JOURNAL (every phase written
before it runs and after it concludes; a record with no ending is an interrupted run, carried
forward whole and replayed) and a HOLD (who, which machine, which process, when, which verb, which
run; no clock arithmetic; a standing hold is a door that only `--break-lock <who>` passes). It left
two gaps:

1. **Only `init` held the host.** A `render`, `move`, `evaluate` or `upgrade` could write into a
   host another runtime was installing into. `upgrade` was partly covered by accident — it hands its
   verdict to the installer — but the hold then named the step (`init`), not the run (`upgrade`),
   and the reconciliation was printed against a tree someone else was writing.
2. **Neither record had a kit schema.** Each named a `SCHEMA_VERSION` in its module while every
   other host document validates through `manifest.validate` — two homes for one shape, one of
   them prose.

## The field

Every mature single-writer mechanism does the same three things, and this kit's init hold already
did them: it **refuses a second writer**, it **names the hold** that refused it, and it makes
**breaking a stale hold an explicit, named, human act**.

- `git`'s `index.lock` — created exclusively by any command that writes the index; a second writer
  fails naming the file; a stale one is removed by a human, never by age.
- `apt` / `dpkg` frontend lock — taken by every operation that mutates the package database, not
  only by install; read-only queries take none.
- Terraform state locking — every operation that may write state takes it; `force-unlock <LOCK_ID>`
  requires the lock's own id, so a break names exactly what it breaks. (Terraform also locks
  `plan`, for a consistent read of remote state. This kit deliberately does not: its plan reads a
  local tree and must leave it byte-identical, and a lock written by a plan would be a write.)
- PostgreSQL advisory locks and `flock(2)` — the primitive underneath: an exclusive hold scoped to
  a named subject, released by its holder; neither guesses liveness from age.
- SQLite's lock escalation — a connection reads under a shared lock and escalates to RESERVED only
  at its first write. This is the shape of "take the hold at the moment the run becomes a writer".

## The decision

1. **The hold is the HOST's, not a verb's.** One document (`host.lock`, in the plane the manifest
   classes `ephemeral`), one shape (`hold`), taken by whichever run writes the host.
2. **Which verbs hold is READ from declarations, never listed.** A verb holds the host iff it
   declares `MUTATES` and declares no `SUBJECT` of its own — a verb that writes somewhere other
   than the tree `--root` names says so by declaring what it writes. (A literal `"host"` subject
   was tried and refused by the boundary fitness function `test_71`: the interpreter may not spell
   a term no schema declares.) `hostlock.holds(module)` is the one reading; `hostlock` holds
   no verb name. Today that set is `evaluate · init · move · render · upgrade`.
3. **Guarded on arrival, taken at the first write, closed in a `finally`.** Every held verb calls
   `hostlock.arrive` first (a pure READ — a held host is named as the cause before anything else is
   said) and takes the hold only where it becomes a writer (`hostlock.held` around its write, or
   `hostlock.writer` at init's first writing phase). A `--plan` and every refused run take no hold.
   *A guard that protects a write must never itself be the first write* — the init slice paid for
   that lesson with five red "refused and mutates nothing" tests, and this decision keeps them green.
4. **A nested write is the same run.** A render carried out by a move, or an install carried out by
   an upgrade, borrows the one hold of the run that took it; the hold and the journal carry the RUN's
   verb. A process holds a host at most once.
5. **Both records have one home for their shape.** `hold.schema.json` and `journal.schema.json` are
   registered in the manifest; the version written is read from each schema's `schema_version`
   const, and the modules' `SCHEMA_VERSION` constants are removed. Every write validates first; a
   record on disk that does not honour its schema is REFUSED and never overwritten (`KIT0010` for a
   hold, new `KIT0031` for a journal) — the evidence of a dead run is not the next run's to discard.

`lock` declares `SUBJECT = "kit"`: it writes the kit's own lockfile through a workspace rooted at
the kit and scoped to that one path, never the host `--root` names, so the host's hold is not its to
take. Two authors locking one kit at once is a real but different subject (the authoring tree), and
it is named as a gap rather than folded into a host mechanism.

## Rejected alternatives

- **Take the hold on arrival, in the entry point, for every MUTATES verb.** The simplest code, and
  wrong: a hold written by a run about to be refused is a mutation, and it turned five
  refused-and-mutates-nothing tests red when init tried it.
- **A hand-kept list of held verbs in `hostlock` (or in the CLI).** A closed enumeration beside the
  declarations it duplicates; the first new writer would be unheld until someone remembered the list.
- **One lock per verb (`init.lock`, `move.lock`, …).** Two different verbs writing one tree are the
  exact failure; per-verb locks would admit them.
- **A timeout / age-based stale detection.** Breaks a slow live run as readily as a dead one and puts
  two writers in one tree with a reassuring message; the init hold already refused it.
- **Keep `SCHEMA_VERSION` in the modules and "keep it in sync" with the schema.** Synchronization by
  discipline is not a mechanism; the schema is the one home and the version is read from it.

## Consequences

- A host that was held by an older kit's `init.lock` is not read by this one. The kit is pre-1.0
  and no host in the field carries a standing one; a migration is not built (named, not implied).
- Every held verb now leaves a CLOSED hold behind after it writes (`released_at`, `exit_code`).
- The held set is still enforced per verb by a call the verb makes; a new host-writing verb that
  declares `MUTATES` but forgets `arrive`/`held` is caught by the fitness function below, not by
  construction. The by-construction form — the host workspace port escalating to the hold at its
  first write, as SQLite does — is the destination; it needs the workspace port, outside this slice.

## Fitness functions

`tests/acceptance/fresh-repo/test_one_writer.py`:

- `test_196` — every verb the declarations say holds the host is refused (exit 3) at a host a REAL
  killed init still holds; the refusal names owner, machine, pid, verb, run and moment; the host is
  left as it was save the receipt of the refusal; every mutating verb outside the set declares a
  subject other than the host.
- `test_197` — `render` takes and closes the hold under its own verb and run.
- `test_198` — an install carried out by `upgrade` is held and journalled as `upgrade`, one run id.
- `test_199` — `--plan` of every held verb leaves the last hold byte-identical.
- `test_200` — both records validate against their schemas, carry the schema's version, and no
  module declares its own.
- `test_201` — a hold or journal on disk that does not honour its schema is refused by code and
  never overwritten.
