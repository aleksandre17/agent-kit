# The records map — where everything lives

> PROJECTION. Do not edit: delete this whole plane and run `render`, and it comes back byte-identical.
> Kit version 0.4.2. Projected from governance's `host_layout` declaration and its
> `record_keeping` vocabulary (ADR-015 amendment 8).

Consult this map INSTEAD of searching the tree. Find the row whose **read when** matches the task in
front of you, and read that place; to write, find the row that **holds** what you are about to
write, and write only there, only if you are its **writer**. A place marked PENDING is declared and
has no real content yet: it names the link that will give it content. It is not missing, and
nothing belongs in it until then. A place marked ONLY WITH a capability exists on a host that has
enabled that capability.

Rows are in the declaration's order, which walks the planes: the pinned kit, the host's own
declarations, knowledge, projections, runtime state, automation, then the documentation and work
planes.

| place | holds | writer | read when | lifecycle | state |
| --- | --- | --- | --- | --- | --- |
| `.agents/kit/` | pinned-release | kit-publisher | how does the kit work; a gate fails and its rule must be read; which schema governs this document; run the kit offline;  | replaced-by-release | always |
| `.agents/taken/` | pinned-release | kit-verb | which capabilities this host added to its release; a runtime adapter was taken; a take fails its integrity gate;  | replaced-by-release | always |
| `.agents/project/taken.json` | take-declaration | owner | what did this host take beside the release; who took a capability and when; take or drop an adapter;  | living | always |
| `.agents/project/project.json` | host-declaration | owner | which capabilities are enabled; what this project is; enable or disable a capability;  | living | always |
| `.agents/project/profile.json` | environment-reading | kit-verb | what tooling this repository uses; a check reports the reading stale; why was the install adapted this way;  | current-only | always |
| `.agents/project/kit.lock.json` | integrity-pin | kit-verb | which kit version is installed; verify the pinned copy; upgrade the kit;  | replaced-by-release | always |
| `.agents/project/roster.json` | staffing | owner | who handles this kind of work; dispatch a task to an agent; add or retire a role;  | living | ONLY WITH roles |
| `.agents/project/roles/` | role-definition | owner | define or change a role; why an agent behaves as it does; a role overlay names an unknown archetype;  | living | ONLY WITH roles |
| `.agents/project/doctrine/` | host-law | owner | which laws bind this project; review a change against the rules; amend a law;  | living | ONLY WITH doctrine |
| `.agents/project/doctrine/law-scopes.json` | host-law | owner | which directories carry laws of their own; declare or remove a module's laws; a scoped law is refused;  | living | ONLY WITH governance |
| `.agents/project/doctrine/laws/` | host-law | owner | what a module's own laws say; amend a scoped law;  | living | ONLY WITH governance |
| `.agents/knowledge/private/` | private-memory | owning-role | start a session as a role; the owner corrected this before; record a lesson learned;  | curated | PENDING — link E |
| `.agents/knowledge/shared/` | shared-knowledge | curator | coordinate with another agent; a fact more than one role relies on; promote a lesson to the team;  | curated | PENDING — link E |
| `.agents/generated/roles/` | projection | renderer | load a role's full brief; a role file looks out of date;  | regenerable | ONLY WITH roles |
| `.agents/generated/skills/` | projection | renderer | which skills are available; load a skill for this task;  | regenerable | PENDING — link C |
| `.agents/generated/INDEX.md` | projection | renderer | where does this live; where should I write this; start any task; before searching the tree;  | regenerable | always |
| `.agents/generated/runtimes/` | projection | renderer | how a runtime is wired; a runtime adapter file is stale;  | regenerable | ONLY WITH runtimes |
| `.agents/runtime/receipts/` | run-evidence | runtime-observer | did the run actually do it; audit what an agent changed; a claim of green needs evidence;  | rotated | ONLY WITH observability |
| `.agents/runtime/telemetry/` | measurement-stream | runtime-observer | how much did this cost; token usage per agent; which runs are wasteful;  | rotated | PENDING — link C |
| `.agents/runtime/ground/` | dispatch-ground | dispatcher | receive a dispatch; what is already verified; brief an agent;  | current-only | ONLY WITH operating |
| `.agents/runtime/guards/` | guard-state | runtime-observer | a hook blocked an edit; why was this write refused;  | current-only | PENDING — link C |
| `.agents/runtime/init.journal` | operation-journal | kit-verb | init was interrupted; resume or recover an install; what did the last install do;  | per-operation | always |
| `.agents/runtime/init.lock` | exclusive-hold | kit-verb | a kit command says the host is held; clear a stale hold;  | per-operation | always |
| `docs/intent/` | intent | owner | why are we building this; what does the owner want; judge whether work serves the goal;  | living | PENDING — link F |
| `docs/decisions/` | decision | decision-authority | why is it built this way; a change crosses a boundary; propose an architecture change; is this already decided;  | permanent | ONLY WITH knowledge |
| `docs/reference/` | reference | curator | look up a register or ledger; which standards are adopted; what is the current drawing;  | living | ONLY WITH knowledge |
| `docs/guides/` | guide | curator | how do I do this; set up the project; run a procedure step by step;  | living | PENDING — link F |
| `docs/work/CONTINUE-HERE.md` | work-position | dispatcher | resume work; start a new session; what is next;  | current-only | PENDING — link F |
| `docs/work/BOARD.md` | work-queue | dispatcher | what is in flight; pick the next task; plan the work;  | living | ONLY WITH delivery |
| `docs/work/cards/` | work-card | assigned-agent | take a task; what does done mean for this task; update a task's state;  | closed-then-archived | ONLY WITH delivery |
| `docs/work/evidence/` | work-evidence | assigned-agent | prove a card is done; record an audit or probe; what did the investigation find;  | closed-then-archived | ONLY WITH delivery |
| `docs/archive/` | retired-record | archivist | what was decided before and retired; history of a closed piece of work;  | archived | PENDING — link F |

