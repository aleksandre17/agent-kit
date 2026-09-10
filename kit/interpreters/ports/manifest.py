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

    def __init__(self, kit_root: Path) -> None:
        self._root = Path(kit_root).resolve()
        if not (self._root / "MANIFEST.json").is_file():
            raise ManifestError(f"no MANIFEST.json under {self._root}")
        self._schemas: dict[str, dict] = {}
        self._raw = self._read("MANIFEST.json")
        # The manifest names its own schema registry, so the registry is loaded before the
        # manifest can be judged -- and the manifest is judged before anything else is read.
        for name, rel in self._raw.get("schemas", {}).items():
            self._schemas[name] = self._read(rel)
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

        self._detectors = []
        for rel in self._raw["detectors"]:
            raw = self._read(rel)
            self._require_valid(raw, "detector", rel)
            self._detectors.append(raw)

    # -- reading ----------------------------------------------------------------------------
    def _read(self, rel: str):
        target = self._root / rel
        if not target.is_file():
            raise ManifestError(f"declared file does not exist: {rel}")
        try:
            return json.loads(target.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ManifestError(f"{rel}: not readable as JSON -- {exc}") from exc

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
        return {
            entry["id"]: {k: v for k, v in entry.items() if k not in ("id", "declaration")}
            for entry in self._raw["capabilities"]
        }

    @property
    def detectors(self) -> list:
        return list(self._detectors)

    def schema(self, name: str) -> dict:
        if name not in self._schemas:
            raise ManifestError(f"no schema named {name!r} is declared by this kit")
        return self._schemas[name]

    def validate(self, instance, schema_name: str) -> list[str]:
        return validation.validate(instance, self.schema(schema_name))

    def payload_text(self, rel: str) -> str:
        target = self._root / rel
        if not target.is_file():
            raise ManifestError(f"declared payload source does not exist: {rel}")
        return target.read_text(encoding="utf-8")
