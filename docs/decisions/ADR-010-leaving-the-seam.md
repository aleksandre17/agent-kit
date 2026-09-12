# ADR-010 — Leaving the seam: a signed steward transfer, one path at a time, and no `eject`

- **Status**: Accepted
- **Date**: 2026-09-12
- **Supersedes**: nothing
- **Amends**: ADR-002 (the estate gains a signed transfer; the reconciler reads it), and rules on
  `docs/proposals/PROPOSAL-agent-framework-layout.md` §6, which proposed `eject` and was never
  decided

## The situation

The proposal named five verbs, one of them `eject`: *"dissolve the seam: reclassify all VENDOR
as BINDING, drop the lock, record the decision."* No ADR ruled on it, and `kit/README.md` has
said since that `eject` is designed and not built. The need behind it is real: a host that wants
to own something the kit vendored into it — to edit it as its own, and to stop the kit replacing
it — had exactly two options, and both were wrong. It could edit the vendored file and live with
`diverged-kept` on every upgrade and a whole-upgrade refusal the first time upstream touched the
same file (ADR-002 §3, 8c/8d); or it could disable the capability that shipped it, losing every
other path, gate and document of that capability to keep one file.

What is already possible, and is not rebuilt here: a capability is left with `--disable`;
vendored doctrine is qualified by declaring a stance, never by editing it (ADR-004); a gate's
stance is set by the host, except for floors (ADR-006).

## The field

| system | what "leaving" is | what it teaches |
|---|---|---|
| Create React App `eject` | one-way, all-or-nothing copy of the whole toolchain into the app | widely regretted: to change ONE setting you inherit ALL of them and stop receiving fixes for every one. CRA is now deprecated |
| Angular `ng eject` | the same idea | removed |
| Vite, Next.js | no eject; per-concern escape hatches (config hooks, a plugin, one file overridden) | leaving is granular by design, and the platform keeps working around the part you took |
| shadcn/ui | you OWN the copied source from the first day; no upstream to reconcile | ownership is a property of a path, decided at the moment it is taken |
| Terraform `state rm` / `removed` and `moved` blocks | hand ONE resource out of management, recorded in config, never the whole state | the grain is the resource, the act is declared and planned, the rest of the state is untouched |
| chezmoi `forget` | stop managing one target; the file stays | the file and the account of it are two different things |
| git subtree split | detach a subtree with its history | history is not rewritten by leaving |

The field says the proposal was wrong in exactly the way CRA was wrong: it made leaving
all-or-nothing, and it made the unit of leaving the thing the host least wants to leave. Every
system that survived moved to a granular hand-over at the grain of one managed thing.

## Decision

### 1. There is no whole-seam `eject`

`eject` is not built and will not be. What it would do is either destructive or already true:

- *Reclassify every vendor path as binding* — the host owns nothing it did not already hold. The
  bytes are in its tree and its history; the only thing `eject` would change is that the kit
  stops vouching for all of them at once, which is the CRA failure.
- *Drop the lock* — the lock is the KIT's reading of itself (`kit/kit.lock.json`), not the host's;
  a host has no lock of the kit to drop. Deleting the estate instead would destroy the one record
  of what the host was given (ADR-002 §1) at the moment it is most needed.
- *Leave the kit entirely* — is done by no longer running it. A verb whose only honest output is
  "you may now stop" is a verb that writes a lie about having done something.

### 2. Leaving is a STEWARD TRANSFER of one path, through a door: `cede`

`cede --path <path>[,<path>...] --approve <who>` hands paths the kit shipped to the host.

- **It is a door** (`doors.py`): without `--approve` it stalls with the pending exit code and
  writes nothing; `--plan` states the write and what the host loses, and writes nothing.
- **It is recorded on the row it is about.** The estate row gains `ceded: {signed_by, signed_at,
  held}` — who, when, and the digest the host held at that moment — and the row's `class`
  becomes the class the transfer declares. `mode` is NOT rewritten: it says what wrote the bytes,
  and history does not change hands. The estate's own `taken_at` and `signed_by` do not move:
  nothing was delivered.
- **It is whole or nothing.** Every asked path that cannot change hands is named at once and none
  does (`KIT0035`): a path the record does not carry, one already ceded (its signer named), one
  whose steward offers no transfer, one whose transfer names a class the kit does not declare.

### 3. What a transfer IS lives in the declaration, not the verb

`stewardship.json` gains two optional, additive properties (ADR-009 §5: no version moves):

