# Changelog

Upstream only. This file is never vendored into a host: an append-only release record grows with
the framework's age rather than the host's needs. A host's legitimate question is narrower — *what
changed between the version I have and the version I am moving to* — and it is answered at the
moment of need by `upgrade --plan`, which names every path that changes between the two.

## 0.4.1 — 2026-10-18

**Fixed — a release that changed a bundle moves its version**
- engineering-standards 1.3.0: 0.4.0 added the security chapter's silent-loss standards (OWASP A09/A10:2025,
  CWE-222/223/390/636) and kept the bundle at 1.2.0, so a host that held 1.2.0 could not take it -- a take
  refuses changed bytes under a pinned version (KIT0032), as it must.
- A test holds every published capability to this before release: one whose bytes moved since the last
  release tag and whose version did not is refused (`tests/unit/test_release_versions.py`).

## 0.4.0 — 2026-10-18

**Added — a stopgap is declared debt, a gate is met at what it guards (ADR-024 amendment 1)**
- engineering 1.2.0: three MUST rules -- `a-stopgap-is-declared-debt` (enforced by the new policy's edit
  gate), `a-gate-is-met-at-what-it-guards` and `quality-never-regresses` (both enforced by review against
  the engineering-standards catalogue); `decisions-recorded` is raised to MUST, enforced by FF-WORK-CLASSES.
- A decision a card owes keeps its kind's declared shape (`kinds[].shape` in the record-keeping vocabulary,
  after MADR, Nygard and ISO/IEC/IEEE 42010): the question, the options and why the rejected lost, the
  decision, its consequences and at least one source weighed. It holds cards in a working state, never a
  decision a card already landed on; FF-WORK-CLASSES names what a short decision lacks. Every address moves to 1.2.0; a host
  re-addresses its stances when it takes the bundle.
