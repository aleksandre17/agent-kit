---
kind: decision
authority: canonical
owns: starting-a-host
---

# ADR-023 — A new host starts in one door, and is served to the field's standards

- **Status:** accepted (2026-10-16, owner-delegated)
- **Deciders:** the owner's delegate, on the owner's instruction that the kit be a working framework a
  new project receives whole, judged against current practice from outside and not by its own rules.
- **Amends:** ADR-013 (serving a runtime): what the briefing carries and how a hook fails.

## Context

Each new project needed seven acts and two hand-written JSON declarations before `check` went
green: `init` twice, `take` per adapter and bundle, editing the answer to enable them, writing a
runtime descriptor per surface, `render`, and `activate`. An external audit then held the kit
against current practice (AGENTS.md, Agent Skills, OWASP LLM06, OpenSSF Scorecard, Diátaxis) and
found, among other things:

- the served briefing told an agent nothing about how to build or test the project, and on a fresh
  host it served the laws seed's own authoring instruction ("Delete the sentence you are reading")
  as if it were a law;
- the Claude Code and Codex hooks ran a bare `python`, so a machine without it ran no judge at all:
  in Claude Code a non-2 exit does not block, so the gate failed open;
- nothing stopped an interactive session from hand-editing the pinned kit or a generated page; it
  was caught only later, by `check`;
- the kit's own suites ran in no CI, and the one workflow template pinned its action by tag;
- the verb table in `kit/README.md` listed 11 of 21 verbs, and the README said "day one".

## Decision

1. **Starters.** A starter is a document published beside the kit (`starters/<id>.json`, schema
   `starter`) declaring what a new host takes, which runtimes it serves and which surfaces it
   activates. Verb `start --path <starter> --approve <who>` walks it as the verbs a person would
   run, each a separate run of the same kit, printed with its exit; the first failure stops the walk
   (`KIT0073`), and what landed stays because each act is safe to repeat. One door, one name on
   every act. Activation precedes the attesting `init`, whose closing `check` must not meet a served
   setting not yet pointed at what it serves. A starter decides what a host RUNS, never what it
   HOLDS: laws and stances stay unanswered and are named as such. `standard` serves Claude Code,
   Codex (AGENTS.md, which most other agents also read) and git, takes the cardinals and the
   conduct, and activates the commit gate.
2. **Commands in the briefing.** Projection `.agents/generated/evaluation/COMMANDS.md`, one line per
   consumed reading (`build-command`, `test-command`), inlined in the briefing. Detector
   `stack-kit-commands` reads `stack-kit.json` `commands.test` / `commands.build` as the host
   spelled them; an undeclared command is named as undeclared, never invented. The laws seed no
   longer serves authoring prose: an HTML comment and "No project law is declared yet."
3. **A plane is written by its writer.** Gate kind `plane-held-by-its-writer` (`FF-PLANE-WRITER`,
   floor enforce) refuses an edit inside the `vendor` and `projection` planes from the runtime
   classes it names (`an-interactive-session`), with the verb to run instead. The judge learns the
   writer's class from the runtimes served through the surface (`attestation.classes_through`). A
   batch writer (a commit, CI) carries what the plane's own verb wrote and is judged by `check`; a
   writer of unknown class is judged, never exempt.
4. **Hooks fail closed.** The Claude Code and Codex hook commands probe `python3`, `python`, `py`
   as the git hook does, and refuse with the surface's refusal exit when none runs.
5. **Pinned by commit.** The github-actions template pins `actions/checkout` by full SHA (v6.1.0,
   verified with `git ls-remote`). The kit's own suites run on Ubuntu and Windows, Python 3.10 and
   3.13 (`.github/workflows/tests.yml`, owner-authored).
6. **The verb table is derived.** `kit/README.md` carries the table between markers, built from
   each verb's `SUMMARY` and `MUTATES`; `test_verb_reference` fails when it drifts. The README
   is rewritten: what the kit gives, a quick start through `start`, a glossary of the kit's words
   in common terms, and an honest status.

## Considered options

- *A bootstrap script outside the kit* — rejected: a second home for what each verb already owns,
  and nothing would hold it to the verbs' doors.
