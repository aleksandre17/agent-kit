"""The kit's entry point. It resolves a verb by name and hands it a context -- nothing else.

Verbs are discovered from `verbs/`: a new verb is a file, never an edit here. The CLI knows no
verb's name, no capability, no path convention beyond the one it was given at the boundary.

    python kit/interpreters/cli.py <verb> --root <host-repo> [--kit <kit-dir>]
"""

from __future__ import annotations

import argparse
import importlib
import os
import shutil
import sys
from pathlib import Path

#: The interpreter lives INSIDE the payload it ships, so importing itself would drop bytecode
#: into the one tree whose entire premise is that every path resolves to a declared class. That
#: is not a tidiness problem and it is not git's problem: it is the kit reproducing, against
#: itself, the condition it exists to prevent. Set before the first kit module is imported, so
#: nothing is written; `kit.lock.json` is the other half, which refuses to ship what appears
#: anyway. A fence hides the state; this stops producing it.
sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
#: Every family of modules under the interpreter, DISCOVERED. A hand-kept list of the families
#: would be a closed enumeration in the one file that is supposed to know no family's name: the
#: first time a capability brought a new kind of module, the entry point would need an edit.
for extra in [HERE, *sorted(p for p in HERE.iterdir()
                            if p.is_dir() and not p.name.startswith("_"))]:
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

import clock as clock_port  # noqa: E402
import observation  # noqa: E402
import pin  # noqa: E402
from context import Context  # noqa: E402
from errors import KitError  # noqa: E402


def measure_console() -> None:
    """The console is a boundary like any other: the kit writes UTF-8 and says so, rather than
    inheriting whatever code page the host shell happened to start with and garbling its own
    report. Measured once, here, before a byte is printed."""
    for stream in (sys.stdout, sys.stderr):
        if getattr(stream, "encoding", "").lower().replace("-", "") != "utf8":
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, ValueError):  # a stream that cannot be reconfigured
                pass


def available_verbs() -> list[str]:
    return sorted(p.stem for p in (HERE / "verbs").glob("*.py") if not p.stem.startswith("_"))


def main(argv=None) -> int:
    measure_console()
    verbs = available_verbs()
    parser = argparse.ArgumentParser(prog="kit", description="Install and hold an agent kit in a host repository.")
    parser.add_argument("verb", choices=verbs, help="one of the declared verbs")
    parser.add_argument("--root", required=True, help="the host repository to act on")
    parser.add_argument("--kit", default=str(HERE.parent),
                        help="the kit payload directory, or a release SOURCE read at a revision: "
                             "git+<repo>@<rev>#subdirectory=<dir> (ADR-016)")
    parser.add_argument("--plan", action="store_true",
                        help="print the exact set of writes and exit without touching a byte")
    parser.add_argument("--enable", type=_ids, default=None,
                        help="this host's set is exactly these capabilities (comma-separated)")
    parser.add_argument("--disable", type=_ids, default=None,
                        help="this host's set is every available capability except these")
    parser.add_argument("--approve", default=None,
                        help="walk a door: accept what is drafted or declared, recorded by name")
    parser.add_argument("--break-lock", default=None, metavar="WHO",
                        help="break a hold that is standing on this host, by name: a DECLARATION "
                             "that the run holding it is dead. No machine may make it, and no "
                             "amount of elapsed time makes it for anyone")
    parser.add_argument("--card", default=None, help="the card a verb acts on, by id")
    parser.add_argument("--to", default=None, help="the state a card is being moved to")
    parser.add_argument("--by", default=None, help="who is making this move, recorded on the card")
    parser.add_argument("--path", type=_ids, default=None,
                        help="the host path(s) a verb acts on (comma-separated)")
    parser.add_argument("--surface", default=None,
                        help="the runtime surface a verb speaks through, by id -- how a served hook "
                             "says which product handed it the event on stdin")
    parser.add_argument("--map", default=None,
                        help="a migration map: the host's signed statement of what becomes of "
                             "its prior agent system (ADR-011)")
    parser.add_argument("--roster", default=None, metavar="DIGEST",
                        help="the digest of the succession roster a door accepts, as --plan printed "
                             "it: the act refuses if the roster it reads now is not this one (ADR-012)")
    args = parser.parse_args(argv)

    host = Path(args.root).resolve()
    if not host.is_dir():
        print(f"kit: --root {host} is not a directory", file=sys.stderr)
        return 2

    # A release SOURCE is resolved here, at the boundary, into a directory holding exactly that
    # revision -- and refused if that revision is not a release. The scratch it lands in is outside
    # every host and is removed however the run ends (ADR-016).
    kit_root, scratch = Path(args.kit), None
    if pin.is_source(args.kit):
        kit_root, scratch = pin.fetched(args.kit)
    try:
        return _run(args, host, kit_root)
    finally:
        if scratch is not None:
            shutil.rmtree(scratch, ignore_errors=True)


def _run(args, host: Path, kit_root: Path) -> int:
    ctx = Context(kit_root=kit_root, host_root=host,
                  clock=clock_port.from_environment(os.environ))
    module = importlib.import_module(args.verb)

    # What a verb may be ASKED for is a property the verb declares, read generically. The CLI
    # still knows no verb's name: a verb that writes nothing says so, and asking it for a plan is
    # refused rather than answered with an empty one -- an empty plan reads as "nothing to do".
    if args.plan and not getattr(module, "MUTATES", False):
        print(f"kit: {args.verb} writes nothing, so there is nothing to plan", file=sys.stderr)
        return 2

    # WHICH kit is speaking is stated on the first line of every run. A host that carries its own
    # pinned kit and a host driven from a working tree read identically otherwise -- and the one
    # question a reader of any output must be able to answer is what actually ran (ADR-016).
    print(f"kit {ctx.manifest.version} · {args.verb} · {host.as_posix()} · "
          f"kit at {ctx.manifest.root.as_posix()}")

    # Whatever the enabled capabilities declared should watch a run like this one is opened HERE
    # -- before the verb, before even the precondition that could refuse it -- and closed in a
    # `finally`. The order is the whole guarantee and it is the one thing that cannot be added
    # afterwards: a record written only at the end says nothing about a run that never reached
    # the end, and a run that dies mid-way leaves work that reads exactly like finished work.
    # A process that is KILLED never reaches the close, and its record stays open forever. That
    # is the mechanism succeeding, not failing.
    watching = observation.opened(ctx, args, module, args.verb)
    code, message = 1, None
    try:
        if getattr(module, "REQUIRES_APPROVED_HOST", False):
            ctx.require_approved()
        code = module.run(ctx, args)
        return code
    except KitError as refusal:
        # A refusal is an ENDING. The run was turned away, said why, and did not vanish -- and a
        # record unable to tell those two apart would be the one lie this exists to prevent.
        code, message = refusal.exit_code, str(refusal)
        raise
    except BaseException as unforeseen:  # noqa: BLE001 -- re-raised; only the record is added
        message = f"{type(unforeseen).__name__}: {unforeseen}"
        raise
    finally:
        observation.closed(watching, code, message)


def _ids(text: str) -> list:
    return [part.strip() for part in text.split(",") if part.strip()]


def guarded(argv=None) -> int:
    try:
        return main(argv)
    except KitError as refusal:
        # The code leads, bracketed, so a machine matches `^kit: \[(\w+)\] ` and never the prose
        # (ADR-005). A refusal with no code says so -- an honest absence, never an invented code.
        print(f"kit: [{refusal.code or 'uncoded'}] {refusal}", file=sys.stderr)
        return refusal.exit_code


if __name__ == "__main__":
    raise SystemExit(guarded())
