"""The context a verb is handed. It carries ports, never policy."""

from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

import resolver
from errors import KitError, PendingApproval
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
        #: The records THIS process opened and has not yet closed. A run cannot judge its own
        #: liveness: a record still open because the run holding it is the one asking is not a
        #: run that died, and a sensor unable to tell the two apart would report every healthy
        #: run as a corpse. Carried as a READING the context can state, so that a declaration
        #: names what to do about it and no interpreter holds a hidden exemption.
        self.in_flight = set()

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

    def classify(self, facts: dict) -> tuple[list, list, dict]:
        """What the MEASUREMENT decides: candidates, the unavailable with their reasons, and the
        provisions those absences take with them. Never refuses -- so a caller can report the
        measured absence before anything is refused on account of it."""
        return resolver.classify(self.manifest.capabilities, facts)

    def compose(self, candidates, blocked=None) -> list:
        """What the DECLARED SET decides: order, or refusal. The composition semantics live in
        `resolver`, which holds no port and no state; this only hands it declarations."""
        return resolver.compose(candidates, blocked)

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

    # -- the host's own answer --------------------------------------------------------------
    def install_of_mode(self, mode: str, required: bool = True):
        """The one install statement in this kit that works in `mode`. The answers file and the
        reading are found by asking the DECLARATIONS where they live, never by a path constant
        held in the interpreter: a path written into the interpreter is a second home for a
        truth a capability already states, and it is the home that cannot be changed.

        TWO is always a defect and is always refused -- two answers files is a second home for
        the same host truth. ZERO is refused only where the answer is actually NEEDED. A kit that
        declares none is malformed, but saying so early would put this judgement in front of the
        composition refusal that explains WHY the declaration went missing, and a cause that
        arrives after its consequence is not a report.
        """
        found = [i for c in self.manifest.capabilities for i in c.installs if i["mode"] == mode]
        if len(found) > 1 or (not found and required):
            raise BindingError(
                f"this kit declares {len(found)} installs in mode {mode!r}; exactly one is "
                f"required, because the host has exactly one of these to answer with"
            )
        return found[0] if found else None

    def host_answers(self, required: bool = True):
        """The ANSWERS FILE: what this host chose, in the host's own plane. `None` when the host
        has never answered -- an absence the caller must name, never assume past."""
        item = self.install_of_mode("declaration", required=required)
        if item is None:
            return None
        if not self.workspace.exists(item["target"]):
            if required:
                raise BindingError(f"{item['target']}: declared host truth is absent; run `init` first")
            return None
        return self.binding(item["target"], item["validates"])

    def require_approved(self) -> dict:
        """Cardinal V at the one door where a human stands. An install whose approval never came
        is a DECLARED, DATED state on disk, and every later phase refuses while it stands -- so a
        stalled install reads as stalled, rather than as a half-built host that looks finished."""
        answers = self.host_answers()
        if answers["status"] != "accepted":
            item = self.install_of_mode("declaration")
            raise PendingApproval(
                f"{item['target']} is status {answers['status']!r}, drafted at "
                f"{answers['drafted_at']} and never approved. This host has chosen "
                f"{answers['capabilities']} but nobody has accepted the choice, so nothing "
                f"downstream may run on it. Approve with: init --approve <who>"
            )
        return answers

    def select(self, candidates, enable=None, disable=None) -> list:
        return resolver.select(candidates, self.manifest.policies, enable, disable,
                               known=[c.id for c in self.manifest.capabilities])

    def enabled_capabilities(self) -> list:
        """The host's declaration is the source of truth once it exists."""
        wanted = set(self.host_answers()["capabilities"])
        return resolver.arrange([c for c in self.manifest.capabilities if c.id in wanted])

    def class_declarations(self) -> list:
        """Every DECLARED path→class statement: plane roots from the manifest, exact targets
        from capability declarations. Nothing is inferred from a folder's name."""
        declared = [(plane["root"].rstrip("/") + "/", plane["class"]) for plane in self.manifest.planes]
        for capability in self.manifest.capabilities:
            for item in capability.installs:
                declared.append((item["target"], item["class"]))
        return declared
