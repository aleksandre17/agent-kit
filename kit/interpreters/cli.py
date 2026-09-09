"""The kit's entry point. It resolves a verb by name and hands it a context -- nothing else.

Verbs are discovered from `verbs/`: a new verb is a file, never an edit here. The CLI knows no
verb's name, no capability, no path convention beyond the one it was given at the boundary.

    python kit/interpreters/cli.py <verb> --root <host-repo> [--kit <kit-dir>]
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for extra in (HERE, HERE / "ports", HERE / "verbs"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

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
    args = parser.parse_args(argv)

    host = Path(args.root).resolve()
    if not host.is_dir():
        print(f"kit: --root {host} is not a directory", file=sys.stderr)
        return 2

    ctx = Context(kit_root=Path(args.kit), host_root=host)
    module = importlib.import_module(args.verb)
    print(f"kit {ctx.manifest.version} · {args.verb} · {host.as_posix()}")
    return module.run(ctx, args)


def guarded(argv=None) -> int:
    try:
        return main(argv)
    except KitError as refusal:
        print(f"kit: {refusal}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(guarded())
