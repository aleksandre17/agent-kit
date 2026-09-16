"""SUCCESSION -- what becomes of a host's PRIOR agent system when this kit takes over (ADR-011).

`adopt` (ADR-003) reads inside the kit's planes and nowhere else. A host that already runs an
agent system of its own keeps that system somewhere else entirely, and no reading had ever seen
it. This module is the reading that does -- and it is a READING: it writes nothing, moves nothing,
and decides nothing.

The split it rests on is the whole of ADR-011:

    the MACHINE produces the census and MEASURES   -- every path inside a DECLARED boundary, and
                                                     what can be proven about each one (the plane
                                                     it sits in, a kit target it stands on, kit
                                                     bytes it is identical to, a link it is)
    the MAP DECLARES                               -- host data, signed and dated: the boundary of
                                                     the prior system, and one disposition per
                                                     path, from the kit's declared vocabulary

A path's destination is not in its bytes, so SOMEWHERE a judgement is made. It is made in the
map, where it is stored, dated, signed and diffable -- never here, as a heuristic, and never as a
default. A measurement EVIDENCES a row and VERIFIES it; it never assigns one. A path no row
answers is `undecided`, counted and named.

This interpreter knows no runtime, no product, no directory name and no disposition by name. The
boundary comes from the manifest's planes and install targets (the kit's own surface) and from
the map's `prior` roots (the host's); the vocabulary comes from whichever capability declares a
`succession` document; a reference is checked by its declared KIND through the registry below.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath

import runtime as runtime_port
from errors import KitError

#: The schema kinds this module reads. Named once, as kinds -- where a document of each kind lives
#: is asked of the declarations (the vocabulary) or given at the boundary (the map).
VOCABULARY = "succession"
MAP = "migration-map"


class SuccessionRefused(KitError):
    """The migration map, or the vocabulary it is read against, cannot be read as declared. Every
    defect is named at once and NO roster is printed: a roster computed from a map that says
    something it cannot mean would be a confident reading of nothing."""

    code = "KIT0036"


# -- references: how a carried value is checked, by the KIND a disposition declares ------------
def _plane(ctx, value: str):
    for plane in ctx.manifest.planes:
        root = plane["root"].rstrip("/")
        if value.rstrip("/") == root or value.startswith(root + "/"):
            return None
    return f"{value!r} lies in no plane this kit declares {[p['root'] for p in ctx.manifest.planes]}"


def _capability(ctx, value: str):
    known = sorted(c.id for c in ctx.manifest.capabilities)
    return None if value in known else f"{value!r} is no capability this kit declares {known}"


def _statement(ctx, value: str):
    return None if value.strip() else "an empty statement states nothing"


#: kind -> (check, relocates). A reference that RELOCATES states where the path's bytes go, and
#: the path's remainder below its row is carried below it. A new kind is a row here; a vocabulary
#: naming a kind that is not here is refused, never ignored.
REFERENCES = {
    "plane": (_plane, True),
    "capability": (_capability, False),
    "statement": (_statement, False),
}

#: effect -> whether it takes its destination from a RELOCATING reference the row carries (True)
#: or sends the path aside into the observed plane (False). Carrying either out is the same act --
#: one rename -- and no effect destroys bytes a host authored (ADR-012). A disposition declares
#: its effect; an effect that is not here is refused, and an effect is never inferred from the
#: fields a row happens to carry, because an effect that had to be guessed would be a deletion
#: by default.
def _relocated(row: dict, path: str, _aside: str) -> str:
    field = next(f for f, kind in row["refers"].items() if REFERENCES[kind][1])
    return row["carried"][field].rstrip("/") + path[len(row["path"]):]


def _set_aside(_row: dict, path: str, aside: str) -> str:
    return f"{aside}/{path}"


EFFECTS = {
    "relocate": (_relocated, True),
    "remove": (_set_aside, False),
}


# -- the declarations ----------------------------------------------------------------------------
def vocabulary(ctx) -> dict:
    """The one declared succession vocabulary, asked of the capabilities -- never a path held here."""
    found = [(c.id, c.documents[d["id"]]) for c in ctx.manifest.capabilities
             for d in c.raw.get("documents", []) if d["validates"] == VOCABULARY]
    if len(found) != 1:
        raise SuccessionRefused(
            f"this kit declares {len(found)} {VOCABULARY!r} documents "
            f"{[owner for owner, _ in found]}; exactly one is required, because a disposition "
            f"with two homes has two meanings")
    words = found[0][1]
    ids = [d["id"] for d in words["dispositions"]]
    faults = [f"disposition {i!r} is declared more than once" for i in sorted(set(ids)) if ids.count(i) > 1]
    if words["undecided"]["id"] in ids:
        faults.append(f"{words['undecided']['id']!r} is the name of the unanswered state and may "
                      f"not be a disposition a row can assign")
    faults += [f"disposition {d['id']!r} carries {c['field']!r} referring to {c['refers']!r}, a "
               f"kind this interpreter cannot check {sorted(REFERENCES)}"
               for d in words["dispositions"] for c in d["carries"] if c["refers"] not in REFERENCES]
    for d in words["dispositions"]:
        relocating = [c["field"] for c in d["carries"] if REFERENCES.get(c["refers"], (0, False))[1]]
        if "effect" not in d:
            continue
        if d["effect"] not in EFFECTS:
            faults.append(f"disposition {d['id']!r} declares the effect {d['effect']!r}, which this "
                          f"interpreter cannot carry out {sorted(EFFECTS)}")
        elif len(relocating) != (1 if EFFECTS[d["effect"]][1] else 0):
            faults.append(f"disposition {d['id']!r} declares the effect {d['effect']!r} and carries "
                          f"{len(relocating)} destination field(s) {relocating}; the effect needs "
                          f"{1 if EFFECTS[d['effect']][1] else 0}, so where its paths go is not stated once")
    home = _relative(words["residence"])
    declared = [i["target"] for c in ctx.manifest.capabilities for i in c.installs]
    if home is None or _plane(ctx, home) or home not in declared:
        faults.append(f"the map's residence {words['residence']!r} is not a path in a plane that a "
                      f"capability declares as an install target; a map living there would be a "
                      f"path nothing accounts for")
    if faults:
        raise SuccessionRefused("the succession vocabulary cannot be read:\n  " + "\n  ".join(faults))
    return words


def _relative(text: str):
    """A host-relative POSIX path, or None if it leaves the host or is not relative."""
    norm = text.replace("\\", "/").rstrip("/")
    pure = PurePosixPath(norm)
    if not norm or pure.is_absolute() or ":" in norm or ".." in pure.parts:
        return None
    return pure.as_posix()


def read_map(ctx, given, words: dict):
    """The host's map, validated against its schema AND against the vocabulary, or None when none
    was given. Every fault is collected and the map is refused WHOLE."""
    if given is None:
        return None
    path = Path(given).resolve()
    if not path.is_file():
        raise SuccessionRefused(f"{path.as_posix()}: no migration map is there")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SuccessionRefused(f"{path.as_posix()}: not readable as JSON -- {exc}") from exc
    faults = ctx.manifest.validate(document, MAP)
    if faults:
        raise SuccessionRefused(f"{path.as_posix()} does not honour schema {MAP!r}:\n  " + "\n  ".join(faults))

    declared = {d["id"]: d for d in words["dispositions"]}
    prior, rows, seen = [], [], set()
    for root in document["prior"]:
        rel = _relative(root)
        if rel is None:
            faults.append(f"prior root {root!r} is not a path inside this host")
        else:
            prior.append(rel)
    for index, row in enumerate(document["rows"]):
        where = f"rows[{index}] {row['path']!r}"
        rel = _relative(row["path"])
        if rel is None:
            faults.append(f"{where}: not a path inside this host")
            continue
        if rel in seen:
            faults.append(f"{where}: a second row for the same path -- one path, one answer")
        seen.add(rel)
        meaning = declared.get(row["disposition"])
        if meaning is None:
            faults.append(f"{where}: disposition {row['disposition']!r} is not declared "
                          f"{sorted(declared)}; {words['undecided']['id']!r} is never assigned, "
                          f"it is what no row says")
            continue
        wanted = {c["field"]: c["refers"] for c in meaning["carries"]}
        carried = {k: v for k, v in row.items() if k not in ("path", "disposition")}
        faults += [f"{where}: {meaning['id']!r} carries {field!r}, and this row does not"
                   for field in sorted(set(wanted) - set(carried))]
        faults += [f"{where}: {meaning['id']!r} carries no {field!r}; a field the disposition does "
                   f"not declare is a statement nothing will read" for field in sorted(set(carried) - set(wanted))]
        for field in sorted(set(wanted) & set(carried)):
            value = carried[field]
            if not isinstance(value, str):
                fault = "not a string"
            elif REFERENCES[wanted[field]][1] and _relative(value) is None:
                fault = "a destination must be a path inside this host"
            else:
                fault = REFERENCES[wanted[field]][0](ctx, value)
            if fault:
                faults.append(f"{where}: {field} -- {fault}")
        rows.append({"path": rel, "disposition": meaning["id"],
                     "carried": {f: carried.get(f) for f in wanted}, "refers": wanted})
    if faults:
        raise SuccessionRefused(f"{path.as_posix()} cannot be read as a migration map:\n  "
                                + "\n  ".join(faults))
    return {"file": path, "declared_by": document.get("declared_by"),
            "declared_at": document.get("declared_at"), "prior": prior, "rows": rows}


# -- the census and what is measured -------------------------------------------------------------
def boundary(ctx, mapped) -> list:
    """(root, who declared it). The kit's own surface -- its planes and every install target
    outside them -- is always in the boundary; the map adds the prior system's roots."""
    roots = [(p["root"].rstrip("/"), f"the kit (plane {p['class']})") for p in ctx.manifest.planes]
    for capability in ctx.manifest.capabilities:
        for item in capability.installs:
            target = item["target"].rstrip("/")
            if not any(target == r or target.startswith(r + "/") for r, _ in roots):
                roots.append((target, f"the kit (installed by {capability.id})"))
    # A path a runtime reads is the kit's surface as surely as an install target: the kit will
    # write there on the next render (ADR-013/014). Asked of the port that owns the answer.
    for target, who in runtime_port.reach(ctx, ctx.manifest.capabilities):
        if not any(target == r or target.startswith(r + "/") for r, _ in roots):
            roots.append((target, f"the kit ({who})"))
    for root in (mapped or {}).get("prior", []):
        roots.append((root, "the migration map"))
    return roots


