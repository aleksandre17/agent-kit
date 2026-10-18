"""start -- carry a host from nothing to a served, checked install in one door, by a STARTER.

    python kit/interpreters/cli.py start --root <host> --path starters/<id>.json --plan
    python kit/interpreters/cli.py start --root <host> --path starters/<id>.json --approve <who>

Every act a new host needs already has its own door: `init` drafts and accepts the answer, `take`
places what the release did not issue, `render` serves, `activate` points a setting outside the
tree. A host that walks them by hand walks seven doors and writes two kinds of declaration in JSON
nobody showed it. A STARTER (published beside the kit, like an adapter or a bundle) declares that
walk once: what to take, which runtimes to serve, which surfaces to activate. This verb holds none
of it (ADR-023).

It is ONE door because it is one decision -- "this host starts from this starter" -- and the name
given is recorded on every act it carries out. Each act is the verb a person would have run, as a
separate run of this same kit, printed with its exit; the first that fails stops the walk, and what
already landed stays, because every one of those verbs is safe to walk again. The host's own
answers -- each doctrine stance, each law -- stay unanswered and are named as such: a starter
decides what a host RUNS, never what it HOLDS.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import doors
import ephemeral
import hostlock
import take as take_verb
import serving
from context import Context
from errors import KitError

SUMMARY = "carry a host from nothing to a served, checked install in one door, by a published starter"
MUTATES = True
REQUIRES_APPROVED_HOST = False
#: Every write is an act of its own run, observed by that run's own record; this run's two
#: in-process writes (the answer's set, the runtime declarations) are each one atomic write of a
#: declaration that the next `start` writes again (ADR-023 amendment 1).
DELEGATES = True

#: The schema a starter honours, by the name the manifest registers it under.
SCHEMA = "starter"


class StartError(KitError):
    """A starter that is not one, or an act of the walk that failed."""

    code = "KIT0073"


def _starter(ctx, args, declaration: str) -> tuple:
    if not args.path or len(args.path) != 1:
        raise StartError("start needs --path <starter.json>: the one published starter this host starts from")
    path = Path(args.path[0]).resolve()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StartError(f"{path.as_posix()}: not readable as a starter -- {exc}") from exc
    errors = ctx.manifest.validate(raw, SCHEMA)
    if errors:
        raise StartError(f"{path.as_posix()} does not declare a starter:\n  " + "\n  ".join(errors))
    takes = [(path.parent / rel).resolve() for rel in raw["takes"]]
    missing = [t.as_posix() for t in takes if not (t / declaration).is_file()]
    if missing:
        raise StartError(f"{raw['id']}: takes no capability at {', '.join(missing)}")
    return raw, takes


def _ids(takes, declaration: str) -> list:
    return sorted(json.loads((t / declaration).read_text(encoding="utf-8"))["id"] for t in takes)


def run(ctx, args) -> int:
    # A host another run is holding is refused before the walk: its first act would be refused by
    # the hold, and that refusal must never read as the draft the walk expects (ADR-007).
    hostlock.arrive(ctx, args)
    # What a take reads to know a capability is the take plane's own declaration, never a filename.
    declaration = take_verb.homes(ctx)[0]["declaration"]
    starter, takes = _starter(ctx, args, declaration)
    who = args.approve
    taken = _ids(takes, declaration)
    # The opening acts install the kit into a host that has none. A host that has already accepted
    # its answer has the kit: its closing `init` re-attests what this walk changes, and the opening
    # one would only judge, before the walk could repair it, a reading the walk is about to retake.
    accepted = doors.walked(ctx.host_answers(required=False) or {})
    walk = [] if accepted else [("init", []), ("init", ["--approve", who or "<who>"])]
    walk += [("take", ["--path", ",".join(t.as_posix() for t in takes), "--approve", who or "<who>"]),
            ("enable", taken), ("runtimes", [r["id"] for r in starter["runtimes"]]),
            # A take may bring a detector (a product's adapter reads that product's file), so the
            # reading the first `init` took can be stale now: the walk re-reads it through its door.
            ("retake", ["--approve", who or "<who>"]), ("render", []),
            # From the first day a change is weighed by where it lands and proved by what proves that place:
            # the areas are drafted from the modules a build tool declares (only added, never rewritten).
            ("areas", ["--approve", who or "<who>"])]
    # Activation precedes the attesting init: that init ends in `check`, and a served setting not
    # yet pointed at what it serves is a failure `check` must report, not one to walk past. That check
    # is the walk's last: a second one on the same bytes would prove nothing new (Cardinal IX).
    walk += [("activate", ["--surface", s, "--approve", who or "<who>"]) for s in starter["activate"]]
    walk += [("init", ["--approve", who or "<who>"])]
    print(f"start: {starter['id']} -- {starter['summary']}")
    for verb, words in walk:
        print(f"  {verb}  {' '.join(words)}")
    if args.plan:
        return 0
    if not who:
        doors.refuse(f"this host would start from {starter['id']!r}: {len(walk)} act(s), each recorded "
                     f"under one name", "person who owns this host",
                     "start --root <host> --path <starter.json> --approve <who>",
                     "Starting a host decides what it runs; the record of every act names who decided.")

    host, kit = ctx.workspace.root, ctx.manifest.root
    said: list = []
    try:
        for verb, words in walk:
            if verb == "enable":
                _enable(kit, host, ctx.clock, words)
            elif verb == "runtimes":
                _runtimes(kit, host, ctx.clock, starter["runtimes"])
            else:
                said.append(_act(kit, host, verb, words, args))
    finally:
        kept = _keep(ctx, said)
    # The closing check's own verdict, as it said it -- a failure held under a stance that does not fail
    # check is still a failure, and a walk that ends green never reads as one that ended clean (CWE-223).
    for line in (said[-1][2].splitlines() if said else []):
        if line.startswith("check:"):
            print(f"  {line}")
    print(f"start: {starter['id']} carried this host to a served, checked install by {who}; "
          f"what it HOLDS -- each stance, each law -- is still the host's to answer. Every act's whole "
          f"output: {kept}")
    return 0


def _keep(ctx, said: list) -> str:
    """Every act's whole output, in the plane that holds what a run leaves behind: a walk prints one line
    per act, and the rest is kept, never dropped (CWE-222)."""
    rel = ephemeral.place(ctx, "start.log")
    ephemeral.scope(ctx).write_text(rel, "".join(
        f"$ {verb} {' '.join(words)}\n{output}\n" for verb, words, output in said))
    return rel


def _act(kit: Path, host: Path, verb: str, words: list, args) -> tuple:
    argv = [sys.executable, "-I", "-B", str(Path(__file__).resolve().parent.parent / "cli.py"), verb,
            "--root", str(host), "--kit", args.kit, *words]
    ran = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8")
    drafted = verb == "init" and not words and ran.returncode == doors.PendingApproval.exit_code
    print(f"  [{verb} exit {ran.returncode}{' -- drafted, as the walk expects' if drafted else ''}]")
    if ran.returncode != 0 and not drafted:
        raise StartError(f"the walk stopped at `{verb} {' '.join(words)}` (exit {ran.returncode}):\n"
                         + (ran.stdout + ran.stderr).strip())
    return verb, words, ran.stdout + ran.stderr


def _answers(kit: Path, host: Path, clock) -> tuple:
    ctx = Context(kit_root=kit, host_root=host, clock=clock)
    item = ctx.install_of_mode("declaration")
    owner = next(c for c in ctx.manifest.capabilities for i in c.installs if i["target"] == item["target"])
    return ctx, item, owner


def _enable(kit: Path, host: Path, clock, ids: list) -> None:
    ctx, item, owner = _answers(kit, host, clock)
    answer = ctx.binding(item["target"], item["validates"])
    enabled = sorted(set(answer["capabilities"]) | set(ids))
    if enabled != answer["capabilities"]:
        ctx.workspace.scoped(owner.targets()).write_json(item["target"], {**answer, "capabilities": enabled})
    print(f"  [enable {', '.join(ids)}]")


def _runtimes(kit: Path, host: Path, clock, runtimes: list) -> None:
    """Each runtime instance, in the declaration the SERVING capability composes its instances from
    -- found by the shape it serves, never by a name -- and validated by that declaration's schema."""
    ctx = Context(kit_root=kit, host_root=host, clock=clock)
    server = next(c for c in ctx.manifest.capabilities
                  if any(i.get("shape") == serving.SHAPE for i in c.installs))
    item = next(i for i in server.installs if i.get("reads_as") == server.raw["composes"]["instances"])
    ws = ctx.workspace.scoped(server.targets())
    written, kept = [], []
    for row in runtimes:
        rel = f"{item['target'].rstrip('/')}/{row['id']}.json"
        if ctx.workspace.exists(rel):  # the host's own instance stands: kept, and said to be
            kept.append(row["id"])
            continue
        document = {"schema_version": ctx.manifest.version_of(item["validates"]), **row}
        errors = ctx.manifest.validate(document, item["validates"])
        if errors:
            raise StartError(f"the starter's runtime {row['id']!r} does not honour "
                             f"{item['validates']!r}:\n  " + "\n  ".join(errors))
        ws.write_json(rel, document)
        written.append(row["id"])
    print(f"  [runtimes written: {', '.join(written) or 'none'}"
          + (f"; the host's own kept: {', '.join(kept)}" if kept else "") + "]")
