"""A Mustache subset -- the projection renderer.

Why a subset and not a dependency: a host must be able to run the kit having installed nothing.
Why Mustache and not an invention: it is the proven logic-less template standard, and logic-less
is the point -- a projection template that could branch would be behaviour smuggled into the
PROJECTION plane, which Cardinal IV forbids as firmly as behaviour in a declaration.

Supported: `{{ name }}` (dotted paths, `.` for the current item), `{{#name}}...{{/name}}`
(list -> iterate, truthy -> once, falsy/empty -> skip), `{{^name}}...{{/name}}` (inverted).
Refused loudly: partials, lambdas, `{{{ }}}`, set-delimiters, and any missing key. A renderer
that silently emits an empty string for a name it could not resolve is a surface that lies.
"""

from __future__ import annotations

import re

from errors import KitError

_TAG = re.compile(r"\{\{([#^/]?)\s*([^{}]*?)\s*\}\}")
_NAME = re.compile(r"^[A-Za-z0-9_.]+$|^\.$")

_MISSING = object()


class TemplateError(KitError):
    """The template used syntax outside the supported subset, or named something absent."""


def _resolve(name: str, stack: list):
    if name == ".":
        return stack[-1]
    head, _, rest = name.partition(".")
    for frame in reversed(stack):
        if isinstance(frame, dict) and head in frame:
            value = frame[head]
            for step in filter(None, rest.split(".")):
                if not isinstance(value, dict) or step not in value:
                    return _MISSING
                value = value[step]
            return value
    return _MISSING


def _stringify(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    return str(value)


_STANDALONE = re.compile(r"^[ \t]*(\{\{[#^/][^{}]*\}\})[ \t]*\r?\n", re.MULTILINE)


def render(template: str, view: dict) -> str:
    # Mustache's standalone-line rule: a line holding nothing but a section tag contributes no
    # line of its own to the output. Without it every section would emit a stray blank line.
    tokens = _tokenise(_STANDALONE.sub(r"\1", template))
    out = _render_tokens(tokens, [view])
    return out


def _tokenise(template: str) -> list:
    tokens: list = []
    position = 0
    for match in _TAG.finditer(template):
        if match.start() > position:
            tokens.append(("text", template[position:match.start()]))
        sigil, name = match.group(1), match.group(2)
        if "{" in name or "}" in name:
            raise TemplateError(f"unsupported tag {match.group(0)!r} (triple-mustache is refused)")
        if not _NAME.match(name):
            raise TemplateError(
                f"unsupported tag {match.group(0)!r}: a name may only be a dotted path or '.'"
            )
        kind = {"": "var", "#": "section", "^": "inverted", "/": "end"}[sigil]
        tokens.append((kind, name))
        position = match.end()
    if position < len(template):
        tokens.append(("text", template[position:]))
    return tokens


def _render_tokens(tokens: list, stack: list) -> str:
    out: list[str] = []
    index = 0
    while index < len(tokens):
        kind, value = tokens[index]
        if kind == "text":
            out.append(value)
            index += 1
        elif kind == "var":
            resolved = _resolve(value, stack)
            if resolved is _MISSING:
                raise TemplateError(f"template names {value!r}, which the view does not carry")
            out.append(_stringify(resolved))
            index += 1
        elif kind in ("section", "inverted"):
            body, index = _slice_section(tokens, index, value)
            resolved = _resolve(value, stack)
            if resolved is _MISSING:
                raise TemplateError(f"template opens section {value!r}, which the view does not carry")
            if kind == "inverted":
                if not resolved:
                    out.append(_render_tokens(body, stack))
            elif isinstance(resolved, list):
                for item in resolved:
                    out.append(_render_tokens(body, stack + [item]))
            elif resolved:
                frame = resolved if isinstance(resolved, dict) else {}
                out.append(_render_tokens(body, stack + [frame]))
        else:
            raise TemplateError(f"closing tag {value!r} has no opening section")
    return "".join(out)


def _slice_section(tokens: list, start: int, name: str) -> tuple[list, int]:
    depth = 0
    index = start + 1
    while index < len(tokens):
        kind, value = tokens[index]
        if kind in ("section", "inverted"):
            depth += 1
        elif kind == "end":
            if depth == 0:
                if value != name:
                    raise TemplateError(f"section {name!r} is closed by {value!r}")
                return tokens[start + 1:index], index + 1
            depth -= 1
        index += 1
    raise TemplateError(f"section {name!r} is never closed")
