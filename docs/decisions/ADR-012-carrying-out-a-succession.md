# ADR-012 — Carrying out a succession: the map at its residence, a door that accepts the roster by its digest, and no byte destroyed

- **Status**: Accepted
- **Date**: 2026-09-12
- **Supersedes**: nothing
- **Amends**: ADR-011 (closes `GAP-MAP-RESIDENCE` and `GAP-CENSUS-EXCLUSION`; a disposition now declares its EFFECT), ADR-002 (the estate accounts for what a host GAVE UP at a succession door)

## The situation

ADR-011 built the reading: `inherit` takes a census inside a declared boundary, measures, and prints
what a signed migration map assigns — writing nothing. It named three things the act of carrying a
roster out needed and could not yet state honestly: where the map LIVES, a DOOR that accepts it by
digest, and a WHOLE refusal while anything is `undecided`. This is that act, and it is the most
destructive thing this kit will ever do: it takes files a host authored out of the host's tree.

## The central question

**What proves that the roster carried out is the roster that was signed?** The map's digest does
not: the map can be unchanged while the TREE it was read against moves — a file edited by another
runtime, a new file under a moved directory, a destination that appeared. A signature over the map
alone would authorise an act over bytes nobody read. So the thing accepted is the ROSTER: the map's
digest together with every path, the digest of its bytes, its disposition, its effect and where it
goes. The act re-reads the host at the moment it becomes a writer and computes that digest again;
a different value is refused whole. The machine never acts on a reading it did not just take.

## The decision

1. **The map RESIDES in the binding plane**, at one path the succession vocabulary declares
   (`residence`: `.agents/project/succession/migration-map.json`), which the governance capability
   SEEDS BLANK (`{schema_version, prior: [], rows: []}`, validated as `migration-map`) — so the map
   is an ACCOUNTED path (`FF-KIT-CLASS` holds), discoverable where the host will author it, and
   thereafter the host's own, committed and reviewed. A blank map declares no prior system and is
   signed by nobody; `declared_by`/`declared_at` are its signature, and a map with rows and no
   signature is read and never carried out. The vocabulary's residence is refused unless it is a
   declared install target in a plane. (A `space` was the first form and was rejected: every
   governance target is a FILE a fresh install holds, and an empty directory is not one.)
   `takeover` reads ONLY the map there and refuses `--map`: a map passed from anywhere is a
   judgement with no home. `inherit` reads the residence when no `--map` is given, so the reading
   printed is the reading carried out.
2. **The door accepts the ROSTER BY ITS DIGEST.** `takeover --plan` prints the roster and
   `roster <sha256>` — the digest of the canonical JSON of `{map, residence, paths[]}`, each path
   `{path, row, disposition, effect, digest, to}` (a link's digest is of its target text: one path,
   never followed). The act is `takeover --approve <who> --roster <sha256>`; without both it stands
   at the door (exit 3, `KIT0007`, the digest printed); with a digest that is not the digest read
   now it is refused (`KIT0038`) before a byte moves. `--plan` and the act are ONE computation
   (`succession_act.compose`), so they cannot drift. Each path is re-measured again immediately
   before its rename; a path that changed during the act stops it there, the act stays open, and
   the next run names the path.
3. **Refused WHOLE (`KIT0037`) while anything cannot be carried out**: a path under a `prior` root
   that no row answers; a row reaching a path this kit installed (the estate or an install target
   says so) or the map itself; a destination that exists (never overwritten); a destination under no
   space whose install mode the vocabulary declares may `receives` a path. Every fault is named at
   once. The undecided refusal covers the PRIOR boundary the host declared: census paths in the
   kit's own planes that no row answers are counted and printed, and answered for by the estate and
   `adopt`, not by this act.
4. **A disposition DECLARES its effect.** `effect` is read from the vocabulary through the
   interpreter's `EFFECTS` registry — a Strategy per effect that computes the destination
   (`relocate` from the one relocating reference the row carries; `remove` into the aside place);
   an effect not in the registry, or a disposition whose relocating fields do not match its effect,
   refuses the vocabulary (`KIT0036`). A disposition that declares NO effect is readable and never
   carried out: a path it answers refuses the act (expand before contract). An effect is never
   inferred from the fields a row happens to carry — that inference would make every future
   field-less disposition a deletion by default.
5. **Every effect is ONE RENAME, and no byte is destroyed.** A relocated path is renamed into its
   space; a REMOVED path is renamed ASIDE into the observed plane
   (`<ephemeral root>/succession/<map digest[:16]>/<path>`). Deleting it is the host's own ordinary
   act, once satisfied. A rename is atomic within one filesystem, so at every instant a path is
   whole at exactly one of its two names; a rename across filesystems fails loudly rather than
   degrading into a copy. A destination that exists is refused, never replaced
   (`Workspace.relocate`, a new ADDITIVE port method, as is `Workspace.prune`, which removes only
   directories the act left EMPTY, never above the row that answered them).
