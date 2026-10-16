"""Evidence read from inside a DOCUMENT: one key path out of a JSON file. Discovered by the probe
through the kinds registry (`EVIDENCE`)."""

from __future__ import annotations

import json


def _json_path(ws, spec, ours):
    """Read one key path out of a JSON file. Pointer is dot-separated; no expression language."""
    target = ws.path(spec["path"])
    if spec["path"] in ours or not target.is_file():
        return False, None
    try:
        value = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False, None
    for step in spec["pointer"].split("."):
        if not isinstance(value, dict) or step not in value:
            return False, None
        value = value[step]
    return True, value


EVIDENCE = {"json_path": _json_path}
