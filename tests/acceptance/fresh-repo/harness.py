"""The acceptance harness -- scratch hosts, fixture kits, and how a run is READ.

Held apart from any suite for one reason: the vocabulary a run prints is the interpreter's, and
a test that keeps its own copy of it goes on passing after the interpreter has moved. Everything
here either measures the host or parses what the kit said; nothing here asserts anything.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
KIT = REPO / "kit"
CLI = KIT / "interpreters" / "cli.py"

#: Every family of modules under the interpreter, discovered rather than listed -- the same rule
#: the entry point follows, for the same reason: a list here would go stale the first time a
#: capability brought a new kind of module, and it would go stale silently.
for extra in [KIT / "interpreters", *sorted(p for p in (KIT / "interpreters").iterdir()
                                            if p.is_dir() and not p.name.startswith("_"))]:
    sys.path.insert(0, str(extra))

from manifest import Manifest  # noqa: E402
from plan import DISPOSITIONS  # noqa: E402
from workspace import Workspace, WriteScopeError  # noqa: E402

#: The disposition vocabulary is IMPORTED, never restated. A test that keeps its own copy of the
#: words the interpreter prints goes on passing after the interpreter changes them, and is then a
#: second correct reading of a system that has already moved.
ACCOMPLISHED = tuple(DISPOSITIONS.values())


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(root: Path, rel: str) -> dict:
    base = root / rel
    out = {}
    for dirpath, _dirs, files in os.walk(base):
        for name in files:
            whole = Path(dirpath) / name
            out[whole.relative_to(root).as_posix()] = sha(whole)
    return out

WHOLE_HOST = "."


def host_digest(root: Path) -> dict:
    """Every byte in the host except git's own store, which no verb here touches and which
    would otherwise make an honest comparison depend on somebody else's bookkeeping."""
    return {rel: digest_sha for rel, digest_sha in digest(root, WHOLE_HOST).items()
            if not rel.startswith(".git/")}


FIXTURES = Path(__file__).resolve().parent / "fixtures"


def applied(stdout: str) -> list:
    """(disposition, path) for every effect the run actually carried out, in order."""
    done = []
    for line in stdout.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0] in ACCOMPLISHED:
            done.append((parts[0], parts[1]))
    return done


def planned(stdout: str) -> list:
    """(disposition, path) for every effect a `--plan` run SAID it would carry out, in order."""
    rows = []
    for line in stdout.splitlines():
        parts = line.split()
        if len(parts) == 5 and parts[0] in DISPOSITIONS:
            rows.append((DISPOSITIONS[parts[0]], parts[4]))
    return rows


def install_order(stdout: str) -> list:
    """The sequence of paths the run actually touched -- the ORDER, not merely the set."""
    return [path for _disposition, path in applied(stdout)]


class Fixtures:
    """Scratch hosts and fixture kits. Held apart from any TestCase so that a second suite can
    reuse them without inheriting -- and therefore re-running -- somebody else's assertions."""

    maxDiff = None
    _trash: list = []

    @classmethod
    def tearDownClass(cls):
        for path in cls._trash:
            shutil.rmtree(path, ignore_errors=True)

    @classmethod
    def _temp(cls, prefix: str) -> Path:
        made = Path(tempfile.mkdtemp(prefix=prefix)).resolve()
        cls._trash.append(made)
        return made

    @classmethod
    def host(cls) -> Path:
        made = cls._temp("kit-host-")
        subprocess.run(["git", "init", "--quiet", str(made)], check=True, capture_output=True, text=True)
        return made

    @classmethod
    def fixture_kit(cls, name: str, patch=None, add=()) -> Path:
        """A copy of the REAL kit with declarations patched in place. Copied, never re-authored:
        a hand-written fixture of a declaration is a second home for it, and would go on passing
        after the original changed."""
        base = cls._temp(f"kit-fix-{name}-") / "kit"
        shutil.copytree(KIT, base)
        for src, rel in add:
            dest = base / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest)
        if patch:
            patch(base)
        return base

    @staticmethod
    def edit_json(kit: Path, rel: str, mutate) -> None:
        target = kit / rel
        value = json.loads(target.read_text(encoding="utf-8"))
        mutate(value)
        target.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def run_kit(cls, kit: Path, host: Path, verb: str = "init", *flags):
        result = subprocess.run(
            [sys.executable, str(CLI), verb, "--root", str(host), "--kit", str(kit), *flags],
            capture_output=True, text=True,
        )
        print(f"\n$ {verb} {' '.join(flags)} --kit <{kit.parent.name}> --root <host>\n"
              f"[exit {result.returncode}]\n{result.stdout}{result.stderr}")
        return result

    @classmethod
    def installed(cls, kit: Path = KIT, *flags) -> Path:
        """A host that has walked the whole door: drafted, then approved. Every P4-and-later
        assertion runs against an APPROVED host, because that is the only kind that exists."""
        host = cls.host()
        drafted = cls.run_kit(kit, host, "init", *flags)
        assert drafted.returncode == 3, f"init did not stall at the door: {drafted.stderr}"
        approved = cls.run_kit(kit, host, "init", "--approve", "acceptance-suite")
        assert approved.returncode == 0, f"an approved init did not install: {approved.stderr}"
        return host


