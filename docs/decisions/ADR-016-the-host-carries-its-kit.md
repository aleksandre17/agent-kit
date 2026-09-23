# ADR-016 — The host carries its kit: a runnable pinned copy, and what a release is

- **Status:** Accepted (2026-09-13; owner-delegated under ADR-015, link B)
- **Amends:** ADR-001 Part VI (arrow ① — the payload crosses as vendor + lock) by BUILDING it;
  ADR-008 (provenance) by naming where the kit's own signature will sit, still unbuilt.
- **Relates:** ADR-002 (estate) · ADR-004 (what the payload distributes) · ADR-005 (codes) ·
  ADR-006 (stance) · ADR-009 (schema versions) · ADR-015 (the whole line; "one body")

## Context

ADR-015 measured it: installed on a clean host, `.agents/kit/` held nine doctrine pages and **no
interpreter**. Every host was driven from OUTSIDE — `python <framework>/kit/interpreters/cli.py
--root <host>` — so a host could run nothing by itself: no `check` in CI, no edit-time hook, no
offline upgrade. Link C (the enforcement line) cannot exist until this holds, which is why B is
next on the line.

The kit already states what it IS: `kit.lock.json` enumerates every path (the declaration closure
plus the interpreter and prose accounts) with its digest. What was missing was the other half of
the drawn arrow — the host receiving that whole payload, and a word for *which* kit it received.

## Decision

1. **The pinned kit is an INSTALL, declared — not a special path in an interpreter.** `governance`
   declares `{"mode": "pinned", "class": "vendor", "target": ".agents/kit/pinned/"}`. `pinned` is a new row
   in the open `INSTALL_MODES` registry (foresee + apply) and a new row in `stewardship.json`
   (`pinned → release`, a steward whose tree is REPLACED WHOLE and never merged). A dedicated target,
   not the plane root: the vendored doctrine pages already live under `.agents/kit/doctrine/`, and a
   pinned tree interleaved with them would need an exemption list — a privileged path.
2. **The payload is exactly what the lock enumerates, verbatim, beside the lock.** `pin.deliver`
   copies every path the kit's survey accounts for and writes the lock next to them, through a new
   port primitive `Workspace.write_tree`: the tree is staged in a sibling and swapped in by rename,
   so a reader never sees a mixture of two kits. A kit that cannot state what it is (a path
   missing, unaccounted or CRLF) is REFUSED, never pinned partially.
3. **A release is a kit whose bytes equal its own lock; its identity is the SHA-256 of that lock.**
   A released kit pins its own lock byte for byte. A working tree — a fixture, an uncommitted
   change, a kit a host composed by taking adapters — pins a fresh reading labelled
   `X.Y.Z+unreleased` (PEP 440 local version / SemVer build metadata). The label is written INTO
   the pinned lock; equality with a labelled lock is INTEGRITY, never promotion to a release.
4. **Integrity is measured; authenticity is declared absent.** Gate `FF-KIT-PINNED`
   (`pinned-kit-intact`, floor `enforce`) judges the pinned tree against the lock it CARRIES —
   never against the kit that installed it — and names each path with its survey state. Every
   surface that states a release prints `authenticity NOT ESTABLISHED (the kit's own lock carries no
   signature)`.
5. **The pinned copy never re-stamps itself.** Run from `.agents/kit/pinned/`, `init` over an intact
   pinned tree is `keep`; over a changed one it is refused (`KIT0041`) in the PLAN, because
   re-reading a changed tree into a fresh lock would launder the change. The cure is to deliver a
   release over it.
6. **The release artifact is stated by a verb, and read at a revision.** `release` (writes nothing,
   subject = the kit) prints version, full lock digest, path count, the moment the lock was read and
   the authenticity sentence — or refuses a working tree by name. `--kit` accepts a release SOURCE,
   `git+<repo>@<rev>#subdirectory=<dir>`, read with `git archive` at exactly that revision into a
   scratch directory removed after the run; a revision whose tree differs from its own lock is
   refused.
7. **Every run says which kit spoke.** The first line of every run ends `· kit at <root>`. A host
   running its own copy and a host driven from a working tree otherwise read identically.
8. **The framework repository is host #0** (ADR-015, "one body"): it carries its own pinned kit,
   installed from a revision of itself, and runs its verbs from that copy.

## Rejected alternatives

**A. Pin into the plane root (`.agents/kit/` IS the kit), with an exemption list for the doctrine
pages.** This is the literal reading of the blueprint and was the orphaned draft's design (`keep`
sets). Rejected: the pinned tree's own survey would report the doctrine pages as unaccounted, so
every reading would need a list of paths "another declaration accounts for" — a privileged,
hand-kept exemption inside the one tree whose premise is that nothing is exempt (Cardinal II). The
duplication the literal reading avoids is real and is recorded below as a gap, not hidden.

**B. Record each pinned file as its own estate row (a vendor row per path).** Rejected: 150 rows
restating what the pinned lock already states is one truth with two homes (Cardinal III), and the
three-way reconciliation would re-decide, path by path, a question that has one answer — the tree
is the release or it is not. The lock inside the tree is the one home; the estate records the
install.

