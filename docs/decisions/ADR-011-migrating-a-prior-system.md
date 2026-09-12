# ADR-011 — Migrating a prior system: the machine takes the census, a signed map declares, and nothing is defaulted

- **Status**: Accepted
- **Date**: 2026-09-12
- **Supersedes**: nothing
- **Amends**: ADR-003 (the roster reaches past the kit's planes, into a boundary the host declares)

## The situation

`adopt` (ADR-003) reads only inside the kit's four planes. A host that already runs an agent
system of its own keeps it entirely outside them: on the second real host, three of the four
planes do not exist and roughly a thousand files of a prior system (its doctrine, its knowledge,
its runtime adapters, its root law files) had never been seen by any reading. The design promised
that the migration list would be *produced by the machine, never by judgement*, and no machine
for it existed.

The owner's order is binding: the new system is built to 100%, then the existing one is FORCED
TO ADAPT — what is good moves in, what is missing is added, what is redundant is deleted. This
ADR builds the instrument that makes that order mechanical, and it answers one question first.

## The central question

**A prior system's path does not carry its destination in its bytes.** Whether an old role file
becomes a role overlay, whether an old hook is superseded by a capability, whether a knowledge
file is retired — none of it can be read off the path. So *somewhere* a judgement is made. The
only question is WHERE, and this framework's identity answers it: a judgement is a DECLARATION —
stored, dated, signed, diffable — or it is not made at all. It is never smuggled in as a
heuristic over names, and it is never a default.

## The decision

1. **The machine takes the census, inside a DECLARED boundary.** The boundary is the union of
   (a) what the kit itself declares — its planes and every install target outside them — and
   (b) the `prior` roots the host's migration map declares. Every file at or below a root is in
   the census; nothing outside is looked at; nothing is found by resemblance. The interpreter
   knows no runtime, product or directory name. A link is ONE path and is never walked through
   (its referent is stated): a name is not a referent, and counting a junction's target twice
   would be a census of names.
2. **The machine MEASURES; it never assigns.** For each path it states what can be proven: the
   plane it sits in, a kit install target it stands on, kit bytes it is identical to, a link it
   is; for a relocated path, whether the destination is a kit target or already exists.
   Measurements are EVIDENCE printed beside the row and VERIFICATION of the map. A measurement
   never decides a disposition — not even byte-identity to kit payload, because *identical* says
   the kit ships these bytes, not that the host no longer wants its copy where it is.
3. **The MIGRATION MAP declares.** Host data (`migration-map` schema): `declared_by`,
   `declared_at`, `prior` roots, and rows. A row answers the paths at or below its `path` with
   one disposition. The MOST SPECIFIC row answers a path (longest-prefix, as routing tables and
   CODEOWNERS do); a path may be named by only one row, so the answer is always one row.
4. **The vocabulary is closed BY DECLARATION.** The dispositions live in one declared document
   (`succession`, carried by the governance capability): `moves` (carries `to`, a plane
   reference; the remainder below a directory row is carried below its destination) ·
   `superseded` (carries `by`, a capability reference) · `retired` (carries `because`, a
   statement). Each disposition declares exactly the fields a row must carry and what each
   REFERS to; the interpreter checks a reference by its kind through a registry it provides
   (`plane`, `capability`, `statement`) and names no disposition. A new disposition is a row in
   the vocabulary; a vocabulary naming an uncheckable kind is refused, never ignored.
5. **`undecided` is the absence, never a word a row may say.** A path no row answers is
   `undecided`, counted and named. The roster prints every state, zeros included, and the census
   total; it says INCOMPLETE while any path is undecided.
6. **A map that says what it cannot mean is refused WHOLE** (`KIT0036`): not JSON or not the
   shape, a root or row leaving the host, two rows for one path, an undeclared disposition, a
   missing or surplus field, a reference to no plane or no capability, two paths sent to one
   destination. No roster is printed from such a map — a roster computed from it would be a
   confident reading of nothing.
7. **The verb `inherit` is a READING.** It writes nothing, moves nothing, deletes nothing, and
   `--plan` is refused for it as for every non-mutating verb.

## APPLY is the next slice, deliberately

Carrying a roster out is NOT built here. A correct reader and an honest roster are a complete
artifact on their own, and apply depends on three things this slice cannot yet state honestly:
the map's RESIDENCE in the binding plane (it must be the host's committed, reviewed truth before
anything acts on it, and on the second host that plane does not exist yet); a DOOR (ADR-001,
ADR-010) at which a named person accepts the map, recorded with the digest it accepted; and the
refusal of apply while any path is `undecided`. Apply will be a mutating verb, foreseeable with
`--plan`, refusing WHOLE. The owner's order puts it after the new system stands at 100%, which is
exactly where the field puts it: every migration tool below shows the plan before it moves a byte.

