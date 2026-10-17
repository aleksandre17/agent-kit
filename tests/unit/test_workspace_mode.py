"""A rendered file keeps the mode of the file it replaces (found on Linux: a re-render dropped the execute
bit `activate` gave the served git hooks, so git silently skipped them)."""
from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "kit" / "interpreters" / "ports"))

import workspace  # noqa: E402


@pytest.mark.skipif(os.name == "nt", reason="the filesystem keeps no execute bit")
def test_a_replaced_file_keeps_its_execute_bit(tmp_path):
    hook = tmp_path / "pre-push"
    hook.write_text("old\n", encoding="utf-8")
    hook.chmod(0o755)
    workspace.Workspace(tmp_path).write_text("pre-push", "new\n")
    assert hook.read_text(encoding="utf-8") == "new\n"
    assert stat.S_IMODE(hook.stat().st_mode) & 0o111, "the execute bit survived the rewrite"