def _is_link(path: Path) -> bool:
    return path.is_symlink() or bool(getattr(path, "is_junction", lambda: False)())


def census(ctx, roots) -> dict:
    """host-relative path -> the root that brought it in. A link is ONE path and is never walked
    through: its referent is somewhere else, and counting it twice would be a name mistaken for a
    referent. Nothing outside the declared roots is ever looked at."""
    host = ctx.workspace.root
    found = {}
    for root, _who in roots:
        start = host / root
        if _is_link(start) or start.is_file():
            found.setdefault(root, root)
            continue
        if not start.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(start):
            here = Path(dirpath)
            for name in list(dirnames):
                if _is_link(here / name):
                    dirnames.remove(name)
                    filenames.append(name)
            for name in filenames:
                found.setdefault((here / name).relative_to(host).as_posix(), root)
    return found


def kit_bytes(ctx) -> dict:
    """sha256 -> the kit-relative files with those exact bytes."""
    index = {}
    for dirpath, _dirs, files in os.walk(ctx.manifest.root):
        for name in files:
            whole = Path(dirpath) / name
            digest = hashlib.sha256(whole.read_bytes()).hexdigest()
            index.setdefault(digest, []).append(whole.relative_to(ctx.manifest.root).as_posix())
    return index


def _under(path: str, root: str) -> bool:
    return path == root or path.startswith(root + "/")