6. **The act is written before it acts and accounted after.** Phase `record` writes the act
   (kind `succession-act`, versioned per ADR-009, sealed by its digest) into the observed plane
   before the first rename; `carry` renames; `account` appends the whole act — roster, signer,
   moment signed, `started_at`, every run that carried it, `carried_at` — to the estate under
   `succession_acts`, and closes the record. Every writer of the estate carries that list, exactly
   as it carries `taken`. The act holds the host's one hold, taken at the first write (ADR-007),
   and keeps a journal (`takeover.journal`).
7. **A killed act is RECONCILED, never guessed.** It leaves: the hold standing, the journal inside
   `carry`, the act record open (no `carried_at`), the estate unchanged. The next run meets the hold
   as a door (`--break-lock <who>`), then reconciles the open record against the tree — each path is
   *pending* (source holds the signed bytes, destination empty), *carried* (the reverse), or a
   *conflict* (anything else, refused whole for a person). `--plan` says INTERRUPTED with the counts;
   the act is finished at the SAME door with the SAME digest, and the account names both runs. An
   account already in the estate is never appended twice.
8. **Uncommitted changes do NOT refuse.** The digest, not the VCS index, binds what is carried:
   bytes that are dirty at the reading are the bytes signed, and they are carried or set aside
   whole; bytes that change after the reading refuse the act. Consulting the index would be a
   second reading of the same reality taken at another moment (Cardinal III), would make the
   interpreter ask *which VCS are you* (Cardinal VIII), and would add nothing the digest does not
   already prove — while removal-by-rename means no uncommitted work can be lost by the act.
9. **`GAP-CENSUS-EXCLUSION` is closed: there is no exclusion grammar.** A cache or untracked file
   inside a prior root is a path, and it is answered by a row (retired, with its reason) like any
   other. An exclusion would let a path leave no trace in the account, and an exclusion by pattern
   is a heuristic over names.

## The field

| system | what it teaches | taken here |
|---|---|---|
| `terraform plan -out` / `apply planfile` | apply refuses a saved plan when state moved since it was made | the roster digest IS the saved plan's identity; the act re-derives it and refuses a stale one — without `--plan` writing a file |
| Flyway / Liquibase checksums | an applied changeset whose checksum changed is refused | a path whose bytes changed since signing refuses the act, before and during |
| Nix Home-Manager | refuses to clobber an existing file; `-b` moves it aside only on an explicit flag | a destination that exists refuses; a removal is ALWAYS a move aside, because deletion is the one act nobody reviews afterwards |
| `git mv` / git's untracked-overwrite refusal | a rename, and never over something that is there | one rename per path; an existing destination refuses |
| OpenRewrite / codemods | dry-run diff first, apply second | `--plan` is the same computation as the act |
| `rsync --backup` / `--delete` | deletion is opt-in and a backup keeps the replaced bytes | nothing is deleted by the kit; the aside place is named in the account |
| write-ahead logging | intent is durable before the effect | the act record is written before the first rename; the tree plus the record reconcile any interruption |

## Rejected alternatives

- **Delete removed paths, trusting VCS history to hold them.** Untracked and uncommitted bytes are
  in no history; the kit would destroy exactly the work nobody saved, on the strength of a row.
- **Accept the map's digest alone** (a signature in the map or beside it). The tree moves
  independently of the map; the signature would authorise bytes nobody read.
- **A saved plan file written by `--plan`** (terraform's `-out`). `--plan` writes nothing, by law;
  and the file would be a second home of a reading. The digest carries the plan's identity; the act
  recomputes the value.
- **A move as copy + delete.** Two copies at once, a torn copy on a kill, and no atomicity.
- **Refuse when the VCS reports an affected path dirty.** A second reading at another moment, a
  VCS-specific branch in an agnostic interpreter, and weaker than the byte digest it would duplicate.
- **One journal phase per path.** The whole journal rewritten twice per path is O(n²) on a host of a
  thousand paths; rename atomicity makes the tree itself the per-path record, reconciled against
  the act record.
- **Effect inferred from a disposition's carried fields.** A deletion by default for every future
  disposition that carries no destination.

## Consequences

- The real second host can be carried out once its map is at the residence and every prior path is
  answered; that run is the owner's decision, not this slice's.
- Removed bytes accumulate in the observed plane until the host deletes them; the account in the
  estate names every one, so emptying the aside place never makes a path unaccounted.
- Residual window: on POSIX `os.rename` replaces silently, so the no-clobber check stands
  immediately before each rename rather than inside it; on Windows the rename itself refuses.
- The per-path moment recorded is the act's window (`started_at` … `carried_at`), not a moment per
  rename — a per-path moment would cost the O(n²) journal rejected above.
- A map may send paths into any space whose mode the vocabulary says `receives`; whether the files
  honour that space's own gates is then read by `check`, as for any host-written file.

## Fitness functions

`tests/acceptance/fresh-repo/test_takeover.py`, `test_244`–`test_257`, over the FIXTURE prior system
only — including a REAL process killed inside `carry` and the next run's door, reconciliation and
finish. Every one was shown to deny under a named mutation.
