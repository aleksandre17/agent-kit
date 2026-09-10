"""Workspace port -- every filesystem effect, and the scope that bounds it.

Two responsibilities that are really one: the host root is resolved ONCE at the boundary (a path
is a name, and a name is not a referent until it has been measured), and every write is checked
against a DECLARED scope. A capability may write only inside the targets its own declaration
lists; anything else is refused, loudly, before the byte is written. The port holds no knowledge
of which capability it is serving -- the scope arrives as data.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path, PurePosixPath

from errors import KitError


class WorkspaceError(KitError):
    """A path could not be resolved inside this workspace."""


class WriteScopeError(WorkspaceError):
    """A write was attempted outside the declared scope. Refused, not warned about."""


def _normalise(rel: str) -> str:
    """One canonical form for a host-relative path: POSIX separators, no drift."""
    if not rel or rel.strip() != rel:
        raise WorkspaceError(f"not a usable relative path: {rel!r}")
    text = rel.replace("\\", "/")
    pure = PurePosixPath(text)
    if pure.is_absolute() or ".." in pure.parts:
        raise WorkspaceError(f"path must stay inside the workspace: {rel!r}")
    return pure.as_posix()


class Workspace:
    """Rooted, scope-enforcing filesystem access. Reads are unbounded; writes are not."""

    def __init__(self, root: Path, scope: tuple[str, ...] | None = None) -> None:
        self._root = Path(root).resolve()
        self._scope = scope

    @property
    def root(self) -> Path:
        return self._root

    @property
    def scope(self) -> tuple[str, ...] | None:
        return self._scope

    def scoped(self, targets) -> "Workspace":
        """A view of this workspace whose writes are confined to `targets` (files or dirs)."""
        return Workspace(self._root, tuple(sorted(_normalise(t) for t in targets)))

    def unscoped(self) -> "Workspace":
        return Workspace(self._root, None)

    # -- resolution -------------------------------------------------------------------------
    def path(self, rel: str) -> Path:
        return self._root / _normalise(rel)

    def _permit(self, rel: str) -> str:
        norm = _normalise(rel)
        if self._scope is None:
            return norm
        for allowed in self._scope:
            if norm == allowed or norm.startswith(allowed.rstrip("/") + "/"):
                return norm
        raise WriteScopeError(
            f"write refused: {norm!r} is outside the declared scope {list(self._scope)!r}"
        )

    # -- reading ----------------------------------------------------------------------------
    def exists(self, rel: str) -> bool:
        return self.path(rel).exists()

    def read_bytes(self, rel: str) -> bytes:
        """The file as it actually is. Text decoding is a translation, and whoever must MEASURE a
        boundary -- a line ending, a digest -- has to stand before it, not after it."""
        return self.path(rel).read_bytes()

    def read_text(self, rel: str) -> str:
        return self.path(rel).read_text(encoding="utf-8")

    def read_json(self, rel: str):
        return json.loads(self.read_text(rel))

    def files_under(self, rel: str) -> list[str]:
        """Every file below `rel`, host-relative, POSIX-formed, sorted. Directories are not
        classified: a directory is the shape of the tree, a file is the thing that ships."""
        base = self.path(rel)
        if not base.exists():
            return []
        found = []
        for dirpath, _dirnames, filenames in os.walk(base):
            for name in filenames:
                whole = Path(dirpath) / name
                found.append(whole.relative_to(self._root).as_posix())
        return sorted(found)

    # -- writing ----------------------------------------------------------------------------
    def write_text(self, rel: str, content: str) -> None:
        norm = self._permit(rel)
        target = self._root / norm
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)

    def write_json(self, rel: str, value) -> None:
        self.write_text(rel, json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n")

    def make_dir(self, rel: str) -> None:
        """A directory the host will fill. Declared and scope-checked like any other write: a
        space a capability owns is still a write scope, and an unowned one is how files appear
        that resolve to no class."""
        (self._root / self._permit(rel)).mkdir(parents=True, exist_ok=True)

    def remove_tree(self, rel: str) -> None:
        norm = self._permit(rel)
        target = self._root / norm
        if target.exists():
            shutil.rmtree(target)
