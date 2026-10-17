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
    assert marks == {("owner", "t1"): "the passage to bet", ("owner", "t3"): "the passage to bet",
                     ("owner", "t4"): "the lowering to normal (from major)"}
    assert signing.doors_of(marks)["the passage to bet"] == [("owner", "t1"), ("owner", "t3")], \
        "a door walked twice is one door: one signed mark holds it"


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
        signer.run(None, SimpleNamespace(setup=True))  # an agent's shell: nothing is touched, not even the host


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
    assert signing.marks(estate) == {("owner", "t9"): "the acceptance at the top"}
    nested = {"answers": {"approval": {"signed_by": "owner", "signed_at": "t8"}}}
    assert signing.marks(nested) == {("owner", "t8"): "the acceptance at answers.approval"}
    review = {"card": "c", "reviewer": "owner", "verdict": "approved", "at": "t7"}
    assert signing.reviews(review) == {("owner", "t7"): "the review of c (approved)"} and signing.marks(review) == {}
