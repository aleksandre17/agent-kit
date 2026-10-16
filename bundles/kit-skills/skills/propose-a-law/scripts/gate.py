"""Print an edit-gate skeleton for a law, with every field the edit-gate contract requires."""
import json
import sys

gate_id = sys.argv[1] if len(sys.argv) > 1 else "a-new-law"
print(json.dumps({"id": gate_id, "paths": ".*", "forbids": "<a regular expression for the violating text>",
                  "because": "<what the violation costs>", "instead": "<what to write instead>",
                  "proves": {"path": "<a path>", "text": "<text the gate must refuse>"},
                  "admits": {"path": "<a path>", "text": "<a lookalike the gate must admit>"}}, indent=2))
