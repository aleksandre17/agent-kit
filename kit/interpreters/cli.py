"""The kit's entry point. It resolves a verb by name and hands it a context -- nothing else.

Verbs are discovered from `verbs/`: a new verb is a file, never an edit here. The CLI knows no
verb's name, no capability, no path convention beyond the one it was given at the boundary.

    python kit/interpreters/cli.py <verb> --root <host-repo> [--kit <kit-dir>]
"""

from __future__ import annotations

import argparse
import importlib
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for extra in (HERE, HERE / "ports", HERE / "verbs", HERE / "gates"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

import clock as clock_port  # noqa: E402
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
    parser.add_argument("--kit", default=str(HERE.parent), help="the kit payload directory")
    parser.add_argument("--plan", action="store_true",
                        help="print the exact set of writes and exit without touching a byte")
    parser.add_argument("--enable", type=_ids, default=None,
                        help="this host's set is exactly these capabilities (comma-separated)")
    parser.add_argument("--disable", type=_ids, default=None,
                        help="this host's set is every available capability except these")
    parser.add_argument("--approve", default=None,
                        help="walk a door: accept what is drafted or declared, recorded by name")
    parser.add_argument("--card", default=None, help="the card a verb acts on, by id")
    parser.add_argument("--to", default=None, help="the state a card is being moved to")
    parser.add_argument("--by", default=None, help="who is making this move, recorded on the card")
    args = parser.parse_args(argv)

    host = Path(args.root).resolve()
    if not host.is_dir():
        print(f"kit: --root {host} is not a directory", file=sys.stderr)
        return 2

    ctx = Context(kit_root=Path(args.kit), host_root=host,
                  clock=clock_port.from_environment(os.environ))
    module = importlib.import_module(args.verb)

    # What a verb may be ASKED for is a property the verb declares, read generically. The CLI
    # still knows no verb's name: a verb that writes nothing says so, and asking it for a plan is
    # refused rather than answered with an empty one -- an empty plan reads as "nothing to do".
    if args.plan and not getattr(module, "MUTATES", False):
        print(f"kit: {args.verb} writes nothing, so there is nothing to plan", file=sys.stderr)
        return 2

    print(f"kit {ctx.manifest.version} · {args.verb} · {host.as_posix()}")
    if getattr(module, "REQUIRES_APPROVED_HOST", False):
        ctx.require_approved()
    return module.run(ctx, args)


def _ids(text: str) -> list:
    return [part.strip() for part in text.split(",") if part.strip()]


def guarded(argv=None) -> int:
    try:
        return main(argv)
    except KitError as refusal:
        print(f"kit: {refusal}", file=sys.stderr)
        return refusal.exit_code


if __name__ == "__main__":
    raise SystemExit(guarded())