## The field

| system | what it teaches | taken here |
|---|---|---|
| Strangler Fig (Fowler) | the new system grows around the old, one piece at a time | the census names every piece; a row takes one |
| Parallel Change / expand-contract | expand, migrate, contract, never all at once | `moves` expands into a plane; `retired` is the contract, taken later at a door |
| Flyway / Alembic / Liquibase | changesets are declared, ordered, reviewed; `info`/`validate` read before `migrate` | the map is a reviewed declaration; `inherit` is the `info` |
| `terraform import` + `moved` blocks | pre-existing resources enter managed state by one declared mapping each; two sources to one address is an error | a row per mapping; two paths to one destination refused |
| Kubernetes server-side apply | adopting unmanaged objects records WHO owns WHICH field; a conflict is an error unless forced | the map is signed; a conflict is refused, never resolved silently |
| jscodeshift / OpenRewrite | a transformation is a declared recipe, dry-run diff first | the vocabulary is the recipe grammar; the roster is the dry run |
| Nix Home-Manager | refuses to clobber an existing dotfile; backs up only on an explicit flag | measured: "the kit installs here", "destination already exists" — no clobber is ever inferred |

## Rejected alternatives

- **A heuristic classifier over names** (`*.md` under `agents/` → role, `hooks/` → gate). It is
  the precise lie this framework exists to prevent: a class inferred from resemblance, wrong in
  both directions, and invisible when wrong. It also privileges one runtime's conventions.
- **A kit-shipped catalog of known prior systems** (".claude means X, .codex means Y"). A closed
  enumeration of products inside the kit, a second home for every host's layout, and stale the
  day a new runtime appears. The runtime descriptors carry no native paths, and must not.
- **A default disposition for the unanswered** ("everything unmapped is retired", or "is kept").
  A default is a judgement nobody signed; ambiguity resolves to nothing, so it is `undecided`.
- **Letting measurement decide where the map is silent** (byte-identical ⇒ superseded). Two
  homes for one decision and a precedence ladder between them; identity of bytes proves what the
  kit ships, not what the host intends.
- **Folding the reading into `adopt`.** `adopt` answers "may this kit install here", a gate
  that refuses; this answers "what becomes of the prior system", a census that counts. One verb,
  two reasons to change.

## Consequences

- The second host can be read today; its roster without a map shows exactly how little the
  kit's own boundary sees, and with a map shows every path, counted.
- The census reads the FILESYSTEM, not a VCS index: untracked and ignored bytes inside a prior
  root (bytecode caches, for instance) are census members. This is honest — they exist and a
  takeover meets them — but it is an OPEN GAP: `GAP-CENSUS-EXCLUSION`, whether a boundary may
  declare exclusions, and in what grammar, is decided with APPLY.
- `GAP-MAP-RESIDENCE` (where the map lives in the host, and the door that accepts it) is the
  first act of the APPLY slice.

## Fitness functions

`tests/acceptance/fresh-repo/test_succession.py`, `test_231`–`test_243`, over a FIXTURE prior
system (never the real host). Every one was shown to deny under a named mutation of the reader.
The instance-vocabulary scan (`test_71`) already holds the interpreter to reading dispositions and
field names from the declaration, never spelling them.