- *`start` calling the verbs in-process* — rejected: the composition changes after each `take`, and
  a run holding one manifest would be judging a host that moved under it. A separate run per act is
  exactly what a person runs.
- *A starter that also writes stances* — rejected: a stance is the host's own word (doctrine
  schema), and a published default answer reads as one the host gave.
- *A detector that guesses build and test commands from a `.sln` or `angular.json`* — rejected:
  the verification page has always refused to invent a way of proving a change; the cure is a
  declaration a detector reads.
- *Refusing every edit to a kit plane, including commits* — rejected: it refuses the commit of every
  `upgrade`. The writer's class is what distinguishes a hand edit from a verb's output.
- *A separate `agents-md` adapter* — rejected for now: AGENTS.md is already the codex adapter's
  render, and two adapters rendering one target would be two homes. `CLAUDE.md` importing
  `@AGENTS.md` is the remaining step if the two briefings ever need to diverge.

## Not decided here (the owner's)

- A licence: until one is declared the kit cannot legally be adopted outside the owner's work.
- Signed releases and a signed lock (`release` still reports authenticity NOT ESTABLISHED).
- Whether `--approve <who>` must be backed by a signature: today it records a name, and an agent the
  owner delegated to can give it. The judge could refuse `--approve` from an interactive session
  unless the host declares the delegation.

## Proof

Acceptance `test_start` 407–409, `test_commands` 412, `test_enforcement` 289c–289d; unit
`test_verb_reference`. Each mutation-checked: door removed, capability check removed, plane gate
emptied, bare-python hook restored.

## Amendment 1 — a walk is observed through its acts (2026-10-16, owner-delegated)

Walked on its first real host -- one that had already answered -- `start` stopped at its first act:
`init`'s closing `check` failed `FF-RUN-RECEIPT` on `start`'s own record, open because `start` was
still running. On a fresh host the walk had passed only because an unanswered host is watched by
nothing, so the parent run opened no record.

**Decided:** a verb that carries out its writes as separate runs of the kit declares `DELEGATES`; the
run reading carries `delegates`, and both run-receipt observations declare `"delegates": false`.
Each act keeps its own record. `start`'s two in-process writes (the answer's set, the runtime
declarations) are each one atomic write of a declaration the next walk writes again.

*Rejected:* naming the parent's record to the children as in flight (an environment variable any
process could set, hiding a dead run's evidence from `check` -- an exemption no declaration can
see); closing the parent's record before the walk (a record stating an end that had not happened).

Proof: `test_start` 410 (a host walked twice ends green), mutation-checked.

## Amendment 2 — what the first real host found (2026-10-16, owner-delegated)

Walking `start` on the GeoStat host, and then writing its own text into the entry files, found:

- **A host's own edit failed `check`.** The served record digested the whole entry file, so the
  host's edit outside the kit's span left `SERVED.json` unreproducible (`FF-KIT-PROJECTION`) until
  someone ran `render`. A spanned row now records only the span (`span_sha256`, `seed_sha256`) and
  no whole-file `sha256`; the record's paths and its digests are read apart (`prior_rows` for the
  paths a plan and the probe need, `prior` for the files the kit served whole).
- **The entry seed spoke to the owner in the agent's context.** Its paragraph is now one HTML
  comment; claude-code and codex 1.3.1.
- **"No bundle is installed"** was printed on a host that had taken two (fixed in `79af0df`).
- **A gate refused its own declaration.** The first host's `no-connection-string-password` reaches
  every path, and its `proves` is a password: the commit that declared it was refused. The edit-gate
  declaration is no longer judged by the gates it declares (`declared.homes`); `check` still holds it to
  its schema and calibration. `test_enforcement` 289e.
- **A release source had to be on this machine.** `--kit git+<repo>@<rev>` ran `git -C <repo> archive`,
  so a published URL was refused. A repository that is not a local directory is cloned bare into the
  run's scratch first; the revision is still read with `git archive` and refused unless it equals its
  lock. `test_pinned_kit` 279b.