def targets(ctx) -> list:
    return [(item["target"], c.id) for c in ctx.manifest.capabilities for item in c.installs]


def _on_target(path: str, installs) -> list:
    return [cap for target, cap in installs
            if (path.startswith(target) if target.endswith("/") else path == target)]


def measure(ctx, path: str, installs, index) -> list:
    """What can be PROVEN about a path, with no judgement in it."""
    host = ctx.workspace.root
    facts = [f"in plane {p['class']}" for p in ctx.manifest.planes if _under(path, p["root"].rstrip("/"))]
    facts += [f"the kit installs here ({cap})" for cap in _on_target(path, installs)]
    whole = host / path
    if _is_link(whole):
        facts.append(f"a link to {os.path.realpath(whole)}")
    elif whole.is_file():
        same = index.get(hashlib.sha256(whole.read_bytes()).hexdigest(), [])
        facts += [f"byte-identical to kit {rel}" for rel in same]
    return facts


def answer(rows, path: str):
    """The MOST SPECIFIC row at or above this path, or None. Row paths are unique (refused
    otherwise), so the most specific row is always one row."""
    matching = [row for row in rows if _under(path, row["path"])]
    return max(matching, key=lambda row: len(row["path"])) if matching else None


def residence(words) -> str:
    """Where this host's migration map lives, as the vocabulary declares it (ADR-012)."""
    return _relative(words["residence"])


