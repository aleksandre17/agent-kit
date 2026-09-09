"""A deliberately small JSON Schema subset validator.

Why this exists: the kit must run on a host that has installed nothing. A dependency the host
must `pip install` before the gates can run is a defect, so `jsonschema` is not available to us.
The answer is not "skip validation" and not "hand-write checks per file" -- either would put the
contract in two homes. It is: keep JSON Schema as the ONE contract language, and interpret the
subset the kit's own schemas actually use.

Supported keywords: type, enum, const, required, properties, additionalProperties (bool only),
items, minItems, minLength, pattern.
Deliberately unsupported (and refused loudly rather than ignored): $ref, oneOf/anyOf/allOf, not,
dependencies, patternProperties, numeric bounds. An unsupported keyword raises -- a validator that
silently ignores half its schema is a surface that lies.
"""

from __future__ import annotations

import re

SUPPORTED = {
    "$id", "$schema", "title", "description",
    "type", "enum", "const", "required", "properties", "additionalProperties",
    "items", "minItems", "minLength", "pattern",
}

_TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "null": type(None),
}


class UnsupportedSchema(Exception):
    """The schema uses a keyword this interpreter cannot honour."""


def _type_ok(value, name: str) -> bool:
    expected = _TYPES[name]
    if name in ("integer", "number") and isinstance(value, bool):
        return False
    return isinstance(value, expected)


def validate(instance, schema: dict, path: str = "$") -> list[str]:
    """Return a list of human-readable errors. Empty list means valid."""
    unknown = set(schema) - SUPPORTED
    if unknown:
        raise UnsupportedSchema(f"{path}: unsupported schema keywords {sorted(unknown)}")

    errors: list[str] = []

    if "type" in schema:
        names = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        for name in names:
            if name not in _TYPES:
                raise UnsupportedSchema(f"{path}: unknown type {name!r}")
        if not any(_type_ok(instance, n) for n in names):
            return [f"{path}: expected type {'/'.join(names)}, got {type(instance).__name__}"]

    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}")

    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: {instance!r} not one of {schema['enum']!r}")

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: shorter than minLength {schema['minLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errors.append(f"{path}: {instance!r} does not match {schema['pattern']!r}")

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{path}: fewer than minItems {schema['minItems']}")
        if "items" in schema:
            for i, item in enumerate(instance):
                errors += validate(item, schema["items"], f"{path}[{i}]")

    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                errors.append(f"{path}: missing required property {key!r}")
        properties = schema.get("properties", {})
        for key, sub in properties.items():
            if key in instance:
                errors += validate(instance[key], sub, f"{path}.{key}")
        extra = schema.get("additionalProperties", True)
        if extra is False:
            for key in instance:
                if key not in properties:
                    errors.append(f"{path}: property {key!r} is not declared")
        elif extra is not True:
            raise UnsupportedSchema(f"{path}: additionalProperties must be a boolean here")

    return errors
