"""Acceptance: ONE FILE IS ONE MODULE.

A refusal is caught by its CLASS, and a class is an object. When the same source file is
loaded under two names -- once by package path (`ports.manifest`) and once by stem
(`manifest`) -- every class in it exists twice, and an `except ManifestError` holding one copy
does not catch a raise of the other. The refusal then falls through as an unforeseen crash, and
the operator is told about the kit's internals instead of about the host's situation. The name
agreed; the referent did not (Cardinal VII).

It is measured in a FRESH interpreter, after importing every module the kit ships, because a
split only exists once both names have been reached -- and a test process that had already
imported one of them would hide it. It runs with `-B`: a probe that measures the kit must not
WRITE into the kit, and the first version of this test left a `.pyc` in the payload that the lock
then correctly refused to ship.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest

from harness import KIT  # noqa: F401 -- sets the interpreter's path, as every suite here does

INTERPRETERS = KIT / "interpreters"

PROBE = r"""
import importlib, json, sys
from pathlib import Path
root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
import cli  # the real entry point: it prepares the path exactly as an operator's run does
for path in sorted(root.rglob("*.py")):
    if "__pycache__" in path.parts or path.stem.startswith("_"):
        continue
    try:
        importlib.import_module(path.stem)
    except Exception:
        pass  # a module that cannot import alone is not this test's subject
seen = {}
for name, module in list(sys.modules.items()):
    where = getattr(module, "__file__", None)
    if where and Path(where).resolve().is_relative_to(root):
        seen.setdefault(str(Path(where).resolve().relative_to(root)), []).append(name)
print(json.dumps({f: sorted(n) for f, n in seen.items() if len(n) > 1}))
"""


class ModuleIdentity(unittest.TestCase):
    def test_186_no_interpreter_file_is_loaded_under_two_names_so_no_refusal_class_exists_twice(self):
        run = subprocess.run([sys.executable, "-B", "-c", PROBE, str(INTERPRETERS)],
                             capture_output=True, text=True, check=False)
        self.assertEqual(0, run.returncode, f"the probe itself failed:\n{run.stderr}")
        split = json.loads(run.stdout.strip().splitlines()[-1])
        self.assertEqual({}, split,
                         "one source file became two modules, so every class in it -- including "
                         f"its refusals -- exists twice: {split}")


if __name__ == "__main__":
    unittest.main()