**C. Install as a package (`pip install` / a wheel / a zipapp) instead of a vendored tree.**
Rejected: it needs an index or an installer the host must trust and a network the kit cannot stand
behind, it hides the payload from the host's own review and diff, and it breaks the drawn crossing
(① vendor + lock, reviewable in the host's own history). `go mod vendor` + `go.sum` is the proven
form for "the dependency lives in the repository and is checked against its lock".

**D. Sign the lock now with a generated key.** Rejected as an owner door: real authenticity needs
key custody (who holds the private key, where the public key is published, how it is rotated) and
the kit hand-rolls no cryptography. A key an agent generated would print `authenticity
ESTABLISHED` over a trust root nobody chose — the surface lying in its most convincing form.

## What is partial, with the missing part named

- **Authenticity — NOT BUILT (owner door).** The seat is named: a detached signature over the
  lock (`kit.lock.json.sig`), verified through the verifier registry ADR-008 already declares
  (argv + namespace + a host trust root, e.g. `ssh-keygen -Y verify` against
  `.agents/project/allowed_signers`). Missing: the owner's key, its publication, and the decision to
  trust it. Until then every surface prints NOT ESTABLISHED.
- **The changelog delta on upgrade — NOT BUILT.** `CHANGELOG.md` lives outside `kit/` and is never
  vendored, so a fetched release source (`#subdirectory=kit`) carries no record. Missing: a declared
  record location inside the release source and the `upgrade` surface that prints the sections
  between the pinned version and the target (apt-listchanges' question).
- **A host that TAKES adapters pins a composition, labelled `+unreleased`.** Taking an adapter edits
  `MANIFEST.json` (ADR-014's door), so the composed kit is never byte-equal to the release. The
  pinned lock keeps provenance's meaning of "issued": every path the source's own lock did not
  issue is carried, digested and accounted `not-issued`, so a taken capability is still TAKEN when
  the pinned copy speaks (the first draft absorbed them and reported every pin WITHDRAWN — found on
  the live walk of host #2, `test_280`). Missing: the release identity of the CORE surviving the
  composition — "release 0.1.5 + two taken capabilities" — which needs taken capabilities declared
  outside the issued `MANIFEST.json`.
- **The estate records the pinned install with a null digest.** The release identity lives in the
  pinned lock (one home), so reconciliation cannot tell a host-edited pinned tree from an upstream
  change and `upgrade` re-delivers the tree whenever it runs; integrity is judged by the gate
  instead. Missing: a per-mode "measured through" digest (the row's digest = the pinned lock's)
  so the three-way reading covers the pinned tree.
- **The doctrine pages are a second copy.** `.agents/kit/doctrine/*.md` restate files now present
  in `.agents/kit/pinned/capabilities/*/payload/`. Missing: serving doctrine FROM the pinned kit
  (link C/E), after which the vendored pages go.
- **The two-rename swap has a gap.** Between moving the old tree aside and the new one in, a killed
  process leaves `.pinned.<pid>.kit-old` and no target — never torn, and `FF-KIT-PINNED` then fails
  with "no pinned kit"; but the residue itself resolves to the vendor plane's class, so no gate
  names IT (unverified whether a reconciliation does). A single atomic exchange (`renameat2(RENAME_EXCHANGE)`) is POSIX-only and already on
  ADR-015's post-1.0 list.

## Relation to ADR-015 amendment 1 (the drawing is the floor)

Read at ~13:50 on 2026-09-13 as an UNCOMMITTED edit to ADR-015 in the working tree (not made by this
slice, and not staged by it): every path in the Part VI drawing must exist in its drawn place by its
drawn name, and link **L** carries that. The drawing places the pinned copy AT `.agents/kit/` and the
lock the host was given at `.agents/project/kit.lock.json`. This ADR's `.agents/kit/pinned/` (with the
lock inside the tree) is therefore a **scaffold, not the destination**: the target is ONE declaration
(governance's `pinned` install) and the lock's seat is one field, so L moves both without touching the
mechanism. Alternative A was rejected on the CURRENT upstream layout — doctrine pages vendored beside a
kit that has no `kit/doctrine/`. Once the drawn upstream `kit/doctrine/` exists, the pages ARE part of
the pinned tree, the interleave disappears, and so does the second copy named above.

## Consequences

- A host runs `python .agents/kit/pinned/interpreters/cli.py <verb> --root .` with no framework
  checkout on the machine. Link C can now point a hook, a CI job and a runtime at ONE interpreter.
- Every approved host gains one install, one steward row, one gate and ~150 vendored paths; the
  kit's version is 0.1.5. A host installed by 0.1.4 fails `FF-KIT-PINNED` until it upgrades — that
  failure is the true statement "this host cannot run a verb by itself".
- New diagnostic `KIT0041`. `lock.schema.json` widens `kit_version` to admit a local label —
  additive: every document valid before remains valid (ADR-009 expand).
- Fitness functions: `test_273`–`test_280` (`tests/acceptance/fresh-repo/test_pinned_kit.py`).
- **Host #0 runs without `knowledge`** (`--disable knowledge`, a reversible host choice). Its seed
  would write `docs/decisions/ADR-0001-…` beside this repository's `ADR-001…016` — two numbering
  schemes in one declaring folder — and its kind gate would, by its declared patterns, judge
  `docs/reference/STANDARDS-LEDGER.md` (a `CANON-` name in a kind that cannot declare; predicted from
  the declaration, not run). Both are link E's to settle; neither is hidden by the choice.
