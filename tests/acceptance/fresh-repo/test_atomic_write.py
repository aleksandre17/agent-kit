"""Acceptance: A WRITE IS WHOLE OR IT DID NOT HAPPEN.

The kit externalises its state before it can be lost -- the journal before a phase, the receipt
before a run, the hold before a write. That identity is only half-adopted if the record can be
TORN: written in place, a document is honest to the process writing it and unreadable to anyone
reading it at the same moment, and a process killed mid-write leaves a truncated file that parses
as nothing and reads as something. A record nobody can read whole has not been externalised.

Two properties, each attacked rather than asserted:

  1. a reader polling a document while it is rewritten sees the old version or the new one --
     never a torn one;
  2. a write that fails part-way leaves the previous document exactly as it was, and no stray
     behind it.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from harness import KIT  # noqa: F401 -- prepares the interpreter's path

import workspace as workspace_port  # noqa: E402

PORTS = KIT / "interpreters" / "ports"

#: Large enough that an in-place rewrite has a window a polling reader will land in.
BODY = {"rows": [{"i": i, "text": "x" * 64} for i in range(20000)]}

WRITER = r"""
import json, sys, time
sys.dont_write_bytecode = True
sys.path[:0] = [sys.argv[1], sys.argv[2]]
import workspace
from pathlib import Path
ws = workspace.Workspace(Path(sys.argv[3]))
body = {"rows": [{"i": i, "text": "x" * 64} for i in range(20000)]}
deadline = time.monotonic() + float(sys.argv[4])
n = 0
while time.monotonic() < deadline:
    n += 1
    body["generation"] = n
    ws.write_json("doc.json", body)
print(n)
"""


class AtomicWrite(unittest.TestCase):
    def test_194_a_reader_polling_a_document_while_it_is_rewritten_never_sees_it_torn(self):
        with tempfile.TemporaryDirectory() as root:
            ws = workspace_port.Workspace(Path(root))
            ws.write_json("doc.json", dict(BODY, generation=0))
            writer = subprocess.Popen(
                [sys.executable, "-B", "-c", WRITER, str(PORTS), str(PORTS.parent), root, "2.0"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            reads = torn = 0
            generations = set()
            try:
                while writer.poll() is None:
                    try:
                        raw = (Path(root) / "doc.json").read_bytes()
                    except PermissionError:
                        continue  # Windows: the file is mid-rename; that is not a reading
                    reads += 1
                    try:
                        generations.add(json.loads(raw)["generation"])
                    except (ValueError, KeyError):
                        torn += 1
            finally:
                out, err = writer.communicate(timeout=60)
            self.assertEqual(0, writer.returncode, f"the writer died:\n{err}")
            self.assertGreater(int(out.strip()), 5, "the writer barely wrote; nothing was measured")
            self.assertGreater(len(generations), 2, "the reader never saw a rewrite land")
            self.assertEqual(0, torn, f"{torn} of {reads} readings caught a torn document")

    def test_195_a_write_that_fails_part_way_leaves_the_old_document_and_no_stray_behind(self):
        with tempfile.TemporaryDirectory() as root:
            ws = workspace_port.Workspace(Path(root))
            ws.write_json("doc.json", {"version": "old"})
            before = (Path(root) / "doc.json").read_bytes()
            real = os.fsync

            def dies(_fd):
                raise OSError("the disk went away mid-write")

            workspace_port.os.fsync = dies
            try:
                with self.assertRaises(OSError):
                    ws.write_json("doc.json", {"version": "new", "pad": "y" * 100000})
            finally:
                workspace_port.os.fsync = real
            self.assertEqual(before, (Path(root) / "doc.json").read_bytes(),
                             "a failed write damaged the document it was replacing")
            self.assertEqual(["doc.json"], sorted(p.name for p in Path(root).iterdir()),
                             "a failed write left a stray beside the document")


if __name__ == "__main__":
    unittest.main()
