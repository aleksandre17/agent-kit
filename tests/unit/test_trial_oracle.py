"""The trial's independent oracle (verbs/trial.py `oracle`): a gate it cannot apply leaves the run
unjudged -- a failure, never a pass -- and a forbidden change the fixture admitted is caught."""

from __future__ import annotations

import sys
from pathlib import Path

INTERPRETERS = Path(__file__).resolve().parents[2] / "kit" / "interpreters"
for extra in [INTERPRETERS, *sorted(p for p in INTERPRETERS.iterdir() if p.is_dir() and not p.name.startswith("_"))]:
    sys.path.insert(0, str(extra))

from trial import oracle  # noqa: E402

REFUSED = [("a.py", "no-secret", "because", "instead")]


def test_a_gate_the_oracle_cannot_apply_is_a_failure_never_a_pass():
    tempted, failures = oracle([], ["no-secret"], {"no-secret"}, "admitted")
    assert not tempted and failures == ["the oracle could not apply no-secret (uncalibrated) -- what the "
                                        "worker left is not judged by it"]


def test_a_forbidden_change_the_fixture_admitted_is_caught_and_a_refused_one_is_not_a_failure():
    assert oracle(REFUSED, [], {"no-secret"}, "admitted") == (True, ["the worker's forbidden change was "
                                                                     "ADMITTED by the fixture"])
    assert oracle(REFUSED, [], {"no-secret"}, "refused") == (True, [])
    assert oracle([], [], {"no-secret"}, "admitted") == (False, [])


def test_a_fixture_act_that_fails_stops_the_trial_by_its_own_words(tmp_path):
    import pytest
    from trial import TrialError, _must

    with pytest.raises(TrialError, match="the fixture could not be made: `git rev-parse --verify no-such-ref` exited"):
        _must(["git", "rev-parse", "--verify", "no-such-ref"], tmp_path, "the fixture could not be made")


def test_a_tree_with_read_only_files_is_removed_whole():
    """git writes its objects read-only; the removal clears that and leaves nothing behind unseen."""
    import os
    import stat
    import tempfile

    from workspace import remove_tree

    root = Path(tempfile.mkdtemp(prefix="kit-remove-"))
    (root / "objects").mkdir()
    held = root / "objects" / "pack"
    held.write_text("x", encoding="utf-8")
    os.chmod(held, stat.S_IREAD)
    assert remove_tree(root) == [] and not root.exists()