def read(ctx, given) -> dict:
    """The whole reading: every census path with its state, its carried fields, and what was
    measured. With no map given, the map at the declared residence is read where one is there --
    so the reading `inherit` prints is the reading an act is carried out from."""
    words = vocabulary(ctx)
    if given is None and ctx.workspace.path(residence(words)).is_file():
        given = ctx.workspace.path(residence(words))
    mapped = read_map(ctx, given, words)
    roots = boundary(ctx, mapped)
    found = census(ctx, roots)
    installs, index = targets(ctx), kit_bytes(ctx)
    rows = (mapped or {}).get("rows", [])
    entries, destinations = [], {}
    for path in sorted(found):
        row = answer(rows, path)
        facts = measure(ctx, path, installs, index)
        detail = []
        if row is not None:
            for field, value in row["carried"].items():
                if REFERENCES[row["refers"][field]][1]:
                    value = value.rstrip("/") + path[len(row["path"]):]
                    destinations.setdefault(value, []).append(path)
                    facts += [f"destination is where the kit installs ({cap})"
                              for cap in _on_target(value, installs)]
                    if (ctx.workspace.root / value).exists():
                        facts.append("destination already exists in this host")
                detail.append(f"{field}={value}")
        entries.append({"path": path, "root": found[path],
                        "state": row["disposition"] if row else words["undecided"]["id"],
                        "detail": detail, "facts": facts})
    clashes = {dest: srcs for dest, srcs in destinations.items() if len(srcs) > 1}
    if clashes:
        raise SuccessionRefused("the migration map sends more than one path to one place:\n  " + "\n  ".join(
            f"{dest} <- {', '.join(srcs)}" for dest, srcs in sorted(clashes.items())))
    idle = [row["path"] for row in rows if not any(_under(p, row["path"]) for p in found)]
    return {"words": words, "map": mapped, "roots": roots, "entries": entries, "idle": idle}


def report(ctx, reading: dict, moment: str) -> None:
    words, mapped = reading["words"], reading["map"]
    print(f"succession: kit {ctx.manifest.version}, read at {moment} -- a READING; nothing in this "
          f"host is written, moved or deleted")
    if mapped is None:
        print("  map  none -- the prior system's boundary is only what this kit itself declares; "
              "no path outside it is in this census, and no path in it is decided")
    else:
        inside = _under(mapped["file"].as_posix(), ctx.workspace.root.as_posix())
        print(f"  map  {mapped['file'].as_posix()} -- declared by {mapped['declared_by']} at "
              f"{mapped['declared_at']} ({'inside' if inside else 'OUTSIDE'} this host)")
    counted = {}
    for entry in reading["entries"]:
        counted[entry["root"]] = counted.get(entry["root"], 0) + 1
    for root, who in reading["roots"]:
        print(f"  boundary  {root}  {counted.get(root, 0)} path(s)  -- declared by {who}")
    for entry in reading["entries"]:
        tail = "".join(f"  {d}" for d in entry["detail"])
        facts = f"  {{{'; '.join(entry['facts'])}}}" if entry["facts"] else ""
        print(f"  {entry['state']}  {entry['path']}{tail}{facts}")
    for path in reading["idle"]:
        print(f"  idle-row  {path}  -- this row answers no path in the census")
    states = [d["id"] for d in words["dispositions"]] + [words["undecided"]["id"]]
    tally = {state: sum(1 for e in reading["entries"] if e["state"] == state) for state in states}
    for state in states:
        print(f"  count  {state} = {tally[state]}")
    print(f"  count  census = {len(reading['entries'])}")
    unanswered = tally[words["undecided"]["id"]]
    if unanswered:
        print(f"succession: INCOMPLETE -- {unanswered} path(s) are {words['undecided']['id']}; no "
              f"row answers them, and none is defaulted")
    elif not reading["entries"]:
        print("succession: the census is EMPTY -- nothing inside the declared boundary exists, "
              "which is a reading of the boundary and not a finding about any prior system")
    else:
        print("succession: every path in the census is answered by a row")
