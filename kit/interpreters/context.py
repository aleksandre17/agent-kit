"""The context a verb is handed. It carries ports, never policy."""

from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

from errors import KitError
from ports.clock import Clock
from ports.manifest import Manifest
from ports.probe import Probe
from ports.workspace import Workspace

SCHEMA_VERSION = 1


class BindingError(KitError):
    """A host truth is absent, unreadable, or does not honour the schema that declares it."""


class Context:
    def __init__(self, kit_root: Path, host_root: Path, clock=None) -> None:
        self.manifest = Manifest(kit_root)
        self.workspace = Workspace(host_root)
        self.clock = clock or Clock()
        self.probe = Probe(self.workspace)

    # -- boundary ---------------------------------------------------------------------------
    def boundary(self) -> dict:
        """Measured once, at the boundary, and carried with the reading that used it.
        A name is not a referent: the separator, the encoding and the line ending are the
        translation layer between this interpreter and the host, so they are recorded."""
        return {
            "root": self.workspace.root.as_posix(),
            "os": platform.system().lower(),
            "path_separator": "/",
            "encoding": "utf-8",
            "line_ending": "lf",
            "interpreter": "python-%d.%d" % sys.version_info[:2],
        }

    # -- declarations, resolved -------------------------------------------------------------
    def take_reading(self) -> dict:
        facts, results = self.probe.run(self.manifest.detectors)
        return {
            "schema_version": SCHEMA_VERSION,
            "taken_at": self.clock.now(),
            "boundary": self.boundary(),
            "facts": facts,
            "detectors": results,
        }

    def resolve(self, facts: dict) -> tuple[list, list]:
        """Split declared capabilities into satisfied and unavailable. The reason is recorded,
        because an absent capability is a DECLARED state, not a silent omission."""
        enabled, unavailable = [], []
        for capability in self.manifest.capabilities:
            missing = [
                need for need in capability.requires
                if need["kind"] != "fact" or facts.get(need["id"], None) != need.get("equals", True)
            ]
            if missing:
                unavailable.append({
                    "id": capability.id,
                    "reason": "unmet requirement: " + ", ".join(
                        f"{need['kind']}:{need['id']}" for need in missing
                    ),
                })
            else:
                enabled.append(capability)
        return enabled, unavailable

    def binding(self, rel: str, schema: str) -> dict:
        """Read a host truth THROUGH its schema. An unvalidated read is how a malformed file
        becomes a traceback three layers away instead of the named failure it is."""
        if not self.workspace.exists(rel):
            raise BindingError(f"{rel}: declared host truth is absent; run `init` first")
        try:
            value = self.workspace.read_json(rel)
        except json.JSONDecodeError as exc:
            raise BindingError(f"{rel}: not readable as JSON -- {exc}") from exc
        errors = self.manifest.validate(value, schema)
        if errors:
            raise BindingError(f"{rel} does not honour schema {schema!r}:\n  " + "\n  ".join(errors))
        return value

    def enabled_capabilities(self) -> list:
        """The host's declaration is the source of truth once it exists."""
        project = self.binding(".agents/project/project.json", "project")
        wanted = set(project["capabilities"])
        return [c for c in self.manifest.capabilities if c.id in wanted]

    def class_declarations(self) -> list:
        """Every DECLARED path→class statement: plane roots from the manifest, exact targets
        from capability declarations. Nothing is inferred from a folder's name."""
        declared = [(plane["root"].rstrip("/") + "/", plane["class"]) for plane in self.manifest.planes]
        for capability in self.manifest.capabilities:
            for item in capability.installs:
                declared.append((item["target"], item["class"]))
        return declared
