"""The `mcp-servers` resolver -- every Model Context Protocol server this host serves its runtimes,
with what each runtime may do with its tools, decided by the server's declared TRUST (ADR-024).

A server is declared once, in the kit's own terms (`mcp-servers`): how it is reached, the NAMES of the
environment variables it needs -- never a value, so a secret has no field to be written into -- the
tools it offers with the EFFECT of each (read, write, exec), and its trust. The trust levels are a
declared vocabulary (`mcp-trust`): which effects a level lets a runtime use without asking, and what
happens to a tool the declaration does not name. A runtime adapter turns the result into its
product's own file; nothing here knows a product.

Content a tool returns is DATA, never instructions (the `untrusted-content` policy): an untrusted
server is held to the effects its level allows, so a page an injected instruction arrives in cannot
reach a write or an exec through it.
"""

from __future__ import annotations

import declared
from errors import KitError

SERVERS = ({declared.CONTRACT: "mcp-servers"}, "servers")
LEVELS = ({declared.CONTRACT: "mcp-trust"}, "levels")


class TrustError(KitError):
    """A server declares a trust level no vocabulary declares, or a tool twice."""

    code = "KIT0075"


def _servers(ctx, params) -> dict:
    levels = {row["id"]: row for row in declared.rules(ctx, *LEVELS)}
    rows, allowed, denied = [], [], []
    for server in declared.rules(ctx, *SERVERS):
        level = levels.get(server["trust"])
        if level is None:
            raise TrustError(
                f"MCP server {server['id']!r} declares trust {server['trust']!r}, which no trust "
                f"vocabulary declares (declared: {sorted(levels)}); a server whose trust means nothing "
                f"would be served with whatever a product does by default")
        names = [tool["name"] for tool in server.get("tools", [])]
        if len(names) != len(set(names)):
            raise TrustError(f"MCP server {server['id']!r} declares a tool twice")
        tools = [{**tool, "allowed": tool["effect"] in level["allows"]} for tool in server.get("tools", [])]
        allowed += [{"server": server["id"], "tool": t["name"]} for t in tools if t["allowed"]]
        denied += [{"server": server["id"], "tool": t["name"]} for t in tools if not t["allowed"]]
        rows.append({
            "id": server["id"], "summary": server.get("summary", ""), "trust": server["trust"],
            "stdio": server["transport"] == "stdio", "http": server["transport"] == "http",
            "command": server.get("command", ""), "args": list(server.get("args", [])),
            "env_vars": [{"name": n} for n in server.get("env_vars", [])],
            "url": server.get("url", ""), "bearer_env": server.get("bearer_env", ""),
            "headers_env": [{"header": h, "name": n} for h, n in sorted((server.get("headers_env") or {}).items())],
            "has_headers_env": bool(server.get("headers_env")),
            # Every header an http server is sent, as (header, prefix, variable): the bearer token
            # in the RFC 6750 form, and each declared header as its variable's whole value.
            "headers": ([{"header": "Authorization", "prefix": "Bearer ", "name": server["bearer_env"]}]
                        if server.get("bearer_env") else [])
                       + [{"header": h, "prefix": "", "name": n}
                          for h, n in sorted((server.get("headers_env") or {}).items())],
            "tools": tools,
            "allowed_tools": [t["name"] for t in tools if t["allowed"]],
            "denied_tools": [t["name"] for t in tools if not t["allowed"]],
            # What a product does with a tool the declaration does not name: `deny` restricts the
            # server to its allowed tools where the product can say so; `ask` leaves the product's prompt.
            "restricted": level["undeclared"] == "deny",
        })
    return {"any": bool(rows), "servers": rows, "allowed": allowed, "denied": denied,
            "approved": [{"id": row["id"]} for row in rows]}


RESOLVES = {"mcp-servers": _servers}