## What a place may hold

| kind | meaning |
| --- | --- |
| pinned-release | A verbatim copy of one published kit release. The host runs it and never edits it; a change here is a change of release, not of content. |
| integrity-pin | Which release a host was given and the digests that prove the copy is that release. Read to verify, never to learn. |
| take-declaration | What a host added beside its pinned release: one row per taken capability, with where it came from, the digest of its copy, who took it and when. Stated by the owner, never by the publisher. |
| environment-reading | A measurement of the host as it was found, stamped with the moment it was taken. True of that moment only. |
| host-declaration | The host's own answers: what this project is and which capabilities it enables. Stated, not measured. |
| staffing | Who is on the team: which roles are filled, by what, for which work. |
| role-definition | What one role is: the archetype it composes and the host's delta over it. |
| host-law | Binding doctrine this host adds over the kit's: laws a gate or a reviewer may hold work to. |
| private-memory | What one role learned and keeps for itself: corrections, validated approaches, its own open threads. |
| shared-knowledge | Curated facts more than one role must read the same way. The coordination plane, not a notebook. |
| projection | A surface derived from declarations. It carries no truth of its own: delete it and it comes back byte-identical. |
| run-evidence | What a run observably did: receipts and dispositions written as it happened. Evidence, never testimony. The specification's EVIDENCE class arrives here and at `work-evidence`: ours splits it by what produced the reading -- a run, or an agent doing a card. |
| measurement-stream | Accumulating measurements of cost and usage, one row per event, read in aggregate. |
| eviction-record | What a bounded artifact held before an accepted write removed it: the TEXT that left, with the moment it left and where it landed, or that it landed nowhere (ADR-020 decision 2). Append-only and unbounded, because it is the RECORD and the artifact it came from is the POSITION -- one artifact may hold only one of those, or currency becomes purchasable with history at the moment of most pressure. It is read to RECOVER, which is why it preserves the prose and not a digest of it: a digest proves that something was lost and returns nothing. Neither of the two journals beside it: an `operation-journal` records the steps of one operation and is cleared when it ends, and a `measurement-stream` accumulates numbers -- this accumulates what was TRUE, and nothing in it is ever compacted while no retention passage is declared. |
| dispatch-ground | Facts already verified for a dispatch, each with the instrument and the moment of its reading, so the receiver builds on them instead of re-deriving them. |
| guard-state | The live state an enforcement hook keeps between calls: counters, open holds, what it has already refused. |
| operation-journal | The step-by-step record of one mutating operation: what was intended and what was done, so an interrupted operation is recoverable and never reads as success. |
| exclusive-hold | The mark that one writer holds the host. Its presence is the fact; it carries nothing else. |
| automation-definition | Machine-run pipelines: what runs on which event, and which gates it holds a change to. |
| intent | Why the work exists and what outcome it serves: vision, goals, the owner's standing requirements. |
| decision | A binding choice with its context, the alternatives rejected and its consequences. Authoritative once accepted. The specification's DECISION, and its ARCHITECTURE class too: an architectural statement that BINDS is a decision, and one that merely describes the shape of the system is a `reference` -- the split is by authority, not by subject. |
| reference | Descriptive, current facts about the system -- drawings, models, explanations -- consulted, not followed. The specification's REFERENCE. A reference that accumulates rows is a `register`. |
| guide | How to do one task, step by step, for a reader who already knows what they want. The specification's GUIDE. |
| work-position | Where the work stands right now and the next move: the one page a resuming session reads first. The specification's CONTROL class -- ours is one page with one writer, because a control plane with two authors forks the moment both are right. |
| work-queue | The ordered set of work in flight and next, one line per card. |
| work-card | One unit of work: its outcome, its state, and the artifact each state produces. The specification's WORK class. |
| work-evidence | Reports produced while doing work -- audits, probes, measurements -- that support a card or a decision and hold no authority of their own. The specification's EVIDENCE class, narrowed to what a card produced; an unattached reading is a `report`. |
| contract | What two parts of the system promise each other: a schema, an interface, a protocol, a wire format. The specification's CONTRACT. It binds like a decision and differs in what it addresses -- a decision is answerable to a reason, a contract is answerable to the other side, and breaking one is a version, not an amendment. |
| register | An open, appended list that is the ONE home of some set -- a ledger, a roll, an index of what exists. The specification's REGISTER. Its authority is completeness, not prose: a register that is missing a row is wrong in a way a `reference` cannot be, because something read it as the whole set. |
| report | A reading of the system taken at a moment and published on its own account -- an audit, a probe, a measurement that no card commissioned. The specification's REPORT. It states what was found and when, binds nothing, and is replaced by the next reading rather than amended; evidence attached to a card is `work-evidence`. |
| historical | A document kept, where it is, for the record of what was once believed or done. The specification's HISTORICAL, and dead BY DECLARATION -- which is what distinguishes it from `retired-record`, dead by location: this one still sits among living documents and must therefore say so itself. |
| retired-record | A record no longer current, kept for its history. Dead by location: nothing here binds. |