- Policy `declared-stopgaps` 1.0.0: an edit introducing one of the stopgap comment tags its gate lists
  (`policies/declared-stopgaps/payload/edit-gates.json`, the tags' one home) without a tracking reference
  on the same line (`ABC-123`, `#123`, `card: <id>`) is refused; prose and code that only use the words
  are admitted.

**Added — nothing is lost silently (ADR-024 amendment 2)**
- engineering 1.2.0: MUST `nothing-is-lost-silently` -- a cut says how much and where the whole is kept, an
  error is handled or propagated, an unreadable input is NOT MEASURED or refused, a step that ran nothing is
  not counted as run (CWE-222, CWE-223, CWE-390, CWE-636; OWASP A09/A10:2025), enforced by review. The
  engineering-standards security chapter names the standards and what each asks.
- KIT0093 (a detector's evidence is there and cannot be read) and KIT0094 (a peer's recorded write cannot be
  read): each refuses where the kit read the input as absent.

**Fixed — found by an audit for that class**
- `check --brief` names every passing gate whose lines it leaves out (NOT MEASURED, a reading's counts).
- `start` keeps every act's whole output in the observed plane (`start.log`), shows the closing check's own
  verdict, and checks once: the closing `init` already ends in `check`, and a second one on the same bytes
  proved nothing new. It says which runtimes it wrote and which of the host's own it kept.
- `trial` fails a run its oracle cannot judge (an uncalibrated gate), stops on a fixture act that fails, names
  every failing gate of the fixture's check, and removes its scratch whole (git's read-only objects once
  left it behind); `memory` names a note an uncalibrated gate could not judge.
- The cost frontier counts a run that reported no token count as unmeasured, never as 0: the cost it shows is
  a floor, and every budget measure is not measurable while any run or task record is unread.
- A test report counter that does not parse is unreadable, never 0 failures; a malformed JSON file a detector
  reads refuses the reading; ledger lines, transcript lines, route documents, context pages, budget rows and
  module maps that cannot be read are counted or named; `doctor` judges a hook through the entry point the hook
  runs, never the kit's own in its place, and prints why a dead one did not refuse.
- `upgrade --mode laws` names every line the retired page holds outside its numbered laws before removing it.
- Cuts state what they cut (`pin`, review errors, an eval's repeated task); signature evidence is kept whole.


## 0.3.1 — 2026-10-17

**Fixed — a hook's git environment no longer redirects the kit's reading of another repository**
- The version-control port runs git without the variables git calls repository-local
  (`git rev-parse --local-env-vars`: `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE` and their kin), as git's
  own submodule code does. Git exports them to a hook run from a linked worktree, and `-C` into the kit's
  submodule then read the superproject: FF-KIT-PINNED saw the host's HEAD where the kit's stood, and the
  push gate refused a clean push. `sources` (a release read at a revision) runs git the same way.
- `kit/VERSION` states 0.3.1 again; 0.3.0 shipped it at 0.2.0 beside a manifest at 0.3.0.

## 0.3.0 — 2026-10-17

**Fixed — a re-audit's four logic defects; the trust model said as it is (ADR-025 amendment 5)**
- FF-WORK-SIGNED: a door walked twice is held by its LATEST mark (`signing.holds`), never by an earlier
  signed walk -- a later unsigned passage in the owner's name fails (N1).
- `prove`: everything runs every area's `proved_by` and `default_proved_by` as published, with the MUSTs'
  commands, each once -- never weaker than a scoped proof (N2); the work-class catalogue is read at the
  published base, as pushed only where it is absent there, said so (N5).
- `prove --pushed` refuses a pushed sha that is not HEAD or a working tree that is not clean, `--full`
  included: it judges the working tree.
- `areas`: a root module waits for the kit planes; a drafted area carries `drafted_as` (delivery-areas
  schema) and is redrafted while unedited; an area the host wrote is never touched (M3/N4).
- github-actions 1.6.1: the workflow runs `prove --full` on the checked-out commit. Hooks are feedback; CI,
  required by branch protection, is the authority; the proof cache is a local speed-up CI never reads.

**Fixed — a push can no longer go out green with a red or unproved change (ADR-025 amendment 4, review)**
- `prove` reads areas and commands as the published side holds them; a narrowed `proved_by` /
  `default_proved_by` or a removed or rewritten command is loosening (`weighing.loosened`).
- Downstream areas (`feeds`) are proved with the change; a MUST holds only where its own enforcer ran.
- The pre-push hook passes the pushed refs (`prove --pushed`, git adapter 1.6.0); a pushed sha that is
  not HEAD, or an unreadable range, is proved by everything.
- A proof record is honoured only when it names the same command, tree, kit version and declarations.
- `proof_for` no longer raises when no class owes a decision; it proves by everything and says so.
- `areas`: the root module excludes claimed paths whole; the kit planes are one costly area (drafted once
  the areas are committed); marker module maps (java 1.1.0, node 1.1.0) draft modules and their commands.
- `check --brief`: a gate's own lines appear only with its header.
- `retake --approve` renders what it serves, as `init` does.
- FF-NORMS reports a stance a new bundle version orphaned (`NT-READDRESS`); `upgrade --mode addresses`
  re-addresses it at the owner's door.
- The kit's own asserted prose (setup blueprint, upstream layout, verb table) is proved by `host:unit`.
- The commit floor (`message`, `weigh --each`, an emergency's debt) weighs the proof commands too: a commit
  that rewrites or removes a host's command is loosening, as at `prove` (`workclass.commands_at`).
- `prove` reads the MUSTs, and the enforcers they name, as the published base held them: a push cannot drop
  the enforcer that would prove it; a norms file absent there is read as pushed, and said so.
- `areas`: the kit planes hold the repository's own metadata files the vcs port names (`.gitmodules`,
  `.gitattributes`, `.gitignore`).
- With no repository to ask, a `glob_any` walk passes over the kit's own planes, a vendored kit, a nested
  repository and the directories a detector names in its new `prune` (java 1.1.1, node 1.1.1:
  `node_modules`, `target`, `build`); a glob's `[...]` class is read as one character.
- `docs/guide/setup.md` §2: a card's walk `intake -> shaped -> in-flight` with its JSON; `weigh --path` is
  comma-separated; `--each` needs `--head`.

**Added — proof is weighed as the work is (ADR-025 amendment 4)**
- An area declares what proves it (`proved_by`, and `default_proved_by` for paths no area claims).
  `prove` weighs what the push carries and runs only what the touched areas declare -- `check` alone for
  prose. A change owing a decision, an area that declares no proof, a host that weighs nothing, or
  `--full` runs every command a MUST names; it says which, and why.
- Verb `areas`: a host's areas drafted from the modules its build tool declares (a MODULE MAP its adapter
  publishes: stack-kit's, 1.3.0) -- one per module, proved by its own tests; the tool's declarations
  (costly); prose (check alone). It only adds; writing is a door; `start` walks it.
- With no area's proof and no MUST, `prove` runs the test command the host's reading declares.
- Adapter `java` 1.0.0: a Maven project (pom.xml) and a Gradle project (build.gradle*) are read as
  `stack.java`; the standard starter takes it.
- A host declares its own proof commands in its delivery policy (`commands`, vouched as `host:<key>`),
  and an area's `proved_by` runs whether or not a MUST names it; the kit proves itself with them.
- `check --brief`: what fails and the summary only -- the listing an agent reads. The agents' skill
  (kit-skills 1.3.4) opens a card with a verb and its shape, says what to report when no test
  command is declared, never weighs a guessed path, and leaves an ADR `proposed` for the owner
  (found by measuring an agent across five classes of task: all five walked right).
- `check` says what judging cost, every run: how many gates, how long, and the three slowest.
- Nothing is proved twice on the same bytes: a command green on a clean tree is remembered by that
  tree's id and not run again while the tree is the same; any change, a dirty tree or `--full` runs it.
- Cardinal IX (cardinals 1.1.0) -- every cost follows the change it serves: ceremony, proof, review,
  context and waiting are computed from the change and grow only with its risk; both directions, too
  heavy and too light, are defects. Every cardinal's address moves to `cardinals@1.1.0#…`.

**Added — an owner's mark is a signature, not a name (ADR-025 amendment 3)**
- Verb `signer`: where owner signing stands; `--setup`, the owner's own act in their own terminal --
  git and ssh-keygen checked, the key made by `ssh-keygen` (which alone asks for the passphrase),
  refused if it opens without one, registered in the host's allowed-signers file (seeded by
  `delivery`), git told how to sign, a sign-and-verify round trip, the fingerprint to compare.
- FF-WORK-SIGNED: where the host declares `owner_signing`, a door's mark holds only where a commit
  the principal it names signed INTRODUCED it (the record diffed against the commit's parent),
  verified by git against the trust root as accepted at that parent -- never the file the tree holds
  now; the first root naming a principal is the bootstrap, trusted on first use, and a change to who
  may sign holds only when a signer the parent allowed signed it. A mark is keyed by its place in the
  record, who and when, so a replay onto another door is a new mark. Marks standing where signing
  began -- the later of the first root naming a principal and the first policy declaring it -- hold;
  marks not yet committed are reported; an archived card's history is followed across the move. Once
  signed, removing `owner_signing` or repointing its `signers` holds only in a signed commit. It reads
  every record in the binding places -- an install's or upgrade's acceptance, and a review in the
  name of someone who signs, as well as a card's doors -- and a shallow clone is not measured.
- `signer --setup` warns when the owner's global git configuration signs every commit or already names
  the key as its `user.signingkey`.
- A card's `origin` holds `decision` only in a place the host's layout declares holds decisions: a
  vendored kit's own ADR no longer counts as the host's ruling.

**Added — work is weighed before it is walked (ADR-025), slice S1**
- `delivery` 0.2.0: the work-class catalogue (`standard`, `normal`, `major`, `program`, `emergency`;
  each with the records it requires, its doors and the practice it is aligned with), the undo-cost
  scale and the record vocabulary; the host's areas seed `.agents/project/delivery/areas.json`.
- Verb `weigh`: a change's class computed from the areas it touches -- the working change, a
  `--base/--head` range, or `--path` -- and what that class requires; `--class` refuses a lighter
  declaration (KIT0086). An undo cost nobody declared is refused (KIT0085).
- A standard change no longer needs a card: its commit is its record (delivery rule 4 revised).
- S2: the message hook holds the floor (a lighter declaration, a missing or idle card, a card shaped
  lighter than the change: refused); tailoring by area (`at_least`, `requires`); the Cynefin
  uncertainty on cards; `normal` cards enter the work without the owner's bet; FF-WORK-CLASSES.

**Added — the claim ladder, deferrals and a program's order (ADR-025 S3-S5)**
- Evidence classes (`static` < `tested` < `runtime` < `production`; `review`, `owner`), declared with the
  kinds of proof worth each; a criterion's `needs` -- weaker evidence leaves it unproven.
- Proof kinds `test-report-passed` (JUnit XML, TRX), `review-approved` (a review record by someone who
  is not an author; schema `review-record`), `predecessors-closed`.
- `due_when` on a deferred card and FF-WORK-DEFERRALS (due when its trigger holds; untriggered counted);
  verb `capture` (a finding as a card in the initial state, with its origin; KIT0088).
- `after` between cards: entering the work waits for what it comes after; FF-WORK-ORDER refuses a
  cycle or a dangling name and reports finished work that stops holding as REGRESSED.
- Lifecycle states may be marked `defers` and `closed`.

**Added — the emergency debt, the ceremony reading, a bounded surface (ADR-025 S6, S8)**
- FF-WORK-EMERGENCY: every `Work-Class: emergency` commit is owed a card that `repays` it; past the
  host's `emergency_debt_days` an unpaid one fails, before them it is reported.
- FF-WORK-CEREMONY: finished cards per class, their criteria and median lead time (DORA), read
  from the cards alone and never failed.
- The board lists closed states by their newest `board_recent` and counts the rest out loud; verb
  `archive` moves finished cards past `archive_after_days` into `docs/work/archive/` unless a
  working card still names them (KIT0089). A cost test holds weighing under a second.

**Added — grouping is a view; the archive is foldered by the year a card closed (ADR-025)**
- The board lists a program's parts right after their program in each column, each line saying
  `part of <program>`; the working set stays one flat folder.
- `archive` moves a card into `docs/work/archive/<year it closed>/`; one id still has one home across
  every year's folder.

**Added — no side door, the architecture map, the agents' skill (ADR-025 S7, S8b, S9)**
- `weigh --base --head --each` holds every commit of a range to the floor (CI step in the
  github-actions adapter 1.5.0): a skipped hook is caught where it is pushed.
- Verb `reshape`: raising a card's class is anyone's, lowering it the owner's door (KIT0090); a commit
  that lightens a card without that record is refused.
- A change is weighed by the areas that stood before it; loosening them owes a card, tightening is free.
- Areas carry `owner` and `feeds`: weighing names the downstream, transitively, and the lessons whose
  subject is a touched area.
- kit-skills 1.3.0: `walk-a-piece-of-work` -- how an agent walks a change: weigh first, leave what the
  class requires, judge only what is not computed, capture what it meets, leave doors to people.
- The conformance map gains the standards ADR-025 is aligned with (ITIL 4, DORA, Cynefin, ISO 21502,
  ISO 31000 / 23894, Stage-Gate, Kanban, ISO/IEC/IEEE 15026, ISO/IEC 27001 A.5.3, IEC 61508 / DO-178C,
  ISO/IEC 5338, and Anthropic's agent and context-engineering guidance), each with its evidence.

**Fixed**
- FF-RESIDENCE judges the files the repository carries: what it ignores -- the runtime plane, a
  dispatched worker's copy of the host -- is not a resident, so a host with an `archive/` directory
  no longer fails once a worker has run.
- A referenced `upgrade` creates, once and through its install mode, every host-owned seed or space a
  newer capability introduces; before, the host could not read its own declarations afterwards.
- `declared-rule-holds` refuses to follow a rule into its own evaluation: a finished card proved by
  FF-WORK-ORDER (which re-reads finished cards) recursed without end in `check` and on the board.
- The commit floor names a `Card:` line written outside the final trailer block.
- kit-skills 1.3.1: a card's proof is independent of the card -- never a gate that reads cards or the board.
- Independent audit, before release (ADR-025 amendment 1): one trailer parser and canonical spelling;
  expedite only from a trailer; the bet for classes with doors; area `requires` held at commit;
  `decision` held by a decision document; CI skips commits made before the areas; merges weighed by
  `--cc`; the hook reads the index; demotions by path; loosening by an added cheap area; `chaotic` asks
  `major`; skipped tests prove nothing; the archive keeps referenced cards and paid debts; an owner's
  door is not authorship; Python 3.10 reads a trailing `Z`.
- Verb `prove`: runs every command a MUST norm names as its enforcer (`stack-kit:test`), once each,
  and fails on red; the git adapter 1.5.0 pre-push hook runs it after `check` -- a MUST is enforced
  only where something runs its enforcer (found by an audit: two MUSTs were vouched for by commands
  nothing ran).
- secrets 1.4.0: `no-committed-config-secret` -- a key, secret, password or token with a real value
  in a settings JSON file (found by an audit: a committed JWT key signed a live app's tokens while
  every gate was green). Calibrated to pass public keys, header names, empty values and placeholders.
  1.4.1: narrowed after its first real host -- settings files only (a configuration CATALOGUE's
  lowercase `key` field is metadata, never a key), the name matched case-sensitively.
- A second independent audit (ADR-025 amendment 2): a loosening walks the class of every area it
  loosens, as it stood; an emergency debt is paid only by a card shaped and holding what the commit
  weighs by its parent's areas; `weigh --each --published-as` weighs a first push by what no other
  remote branch carries (github-actions 1.6.0); an area's card-held `requires` raises the class to a
  card; uncertainty raises a classless card; test reports read the way that proves the least (JUnit
  cases and roots, TRX passed == executed); a program's parts stay with it in the archive; a replayed
  lowering approval, a door's carrier, a whitespace paragraph and a doubled trailer are no longer side
  doors; a gate that reads the governed records never proves one (`READS_THE_RECORDS`); a decision is
  what its front matter says; `prove` refuses a MUST whose command cannot be read. secrets 1.4.2:
  snake and short secret names, `launchSettings.json`, and `no-committed-config-secret-in-properties`
  for YAML and properties files.

## 0.2.0 — 2026-10-17

**Added — the agentic layer: every token serves the result (ADR-024)**
- Skills (`skills`, served per product, extended by hosts with chapters); bundles `kit-skills`,
  `engineering-standards` (16 chapters).
- MCP servers by trust (`mcp-servers`, `mcp-trust`), served to `.mcp.json` / `.codex/config.toml`.
- Context measured per layer (FF-CONTEXT), stable-first order, task router seed.
- Policies `untrusted-content`, `memory`, `recovery-points`, `spawn-packets`; `secrets` 1.1.0.
- Task classes, route cells with actor/model/effort/caps/escalation, adapter `options`; stop conditions.
- Verbs `trial` (agent evals; bundle `agent-evals`), `guard`, `spawn`, `doctor`, `extend`, `review`,
  `capsule`; hook posture and receipts; git pre-push; CI `git diff --check`.
- GenAI telemetry names in run records; FF-FRONTIER (tokens per accepted change, script candidates).
- The normative tree (FF-NORMS) and bundle `engineering`; role profiles; extension points (shared
  `extension-points` schema, FF-EXTENSIONS); bundles `change-records`, `execution-graph`, `shared-tree`;
  the conformance map (FF-CONFORMANCE).
- A product's own session lifecycle: verbs `session` (session-start context line), `stop` (the
  continuity capsule's stop gate, served only with the capsule; resolver `contracts`) and `ledger`
  (subagent-stop: requested vs verified model, tokens); hands `context` and `ledger`; claude-code
  1.10.0 serves SessionStart, SubagentStop and Stop; codex 1.7.1 states its events as a claim.
- Review owners: contract `owners`, resolver `declared`, view `owners`; the core seeds
  `.agents/project/owners.json` (extension point); github-actions serves a span of `.github/CODEOWNERS`; surface
  `controls` -- `doctor` names branch protection NOT ASSERTED with the exact `gh api` command.
- Commit messages: contract `message-rules`, gate FF-MESSAGE-RULE (calibrated), verb `message`
  (KIT0082); git 1.3.0 serves `.githooks/commit-msg`; policy `conventional-commits` 1.0.0 (opt-in).
- Referenced install mode: a host holding the kit in its own tree (a submodule) runs it from there with
  no copy -- lock `reference` (path, repository, commit, takes); `upgrade --mode referenced`; module
  `reference`; check, the entry point and every served hook refuse an absent, moved or edited kit
  (KIT0083, with the restoring command); a hook whose host cannot be read keeps its posture. The owners
  seed moved to the core (`runtimes`), beside `mcp-servers`.
- One secrets catalogue: secrets 1.2.0 publishes its edit-gate document's path and contract
  (`policies/secrets/README.md`) for other readers; stack-kit adapter 1.1.0 declares the bridge
  (`security.secretPatterns`). Acceptance test_policies 415 holds the published contract true.
- The whole-tree audit: verb `audit` (KIT0084) runs every calibrated edit gate in force over every
  tracked file, prints path:line, gate and because (never the matched text); extension point
  `known-violations` (contract `known-violations`) acknowledges KNOWN findings with tracking and `until`;
  EXPIRED and STALE named; gate FF-TREE-AUDIT ships `observe` and `check` prints its counts (`REPORTS`).
- One source for a host's laws: a host rule carries `law: <n>` and `enforcement_note` (contract `cardinal`);
  the briefing's law list is rendered from them (`.agents/generated/LAWS.md`, resolver `numbered`); the
  law page `.agents/project/doctrine/laws.md` is deprecated -- no longer seeded, served while present, FF-LAWS
  fails both authored or a gap in the numbers; `upgrade --mode laws` moves each numbered law into a rule.
- A referenced host stays referenced: a plain `upgrade` is `--mode referenced`; `--mode vendored` returns it to
  copies by name. A take re-released at a newer version in the submodule is taken again in the same walk;
  changed bytes under one version stay KIT0032 (ADR-024 decision 22).
- Enforcers an adapter vouches for (contract `enforcers`): adapter `stack-kit` 1.2.0 vouches for each
  `commands.<name>` the host's `stack-kit.json` declares as `stack-kit:<name>`, so a MUST may name it
  (ADR-024 decision 23).


**Changed — every dispatch table is a discovered registry; the core reaches ports only through the root (ADR-023 amendment 5)**
- Families `modes/`, `shapes/`, `readers/`, `resolvers/`; `installmodes`, `shaping`, `serving`,
  `dispatching`, `taskrecord`, `routegraph`; `ports/sources.py`; `ports/runtime.py` and `accepted.py`
  removed; `manifest.plane()`, `manifest.files()`, `manifest.kit_at()`; workspace `accepted_listing`/`accepted_text`.
- The ecosystem detectors moved to `adapters/{dotnet,node,pnpm,go,python}` (taken by `standard`).
- Unit `test_events_are_provided`; the arrow test refuses a core->port import.

## 0.1.6

**Added — a new host starts in one door, served to the field's standards (ADR-023)**
- Verb `start --path starters/<id>.json --approve <who>`: walks a published starter (take, enable,
  runtimes, render, activate, init, check) as separate runs, stopping at the first failure. Schema
  `starter`, `starters/standard.json` (Claude Code, Codex/AGENTS.md, git; cardinals, conduct). KIT0073.
- The briefing serves the host's build and test commands inline (`COMMANDS.md`); detector
  `stack-kit-commands` reads `stack-kit.json` `commands.test` / `commands.build`. The laws seed serves
  no authoring prose.
- Gate `FF-PLANE-WRITER` (`plane-held-by-its-writer`): an interactive session's edit inside the vendor
  or projection plane is refused with the verb to run instead; commits and CI are judged by `check`.
- Claude Code and Codex hooks fail closed when no Python runs (exit 2), as the git hook did.
- The github-actions template pins `actions/checkout` by commit SHA; the kit's own suites run in CI.
- `kit/README.md` verb table derived from the verbs (`test_verb_reference`); README rewritten with a
  quick start and a glossary.
- `test_start` 407–410, `test_commands` 412, `test_enforcement` 289c–289d.
- A verb that delegates its writes to separate runs declares `DELEGATES` and is observed through
  them (ADR-023 amendment 1): `start` on a host that has already answered no longer fails its own
  acts' `FF-RUN-RECEIPT`.
- A spanned served file records only the kit's span, so the host's own edit to an entry file
  keeps `check` green without a render; the entry seed's note is a comment (claude-code, codex
  1.3.1). `test_entry_files` 341b (ADR-023 amendment 2).
- The edit-gate declaration is not judged by the gates it declares: each carries the text it
  refuses as its `proves`, so a broad gate refused the commit that declared it. `test_enforcement` 289e.
- A collection record whose kind declares no `id` (a runtime observation) is named by its file: two
  runtimes' refusal records no longer collide on an absent id and stop every verb. `test_attestation` 383.
- `--kit git+<url>@<rev>`: a release source that is not a local directory is cloned bare into the
  scratch, then read at its revision as before. `test_pinned_kit` 279b.
- Policies beside the kit (ADR-023 amendment 3): `policies/secrets` 1.0.0 -- edit gates every host
  holds (private keys, cloud access keys, platform tokens), taken by the `standard` starter. Host text
  gates no longer judge the pinned kit or taken capabilities. `test_policies` 413-414.
- A release source cloned from a URL is removed with its read-only git objects: on Windows a plain
  removal left the scratch behind (found by the full suite on `test_pinned_kit` 279).
- Open by declaration (ADR-023 amendment 4): evidence kinds discovered from `interpreters/evidence/`;
  a capability brings detectors as `detector` documents (`adapters/stack-kit` 1.0.0 carries
  `stack-kit-commands`, moved out of the core; core `declared-build-script` added); a surface may declare
  a stdout decision (`hands.refusal.stdout`, `hands.admission.stdout`); `start` retakes after its takes;
  `test_one_name_one_module`. `test_commands` 412b, unit `test_judge_decision`.

**Added — a reading is replaced through a door (ADR-021 amendment 2)**
- Verb `retake`: names every moved fact; `--plan` writes nothing; unapproved it is a door; approved it
  writes the fresh reading with `retaken` (`signed_by`, `signed_at`, `replaces`). `KIT0072`.
  `reading-current` names the remedy in its failure.
- `node-workspace` reads a `package.json` anywhere the repository carries, so a monorepo's nested
  package is evidence. A host with one sees `reading-current` fail once; `retake` is its remedy.
- A take's `source` is recorded relative to the host when it lies inside it.
- A served entry's pointer section ends its line: the next heading opens its own paragraph.
- `test_retake` 404–406, unit `test_entry_sections`.

**Fixed — a space opened before its marker is completed (ADR-021 amendment 1)**
- `space.carried`: a space is there when its directory AND marker are. `init` (space modes) and the
  upgrade reconciliation both read it, so a bare directory left by an older install gets its marker
  instead of vanishing from the next clone and failing `FF-HOST-FLOOR` there. Host #0 completed two.
- `test_fresh_clone` 352.

**Added — THE OPERATING PLANE, slice S8: the conduct, published (ADR-022 decision 11)**
- `bundles/conduct/` 1.0.0 beside the kit: six chapters (protocol, economy, risk, delivery, verification,
  craft), the skill `architecture-standards`, the playbook `a-change-to-an-existing-system` — re-authored from
  the prior system's portable canon in no repository's vocabulary.
- Doctrine grammar: genres `skill` and `playbook`.
- `UPSTREAM-LAYOUT.json`: conduct, skills and playbooks rows built — 47 present, 1 pending, 0 missing.

**Added — THE OPERATING PLANE, slice S7: registers are documents (ADR-022 decision 10, amendment 3)**
- Kinds `register` (rows: id, title, status, at; optional by, note, declared_at, promoted_to, refs) and
  `register-kind`; shipped kinds `standards`, `findings`, `visions`, `gaps`, each status naming the fields it
  requires.
- Capability `operating`: space `docs/work/registers/`, projection `docs/work/REGISTERS.md`, gate
  `FF-REGISTERS-HELD` (kind `register-held`, calibrated): undeclared status, missing required field, and a
  promotion whose target does not cite `<register>#<row>` back each fail by the row's address.
- Delivery's single governed collection is untouched (amendment 3). S7b (handoffs, knowledge planes) named.
- `test_registers` 400–403.

**Added — THE OPERATING PLANE, slice S6: a gate is trusted only after it bit (ADR-022 decision 8)**
- `check`: a gate kind that raises (other than a refusal by name) FAILS under its own stance with the
  crash named; every other gate is still judged. Posture is the existing stance (ADR-022 amendment 2).
- `CALIBRATIONS` registry beside `KINDS`; gate module `calibration` publishes `uncalibrated_gate_kinds`
  (None where no corpus is mapped). First calibrations: `schema-valid`, `path-class-total`.
- Unit `test_gate_calibration`; acceptance `test_gate_crash` 398. S6b (exec/session hands, rings, sunset)
  named, not built.

**Added — THE OPERATING PLANE, slice S5: two principals on one tree, arbitrated (ADR-022 decision 7)**
- Module `claims` and verb `claim`: take (`--by --path --reason`), list, `--release`, break by name
  (`--release --break-lock <who>`, recorded). Kinds `claim` (observed plane, one per principal, no TTL —
  ADR-007) and `arbitration` (`window_minutes`, seeded 0 = only claims arbitrate). KIT0071.
- The judge, before any gate: refuses a path under another principal's standing claim (who, since when,
  why), or written by a peer inside the window unless this principal's claim postdates that write; records
  each admitted write in the principal's own log (`writes/<principal>.jsonl`).
- `attestation.served_through()`: the principals a surface serves, one reading for both uses.
- `test_claims` 390–394.

**Added — THE OPERATING PLANE, slice S4: a capability is believed once it is proven (ADR-022 decision 6)**
- Schema `runtime-observation`; module `attestation` with the provided-event registry `EVENTS`
  (`a-refused-write`). The runtimes capability installs `.agents/runtime/observations/` and declares it the
  composition's `proven` source, so a runtime's page moves a claim to PROVEN only on a record.
- Class vocabulary: `observed_on` names the provided event a capability is observed on; `write-scope` is
  observed on the judge's refusal. The judge records it after refusing — never changing the verdict.
- Not built, named: routing on the attested set; events for the other capabilities.
- `test_attestation` 380–382.

**Added — THE OPERATING PLANE, slice S3: what the work cost, measured (ADR-022 decision 5)**
- Gate module `economy` publishes `peak_context` (largest reported peak) and `calls_per_delivery` (median
  calls of delivered tasks), read from the returns recorded on dispatched tasks; `None` where none returned.
  A host budgets them through its corpus map.
- ADR-022 amendment 1: per-kind ceilings need a budget row that names its subject (owed); the sunset
  measure moves behind S6's calibration; transcript telemetry is S3b, named and not built.
- `test_routing` 366.

**Added — THE OPERATING PLANE, slice S2: a ground is a reading with an expiry (ADR-022 decision 4)**
- Module `readings` + verb `ground`: record `--key --fact --instrument --path`, read `--key`. A reading's
  digest folds the working-tree content of only its declared paths, through what the repository carries;
  it lives in the observed plane (`ground/ledger.jsonl`, append-only, last write per key wins).
  KIT0069 (no instrument / no path), KIT0070 declared miss (exit 4) naming what moved and the instrument.
- A packet's `ground[]` row may cite a ledger `key`; the port refuses a dispatch whose cited ground no
  longer holds, before a worker starts.
- The entry point merges each verb's declared `ARGUMENTS`: a verb with new words is still a file.
- Host floor: `.agents/runtime/ground/` built (capability `operating`).
- `test_ground` 370–373, `test_routing` 365.

**Added — THE OPERATING PLANE, slice S1: a packet names what ends the run (ADR-022)**
- `dispatch-packet` **version 2**: `deliverable` (required), `decision_density`, `reversibility` (required),
  `ground[]` (each with its instrument), `boundaries`, `budget`, `profile`. A v1 packet is refused by
  `KIT0034` (a transient kind; nothing to migrate). The port provides `{deliverable}` to an adapter.
- New capability **`operating`** 0.1.0 (the operating plane's home): seeds an empty `.agents/project/operating/routes.json` (the declared
  zero) and declares `route-table` (cells on the two axes; named verification profiles with a timeout) and
  `dispatch-return` (deliverable status, economy with what was not read, findings, brief quality, growth,
  refusal with argument, alternatives and who decides).
- The port judges a packet against its cell (pair present, role, adapter, required profile, budget, packet
  ceiling) before a worker starts; records the cell or that none was declared; parses and validates a return
  from an artifact the adapter declares `carries` it; runs a named profile in the worker's tree on return,
  bounded by its timeout. A failed return or profile closes the task FAILED, by name.
- `minimum` joins the kit's JSON-Schema subset.
- `test_routing` 360–364.

**Added — THE TREE IS THE DRAWING, slice S5: the floor holds on a fresh clone (ADR-021 decision 8)**
- `floor.observed()`: a drawn place in the observed plane is NOT MEASURED, never failed (generalises the
  ephemeral-clone rule). Unit host #0 floor green.
- `ports/vcs.py` — the one port that asks version control (`run`, `carried`); the ratchet reads through
  it. `Workspace.carried()`; `glob_any` matches what the repository carries (ignore-aware, bounded).
- Governance seed `.agents/.gitattributes` (`* -text`): a clone receives the committed bytes, so the
  pinned kit and projections survive a translating checkout.
- `test_fresh_clone` 350–351.

**Added — THE TREE IS THE DRAWING, slice S4: entry files are the host's (ADR-021 decision 5)**
- Surface render rows may name `span` + `seed`: the file is written once from the seed, the kit owns only
  the span between `kit:begin`/`kit:end`. `derivation` gains public `span`, `spliced`, `withdrawn` (and
  `filled` uses `spliced`) — one marker grammar for every writer of a span.
- Runtime port: the serve record carries `span`, `span_sha256`, `seed_sha256`; `admit` judges a spanned
  file by its span; `withdrawals` removes only the span of a surface no longer served (an untouched seed
  is removed whole); a file the kit last served whole is converted. `render` writes withdrawals.
- Briefing sections may `points` — doctrine and roles are now pointed to, not inlined.
- Measure `served_span_bytes` (gate module `served`), budgeted by the host through its corpus map.
- Adapters `claude-code`, `codex` 1.1.0: briefing and scoped briefing served as spans; seeds added.
- `test_entry_files` 340–346; `test_serving` 262 edits inside the span; `test_adapters` 270 moves seeds.

**Added — THE TREE IS THE DRAWING, slice S3: relocations (ADR-021 decisions 3, 4, 6)**
- Capability `relocations: [{from, to, decision, referenced_by?}]` beside the install that moved; `to` must
  be one of that capability's own targets. New module `relocation.py`; `init` gains the phases
  `relocations` (read, refuse whole) and `relocate` (rename under the run's hold), before the write set is
  foreseen; `upgrade` reconciles through the moved view, so `--plan` is the plan carried out and writes
  nothing. Each move is verified by an h1 at both names; the estate's rows are re-keyed and the move is
  appended to the new estate field `relocated`. **KIT0068** (both places hold something; a host document
  still names the old place, with the exact restatement printed; a relocation to a place not installed).
- Moved: delivery cards → `docs/work/cards/`, board → `docs/work/BOARD.md`, new space `docs/work/evidence/`;
  host law (`laws.md`, `law-scopes.json`, `laws/`) → `.agents/project/doctrine/`, scope pages declared
  `referenced_by` the scopes document; `governance/INDEX.md` → `governance/CAPABILITIES.md`.
- The anti-clobber rule judges only SERVED paths outside the planes; a declared projection install there
  (the board) is the kit's own path, held by `check`'s reproduction.
- Suites read every moved path from its declaration (`harness.install_target`); `test_relocation` 330–333.

**Added — THE TREE IS THE DRAWING, slices S1–S2 (ADR-021)**
- Layout grammar (expand-only, schema v1): `realised_as {path, decision, pending?}` — a drawn path whose
  truth a named decision placed elsewhere; `declared_by` — a path beyond the drawing kept by a decision;
  `closed` — the directories a drawing is exhaustive at. The floor gate judges a realised row at its
  realised place, prints REALISED, refuses a row both pending and realised, and waits a realised form not
  yet built on its own link. `floor.unclosed()` names every tracked child of a closed directory no row
  covers (the caller supplies the tracked reading).
- `UPSTREAM-LAYOUT.json` restated: `kit/doctrine/` realised in the capabilities (ADR-004 ②), `CARDINALS.md`
  in `bundles/cardinals/`, protocol/economy/risk in `bundles/conduct/` (pending F), lifecycle and
  verification in their capabilities, `interpreters/hooks/` as the one `judge` (ADR-017), skills and
  playbooks as bundle genres (pending C); `fitness/` no longer pending (it exists); host #0's own tree,
  `adapters/`, `bundles/`, `.github/`, `kit/{README.md,diagnostics.json,kit.lock.json}` declared. Upstream:
  42 present, 6 pending, 0 missing, 0 undeclared. Host layout: `roster.json` realised as `roles/`.
- **`bundles/cardinals/` 1.0.0** — the owner's eight cardinals as a doctrine bundle, published BESIDE the
  kit; the issued manifest still ships no doctrine. Acceptance `test_bundles` (320–322): outside the
  manifest, documents valid, a fresh pinned host takes it, its roll names all eight UNANSWERED, `check` green.

**Added — the DISPATCH PORT: one place a worker is started (ADR-017 link C, slice C2)**
- Port `interpreters/ports/dispatch_port.py` + verb `dispatch` (reads one packet on stdin; `--plan` writes
  nothing). The verb is a mouth, not a gate: refusing, leasing, isolating, starting and recording are all
  the port's, so a task handed over by a runtime hook, another verb, a shell or a second intelligence meets
  the same judgement. Order: refuse on pure reads → lease the path → open the task record at `submitted` →
  isolate → start at `working` → close once with the state the ADAPTER's declaration says the ending meant,
  the artifacts read from the channels it named, and the exit code recorded BESIDE the state.
- **KIT0049** (a task the port will not start: unreadable, incomplete, unrouted, already dispatched, or a
  placeholder this packet states no value for — never filled with a blank), **KIT0050** (no adapter taken;
  zero or two isolation providers; a placeholder or channel the port does not provide; a declared program
  absent on this machine), **KIT0051** (the task vocabulary's two homes have parted) — issued 51.
- Schemas: `dispatch-packet` (a complete task: routed `id`, `route`, `instruction`, `branch`; optional
  `role` and `routed_by` testimony — and deliberately NO path), `task` (A2A's six states, one home; packet
  carried opaquely; artifacts), `dispatch-adapter` (how an intelligence is started, what it returns and
  from which channel, what exit means completed), `workspace-provider` (how an isolated tree is made and
  withdrawn). Adapters found by the CONTRACT their document keeps: the port names no runtime and no id.
- Adapters: `claude-subagent` 1.0.0 (dispatch, published apart from the runtime adapter of the same
  product — being served and being startable as a worker are two reasons to change); `git` 1.0.0 gains
  `workspaces.json` (`git-worktree`). Both are CLAIMS: neither has been observed running by the port.
- `hostlock.take(..., registers=False)`: the host's own hold mechanism, on one path — same document, same
  break-by-name door, and a per-path hold that does not register as the hold on the host. No second lease.
- Tests: `tests/unit/test_dispatch_port.py` (the reading is the port's; an argv is filled only with provided
  placeholders; the task vocabulary's one home, measured and shown to bite; completeness read from the
  schema) and `test_313`/`test_314` (refused through the CLI verb AND a direct in-process call, with
  nothing leased or made either way; then leased, isolated, started, recorded — through a FIXTURE adapter
  nobody shipped). NOT built here, deliberately: `codex-exec`, the visibility wrapper, `input-required`,
  OTel `gen_ai` receipts, and admission of a returned change (C3/C4).

**Added — the CI PROJECTION: the return point nobody skips (ADR-017 link C, slice C1c part 4, last of C1)**
- Adapter `github-actions` 1.0.0 (surface `github-actions`, the only place the product is named): renders
  `.github/workflows/kit-gates.yml` (view `enforcement`) -- on `push` + `pull_request`, `actions/checkout`
  (fetch-depth 0), then two `shell: sh` steps running the PINNED kit (`{vendor}/interpreters/cli.py`, never
  `--kit`, never fetched): `check --surface github-actions`, and `judge --surface github-actions` over
  `git diff -U0 <base> HEAD`. Base read from `$GITHUB_EVENT_PATH` (`pull_request.base.sha`, else `before`;
  empty/all-zero -> the empty tree: everything introduced). Fails CLOSED on no Python, unreadable event,
  unreadable diff. `hands` identical to `git-commit`'s (patch, `nothing: admitted`, exit 1). No `${{ }}`
  expressions (they collide with the template grammar, and the event file is the documented one home).
- Selection is DECLARED, never measured: a host serves it by a runtime descriptor naming the surface
  (host #0: `.agents/project/runtimes/github-actions.json`, class `a-batch-invocation`). `ci.workflows`
  cannot choose a provider (zero workflows on a host that has none yet; `.github/workflows/` is read by more
  than one product) -- so no `ci.*` fact drives the projection, and none is required.
- Schema `runtime-surface`: optional `clone` (`working`|`ephemeral`). Verb `check --surface <id>` runs the
  gates as seen from that surface's clone; an undeclared surface is refused under **KIT0048** (issued 48).
  Through an `ephemeral` clone, `FF-RUNTIME-ACTIVE` names each working-clone setting NOT MEASURED (moment
  stated) and `FF-HOST-FLOOR` names rows inside the OBSERVED plane NOT MEASURED -- MEASURED need: a copy of
  host #0 with only versioned files failed `FF-HOST-FLOOR` on `.agents/runtime/{receipts/,init.journal,
  init.lock}` and `FF-RUNTIME-ACTIVE` would read INACTIVE: CI would have been red on every push.
- Probe: a path the kit's own record says it SERVED is never evidence about the host (all evidence kinds;
  `Context._served_paths` reads `SERVED.json`). MEASURED need: rendering the workflow flipped
  `ci.workflows` and failed `FF-READING-FRESH` -- a measurement observing the kit's own output.
- Records map: the `.github/workflows/` row LEAVES kit core `governance/host-layout.json` (a product path in
  the kit) for the adapter's `floor` (holds automation-definition, writer OWNER, lifecycle living). Ownership
  rule: the directory is the owner's; the kit is a tenant of exactly the path its record names; a host
  file at that path is refused (KIT0039, no new code), one beside it is never touched. Still `pending: C`:
  the floor grammar binds a row to ENABLED, not SERVED -- see GAP-L2.
- Tests: new `test_ci_projection.py` `test_296`-`test_298` (served text names pinned check+judge through
  the surface, no `--kit`; check through ephemeral: no FAIL, NOT MEASURED; plain check still INACTIVE;
  KIT0048; KIT0039 on a host file at the target, sibling untouched; the served `run: |` blocks executed by
  `sh -e` against a fixture repo: PR / push / zero-sha events REFUSE a violation, a clean push admitted, an
  unreachable base refused). `test_302` reads JSON only for `.json` targets; `test_303` no longer assumes
  exactly two unactivated adapters. Suites run: ci_projection, commit_gate, adapters, serving, taken,
  host_floor, boundary, diagnostics, enforcement (60 passed, 1 skipped); detectors, observability,
  scoped_law green earlier in the slice.
- Host #0: lock -> upgrade -> take `github-actions` -> enabled in `project.json` (KIT0025 says the answers
  file is the door) -> descriptor -> init --approve `owner-aleksandre17:explicit-2026-09-17` -> render
  (`created .github/workflows/kit-gates.yml`) -> `check: 0 gate(s) failed`; through the surface also 0.
  Local step run on a versioned-files copy of host #0: violation in `kit/` (committed `--no-verify`) ->
  check 0, judge REFUSED `no-product-in-the-shipped-kit`, exit 1; clean push -> judge admits, exit 0.
- UNVERIFIED (only a real push proves): the runner reads the file and runs `sh -e`; `GITHUB_EVENT_PATH`
  field shapes; merge-commit HEAD on `pull_request`; `actions/checkout@v4` (a fetched ACTION, not a kit;
  not SHA-pinned); force-push with an unreachable `before` (refuses -- fail closed, red); fork PRs;
  runner Python. No `actionlint`/`act` on this machine; not installed.
- Not decided here (ADR-worthy): the duplicated `hands` patch grammar in `git` and `github-actions`
  (one truth, two homes -- a shared unified-diff grammar is the cure); whether `check --surface` on a
  working machine should be refused for ephemeral surfaces (today it is declared and printed, not policed).

**Added — the COMMIT GATE: `core.hooksPath` (ADR-017 link C, slice C1c part 3)**
- ADR-017 decision 5 says a runtime with no proven pre-write block is held by "verification at
  return" instead of prevention at write. A commit is the return point every runtime, tool and human
  shares, so the git hook is where that verification lives -- the SAME judge and the SAME host gates.
- Adapter `git` 1.0.0 (surface `git-commit`, the only place the product is named): render
  `.githooks/pre-commit` (LF, `#!/bin/sh`, fails CLOSED if the staged diff or Python cannot be
  read); `hands.carries: patch` (stdin IS `git diff --cached -U0`) and `hands.nothing: admitted`
  (a pure deletion introduces no text, declared); refusal exit 1; floor row `.githooks/` (pending C).
- Schema `runtime-surface`: `hands.carries` (`event`|`patch`), `hands.nothing` (`refused`|`admitted`),
  `patch.from` no longer required; new `activation` block (setting, points_at, read/set/unset argv,
  occupied {read, inert}). `judge` + `gates/edits.py` read a carried patch; no product word added.
- `runtimes` 0.3.0: gate `FF-RUNTIME-ACTIVE` (kind `served-setting-active`, `gates/activated.py`) READS
  the setting on every `check` and names INACTIVE / ELSEWHERE / UNREADABLE (fail) or ACTIVE (with the
  moment read), plus a missing execute bit on mode-keeping filesystems.
- Verb `activate` (door): `--plan`, `--approve`, `--to inactive`. Refuses under **KIT0047** a surface not
  served, a setting that names elsewhere (never clobbered, never withdrawn), live non-sample entries in
  `git rev-parse --git-path hooks`, anything unreadable; reads back after the change. `activation.py`
  (interpreter root) holds the reading; `ports/runtime.py` gains `served_surfaces` (from SERVED.json).
- Tests: `test_292`-`test_295` (fixture git repos: INACTIVE/ELSEWHERE/ACTIVE; plan/unapproved/clobber/
  occupied refusals; git refuses a violating commit, records clean + pure deletion; withdrawal).
  `test_288`/`test_289` read JSON only for `.json` targets and honour `nothing: admitted`.
  Takes/scoped-law suites take `UNACTIVATED` adapters (no surface declares `activation`, read from each adapter's documents); `test_258` walks `activate` for a surface that declares it.
- MEASURED (git 2.39.1.windows.1): hooks in a hooksPath dir run from the worktree root with no exec
  bit; non-zero exit refuses the commit. Host #0: git adapter taken + enabled, descriptor
  `git-commit` (class `a-batch-invocation`), `core.hooksPath=.githooks` by
  `owner-aleksandre17:explicit-2026-09-17`; a product word staged into `kit/` REFUSED by git, a clean
  commit admitted; both probes undone (HEAD e50dfa7).
- UNVERIFIED / not built: POSIX exec bit after re-render (render rewrites atomically, dropping the
  mode -- `check` reports it, `activate` restores it); `--no-verify` bypass (CI projection out of
  scope); GAP-A1 (who activated is journalled, not in the estate).

**Added — scoped law: per-directory entry files (ADR-017 link C, slice C1c part 2)**
- `governance` 0.2.0: schema `law-scope`; seed `.agents/project/law-scopes.json` (ships `scopes: []`,
  `reads_as: law_scopes`); space `.agents/project/laws/` (where scoped law pages live, accounted).
  A scope row = `{id, dir, page, says?}` -- a law PAGE (same grammar as the root law page) plus the
  one proposition "binds below `dir`". Two `host_layout` rows.
- `runtimes` 0.2.0: view `scoped-briefing` (`scopes: {sources: {validates: law-scope}, list, at: dir}`,
  one section with `from_field: page`). `ports/runtime.py` places `<dir>/<surface target>` per scope,
  recorded in `SERVED.json` like every served file, so departure (render removes), collision refusal,
  `reach`/`succession` see them with no new code path. Refused before any write under **KIT0046**: a
  dir that is not a plain in-host path, is missing, is the root, or lies in a kit plane.
- Adapters `claude-code` / `codex` 1.1.0: a `scoped-briefing` render row (`CLAUDE.md` / `AGENTS.md`) and
  `payload/scoped.md.mustache`; `says` cites the nested-file behaviour, marked UNVERIFIED. `kit/` names
  no runtime file (test_312).
- Host #0: scope `fresh-repo-suite` over `tests/acceptance/fresh-repo` (laws restated from `harness.py`,
  suite docstrings, `boundary.json`, ADR-001 T1) -> `tests/acceptance/fresh-repo/{CLAUDE,AGENTS}.md`.
- Found, not cured (GAP-S1): walking `kit/interpreters/` served files INTO the kit source tree, and `lock`
  then refused the kit (KIT0026) -- the port cannot see a publication tree no declaration names.
  Also observed: departure prunes an EMPTY host directory that the kit did not create.

**Added — `fitness`: the abstract ARROW (ADR-017 link C, slice C1c part 1)**
- New capability `fitness` (requires `enforcement`), schema `arrow`, seed `.agents/project/fitness/arrow.json`
  (ships empty), gate `FF-ARROW` (kind `arrow-held`, ships at the declared default stance -- ADR-006: a kit never ships looser; a host loosens only by a signed stance row). A host declares `imports` (per file
  kind: a reference pattern, `locates` templates with `{ref}`/`{dir}`, optional `separator`), `layers`
  (`within` + `paths`) and `rules` (`from`, `may`, because/instead). Readings and rules each carry
  proves/admits calibration. No language, layer or import syntax lives in `kit/` (test_303).
- ONE edit judge: gate modules now export `EDITS` beside `KINDS`; `check.registry(entry)` discovers
  both; `judge` applies every enabled gate whose kind has an `EDITS` entry. `edits.rules_of` removed.
- Field form: ArchUnit layered rules / import-linter `layers` contract / dependency-cruiser `forbidden`
  / eslint `no-restricted-imports`; the edit-time half judges only introduced text. A FreezingArchRule-style
  `observe` ship was considered and dropped: with zero violations on host #0 a ratchet is unnecessary, and
  the edit judge still refuses every new backward import.
- Host #0: `fitness` enabled; arrow declared over `kit/interpreters/` (verbs, gates, observers, ports,
  base). The one violation it found (`gates/core.py -> verbs/render.py`, gates-never-reach-verbs) is
  cured at the root: the projection computation moved to base module `kit/interpreters/projection.py`;
  `verbs/render.py` keeps `run` (and re-exports its surface), `gates/core.py` imports `projection`.
- Not built: a reference that resolves through a package/alias map (only templates); cycle detection
  inside the allowed set (base<->ports is a real cycle, permitted by the rules as declared).

**Fixed — `judge` never admits an edit it could not place (Cardinal VII)**
- On a drive-lettered filesystem a drive spelled as a POSIX mount (`/c/...`, `/cygdrive/c/...`) is
  normalised by ONE form rule in `gates/edits.py`; any other rooted path without a drive raises
  `Unplaceable` and `judge` REFUSES. Previously both read as "outside this host" and passed (fail-open).

**Changed — the pin is written when the bytes arrive (ADR-018 amendment 2; closes the take→init window)**
- `take --approve` writes the ADR-008 provenance pin for each take AT ARRIVAL, marked
  `trust: {basis: trust-on-first-use}` with authenticity `not-yet-read` (new declared word in
  `provenance.json`); a retake of equal bytes keeps its pin, a newer version supersedes it, changed
  bytes at the same version or an older version are refused (KIT0045).
- `take` now HOLDS the host as its one writer (ADR-007): its writes run under `hostlock.held`.
  Still not built: a take journal.
- `init --approve` ATTESTS a trust-on-first-use pin (authenticity read, `trust: {basis: attested,
  attested_by, attested_at}`); bytes that no longer equal the pin read `drifted` and init refuses.
  Without an approval an unattested pin waits at the provenance door like a first contact.
- `taken-intact` FAILS on a take with no pin; the `NOT YET PINNED` pass state is removed. A pin
  written before amendment 2 carries no `trust` field and reads as attested (it was pinned at an
  approved door). `estate.schema.json` gains optional `trust`.
- `trust.basis` is an open word declared in `provenance.json` `trust` (no schema enum), each row naming the moment the interpreter writes it (`written_at`: `arrival` | `approval`, a schema enum; exactly one row per moment); `taken-intact` fails an undeclared basis, and an unapproved `init` says a trust-on-first-use pin awaits attestation.

**Changed — the take digest has one home (ADR-018 amendment 1)**
- `taken-intact` judges each take against its ADR-008 provenance pin, never its row; a take not yet
  pinned is printed `NOT YET PINNED` (not failed). `take` no longer writes `digest` and sheds it from
  carried rows; `taken.schema.json` makes `digest` optional and deprecated (removed next version).

**Added — link C, slice C1b: TAKEN CAPABILITIES LIVE BESIDE THE PINNED KIT (ADR-018; cures GAP-T1)**
- **Two homes, one composition.** Governance declares the take PLANE (install mode `taken`,
  `.agents/taken/`, opened as a space; `declaration` + `namespace` are new optional install fields) and
  the take DECLARATION (mode `taken-declaration`, `.agents/project/taken.json`, schema `taken`, seeded as
  a declared zero). `.agents/kit/` is never written by a take and stays byte-equal to its lock.
- **The loader composes.** `manifest.composed(kit, host)` = issued `MANIFEST.json` + every take row,
  each resolved to its plane by `Manifest.path` (the one resolver; `_read`, `payload_text` and
  provenance's signature read go through it). Context speaks with the composed manifest; no projection
  learns where a capability came from. An issued id taken again is refused at the take and at every
  load: `TakeShadows`, **KIT0044**. A row whose plane is gone is refused at load (KIT0015).
- **`take` verb** (new file, a DOOR): `take --root . --path <dir>[,<dir>] [--approve <who>]` copies
  each published capability verbatim into its plane and writes its row (`id`, `source`, `digest` =
  h1 over the whole copied tree in the kit namespace, `taken_by`, `at`). Unapproved it names the takes
  and refuses (KIT0007); a bad take is **KIT0045**. Enabling the take (`project.json`) and pinning its
  provenance (`init --approve`) remain the acts they were.
- **`FF-TAKEN-INTACT`** (kind `taken-intact`, `gates/taken.py`) judges each take against its row's
  digest and fails a directory in the plane no row declares. `FF-KIT-PINNED` unchanged. Provenance's
  digest of a take is the same h1 over the same tree (one algorithm, `provenance.h1`).
- **Surfaces state the composition:** the CLI's first line and `pin.identity` print
  `release <v> + taken: <ids>`.
- Records map: host_layout rows `.agents/taken/` (pinned-release / kit-verb / replaced-by-release) and
  `.agents/project/taken.json` (new kind `take-declaration` / owner / living); stewardship modes rows.
- Tests: `test_taken.py` 300-304 (fresh fixture host takes both adapters, serves `.claude/settings.json`
  + `.codex/hooks.json`, `check: 0 gate(s) failed`); `test_280` now proves the take accounted in its
  own plane (the pinned lock carries no `not-issued` path).

**Not built (C1b)**
- **Migration of a host whose takes sit inside its pinned tree** (ADR-018 consequence: `upgrade` moves
  each `not-issued` path into `.agents/taken/<id>/` and writes its row). Not small: `upgrade` delegates
  every write to `init`, which has no mode that relocates a vendor-tree path into another plane; needs
  its own slice. Such a host keeps working on the old `+unreleased` route.
- `adapters/README.md` still describes the ADR-014 take (copy into `kit/capabilities/` + manifest
  row); outside this slice's write set.
- The `take` verb does not take the host hold as a writer (it `arrive`s only) and is not journalled.
- The take row's `digest` and the estate's provenance pin carry the same measured value in two
  documents (ADR-018 decision 3 vs ADR-008 pin) -- a Cardinal III tension, recorded, not resolved here.

**Added — link C, slice C1a: THE ENFORCEMENT LINE (ADR-017 row C1, first part; UNFINISHED on host #0 — see Blocked)**
- **`enforcement` capability** (kit core, names no product): the host declares EDIT GATES in
  `.agents/project/enforcement/edit-gates.json` (schema `edit-gate`: a path pattern, a pattern over the
  text an edit INTRODUCES, `because`/`instead`, and a calibration pair `proves`/`admits`). The kit ships
  zero gates. `FF-EDIT-GATE` (kind `edit-gates-calibrated`) fails an uncalibrated gate. Gates judge the
  introduced text, never the whole file -- a ratchet: new lines are held, the edit repairing an old one
  is not refused.
- **`judge` verb -- the hook.** Vendored in the pinned kit; reads the product event on stdin; resolves
  `--surface <id>` to that surface's new `hands` block (dotted event keys for paths and introduced text,
  an optional patch grammar as two patterns, the refusal exit code). Holds no policy and no product
  (`test_291`). An event naming no path is REFUSED as unjudged; an uncalibrated gate is named as NOT
  APPLIED (and `check` fails it) rather than refusing every edit on its word. Refusal code KIT0043.
- **Served settings.** The runtimes served install offers a new `enforcement` view; `vendor` (the
  manifest's vendor plane root) joins the served frame so a template never spells `.agents/kit`. Adapters:
  claude-code serves `.claude/settings.json` (PreToolUse, `Write|Edit|MultiEdit|NotebookEdit`, blocks
  before the write); codex serves `.codex/hooks.json` (post_tool_use, `apply_patch`, flags AFTER the write
  -- codex has not proven `pre_exec_block`; ADR-017 decision 5). New CLI option `--surface`.
- Host #0 enables `enforcement` (`project.json`); `check: 0 gate(s) failed` with FF-EDIT-GATE PASS.
- Tests: `test_enforcement.py` 288-291.

**UNVERIFIED (Cardinal VII)**
- codex: every `tool_input.*` key and the apply_patch grammar in `hands`; the `.codex/hooks.json` location
  and exit-2 semantics on `post_tool_use` are taken from a prior hand-built system's receipts on this
  machine, not observed through THIS kit. claude-code keys and exit-2 PreToolUse refusal: same provenance.
- Neither product has been observed RUNNING the served hook. Windows 8.3 short vs long path forms are
  compared by `normcase`/`abspath` only.

**Blocked -- the host #0 live walk of served settings (GAP, owner door + a seam defect)**
- Taking an adapter on a host that carries a pinned kit is IMPOSSIBLE today: ADR-014 takes an adapter by
  placing it in the kit tree and adding a MANIFEST row, and ADR-016 holds that tree to its own lock.
  Measured on a scratch copy of host #0: `init --approve` pins both adapters and then refuses KIT0041
  (pinned kit no longer equals its lock, 11 paths); `check` fails FF-KIT-PINNED and FF-PROVENANCE-PINNED.
  Proposed cure (needs an ADR): a TAKEN capability resides outside the vendor tree in its own declared
  place, found by the manifest loader beside the pinned kit, pinned by provenance, never by the kit lock.
- The take is also a DOOR only the owner may walk; no agent approved it on host #0. On the scratch copy
  the served hook commands, run verbatim, refused a violating Claude Write (absolute Windows path, exit 2),
  passed a clean Edit (exit 0), refused a violating codex patch (exit 2) and an unreadable event (exit 2).

The host tree meets the drawn floor (link L3a of ADR-015's line), and the last thing that kept it
from meeting it: a declared empty directory could not survive a clone.

**Fixed within C1a -- the suite made green again (4 failures, each at its root)**
- `KIT0043` was appended but the registry's `issued` high-water mark stayed 42; now 43
  (`test_180` held the density law, correctly).
- `test_260` asserted the host's law in EVERY document render; it now selects by the render's
  declared VIEW -- only a view with a section reading the binding plane carries law. A settings
  file is not a briefing; the design was right, the test inferred shape from "not a directory".
- `test_264` built its third runtime as "briefing = document, every other view = collection", a
  privileged view name: the `enforcement` document became a collection with no `over`
  (`KeyError`). The copied row now keeps the SHAPE of the row it copies; interpreter untouched.

**Fixed**
- **A declared space now survives the repository.** `mode: space` and a collection projection over
  a set the host has not filled each own a directory whose honest state is EMPTY. The kit made it;
  git carries files, not directories; the path was gone on the next checkout, and `FF-HOST-FLOOR`
  then reported a DRAWN path as MISSING on a host where nothing was wrong (Cardinal VII — the kit
  and git agreed on the name and disagreed on whether it existed, each locally right). The emptiness
  is now carried in a form both read the same way: one marker, written UNCONDITIONALLY into every
  declared space and every collection projection, and PLANNED rather than applied as a side effect
  (a path the plan did not promise is a path nothing renders). Its sentence states the space and
  never its contents, because a marker that appeared only in EMPTY collections was a variation
  between hosts with no declared cause.
- `.agents/project/roles/`, `.agents/generated/roles/` and `.agents/generated/runtimes/` — three
  drawn paths — are present on host #0, which now checks with **0 gates failed**.

**Added — link L3b: the layout is the RECORDS MAP (ADR-015 amendment 8)**
- **Every drawn host place declares its record keeping.** Each of the 29 `host_layout` entries now
  carries `holds` (the kind of truth living there), `writer` (who may write it), `read_when` (the task
  triggers that pull it into context) and `lifecycle` (how it ages, ISO 15489's disposition) --
  pending places included, because a place with no content yet still has a declared home.
- **`record_keeping`, an OPEN vocabulary** (`capabilities/governance/record-keeping.json`, schema
  `record-keeping`): three registries -- 26 `kinds`, 11 `writers`, 10 `lifecycles` -- each a list of
  `{id, summary}`. The schema bounds the shape of a row, never the set of rows.
- **`FF-RECORDS-DECLARED`** (`reference-declared-across`, floor `enforce`): every `holds`, `writer`
  and `lifecycle` resolves to a vocabulary row; calibrated per reference; no new gate kind.
- **`.agents/generated/INDEX.md`, the map projected** (`payload/RECORDS-MAP.md.mustache`): one row
  per place with its four words and its state -- `PENDING -- link X`, `ONLY WITH <capability>` or
  `always` -- then the three registries as legends. `.agents/generated/governance/INDEX.md` is
  unchanged. The floor row loses `pending: L3b`.

**Changed -- an EXPAND, not a version move (ADR-009 rule 5)**
- The four fields are OPTIONAL in `layout` v1. Required would be breaking (rule 5), would refuse
  `docs/reference/UPSTREAM-LAYOUT.json` (the upstream box, not yet mapped) and adapter `floor` rows,
  and rule 6 would demand a migration whose only step cannot exist: `holds`/`writer`/`lifecycle`
  are judgements no pure step can derive. Presence on every host place is held by
  `test_285` over the one shipped declaration. CONTRACT (const 2, required) is owed once the upstream
  box and adapter floor rows are mapped.

**Added**
- **`space.marker` — a capability declares how a directory is carried.** The marker's FILENAME
  (`.gitkeep`, the field's own convention, so it explains itself to a reader who has never met this
  kit) is a DECLARATION in the capability that can never be disabled, not a constant in an
  interpreter: a filename written into a host is policy, and a path segment no declaration carries
  is a name no host was ever told. Schema-bound; `KIT0042` refuses a kit where no capability
  declares one, or more than one does. `kit/interpreters/space.py` is its one home.

**Changed**
- `test_90`/`test_100` asserted *the plane holds nothing, the same fact told by the filesystem*.
  That was true of a filesystem and false of a clone; they now assert the stronger claim — no page
  is projected, and the space still exists.

## 0.1.5 — unreleased

The host carries its kit (ADR-016, link B of ADR-015's line). Until now a host held doctrine pages
and no interpreter, and was driven from outside by a framework checkout.

**Added**
- **The pinned kit.** `governance` installs the WHOLE kit — every path its lock enumerates,
  verbatim, beside the lock — at `.agents/kit/pinned/` (install mode `pinned`, steward `release`). A
  host runs `python .agents/kit/pinned/interpreters/cli.py <verb> --root .` with no framework on the
  machine. The tree is staged and swapped in by rename (`Workspace.write_tree`).
- **What a release is.** A kit whose bytes equal its own lock; identity = SHA-256 of that lock. A
  working tree pins as `X.Y.Z+unreleased`. `release` states the identity — and `authenticity NOT
  ESTABLISHED`, because the lock is not signed — or refuses a working tree.
- **`--kit git+<repo>@<rev>#subdirectory=<dir>`**: a release read at a revision, never a working tree.
- Gate `FF-KIT-PINNED`; diagnostic `KIT0041`; every run's first line names the kit that spoke.

**Not recorded:** 0.1.3 and 0.1.4 shipped without a section here. The absence is declared, not
reconstructed.

## 0.1.2 — unreleased

Host choice, and the one door where a human stands. Until now a `capabilities` field existed that
no interpreter read as a CHOICE, so composition was proved as a property of DECLARATIONS and never
of a host's decision — and the interesting failures live exactly there.

**Added**
- **Selection.** `--enable` / `--disable` author the answers file *before it exists*; afterwards
  `.agents/project/project.json` IS the set and a flag that contradicts it is refused. `select` is
  a pure function beside `classify` and `compose`: it refuses an id no capability declares, and it
  reads `never_disabled` — which now decides something instead of describing an intention.
- **`--plan`**, a flag on every verb declaring `MUTATES`, never a sixth verb. It prints path,
  class, mode, owning capability and whether each path would be created, kept, replaced or
  removed, and exits without touching a byte. It is not a preview: each install mode has a
  FORESEE half and an APPLY half, and the apply is handed the foreseen disposition. A plan cannot
  drift from its apply because there is only one decision.
- **P3, the human door.** `init` measures, resolves and DRAFTS; nothing else is written until an
  owner approves with `--approve <who>`, recorded as `signed_by` / `signed_at`. An install whose
  approval never came is a dated `draft` on disk with its own exit code (3), and every verb
  declaring `REQUIRES_APPROVED_HOST` refuses while it stands, naming the date.
- Verb-declared preconditions, read generically: the CLI still knows no verb's name.
- Acceptance grew from 27 to 31 assertions and was split into `harness.py` + three suites; the
  disposition vocabulary is now IMPORTED by the tests rather than restated in them.

**Changed**
- `enabled_capabilities` and `render` no longer hold the answers-file path as a constant: the path
  and its schema are found by asking the DECLARATIONS which install works in that mode.
- The blocked-provision clause is written where the block was decided, so a refusal says
  *cannot support* (a measured fact) or *chose to disable* (a decision), not merely *missing*.

**Fixed**
- Looking up the answers file refused before the composition refusal that explained why the
  declaration was missing — the slice-B failure shape, in a new layer. Zero installs in a mode is
  now refused only where the answer is needed; two is always refused.

## 0.1.1 — unreleased

The second capability, and therefore the first time composition is exercised rather than designed.

**Added**
- `resolver.py`: composition semantics as a pure function over declarations — no port, no state,
  no capability's name. `classify` measures and never refuses; `compose` refuses and never
  measures. `requires` of kind `capability` is matched against what capabilities **provide**;
  ordering is topological with a sorted frontier, so it cannot depend on declaration order;
  `conflicts` and shadowed install paths are refused before the first byte.
- `capabilities/knowledge/`: a document's KIND decides whether it may declare a rule. Diátaxis
  crossed with MADR (canonical `docs/decisions/`, adopted rather than invented) and the Kind Law.
- Gate kind `title-claim-within-authority` (`FF-KIND-AUTHORITY`): compares a name's CLAIM with a
  location's GRANT, both arriving as declaration data. It reads no content, because authority
  was never a property of prose.
- Eight composition assertions, each negative case built from a throwaway copy of the real kit
  with its declarations patched — no real capability was deformed to manufacture a failure.

**Changed**
- `init` reports the reading and every unavailable capability BEFORE the set is composed. Adding
  capability-level requirements had made the refusal fire first, so the honest report of a
  measured absence — slice A's `unavailable governance` — was swallowed by its own consequence.
  The assertion that caught it was right; the design was wrong, and the design moved.

## 0.1.0 — unreleased

The walking skeleton: one capability, three verbs, four ports, and an acceptance test that
installs into a repository the kit has never met.

**Added**
- `MANIFEST.json` declaring four classes, four planes, one capability, three detectors and the
  schema registry; schemas for manifest, capability, project, profile and detector.
- Ports: `Manifest` (the only reader of declarations, validating each as it reads),
  `Workspace` (root measured once, writes confined to a declared scope), `Probe` (the single
  generic detector evaluator, with an open registry of evidence kinds), `Clock` (so a reading can
  state when it was taken).
- Verbs `init`, `render`, `check`, discovered by name from `interpreters/verbs/`.
- `template.py`: a Mustache subset, so the projection renderer needs no dependency and cannot
  branch.
- Gates `FF-BINDING-SCHEMA-*`, `FF-KIT-CLASS`, `FF-KIT-PROJECTION`, `FF-READING-FRESH`, declared by
  the capability and interpreted by kind.
- `tests/acceptance/fresh-repo/`: eleven assertions against a scratch git repository.

**Fixed, in the half that existed before anything had ever been run**
- `capabilities/governance/payload/INDEX.md.mustache` was Handlebars (`{{#each}}` / `{{this.x}}`)
  under a Mustache name. Rewritten as Mustache; the renderer refuses the syntax that was there.
- Detector declarations had no schema and were therefore the only unvalidated declarations in the
  kit. Added `schemas/detector.schema.json` and registered it in the manifest.
- A malformed host binding surfaced as a Python traceback instead of a named refusal. Added
  `errors.KitError`, read every binding through its schema, and gave the entry point one line and
  a non-zero exit.
- The console was assumed to be UTF-8 and was not; the kit now measures and sets that boundary
  before it prints.

**Deliberately not built** — `upgrade`, `eject`, `kit.lock.json`, roles, playbooks, runtime
descriptors, and adoption of a non-empty repository.
