"""Manifest port -- the ONE reader of the payload declaration.

Everything the interpreter is allowed to know about what exists arrives through here, and arrives
already validated against the schema that declares its shape. Nothing downstream re-reads a
declaration file; nothing downstream trusts one that was never checked.
"""

from __future__ import annotations

import json
from pathlib import Path

import validation
from errors import KitError


class ManifestError(KitError):
    """A payload declaration is missing, unreadable, or does not honour its own schema."""

    code = "KIT0015"


#: The one property through which EVERY document the kit reads or writes states its shape
#: version (ADR-009). Its value is declared once, as the `const` of that property in the kind's
#: own schema; nothing else in the kit may hold a document's version.
VERSION = "schema_version"


class NewerDocument(KitError):
    """A document states a shape version HIGHER than the one this kit's schema declares: it was
    written by a newer kit. It is refused, never read as if it were understood (ADR-009)."""

    code = "KIT0033"


class OlderDocument(KitError):
    """A document states a shape version LOWER than the one this kit's schema declares, and the
    kit declares no migration that would carry it forward. Refused by name (ADR-009)."""

    code = "KIT0034"


class TakeShadows(ManifestError):
    """A capability a host TOOK carries the id of one the release ISSUED. A take never shadows the
    release (ADR-018 decision 4): refused by name, never resolved by an order of precedence."""

    code = "KIT0044"


#: The install modes through which governance DECLARES where a host's takes live: the plane that
#: holds each verbatim copy, and the one document that states what was taken (ADR-018). Named here
#: as `pin` names its own modes -- the targets, file names and namespace are the declaration's.
TAKEN_MODE = "taken"
TAKEN_DECLARATION_MODE = "taken-declaration"


def composed(kit_root: Path, host_root: Path) -> "Manifest":
    """The manifest a host SPEAKS WITH: the issued release, plus every row of the host's take
    declaration resolved to its plane (ADR-018 decision 4). Where the release declares no take
    plane, or the host declares no takes, the release alone is the answer -- a declared zero."""
    issued = Manifest(kit_root)
    found = {mode: [i for c in issued.capabilities for i in c.installs if i["mode"] == mode]
             for mode in (TAKEN_MODE, TAKEN_DECLARATION_MODE)}
    if any(len(items) != 1 for items in found.values()):
        return issued
    plane, statement = found[TAKEN_MODE][0], found[TAKEN_DECLARATION_MODE][0]
    target = Path(host_root) / statement["target"]
    if not target.is_file():
        return issued
    try:
        document = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManifestError(f"{statement['target']}: not readable as JSON -- {exc}") from exc
    issued._require_valid(document, statement["validates"], statement["target"])
    if not document["takes"]:
        return issued
    takes = []
    for row in document["takes"]:
        prefix = f"{plane['namespace']}{row['id']}/"
        takes.append({"id": row["id"], "prefix": prefix,
                      "declaration": prefix + plane["declaration"],
                      "home": Path(host_root) / plane["target"] / row["id"],
                      "row": row})
    return Manifest(kit_root, takes)


def _versioned(schema: dict):
    """The object schema that carries the version: the document itself, or -- for a document
    that is a list of records -- each record. Read from the schema's SHAPE, never from its name."""
    if schema.get("type") == "array" and isinstance(schema.get("items"), dict):
        return schema["items"]
    return schema


def _stated(instance, schema: dict) -> list:
    """Every version the instance STATES where its schema says a version lives. A statement that
    is not an integer is left to shape validation, which names it; this reads only real versions."""
    carriers = instance if _versioned(schema) is not schema else [instance]
    if not isinstance(carriers, list):
        return []
    found = []
    for carrier in carriers:
        if isinstance(carrier, dict) and VERSION in carrier:
            value = carrier[VERSION]
            if isinstance(value, int) and not isinstance(value, bool):
                found.append(value)
    return found


class Capability:
    """A capability declaration, read-only. It declares; it never acts."""

    def __init__(self, raw: dict, documents=None) -> None:
        self._raw = raw
        self._documents = documents or {}

    @property
    def documents(self) -> dict:
        """The declarations this capability SHIPS, by the id it gave them, already validated
        against the schema it named. The base declaration stays thin: a capability that needs a
        lifecycle brings its own document rather than growing a field on every other capability."""
        return dict(self._documents)

    @property
    def governs(self):
        """The collection this capability holds and the lifecycle it moves through, or None."""
        return self._raw.get("governs")

    @property
    def evaluates(self):
        """The declaration this capability holds JUDGEMENTS over, or None. Absent is the honest
        answer for every capability that judges nothing, which is most of them."""
        return self._raw.get("evaluates")

    @property
    def raw(self) -> dict:
        return self._raw

    @property
    def id(self) -> str:
        return self._raw["id"]

    @property
    def version(self) -> str:
        return self._raw["version"]

    @property
    def summary(self) -> str:
        return self._raw.get("summary", "")

    @property
    def requires(self) -> list:
        return self._raw["requires"]

    @property
    def installs(self) -> list:
        return self._raw["installs"]

    @property
    def gates(self) -> list:
        return self._raw["gates"]

    @property
    def observes(self) -> list:
        """What this capability declares should WATCH a run. Absent is a declared state and not a
        gap: most capabilities watch nothing, and one that watches nothing says so by declaring
        nothing -- which is why this field is optional and an empty list is its honest answer."""
        return self._raw.get("observes", [])

    def targets(self) -> tuple[str, ...]:
        """The write scope this capability declared for itself. Nothing else may be written."""
        return tuple(item["target"] for item in self.installs)

    def installs_of_class(self, class_name: str) -> list:
        return [item for item in self.installs if item["class"] == class_name]