## Who may write

| writer | meaning |
| --- | --- |
| kit-publisher | The upstream kit, through a release. No host hand writes here; a host that disagrees changes release. |
| kit-verb | A kit command that mutates the host (init, lock, upgrade), under the host hold and through its plan. |
| renderer | The render verb, and nothing else. A hand edit here is a defect that the next render erases. |
| runtime-observer | An observer or hook, recording what happened as it happened. No agent writes here by hand. |
| owner | The accountable human. Agents may draft; the write that makes it true is the owner's. |
| decision-authority | Whoever the host's governance lets accept a decision -- drafted by any role, accepted on record. |
| dispatcher | The session that dispatches work and holds the position: one writer, so the position cannot fork. |
| owning-role | The one role the place belongs to. Every other role reads, if it reads at all. |
| curator | Whoever promotes knowledge into a shared place: a row enters by curation, never by a passing write. |
| assigned-agent | The agent executing the card that produces the artifact, within that card's declared write set. |
| archivist | The act that retires a record: content arrives here only by transfer from its living place, never by authoring. |

## How a place ages

| lifecycle | meaning |
| --- | --- |
| replaced-by-release | Replaced whole when the host takes another release; the previous copy is not retained here -- its release is its archive. |
| regenerable | Destroyed and recreated at will from its declarations; never backed up, never migrated, never hand-kept. |
| current-only | Only the latest state is kept; each write replaces the last, and the moment it was taken travels with it so staleness is visible. |
| living | Amended in place by its writer for as long as it is true; version control is its history. |
| permanent | Never edited once accepted; superseded only by a new record that names it, and kept forever. |
| curated | Kept while it earns its place; reviewed, promoted or pruned by curation, never silently grown. |
| rotated | Appended while it is recent, kept for a declared retention window, then rotated out whole. |
| append-only | Only ever extended, never amended and never compacted: each line is true of the moment it was written and is not revisited when the world moves on. It differs from `rotated` in the one way that matters -- `rotated` declares a window after which content is dropped whole, and this declares that no such passage exists yet, so nothing may be dropped at all. A place whose content is the only surviving copy of something takes this and nothing weaker. |
| per-operation | Exists for one operation: made when it starts, cleared when it ends; its survival past the end is itself the signal of an interruption. |
| closed-then-archived | Active while its work is open; when the work closes it is transferred to the archive, never deleted. |
| archived | Terminal. Frozen as it was transferred; read for history, never amended, never binding. |
