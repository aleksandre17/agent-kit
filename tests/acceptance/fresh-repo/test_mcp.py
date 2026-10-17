"""Acceptance: an MCP server is declared once, by trust, and served to every product (ADR-024).

A host declares its Model Context Protocol servers in the kit's own terms -- how each is reached, the
NAMES of the variables it needs, its tools with their effects, and its trust -- and every adapter that
renders the MCP view turns them into its product's file. Held here:

  1. on a started host, every declared server reaches every product file that renders the view (each
     parsed as its product parses it), `check` is green, and the effects an untrusted server's level
     does not allow are DENIED while a trusted server's are allowed;
  2. a server at a trust level no vocabulary declares is refused by its code, and a value written where
     only a variable's name may stand is refused by the contract -- a secret has no field to live in.

Every path, view, level and code is read from the declarations and the module that owns it.
"""

from __future__ import annotations

import json
try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10: no TOML reader in the standard library
    tomllib = None
import unittest

from harness import KIT, REPO, Fixtures

import derivation
import serving
import mcp as mcp_resolver
from context import Context
from manifest import Manifest
from test_adapters import ADAPTERS, surfaces_of
from test_pinned_kit import said

CORE = Manifest(KIT)
KIND = next(iter(mcp_resolver.RESOLVES))
VIEW = next(v["id"] for c in CORE.capabilities for i in c.installs if i.get("shape") == serving.SHAPE
            for v in i["serves"]["views"] if "sections" not in v
            and any(carry["kind"] == KIND for carry in v.get("carries", [])))
HOST_SERVERS = next(i["target"] for c in CORE.capabilities for i in c.installs if i.get("validates") == KIND)
LEVELS = {row["id"]: row for c in CORE.capabilities for d in c.raw.get("documents", [])
          if d["validates"] == "mcp-trust" for row in c.documents[d["id"]]["levels"]}
OPEN = next(i for i, row in LEVELS.items() if set(row["allows"]) >= {"read", "write", "exec"})
GUARDED = next(i for i, row in LEVELS.items() if "write" not in row["allows"])
STARTER = REPO / "starters" / "standard.json"
TAKEN = [(STARTER.parent / rel).resolve() for rel in json.loads(STARTER.read_text(encoding="utf-8"))["takes"]]
FILES = sorted({(r["target"], r.get("span"), tuple(r.get("comment") or ())) for a in ADAPTERS if a.resolve() in TAKEN
                for s in surfaces_of(a) for r in s["renders"] if r["view"] == VIEW})

SERVERS = [
    {"id": "fixture-web", "trust": GUARDED, "transport": "http", "url": "https://example.invalid/mcp",
     "bearer_env": "FIXTURE_TOKEN", "tools": [{"name": "fetch", "effect": "read"}, {"name": "post", "effect": "write"}]},
    {"id": "fixture-local", "trust": OPEN, "transport": "stdio", "command": "fixture-mcp", "args": ["--ro"],
     "env_vars": ["FIXTURE_URL"], "tools": [{"name": "query", "effect": "read"}, {"name": "drop", "effect": "exec"}]},
]


def _keys(value) -> set:
    if isinstance(value, dict):
        return set(value) | {k for v in value.values() for k in _keys(v)}
    if isinstance(value, list):
        return {k for v in value for k in _keys(v)}
    return set()


def _parsed(text: str, target: str, span, comment):
    if span:
        text = derivation.span(text, span, list(comment) or None)
    if target.endswith(".toml"):
        if tomllib is None:
            raise unittest.SkipTest("Python 3.10 has no tomllib: the TOML a product reads is proven on 3.11+, never assumed here")
        return tomllib.loads(text)
    return json.loads(text)


class Mcp(Fixtures, unittest.TestCase):

    def started(self, servers):
        host = self.host()
        ran = self.run_kit(KIT, host, "start", "--path", str(STARTER), "--approve", "acceptance-suite")
        self.assertEqual(0, ran.returncode, said(ran))
        (host / HOST_SERVERS).write_text(json.dumps({"schema_version": 1, "servers": servers}, indent=2) + "\n",
                                         encoding="utf-8", newline="\n")
        return host

    def test_430_every_server_reaches_every_product_and_an_untrusted_effect_is_denied(self):
        self.assertTrue(FILES, "the standard starter serves at least one product that reads MCP servers")
        host = self.started(SERVERS)
        self.assertEqual(0, self.run_kit(KIT, host, "render").returncode)
        for target, span, comment in FILES:
            with self.subTest(file=target):
                keys = _keys(_parsed((host / target).read_text(encoding="utf-8"), target, span, comment))
                self.assertTrue({s["id"] for s in SERVERS} <= keys, keys)
        self.assertEqual(0, self.run_kit(KIT, host, "check").returncode)
        seen = mcp_resolver.RESOLVES[KIND](Context(kit_root=KIT, host_root=host), {})
        self.assertIn({"server": "fixture-web", "tool": "post"}, seen["denied"])
        self.assertIn({"server": "fixture-web", "tool": "fetch"}, seen["allowed"])
        self.assertIn({"server": "fixture-local", "tool": "drop"}, seen["allowed"])

    def test_431_an_undeclared_level_and_a_written_value_are_refused(self):
        host = self.started([{**SERVERS[1], "trust": "a-level-nobody-declares"}])
        refused = self.run_kit(KIT, host, "render")
        self.assertIn(f"[{mcp_resolver.TrustError.code}]", said(refused))
        (host / HOST_SERVERS).write_text(json.dumps({"schema_version": 1, "servers": [
            {**SERVERS[1], "env": {"FIXTURE_URL": "a value written in the repository"}}]}) + "\n",
            encoding="utf-8", newline="\n")
        checked = self.run_kit(KIT, host, "check")
        self.assertNotEqual(0, checked.returncode)
        self.assertIn("'env' is not declared", said(checked))


if __name__ == "__main__":
    unittest.main()
