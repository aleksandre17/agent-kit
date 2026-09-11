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
import time
from pathlib import Path, PurePosixPath

from errors import KitError


#: A reader holding the target open is the one condition under which a rename is refused, and
#: only on Windows, where an open file cannot be replaced. The reader is transient -- a poll, an
#: editor, an indexer -- so the rename is retried for a bounded moment, and then the refusal is
#: raised as what it is, never swallowed into a write that silently did not happen.
_REPLACE_ATTEMPTS = 50
_REPLACE_PAUSE = 0.02


def _replace(source: Path, target: Path) -> None:
    for attempt in range(_REPLACE_ATTEMPTS):
        try:
            os.replace(source, target)
            return
        except PermissionError:
            if attempt == _REPLACE_ATTEMPTS - 1:
                raise
            time.sleep(_REPLACE_PAUSE)


class WorkspaceError(KitError):
    """A path could not be resolved inside this workspace."""

    code = "KIT0017"


class WriteScopeError(WorkspaceError):
    """A write was attempted outside the declared scope. Refused, not warned about."""

    code = "KIT0018"


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
        """Every write is ATOMIC: the bytes go to a sibling temporary file, are flushed to the
        disk, and then REPLACE the target in one rename. A reader sees the old document or the
        new one and never a truncated one, and a process killed mid-write leaves the old document
        intact. Writing in place was honest to the WRITER and tearable for the READER -- the
        externalise-before-it-is-lost identity half-adopted, because a record nobody can read
        whole has not been externalised.

        The sibling shares the target's directory because a rename is atomic only within one
        filesystem. The residue is DECLARED, not hidden: a process killed between the write and
        the rename leaves a `.<name>.<pid>.kit-tmp` beside the target -- a visible stray the next
        reading names, instead of a silently torn document that reads as a real one."""
        norm = self._permit(rel)
        target = self._root / norm
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.{os.getpid()}.kit-tmp")
        try:
            with open(temporary, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            _replace(temporary, target)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise

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