- **Owed, designed, not built: skills.** The conduct bundle's `skill` and `playbook` records are served
  only as roll entries. Their form in the field is the Agent Skills format (`SKILL.md` with `name` and
  `description`), which Claude Code reads under `.claude/skills/<name>/`. The shape: an optional `body` on
  a cardinal record of those genres, a projection per record into `.agents/generated/skills/` (the drawn,
  pending row), and a `skills` view each runtime adapter renders where its product reads skills.

*Rejected:* re-rendering the record on every `check` (a gate that writes is not a gate); keeping a
whole-file digest beside the span's for the departing case (a host's file is never removed on the
strength of its own text matching an old digest -- a departing spanned file is withdrawn by its span).

Proof: `test_entry_files` 341b (the host edits its own text, `check` stays green without a render),
mutation-checked; `test_serving` 258 reads a spanned row by its span.

## Amendment 3 — a rule true of every host is written once: policies (2026-10-16, owner-delegated)

The owner: ten projects must stand on one architecture, its principles, structure and organisation,
and nothing that is true of all of them may be written by hand in each. The doctrine already travels
that way (bundles); the edit gates did not. GeoStat's first gates mixed two kinds: what only GeoStat
knows (BioStar is read-only, DDL lives in its migrations folder) and what every repository holds
(no committed key or token), and the second kind would have been copied into every host.

**Decided:**
- `policies/<id>/`, beside `adapters/`, `bundles/` and `starters/`: a published capability whose documents
  keep the `edit-gate` contract. Enforcement already reads every such document an enabled capability
  ships (`{"validates": "edit-gate"}`), so a taken policy binds at every edit and every commit with no
  interpreter change. First policy: `secrets` 1.0.0 -- private keys, cloud access key ids, platform
  tokens (the widely published token shapes, narrowed so a placeholder or a public key is admitted).
  The `standard` starter takes it.
- Host text gates do not judge the publisher's planes (the pinned kit, every taken capability): those
  bytes are held by their digests (`pinned-kit-intact`, `taken-intact`), and a policy carries, as each
  gate's `proves`, the very text it refuses -- judged, the commit that takes it would be refused.

*Rejected:* a kit-shipped default gate set (the issued kit carries no policy, ADR-004; a host holds a
rule by taking it); putting policies in `bundles/` (a bundle is doctrine, answered by stances; a policy
is enforced, not answered); a host-side copy of the shared gates (ten copies, ten drifts).

Proof: acceptance `test_policies` 413 (contract and calibration of every policy), 414 (a started host
commits its own install and is refused each forbidden text at the commit), mutation-checked.

## Amendment 4 — a new product, a new kind of evidence: by declaration (2026-10-16, owner-delegated)

The owner: a new driver, a new language, a new product must be addable without touching the kit --
SOLID, open by declaration, no closed sets. An independent read-only audit found the interpreters free
of product names, and three places where extension still needed a kit edit:

- **Evidence kinds were a literal dict** in the probe. They are now discovered (`kinds.registry` over
  `interpreters/evidence/`): a new kind of evidence is a module, and the probe is not edited.
- **Detectors came only from the release's hand-kept list**, so a product's reading had to live in the
  core (`stack-kit-commands` did). A composed capability now brings detectors as documents under the
  `detector` contract; one id, one detector. `stack-kit-commands` moved to `adapters/stack-kit/` (the
  standard starter takes it), and a core `declared-build-script` keeps the build reading measurable on
  a host without it. `start` re-reads the reading after its takes (`retake`), since a take may bring a
  detector. On a host that has already accepted its answer the walk skips its two opening `init` acts:
  they would judge, before the walk could retake it, a reading the walk is about to replace
  (`test_start` 411; found on the first host, whose reading the moved detector made stale).
- **A hook could refuse only by exit code.** A surface may declare the decision text a product reads on
  stdout (`hands.refusal.stdout` with `{reason}`, `hands.admission.stdout`); the judge then writes every
  line of its own to stderr, and the entry point writes the judge's header there too
  (`STDOUT_IS_THE_PRODUCTS`).
- **Guard:** interpreters are imported flat, so two modules with one name would shadow each other
  silently; `test_one_name_one_module` refuses it.