- `transfers_to: {steward, class}` on a steward — whether its paths can be taken over, who answers
  for them afterwards, and the ONE class they hold afterwards. Only `kit` declares one
  (`→ ceded`, `binding`). `host`, `host-space`, `derived` and `record` declare none, because a host
  cannot take what is already its own and a projection or a record has no bytes anyone could own.
- `named: true` on a steward — every path it holds is printed on every reconciliation, whatever
  its cell.

A new steward, `ceded`, states the verdicts: the file is always kept, never replaced, never
restored; the row is carried (forgotten / orphaned when the kit withdraws the path, as for any
other steward); the surface says `ceded`, `ceded-behind` where upstream has bytes this host no
longer receives, and `ceded-absent` where the host removed it. `introduced` and `collision` are
deliberately unanswered: a path can only be ceded from a row, so neither can be computed, and one
that were would be refused rather than defaulted.

`estate.Stewardship.answering(mode, row)` is the ONE place the steward for a path is resolved:
its mode's steward, or — where the row carries a signed transfer — the steward that one declares.
A row claiming a transfer its steward does not offer is refused (`KIT0008`): a hand-written
signature is not a door. The interpreter names no steward, path, capability or class.

### 4. No writer takes a ceded path back

- `upgrade` resolves the steward through `answering`, so a ceded path's cell is answered by
  `ceded`: an edited ceded file that upstream also changed is `ceded-behind`, kept, and the
  upgrade proceeds — where the same tree without the door refuses (ADR-002 8d).
- `init` run again asks `reconcile.taken_over` before planning: a vendor mode replaces because it
  cannot tell whether the host touched the file, and the record now says, with a name on it.
- `estate.rows` carries a ceded row whatever a run decided, so no re-take can erase a signature.
- Every reading NAMES a ceded path with its signer and moment, including when nothing moved.

### 5. What the host loses, at each grain

| grain | mechanism | loses | keeps |
|---|---|---|---|
| **one path** | `cede` (this ADR) | upgrades to that path (reported as `ceded-behind`, never applied); the kit's vouching for its bytes | every gate of the owning capability at its declared stance, floors included; every other path; the capability's provenance pin (ADR-008); the estate's account of the path |
| **one capability** | `--disable` (exists) | all its paths, gates, documents and upgrades | the rest of the kit |
| **stance on doctrine / a gate** | ADR-004 / ADR-006 (exist) | nothing but the kit's default reading; floors cannot be lowered | the bytes stay the kit's |
| **the whole kit** | stop running it | upgrades, gates, floors, provenance, the estate's meaning | the bytes, in the host's own history |

The four-class seam stays a floor: a ceded path holds exactly one class, the one its transfer
declares, and a transfer to an undeclared class is refused.

### 6. Declared gap

A transfer is one-way in this version: no verb hands a path BACK to the kit. The need is
foreseeable (a host that took a file over and wants upstream again), and its honest form is a
second door recorded on the same row, reconciled as `restored`/`advanced` under the kit steward.
It is not built because nothing has asked for it; it is named here so that the first host that
needs it meets a declared absence, not an improvisation.

## Rejected alternatives

1. **`eject` as proposed — reclassify every vendor path, drop the lock, record the decision.**
   Rejected: all-or-nothing at the grain the host least wants to leave (the CRA / `ng eject`
   failure the field abandoned); "drop the lock" names a document the host does not hold; and it
   has no honest output for the only case it covers that `cede` does not — leaving entirely —
   which is done by not running the kit.
2. **Let the host edit the file and treat the edit as the transfer.** Rejected: ownership would
   be INFERRED from a digest, which is exactly `re-stewarded` happening silently (ADR-002), and a
   later reader could not tell a deliberate take-over from an accidental edit. A door leaves a
   name and a moment; an edit leaves neither.
3. **Reclassify in the kit's declaration (a per-host `installs` override, or `mode: seed` on the
   row).** Rejected: an override file is a second home for the install declaration (Cardinal
   III); rewriting the row's `mode` falsifies history and is refused as `re-stewarded` on the next
   upgrade anyway. The transfer is a fact about THIS host, so it lives on this host's record.
4. **A per-capability cede (`--capability`).** Rejected for now: it is `--disable` plus keeping
   the bytes, and the bytes are already kept; the path grain composes to it (`--path a,b,c`)
   without a second mechanism.

## Fitness functions

`tests/acceptance/fresh-repo/test_leaving_the_seam.py`, `test_219` – `test_230`, each shown to
deny by mutation: the door, the row's record, the class, the reconciler's and `init`'s honouring of
the transfer, the naming on every reading, the declaration deciding which stewards transfer, the
class floor, the refusal of a forged transfer, whole-or-nothing, and one signature per path.
