"""activation -- a SETTING outside the tree that must point at what a served surface serves.

A served file at a path its product never reads is a hook that exists and never fires, and reads
exactly like one that guards. Some products read their served files only once a setting in their
OWN configuration names the directory; that setting lives outside every tree the kit writes, so it
is neither projected nor recorded -- it is READ, every time it matters, and changed only through a
door. Which setting, how it is read, set and unset, and where the product looks while it is unset,
are the surface's `activation` block: argv lists run at the host root. This module names no
product, no setting and no command; it measures what a declaration says to measure.

The one home of the truth is the product's configuration itself. Nothing here keeps a copy of it:
a copy would be a second reading that drifts the moment anyone changes the setting by hand.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import declared
import serving
from errors import KitError

#: The contract a surface document keeps, and the field that declares a setting -- schema words.
SURFACES = {"validates": "runtime-surface"}
LIST = "surfaces"
FIELD = "activation"
PLACEHOLDER = "{points_at}"

#: The four states a reading can name. A setting that cannot be read is never assumed unset.
ACTIVE, INACTIVE, ELSEWHERE, UNREADABLE = "ACTIVE", "INACTIVE", "ELSEWHERE", "UNREADABLE"


class ActivationRefused(KitError):
    """A setting was asked to change that is not this kit's to change, or cannot be measured."""

    code = "KIT0047"


def served(ctx) -> dict:
    """surface id -> its activation block, for every surface the kit's own record says this host
    is served AND that declares a setting. A surface declared but never served activates nothing."""
    on_record = serving.served_surfaces(ctx, ctx.enabled_capabilities())
    return {row["id"]: row[FIELD] for row in declared.rules(ctx, SURFACES, LIST)
            if FIELD in row and row["id"] in on_record}


def argv(activation: dict, which: str) -> list:
    points = activation["points_at"].rstrip("/")
    return [part.replace(PLACEHOLDER, points) for part in activation[which]]


def _ran(root: Path, command: list):
    try:
        return subprocess.run(command, cwd=root, capture_output=True, text=True), None
    except OSError as exc:  # the program itself is absent: unmeasurable, never "unset"
        return None, f"{command[0]!r} could not be run -- {exc}"


def _placed(root: Path, value: str) -> str:
    where = Path(value) if os.path.isabs(value) else root / value
    return os.path.normcase(os.path.abspath(where))


def reading(ctx, activation: dict) -> tuple:
    """(state, value, detail) of the setting NOW. Taken fresh on every call and never stored."""
    root = ctx.workspace.path(".")
    ran, failure = _ran(root, argv(activation, "read"))
    if ran is None:
        return UNREADABLE, None, failure
    value = ran.stdout.strip()
    if ran.returncode != 0:
        if value or ran.stderr.strip():
            return UNREADABLE, value or None, ran.stderr.strip() or f"exit {ran.returncode}"
        return INACTIVE, None, "the setting holds no value"
    if not value:
        return INACTIVE, None, "the setting holds an empty value"
    ours = _placed(root, activation["points_at"].rstrip("/"))
    return (ACTIVE if _placed(root, value) == ours else ELSEWHERE), value, ""


def occupants(ctx, activation: dict) -> list:
    """Live entries where the product looks while the setting is unset: prior work that setting
    it would silently switch off. Unmeasurable is refused, never read as empty."""
    root = ctx.workspace.path(".")
    spec = activation["occupied"]
    ran, failure = _ran(root, list(spec["read"]))
    if ran is None or ran.returncode != 0:
        why = failure or ran.stderr.strip() or f"exit {ran.returncode}"
        raise ActivationRefused(
            f"where this product looks without the setting cannot be measured ({why}); a directory "
            f"that cannot be read is not an empty one, so nothing is switched off on its account")
    place = Path(_placed(root, ran.stdout.strip()))
    if not place.is_dir():
        return []
    inert = re.compile(spec["inert"])
    return sorted(entry.name for entry in place.iterdir() if not inert.search(entry.name))


def unexecutable(ctx, activation: dict) -> list:
    """Served files under the setting's directory a mode-honouring filesystem would not run.
    Where the filesystem keeps no execute bit, nothing is measured and nothing is claimed."""
    if os.name == "nt":
        return []
    place = ctx.workspace.path(activation["points_at"])
    return sorted(p.name for p in place.iterdir()
                  if p.is_file() and not os.access(p, os.X_OK)) if place.is_dir() else []


def make_executable(ctx, activation: dict) -> None:
    """Give every served file under the directory the execute bit, where the filesystem keeps one."""
    if os.name == "nt":
        return
    place = ctx.workspace.path(activation["points_at"])
    for path in (p for p in place.iterdir() if p.is_file()) if place.is_dir() else []:
        path.chmod(path.stat().st_mode | 0o111)