*Rejected:* giving `declares.detectors` (a list of release detector ids) a second meaning as file paths;
moving every ecosystem detector out of the core now (it changes every host's reading at once -- owed
below, with a migration); a product-specific branch in the judge for stdout decisions.

**Owed (measured, not built):** the hand-kept dispatch tables that the discovery doctrine says are rows
(`init.INSTALL_MODES` with `space.MODES` a second home, `projection.PROJECTION_SHAPES`,
`collection.READER_KINDS`, `attestation.EVENTS` with its order-dependent `REFUSED_WRITE`,
`resolution.KINDS`); core modules importing concrete ports (`projection`, `activation`, `spans`,
`succession` → `runtime`; `returns` → `dispatch_port`; `accepted` → `vcs`); "the plane of class X" looked
up in five copies (one `manifest.plane()` accessor); large modules (`dispatch_port` 896 lines, `corpus`
755, `init` 620); the core's ecosystem detectors (dotnet, node, pnpm, go, python) moved to published
bundles with a reading migration; skills (amendment 2).

Proof: acceptance `test_commands` 412b (a taken adapter's detector is read and served; none of its ids is
in the core), unit `test_judge_decision`, `test_one_name_one_module`; mutation-checked (composition
removed, stdout routing removed). `test_detectors` covers the discovered evidence kinds.

## Amendment 5 — every dispatch table is a discovered registry; the core reaches ports only through the root (2026-10-16, owner-delegated)

The owner: finish the kit to the standard it claims -- open by declaration, no closed sets, one source
of truth. Amendment 4 measured what was still owed; this amendment pays it.

**Decided:**
- **Registries, discovered** (`kinds.registry` over a family directory, the mechanism gates, proofs and
  units of spend already used): install modes (`installmodes` over `modes/`; `space.MODES`, the second
  home, removed), projection shapes (`shaping` over `shapes/`), reader kinds (`collection.readers` over
  `readers/`), resolved views (`resolution.registry` over `resolvers/`). A new kind of each is a module.
- **Events are declared by their provider.** `attestation` holds no event table; the verb that observes
  an event publishes `EVENTS` (the judge: `a-refused-write`) and passes its evidence in.
  `test_events_are_provided` holds every `observed_on` to a provider.
- **The core reaches a port only through the composition root** (`cli`, `context`). The served projection
  was a port in name only: its rendering is the `served` shape (`shapes/serve.py`) and its record a core
  module (`serving`); `admission` (pure judgement) moved into the core; HEAD readings are methods of the
  workspace port (`accepted` removed); the release source -- git, archive, scratch -- is a port
  (`ports/sources.py`); the kit's own tree is reached through `manifest.files()` / `manifest.kit_at()`.
  Host #0's arrow declares the `root` and `plugins` layers, and `test_kit_holds_its_arrow` refuses a core
  module that imports a port (mutation-checked).
- **One accessor for a plane:** `manifest.plane(class)`, five copies removed (KIT0006 moved with it).
- **Large modules split by responsibility:** `dispatch_port` (896) into `dispatching` (what a dispatch is,
  read without starting one), `taskrecord` (the record) and the port (the acts); `corpus` (755) into the
  reading, `routegraph` and the `corpus-reading` resolver; `init` (620 -> 487) by moving its modes out.
- **The core reads no ecosystem.** The dotnet, node, pnpm, go and python detectors are published adapters
  (`adapters/<toolchain>/`, 1.0.0), taken by the standard starter. *Reading migration:* a host's reading
  drops those facts at the next `retake` unless it takes the adapters; `start` takes and retakes in one
  walk, and nothing in the kit consumes the facts.
- The boundary sensor reads a discovered registry's keys as provided terms (a deferred mode has no
  behaviour and is still the machine's own row).

*Rejected:* one `registry.py` with every table in it (a second home for each subject, and one module edited
for every new kind); keeping `ports/runtime.py` and allowing base->ports (the arrow would certify the
coupling it exists to refuse); one `ecosystems` adapter for five toolchains (five reasons to change in one
declaration).
