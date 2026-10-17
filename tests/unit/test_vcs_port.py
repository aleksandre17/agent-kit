"""The version-control port answers for the repository a call names, never for one the caller's
environment is bound to: git exports GIT_DIR and its kin to a hook, and a hook that reads a submodule
-- the kit's own pin -- must read the submodule."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parents[2] / "kit"
sys.path.insert(0, str(KIT / "interpreters" / "ports"))

import vcs  # noqa: E402


def _repo(at: Path, word: str) -> str:
    clean = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}  # the fixture's own
    at.mkdir()
    for argv in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
        subprocess.run(["git", "-C", str(at), *argv], check=True, env=clean)
    (at / "f").write_text(word, encoding="utf-8")
    subprocess.run(["git", "-C", str(at), "add", "f"], check=True, env=clean)
    subprocess.run(["git", "-C", str(at), "commit", "-q", "-m", word], check=True, env=clean)
    return subprocess.run(["git", "-C", str(at), "rev-parse", "HEAD"], capture_output=True, text=True,
                          check=True, env=clean).stdout.strip()


def test_a_call_into_another_repository_reads_that_repository_under_a_hooks_environment(tmp_path, monkeypatch):
    host, kit = _repo(tmp_path / "host", "host"), _repo(tmp_path / "kit", "kit")
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "host" / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(tmp_path / "host"))
    monkeypatch.setenv("GIT_INDEX_FILE", str(tmp_path / "host" / ".git" / "index"))
    said, why = vcs.run(tmp_path / "kit", ["rev-parse", "HEAD"])
    assert why is None and said.strip() == kit != host


def test_the_environment_keeps_everything_that_does_not_bind_git_to_a_repository(monkeypatch):
    monkeypatch.setenv("GIT_DIR", "/elsewhere")
    monkeypatch.setenv("GIT_AUTHOR_NAME", "someone")
    env = vcs.env()
    assert "GIT_DIR" not in env and env["GIT_AUTHOR_NAME"] == "someone"