class Manifest:
    """Reads `kit/` and hands back declarations. Holds no policy about what they mean."""

    def __init__(self, kit_root: Path, takes=()) -> None:
        self._root = Path(kit_root).resolve()
        #: kit-namespace prefix -> the plane directory that answers for it (ADR-018). Empty for a
        #: release read alone; every read below resolves through `path`, so no reader learns
        #: which home a declaration came from.
        self._homes: dict[str, Path] = {}
        self._taken: dict[str, dict] = {}
        if not (self._root / "MANIFEST.json").is_file():
            raise ManifestError(f"no MANIFEST.json under {self._root}")
        self._schemas: dict[str, dict] = {}
        self._raw = self._read("MANIFEST.json")
        # The manifest names its own schema registry, so the registry is loaded before the
        # manifest can be judged -- and the manifest is judged before anything else is read.
        for name, rel in self._raw.get("schemas", {}).items():
            self._schemas[name] = self._read(rel)
            self._require_policy(name, rel)
        self._require_valid(self._raw, "manifest", "MANIFEST.json")

        self._capabilities = []
        for entry in self._raw["capabilities"]:
            rel = entry["declaration"]
            raw = self._read(rel)
            self._require_valid(raw, "capability", rel)
            if raw["id"] != entry["id"]:
                raise ManifestError(f"{rel}: declares id {raw['id']!r}, manifest says {entry['id']!r}")
            documents = {}
            for declared in raw.get("documents", []):
                document = self._read(declared["source"])
                self._require_valid(document, declared["validates"], declared["source"])
                documents[declared["id"]] = document
            self._capabilities.append(Capability(raw, documents))

        issued_ids = {c.id for c in self._capabilities}
        for take in takes:
            if take["id"] in issued_ids:
                raise TakeShadows(
                    f"this host took a capability named {take['id']!r}, and the release it runs "
                    f"issued one by that name; a take never shadows the release. Remove the take "
                    f"or take it under a different id")
            self._homes[take["prefix"]] = Path(take["home"])
            self._taken[take["id"]] = take
        for take in takes:
            raw = self._read(take["declaration"])
            self._require_valid(raw, "capability", take["declaration"])
            if raw["id"] != take["id"]:
                raise ManifestError(f"{take['declaration']}: declares id {raw['id']!r}, the take "
                                    f"declaration says {take['id']!r}")
            documents = {}
            for declared in raw.get("documents", []):
                document = self._read(declared["source"])
                self._require_valid(document, declared["validates"], declared["source"])
                documents[declared["id"]] = document
            self._capabilities.append(Capability(raw, documents))

        # The release's detectors, then every document a composed capability ships under the
        # detector contract: a reading of a product's file is published with that product's
        # adapter, never added to the kit core. One id, one detector -- a second is refused.
        self._detectors = []
        owners: dict = {}
        found = []
        for rel in self._raw["detectors"]:
            raw = self._read(rel)
            self._require_valid(raw, "detector", rel)
            found.append(("the release", rel, raw))
        found += [(capability.id, declared["source"], capability.documents[declared["id"]])
                  for capability in self._capabilities for declared in capability.raw.get("documents", [])
                  if declared["validates"] == "detector"]
        for owner, rel, raw in found:
            if raw["id"] in owners:
                raise ManifestError(f"{rel}: detector {raw['id']!r} is already declared by "
                                    f"{owners[raw['id']]}; one reading has one home")
            owners[raw["id"]] = owner
            self._detectors.append(raw)

    # -- reading ----------------------------------------------------------------------------
    def path(self, rel: str) -> Path:
        """Where a kit-relative name RESOLVES: inside the plane of the take whose namespace it is
        spelled in, or inside the release. The one resolver; nothing downstream joins a root."""
        for prefix, home in self._homes.items():
            if rel.startswith(prefix):
                return home / rel[len(prefix):]
        return self._root / rel

    def _read(self, rel: str):
        target = self.path(rel)
        if not target.is_file():
            raise ManifestError(f"declared file does not exist: {rel}")
        try:
            return json.loads(target.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ManifestError(f"{rel}: not readable as JSON -- {exc}") from exc

    def _require_policy(self, name: str, rel: str) -> None:
        """ADR-009, held where every schema is loaded: a kind that cannot say which version it
        is cannot tell a document from the future from one it understands. So every registered
        schema declares its version as an integer `const` >= 1 -- and a kind past version 1
        REQUIRES the statement, because an absent version can only ever mean the first one."""
        carrier = _versioned(self._schemas[name])
        declared = carrier.get("properties", {}).get(VERSION)
        const = declared.get("const") if isinstance(declared, dict) else None
        if not (isinstance(const, int) and not isinstance(const, bool) and const >= 1
                and declared.get("type") == "integer"):
            raise ManifestError(f"{rel}: schema {name!r} does not declare its version as "
                                f"{{\"type\": \"integer\", \"const\": N>=1}} on {VERSION!r} (ADR-009)")
        if const > 1 and VERSION not in carrier.get("required", []):
            raise ManifestError(f"{rel}: schema {name!r} is at version {const} but does not "
                                f"require {VERSION!r}; past version 1 an absent version would be "
                                f"a guess (ADR-009)")

    def _require_valid(self, instance, schema_name: str, where: str) -> None:
        errors = self.validate(instance, schema_name)
        if errors:
            raise ManifestError(f"{where} does not honour schema {schema_name!r}:\n  " + "\n  ".join(errors))

    # -- the surface ------------------------------------------------------------------------
    def raw_ships(self) -> dict:
        """What the kit declares about ITSELF as a set of paths: where its lockfile lives, and
        the rules accounting for what no other declaration can point at. Handed on as data; this
        port holds no opinion about what any of it means."""
        return self._raw["ships"]

    @property
    def root(self) -> Path:
        return self._root

    @property
    def version(self) -> str:
        return self._raw["kit"]["version"]

    @property
    def planes(self) -> list:
        return self._raw["planes"]

    @property
    def capabilities(self) -> list:
        return list(self._capabilities)

    @property
    def policies(self) -> dict:
        """What the KIT declares ABOUT each capability, as opposed to what a capability declares
        about itself: id -> the manifest entry minus the pointer to the declaration. Handed on as
        data so that whoever reads a policy field reads a declaration, never a hard-coded name."""
        issued = {
            entry["id"]: {k: v for k, v in entry.items() if k not in ("id", "declaration")}
            for entry in self._raw["capabilities"]
        }
        # A take carries no policy: the kit declares nothing about what it never issued.
        return issued | {identity: {} for identity in self._taken}

    @property
    def taken(self) -> list:
        """The ids this manifest composes from the host's takes, sorted -- for the surfaces that
        must state the composition (`release <v> + taken: <ids>`). Empty for a release alone."""
        return sorted(self._taken)

    def take_of(self, capability_id: str):
        """(plane directory, kit-namespace prefix, declared row) of a TAKEN capability, or None.
        Asked only by the module that accounts for takes (provenance), never by a projection."""
        take = self._taken.get(capability_id)
        return None if take is None else (take["home"], take["prefix"], take["row"])

    def declaration_of(self, capability_id: str) -> str:
        """The kit-relative path of the file that declares a capability, as the manifest states
        it. Asked by whoever must say which BYTES a capability is -- never reconstructed from its
        id, because a path convention nobody declared is a second home for this row."""
        for entry in self._raw["capabilities"]:
            if entry["id"] == capability_id:
                return entry["declaration"]
        if capability_id in self._taken:
            return self._taken[capability_id]["declaration"]
        raise ManifestError(f"no capability named {capability_id!r} is declared by this kit")

    @property
    def detectors(self) -> list:
        return list(self._detectors)

    def schema(self, name: str) -> dict:
        if name not in self._schemas:
            raise ManifestError(f"no schema named {name!r} is declared by this kit")
        return self._schemas[name]

    def version_of(self, schema_name: str) -> int:
        """The shape version this kit reads and writes for a kind -- as its schema declares it.
        Every writer stamps THIS; no module holds a version of its own (ADR-009)."""
        return _versioned(self.schema(schema_name))["properties"][VERSION]["const"]

    def validate(self, instance, schema_name: str) -> list[str]:
        """Shape errors, after the VERSION is settled. A document at a version this kit does not
        read is refused by name before its shape is judged: judging a future shape by today's
        schema would produce a list of errors that describes nothing true (ADR-009)."""
        current = self.version_of(schema_name)
        for found in _stated(instance, self.schema(schema_name)):
            if found > current:
                raise NewerDocument(
                    f"a {schema_name!r} document states version {found}; this kit reads version "
                    f"{current} and will not guess at a shape from a newer kit. Run the kit that "
                    f"wrote it, or upgrade this one."
                )
            if 1 <= found < current:
                raise OlderDocument(
                    f"a {schema_name!r} document states version {found}; this kit reads version "
                    f"{current} and declares no migration from {found}. Run the kit version that "
                    f"wrote it, or re-create the document with this one."
                )
        return validation.validate(instance, self.schema(schema_name))

    def payload_text(self, rel: str) -> str:
        target = self.path(rel)
        if not target.is_file():
            raise ManifestError(f"declared payload source does not exist: {rel}")
        return target.read_text(encoding="utf-8")
