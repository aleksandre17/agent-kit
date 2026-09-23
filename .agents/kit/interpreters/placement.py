"""Placement -- where a path a product handed across the boundary actually LANDS on this machine.

Two readers now need this answer and neither may own it: the `judge` verb, placing a path a runtime
hook handed over before a write, and the dispatch port's admission on return, placing a path a
worker's tree reported after one. A path is measured the same way whoever carries it, so the
measurement has ONE home (Cardinal III) -- and that home is the core, because a gate is built from
this and a port may not reach a gate to borrow it (Cardinal VIII, the arrow).

It is a measurement and never a guess (Cardinal VII): a product may hand an absolute drive path, a
drive spelled as a POSIX mount, a relative path, or either case of a drive, and a rooted path that
names no drive on a drive-lettered filesystem is REFUSED as unmeasurable rather than resolved
against whichever drive happens to be current.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

#: A drive spelled as a POSIX mount (`/c/...`, `/cygdrive/c/...`): how a POSIX shell running on a
#: drive-lettered filesystem names that drive. A rule of the path's FORM, never of a shell's name.
_MOUNTED_DRIVE = re.compile(r"^/(?:cygdrive/)?([A-Za-z])(?=/|$)")


class Unplaceable(ValueError):
    """A handed path this machine cannot place: neither inside the host nor provably outside it."""


def _placed(raw: str) -> str:
    """The raw path in the form THIS machine's path rules read, or Unplaceable. Where paths carry a
    drive, a rooted path without one is read against whichever drive is current -- a guess, and
    a guess about where an edit lands must never resolve to 'elsewhere, so admitted'."""
    if not os.path.splitdrive(os.path.abspath(os.sep))[0]:
        return raw  # this filesystem has no drives: a rooted path is exactly what it names
    mounted = _MOUNTED_DRIVE.match(raw)
    if mounted:
        return f"{mounted.group(1)}:/{raw[mounted.end():].lstrip('/')}"
    drive, _rest = os.path.splitdrive(raw)
    if not drive and raw[:1] in ("/", "\\"):
        raise Unplaceable(f"{raw} is rooted but names no drive, so where it lands is not measurable")
    return raw


def host_relative(root: Path, raw: str) -> "str | None":
    """A path a product handed across the boundary, as the host-relative POSIX path a gate reads --
    or None when it lies outside this host, whose gates do not reach it; Unplaceable when neither
    can be measured. Measured, never assumed: a product may hand an absolute drive path, a drive
    spelled as a POSIX mount, a relative one, or either case of a drive."""
    raw = _placed(raw)
    candidate = Path(raw) if os.path.isabs(raw) else root / raw
    full, base = os.path.normcase(os.path.abspath(candidate)), os.path.normcase(os.path.abspath(root))
    if full != base and not full.startswith(base.rstrip(os.sep) + os.sep):
        return None
    return Path(os.path.relpath(os.path.abspath(candidate), os.path.abspath(root))).as_posix()
