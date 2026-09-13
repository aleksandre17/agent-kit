"""What the kit IS, as a set of paths -- stated by the kit itself, and read at a stated moment.

The kit's whole premise is that every path in a tree resolves to exactly one declared class. It
reproduced against itself the condition it exists to prevent: bytecode appeared *inside the
payload* the first time it ran, an unclassed path in the one tree that is supposed to have none.
It was fenced with `.gitignore`, which stops git seeing it and stops nobody else.

A fence is not a mechanism. This module is: the kit ENUMERATES itself, and anything the
enumeration does not account for is refused rather than shipped.

Two accountings, unioned, and neither of them is a hand-kept list of files:

  * DERIVED -- the closure of the declarations. Start at `MANIFEST.json`, walk every string it
    contains, keep the ones that name a file of this kit, and recurse into the ones that are
    themselves JSON. Every schema, capability, document, detector and payload source is reached
    because a declaration REFERS to it. Nothing here knows the name of any of them, and a
    capability that arrives tomorrow with a field nobody foresaw is accounted for without an
    edit: a declaration that points at a file is what "shipped" means.
  * DECLARED -- `ships.accounts` in the manifest, for what no declaration can refer to: the
    interpreter itself, and the prose. A rule over a DIRECTORY must state the suffix it accounts
    for, because a rule that swallows a whole directory would have swallowed the bytecode too,
    and the defect would have survived its own cure. A rule that matches NOTHING is refused: an
    attribution that cannot fail does not measure, it certifies, and a sensor proves it was
    pointed at something before it is believed.

Three things this module refuses to do, all of them deliberate:

  * it never classifies a path twice -- two accountings claiming one file is a name with two
    meanings, and is an error here rather than a precedence ladder somewhere;
  * it never hashes a file containing a carriage return. A hash is the extreme form of trusting a
    boundary: this repository has already had a byte-reproducibility claim go false the moment it
    crossed git, which is why LF is pinned in `.gitattributes`. A lockfile computed over CRLF
    bytes would be internally perfect and true nowhere else, so the translation is MEASURED here
    and reported by name (`line-endings`), never folded into a generic mismatch;
  * it never writes. The verb writes, through a workspace scoped to the lock path alone.

And the lockfile is a READING, not a property. A digest is what a file was at an instant, and it
reads afterwards exactly like something permanent -- so the document states `taken_at`, and a
comparison against it reports the two moments rather than asserting one of them is now.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import PurePosixPath

from errors import KitError


#: The digest algorithm, named in the document so a reader is never guessing which one produced
#: these sixty-four characters.
ALGORITHM = "sha256"

#: The line ending every shipped file is asserted to have -- an assumption at a boundary, so it
#: is stated in the document and measured on every file rather than believed.
NEWLINE = "lf"

#: The states a shipped path can be in. Every one of them is a word the surface can print; a
#: comparison that returned only true/false would be a mismatch pretending to be a diagnosis.
MATCHED = "matched"
STALE = "stale"
MISSING = "missing"
UNACCOUNTED = "unaccounted"
LINE_ENDINGS = "line-endings"

STATES = (MATCHED, STALE, MISSING, UNACCOUNTED, LINE_ENDINGS)

#: The account a PINNED lock gives a path the kit it was read from did not issue (ADR-016): a
#: capability a host took, a file a working tree added. The pinned tree carries it and integrity
#: covers it, but "the kit's lock accounts for it" must keep meaning "the kit ISSUED it" -- that is
#: how provenance tells what a host took from what the kit shipped (ADR-008). A lock that absorbed
#: taken capabilities would make every one of them read as withdrawn.
NOT_ISSUED = "not-issued"


def issued(lock: dict) -> set:
    """Every path a lock says the kit ISSUED -- its rows, less those it carries as not issued."""
    return {entry["path"] for entry in lock["files"] if entry["accounted_by"] != NOT_ISSUED}

#: The class given to a file reached from a declaration. Which of the two it gets is MEASURED --
#: a file the walk could parse as JSON is a declaration and is walked into; one it could not is
#: payload and is carried. Neither is decided by a name.
DECLARATION = "declaration"
PAYLOAD = "payload"


class LockError(KitError):
    """The kit cannot state what it is: a rule that measures nothing, a rule over a directory
    that names no suffix, or one path accounted for twice."""

    code = "KIT0012"


def _inside(rel: str) -> str | None:
    """The kit-relative form of a string that MIGHT be a path, or None if it cannot be one."""
    if not rel or rel.strip() != rel or "\\" in rel:
        return None
    pure = PurePosixPath(rel)
    if pure.is_absolute() or ".." in pure.parts:
        return None
    return pure.as_posix()


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def _claim(into: dict, rel: str, klass: str, by: str) -> None:
    if rel in into and into[rel] != (klass, by):
        held = into[rel]
        raise LockError(
            f"{rel}: accounted for twice -- as {held[0]!r} by {held[1]!r} and as {klass!r} by {by!r}"
        )
    into[rel] = (klass, by)


def closure(ws, start: str, skip=frozenset(), view=None) -> dict:
    """path -> class, for every file reachable from `start` by the one rule this module knows: a
    string in a declaration that names a file of the tree IS a reference to it. JSON is walked
    into; anything else is payload and carried. `skip` names paths the walk must neither claim nor
    enter, and `view` lets a caller hide a part of one document that is not references. ONE walk,
    used for the kit's account of itself and for the account of any single capability in it --
    a second walker would be a second opinion about what a declaration points at."""
    found: dict = {}
    queue = [start]
    while queue:
        rel = queue.pop()
        if rel in found or rel in skip:
            continue
        raw = ws.read_bytes(rel)
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            value = None
        found[rel] = PAYLOAD if value is None else DECLARATION
        if value is None:
            continue
        if view is not None:
            value = view(rel, value)
        for text in _strings(value):
            candidate = _inside(text)
            if candidate and candidate not in skip and ws.path(candidate).is_file():
                queue.append(candidate)
    return found


def accounted(manifest, ws) -> dict:
    """path -> (class, accounted_by), for every file this kit says it is made of."""
    ships = manifest.raw_ships()
    lock_path = ships["lock"]
    found: dict = {}

    # -- derived: the closure of the declarations ---------------------------------------------
    def without_ships(rel, value):
        # `ships` is the DECLARED accounting, not a set of references. Walking it as though its
        # strings were pointers would make every rule account for its own root twice -- once as a
        # rule and once as a reference -- which is one path with two meanings.
        if rel == "MANIFEST.json":
            return {k: v for k, v in value.items() if k != "ships"}
        return value

    for rel, klass in closure(ws, "MANIFEST.json", {lock_path}, without_ships).items():
        _claim(found, rel, klass, "declaration-closure")

    # -- declared: what no declaration can point at -------------------------------------------
    for rule in ships["accounts"]:
        root, suffix = rule["root"], rule.get("suffix")
        # WHICH KIND of rule this is, is read from the DECLARATION and never from the disk. A rule
        # that stated a suffix scans; a rule that stated none names exactly one file. Deciding it
        # by what happens to exist would mean a deleted file silently changes what its own rule
        # meant -- and the report would then diagnose the rule instead of naming the absence.
        if suffix:
            matched = [rel for rel in ws.files_under(root) if rel.endswith(suffix)]
            if not matched:
                raise LockError(
                    f"ships rule {rule['id']!r}: matched no file under {root!r} -- a rule pointed "
                    f"at nothing passes gloriously and measures an empty set"
                )
        else:
            if ws.path(root.rstrip("/")).is_dir():
                raise LockError(
                    f"ships rule {rule['id']!r}: accounts for the directory {root!r} and states no "
                    f"suffix -- a rule that swallows a directory whole would swallow whatever "
                    f"appears in it, which is the defect this lockfile exists to make impossible"
                )
            # Its absence is not a broken sensor: it is a path this kit says it has and does not,
            # which the survey states in that word.
            matched = [_inside(root)]
        for rel in matched:
            _claim(found, rel, rule["class"], rule["id"])

    return found


def on_disk(manifest, ws) -> list:
    """Every file of the kit as the filesystem currently has it, the lock itself excepted -- the
    lock cannot be part of the set it describes."""
    lock_path = manifest.raw_ships()["lock"]
    return [rel for rel in ws.files_under(".") if rel != lock_path]


def survey(manifest, ws) -> list:
    """Every path the kit accounts for or has, with its state and -- where one could honestly be
    taken -- its digest. Sorted by path: a report is read by people, and by tests."""
    claims = accounted(manifest, ws)
    present = set(on_disk(manifest, ws))
    rows = []
    for rel in sorted(set(claims) | present):
        klass, by = claims.get(rel, (None, None))
        if rel not in claims:
            rows.append({"path": rel, "state": UNACCOUNTED, "class": None,
                         "accounted_by": None, "digest": None})
            continue
        if rel not in present:
            rows.append({"path": rel, "state": MISSING, "class": klass,
                         "accounted_by": by, "digest": None})
            continue
        raw = ws.read_bytes(rel)
        if b"\r" in raw:
            rows.append({"path": rel, "state": LINE_ENDINGS, "class": klass,
                         "accounted_by": by, "digest": None})
            continue
        rows.append({"path": rel, "state": MATCHED, "class": klass, "accounted_by": by,
                     "digest": hashlib.sha256(raw).hexdigest()})
    return rows


def document(manifest, rows, moment: str) -> dict:
    """The reading, as it is stored. `count` is written out rather than left to be counted: a
    zero that nobody printed reads exactly like a scan that found everything in order."""
    files = [{"path": r["path"], "class": r["class"], "accounted_by": r["accounted_by"],
              "digest": r["digest"]} for r in rows]
    return {
        "schema_version": manifest.version_of("lock"),
        "kit_version": manifest.version,
        "algorithm": ALGORITHM,
        "newline": NEWLINE,
        "taken_at": moment,
        "count": len(files),
        "files": files,
    }


def compare(lock: dict, rows: list) -> list:
    """The recorded reading against a fresh one. Returns (state, path, why) for everything that
    is not `matched`, and says WHICH of the two readings said what -- a digest is a reading, and
    two readings of one file disagreeing is not a property of the file."""
    recorded = {entry["path"]: entry["digest"] for entry in lock["files"]}
    fresh = {row["path"]: row for row in rows}
    out = []
    for path in sorted(set(recorded) | set(fresh)):
        row = fresh.get(path)
        if row is None:
            # Recorded, and now neither present nor accounted for. The word is MISSING and not
            # `unaccounted`: `unaccounted` says a path is here that nothing explains, which is the
            # opposite complaint and would send a reader looking for a file that is gone.
            out.append((MISSING, path,
                        f"in a lock taken at {lock['taken_at']}, and the kit neither has it nor "
                        f"accounts for it now"))
        elif row["state"] != MATCHED:
            out.append((row["state"], path, f"the kit as it stands reports {row['state']}"))
        elif path not in recorded:
            out.append((UNACCOUNTED, path,
                        f"accounted for by {row['accounted_by']}, and absent from a lock taken "
                        f"at {lock['taken_at']}"))
        elif recorded[path] != row["digest"]:
            out.append((STALE, path,
                        f"the lock taken at {lock['taken_at']} says {recorded[path][:12]}, "
                        f"this reading says {row['digest'][:12]}"))
    return out
