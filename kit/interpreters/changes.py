"""Change records -- every change states its scope, its requirements, its tests and its evidence, and a
review range is COVERED by verified records (ADR-024).

A change record is the evidence a reviewer and a release gate stand on, in one place, checkable by a
machine: the files it covers, for every requirement this host catalogues an APPLY or a NOT-APPLICABLE
with its reason, the tests run (command, exit code, environment), the evidence files and the digests of
every source it verified -- so a record whose sources moved since it was verified is STALE, and says
so. Supersession is a chain that must end. The coverage reading over a review range (`review`) names
every changed path no VERIFIED record covers.

What this reading certifies is structural and it says so: runtime conformance and production readiness
are NOT ASSERTED here -- only an external authority (a deployed system, an operator) can assert them.
"""

from __future__ import annotations

import hashlib
import posixpath

import collection
import declared

RECORDS = ({declared.CONTRACT: "change-record"},)
CATALOGUE = ({declared.CONTRACT: "requirements"}, "requirements")
VERIFIED, SUPERSEDED, DELETED = "VERIFIED", "SUPERSEDED", "DELETED"
#: The tri-state of what a reading can assert (PASS / NOT_RUN / NOT_ASSERTED): what was not checked is
#: never reported as passed.
CHECKED, NOT_ASSERTED = "CHECKED", "NOT_ASSERTED"


def digest(ctx, rel: str) -> str:
    """sha256 of a file's bytes with CRLF read as LF -- the same digest on every platform."""
    data = ctx.workspace.read_bytes(rel)
    try:
        data = data.decode("utf-8").replace("\r\n", "\n").encode("utf-8")
    except UnicodeDecodeError:
        pass
    return hashlib.sha256(data).hexdigest()


def seeded(ctx, contract: str):
    """The one host document a capability seeds under `contract`, or None before it is installed. Read
    by the gate that judges it, never as a readable of every render: a capability taken by `start` is
    rendered before its seeds are written."""
    for capability in ctx.enabled_capabilities():
        for item in capability.installs:
            if item.get("validates") == contract and item["mode"] == "seed" and ctx.workspace.exists(item["target"]):
                return collection.read(ctx, item, contract).value
    return None


def records(ctx) -> list:
    """(host path, record) for every change record this host declares readable."""
    found = []
    for capability in ctx.enabled_capabilities():
        for item in capability.installs:
            if item.get("validates") == RECORDS[0][declared.CONTRACT] and ctx.workspace.exists(item["target"].rstrip("/")):
                found += collection.read(ctx, item).records
    return found


def _inside(rel: str) -> bool:
    norm = posixpath.normpath(rel)
    return bool(rel) and not rel.startswith("/") and "\\" not in rel and ":" not in rel and not norm.startswith("..")


def validate(ctx, changed=None) -> dict:
    errors, covered = [], set()
    catalogue = {row["id"] for row in (seeded(ctx, CATALOGUE[0][declared.CONTRACT]) or {}).get(CATALOGUE[1], [])}
    seen, supersessions = set(), {}
    for rel, record in records(ctx):
        label = f"{rel}"
        if record["id"] in seen:
            errors.append(f"{label}: the id {record['id']!r} is declared twice")
        seen.add(record["id"])
        if set(record["requirements"]) != catalogue:
            errors.append(f"{label}: states applicability for {sorted(record['requirements'])}, and this host "
                          f"catalogues {sorted(catalogue)} -- every requirement is APPLY or NA, with its reason")
        for path in record["files"]:
            if not _inside(path):
                errors.append(f"{label}: {path!r} is not a path inside this repository")
        if record["status"] == SUPERSEDED:
            supersessions[record["id"]] = record.get("superseded_by", "")
        if record["status"] != VERIFIED:
            continue
        if not record.get("tests") or not record.get("evidence"):
            errors.append(f"{label}: VERIFIED with no test or no evidence")
        for test in record.get("tests", []):
            if test["exit_code"] != 0:
                errors.append(f"{label}: its test `{test['command']}` exited {test['exit_code']}")
        for item in record.get("evidence", []):
            if not ctx.workspace.exists(item["path"]) or digest(ctx, item["path"]) != item["sha256"]:
                errors.append(f"{label}: its evidence {item['path']} is missing or moved since it was verified")
        sources = record.get("source_digests", {})
        if set(sources) != set(record["files"]) - {rel}:
            errors.append(f"{label}: states source digests for {sorted(sources)}, not for every file it covers")
        for path, expected in sources.items():
            here = ctx.workspace.exists(path)
            if (expected == DELETED and here) or (expected != DELETED and (not here or digest(ctx, path) != expected)):
                errors.append(f"{label}: STALE -- {path} is not what it was when the record was verified")
        covered.update(record["files"])
        covered.add(rel)
    for start, target in supersessions.items():
        if target not in seen:
            errors.append(f"{start}: superseded by {target!r}, which no record declares")
        chain, current = set(), start
        while current in supersessions:
            if current in chain:
                errors.append(f"{start}: its supersession is a cycle")
                break
            chain.add(current)
            current = supersessions[current]
    if changed is not None:
        errors += [f"{path}: changed in the review range, and no VERIFIED change record covers it"
                   for path in sorted(set(changed) - covered)]
    return {"status": "FAIL" if errors else "PASS", "errors": errors,
            "change_coverage": CHECKED if changed is not None else NOT_ASSERTED,
            "runtime_conformance": NOT_ASSERTED, "production_readiness": NOT_ASSERTED}
