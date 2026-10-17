"""An owner's mark is a signature where the host declares it (ADR-025 amendment 3): which marks a card
holds, the door each opens, the allowed-signers lines, and the setup's refusals -- no terminal, no
passphrase, a git that cannot verify."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path[:0] = [str(Path(__file__).resolve().parents[2] / "kit" / "interpreters" / d) for d in ("", "verbs")]

import signer  # noqa: E402
import signing  # noqa: E402


def test_a_cards_marks_are_its_door_passages_and_its_lowerings():
    card = {"history": [{"to": "shaped", "at": "t0", "by": "dev"},
                        {"to": "bet", "at": "t1", "by": "dev", "signed_by": "owner", "signed_at": "t1"},
                        {"to": "bet", "at": "t3", "by": "dev", "signed_by": "owner", "signed_at": "t3"}],
            "reshaped": [{"to": "major", "at": "t2", "by": "dev"},
                         {"from": "major", "to": "normal", "at": "t4", "by": "dev", "approved_by": "owner"}]}
    marks = signing.marks(card)
    assert marks == {("history[1]", "owner", "t1"): "the passage to bet",
                     ("history[2]", "owner", "t3"): "the passage to bet",
                     ("reshaped[1]", "owner", "t4"): "the lowering to normal (from major)"}
    assert signing.doors_of(marks)["the passage to bet"] == [("history[1]", "owner", "t1"),
                                                             ("history[2]", "owner", "t3")], \
        "a door walked twice keeps both marks, in the record's order"


def test_a_door_walked_twice_is_held_by_its_latest_mark_never_by_its_first_signed_one_N1():
    first, second = ("history[0]", "owner", "t1"), ("history[4]", "owner", "t5")
    door = "the passage to bet"
    assert not signing.holds([first, second], door, {(first, door)}), "a later unsigned passage is not covered"
    assert signing.holds([first, second], door, {(second, door)}), "a door walked again, signed, holds"
    assert signing.holds([first, second], door, {(first, door), (second, door)})
    slipped = ("history[0]", "owner", "t9")
    assert not signing.holds([slipped, second], door, {(second, door)}), \
        "a forged mark slipped in before a signed one, with a later moment, is not covered"
    assert not signing.holds([first], door, set())


def test_an_allowed_signers_line_names_its_principal_and_only_git():
    line = signing.signers_line("owner", "ssh-ed25519 AAAAC3Nza owner@machine\n")
    assert line == 'owner namespaces="git" ssh-ed25519 AAAAC3Nza', "the key's comment is not carried"
    text = "# who may sign\n" + line + "\n" + 'a,b namespaces="git" ssh-ed25519 BBBB\n'
    assert signing.principals(text) == ["owner", "a", "b"]


def test_the_setup_is_refused_without_a_person_at_a_terminal():
    tty = SimpleNamespace(isatty=lambda: True)
    pipe = SimpleNamespace(isatty=lambda: False)
    assert signer.interactive(tty, tty) and not signer.interactive(pipe, tty) and not signer.interactive(tty, pipe)
    with pytest.raises(signer.SignerError, match="owner's own act, in their own terminal"):
        signer._setup(None, SimpleNamespace(setup=True))  # an agent's shell: nothing is touched, not even the host


def test_a_key_that_opens_without_a_passphrase_is_refused_and_one_that_does_not_is_kept():
    asked = []

    def run(argv, **kw):
        asked.append(argv)
        return SimpleNamespace(returncode=0 if len(asked) == 1 else 255)

    assert signer.opens_without_passphrase("the-declared-tool", Path("k"), run=run)
    assert not signer.opens_without_passphrase("the-declared-tool", Path("k"), run=run)
    assert asked[0][:4] == ["the-declared-tool", "-y", "-P", ""], "the program is the declared verifier's"


def test_a_publishers_line_is_never_a_signer_of_commits():
    text = ('owner namespaces="git" ssh-ed25519 AAAA\n'
            'publisher namespaces="agent-kit-capability" ssh-ed25519 BBBB\n'
            'anyone ssh-ed25519 CCCC\n')
    assert signing.principals(text) == ["owner", "anyone"], "an unrestricted line signs in every namespace"
    assert signing.principals(text, "agent-kit-capability") == ["publisher", "anyone"]


def test_any_acceptance_a_record_carries_is_a_mark_and_a_review_is_one_in_its_reviewers_name():
    estate = {"signed_by": "owner", "signed_at": "t9", "entries": [{"id": "x"}]}
    assert signing.marks(estate) == {("", "owner", "t9"): "the acceptance at the top"}
    nested = {"answers": {"approval": {"signed_by": "owner", "signed_at": "t8"}}}
    assert signing.marks(nested) == {("answers.approval", "owner", "t8"): "the acceptance at answers.approval"}
    review = {"card": "c", "reviewer": "owner", "verdict": "approved", "at": "t7"}
    assert signing.reviews(review) == {("", "owner", "t7"): "the review of c (approved)"} and signing.marks(review) == {}


def test_a_mark_replayed_elsewhere_is_a_new_mark_and_a_commit_brings_only_what_its_parent_lacked():
    signed = {"history": [{"to": "bet", "signed_by": "owner", "signed_at": "t1"}]}
    replayed = {"history": [{"to": "bet", "signed_by": "owner", "signed_at": "t1"},
                            {"to": "done", "signed_by": "owner", "signed_at": "t1"}]}
    before, after = signing.marks(signed), signing.marks(replayed)
    assert signing.introduced(after, before) == {("history[1]", "owner", "t1"): "the passage to done"}, \
        "the same name and moment at another door is another mark (C2)"
    assert signing.introduced(after, after) == {}, "a commit that brings no mark is credited with none (M1)"
    moved = {"history": [{"to": "done", "signed_by": "owner", "signed_at": "t1"}]}
    assert signing.introduced(signing.marks(moved), before) == {("history[0]", "owner", "t1"): "the passage to done"}, \
        "a door changed under a signed mark is a new mark"


def test_the_trust_root_is_the_one_accepted_at_a_position_never_a_later_one():
    accepted = [(3, "a", "owner-key"), (7, "b", "owner-and-second")]
    assert signing.root_at(accepted, 2) == "" and signing.root_at(accepted, 3) == "owner-key"
    assert signing.root_at(accepted, 6) == "owner-key" and signing.root_at(accepted, 9) == "owner-and-second"


def test_the_setup_warns_when_the_owners_global_settings_sign_as_them_everywhere(tmp_path):
    key = tmp_path / "kit_owner_signing"
    key.write_text("k", encoding="utf-8")
    key.with_name(key.name + ".pub").write_text("p", encoding="utf-8")
    assert signer.global_warnings({"commit.gpgsign": "", "user.signingkey": ""}.get, key) == []
    every = signer.global_warnings({"commit.gpgsign": "true", "user.signingkey": ""}.get, key)
    assert len(every) == 1 and "commit.gpgsign=true" in every[0]
    for held in (key, key.with_name(key.name + ".pub")):
        same = signer.global_warnings({"commit.gpgsign": "false", "user.signingkey": str(held)}.get, key)
        assert len(same) == 1 and "global user.signingkey is this key" in same[0]
    assert signer.global_warnings({"commit.gpgsign": "", "user.signingkey": str(tmp_path / "other")}.get, key) == []
