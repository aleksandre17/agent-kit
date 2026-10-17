"""An owner's mark is a signature, not a name, where the host declares it (ADR-025 amendment 3) -- on a
real repository, with real keys: a mark in a commit the owner signed holds; the same mark committed
unsigned, or signed by a key the host does not allow, fails; a door walked again in a signed commit
holds; a mark not yet committed is reported and not failed; a mark that stood before signing was set
up holds as it was; and a change to who may sign holds only when an allowed signer signed it. And the
forgeries an agent that can commit would try: a key it adds vouching for its own commits (C1), a signed
or grandfathered mark replayed onto another door (C2), a forged mark riding a later signed commit (M1),
an existing host turned red by turning signing on (H5), a card the archive moved judged again (H6), and
the declaration itself removed or repointed (H7)."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import unittest

from harness import KIT, Fixtures, install_target

GATE = "FF-WORK-SIGNED"
SIGNERS = ".agents/project/allowed_signers"  # the host's one trust root (ADR-008)


def _git_version() -> tuple:
    said = subprocess.run(["git", "version"], capture_output=True, text=True).stdout
    found = re.search(r"(\d+)\.(\d+)", said)
    return (int(found.group(1)), int(found.group(2))) if found else (0, 0)


@unittest.skipUnless(shutil.which("ssh-keygen") and _git_version() >= (2, 34), "needs ssh-keygen and git 2.34+")
class OwnerMarksSigned(Fixtures, unittest.TestCase):

    def key(self, name):
        made = self._temp(f"key-{name}-") / name
        # A test key without a passphrase: what is proved here is git's verdict, not the owner's secret.
        subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", name, "-f", str(made)], check=True)
        return made

    def git(self, host, *argv, signed_with=None):
        config = ["-c", "user.email=s@invalid", "-c", "user.name=suite", "-c", "core.hooksPath=/dev/null"]
        if signed_with is not None:
            config += ["-c", "gpg.format=ssh", "-c", f"user.signingkey={signed_with.as_posix()}"]
        done = subprocess.run(["git", "-C", str(host), *config, *argv], capture_output=True, text=True)
        self.assertEqual(0, done.returncode, done.stdout + done.stderr)
        return done

    def commit(self, host, message, signed_with=None):
        self.git(host, "add", "-A")
        self.git(host, "commit", "-q", *(["-S"] if signed_with else []), "-m", message, signed_with=signed_with)

    def card(self, host, identity, *moments, state="bet"):
        cards = host / install_target("delivery", reads_as="cards")
        cards.mkdir(parents=True, exist_ok=True)
        history = [{"from": "shaped", "to": "bet", "at": at, "by": "dev", "signed_by": "owner", "signed_at": at}
                   for at in moments]
        (cards / f"{identity}.json").write_text(json.dumps(
            {"schema_version": 1, "id": identity, "title": identity, "state": state,
             "created_at": "2026-10-17T00:00:00+00:00", "history": history}, indent=2) + "\n",
            encoding="utf-8", newline="\n")

    def checked(self, host) -> str:
        said = self.run_kit(KIT, host, "check")
        return said.stdout + said.stderr

    def test_a_name_is_not_a_signature_and_a_signature_is(self):
        host = self.installed()
        owner, stranger = self.key("owner"), self.key("stranger")
        signers = ".agents/project/allowed_signers"  # the host's one trust root (ADR-008)
        public = owner.with_name("owner.pub").read_text(encoding="utf-8").split()
        (host / signers).write_text(f'owner namespaces="git" {public[0]} {public[1]}\n', encoding="utf-8", newline="\n")
        policy = host / install_target("delivery", reads_as="policy")
        body = json.loads(policy.read_text(encoding="utf-8"))
        policy.write_text(json.dumps({**body, "owner_signing": {}}, indent=2) + "\n",
                          encoding="utf-8", newline="\n")
        self.git(host, "config", "gpg.ssh.allowedSignersFile", (host / signers).as_posix())
        self.card(host, "before", "2026-10-01T00:00:00+00:00")
        self.commit(host, "the setup, with a mark that stood before it", signed_with=owner)
        self.assertIn(f"PASS  {GATE}", self.checked(host), "a mark that stood before signing holds as it was")

        self.card(host, "forged", "2026-10-17T01:00:00+00:00")
        self.commit(host, "a mark an agent wrote")
        failed = self.checked(host)
        self.assertIn(f"FAIL  {GATE}", failed)
        self.assertIn("forged.json: the passage to bet is marked by owner, and no commit that principal signed", failed)

        self.card(host, "forged", "2026-10-17T01:00:00+00:00", "2026-10-17T02:00:00+00:00")
        self.commit(host, "signed by a key the host does not allow", signed_with=stranger)
        self.assertIn(f"FAIL  {GATE}", self.checked(host), "a stranger's signature is not the owner's")

        self.card(host, "forged", "2026-10-17T01:00:00+00:00", "2026-10-17T02:00:00+00:00", "2026-10-17T03:00:00+00:00")
        self.commit(host, "the owner walks the door again, signed", signed_with=owner)
        self.assertIn(f"PASS  {GATE}", self.checked(host), "one signed mark holds the door")

        self.card(host, "waiting", "2026-10-17T04:00:00+00:00")
        waiting = self.checked(host)
        self.assertIn(f"PASS  {GATE}", waiting)
        self.assertIn("waiting.json: the passage to bet is marked by owner and not committed yet", waiting)
        (host / install_target("delivery", reads_as="cards") / "waiting.json").unlink()

        evidence = host / "docs" / "work" / "evidence" / "forged"
        evidence.mkdir(parents=True, exist_ok=True)
        (evidence / "review.json").write_text(json.dumps(
            {"schema_version": 1, "card": "forged", "reviewer": "owner", "verdict": "approved",
             "reviewed": "HEAD", "at": "2026-10-17T05:00:00+00:00"}) + "\n", encoding="utf-8", newline="\n")
        (evidence / "agent-review.json").write_text(json.dumps(
            {"schema_version": 1, "card": "forged", "reviewer": "an-auditor-agent", "verdict": "approved",
             "reviewed": "HEAD", "at": "2026-10-17T05:00:00+00:00"}) + "\n", encoding="utf-8", newline="\n")
        self.commit(host, "a review in the owner's name, and one in an auditor's")
        reviewed = self.checked(host)
        self.assertIn("review.json: the review of forged (approved) is marked by owner, and no commit", reviewed)
        self.assertNotIn("agent-review.json", reviewed, "a reviewer who signs nothing is a name, as before")
        (evidence / "review.json").unlink()
        self.commit(host, "the forged review withdrawn", signed_with=owner)

        line = stranger.with_name("stranger.pub").read_text(encoding="utf-8").split()
        with open(host / signers, "a", encoding="utf-8", newline="\n") as more:
            more.write(f'owner namespaces="git" {line[0]} {line[1]}\n')
        self.commit(host, "an agent adds its own key")
        widened = self.checked(host)
        self.assertIn(f"FAIL  {GATE}", widened)
        self.assertIn("changed who may sign, and no allowed signer signed it", widened)


    def entry(self, to, at, who="owner"):
        return {"from": "shaped", "to": to, "at": at, "by": "dev", "signed_by": who, "signed_at": at}

    def write_card(self, host, identity, history, state="bet", where=None):
        folder = host / (where or install_target("delivery", reads_as="cards"))
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{identity}.json").write_text(json.dumps(
            {"schema_version": 1, "id": identity, "title": identity, "state": state,
             "created_at": "2026-10-17T00:00:00+00:00", "history": history}, indent=2) + "\n",
            encoding="utf-8", newline="\n")

    def policy(self, host, mutate):
        policy = host / install_target("delivery", reads_as="policy")
        body = json.loads(policy.read_text(encoding="utf-8"))
        mutate(body)
        policy.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8", newline="\n")

    def signed_host(self, before=None):
        """A host whose owner set signing up in one commit they signed -- after `before(host)`, its history."""
        host = self.installed()
        if before:
            before(host)
        owner = self.key("owner")
        public = owner.with_name("owner.pub").read_text(encoding="utf-8").split()
        (host / SIGNERS).write_text(f'owner namespaces="git" {public[0]} {public[1]}\n', encoding="utf-8", newline="\n")
        self.policy(host, lambda body: body.update(owner_signing={}))
        self.commit(host, "owner signing, set up", signed_with=owner)
        return host, owner

    def test_a_key_a_commit_adds_never_vouches_for_that_commit_or_what_it_signs_C1(self):
        host, owner = self.signed_host()
        stranger = self.key("stranger")
        line = stranger.with_name("stranger.pub").read_text(encoding="utf-8").split()
        with open(host / SIGNERS, "a", encoding="utf-8", newline="\n") as more:
            more.write(f'owner namespaces="git" {line[0]} {line[1]}\n')
        self.commit(host, "an agent adds its own key, signed by it", signed_with=stranger)
        self.write_card(host, "forged", [self.entry("bet", "2026-10-17T01:00:00+00:00")])
        self.commit(host, "and signs a forged mark with it", signed_with=stranger)
        said = self.checked(host)
        self.assertIn(f"FAIL  {GATE}", said)
        self.assertIn("changed who may sign, and no allowed signer signed it", said)
        self.assertIn("forged.json: the passage to bet is marked by owner, and no commit that principal signed", said)

        public = owner.with_name("owner.pub").read_text(encoding="utf-8").split()
        (host / SIGNERS).write_text(f'owner namespaces="git" {public[0]} {public[1]}\n', encoding="utf-8", newline="\n")
        self.commit(host, "the owner takes the key out, signed", signed_with=owner)
        said = self.checked(host)
        self.assertNotIn("changed who may sign", said, "a refused change no longer standing is not reported")
        self.assertIn("forged.json: the passage to bet is marked by owner, and no commit", said,
                      "a mark the stranger signed was read against the root as accepted, which never held its key")

    def test_a_mark_replayed_onto_another_door_is_a_new_mark_C2(self):
        grandfathered = "2026-10-01T00:00:00+00:00"
        host, owner = self.signed_host(
            before=lambda host: self.write_card(host, "old", [self.entry("bet", grandfathered)]))
        self.write_card(host, "fresh", [self.entry("bet", "2026-10-17T01:00:00+00:00")])
        self.commit(host, "the owner walks a door, signed", signed_with=owner)
        self.assertIn(f"PASS  {GATE}", self.checked(host))

        self.write_card(host, "old", [self.entry("bet", grandfathered), self.entry("done", grandfathered)],
                        state="done")
        self.write_card(host, "fresh", [self.entry("bet", "2026-10-17T01:00:00+00:00"),
                                        self.entry("done", "2026-10-17T01:00:00+00:00")], state="done")
        self.commit(host, "an agent copies both marks onto the next door")
        said = self.checked(host)
        self.assertIn(f"FAIL  {GATE}", said)
        self.assertIn("old.json: the passage to done is marked by owner, and no commit", said,
                      "a grandfathered mark replayed")
        self.assertIn("fresh.json: the passage to done is marked by owner, and no commit", said,
                      "a signed mark replayed")

    def test_a_signed_commit_is_credited_only_with_the_marks_it_introduced_M1(self):
        host, owner = self.signed_host()
        self.write_card(host, "card", [self.entry("bet", "2026-10-17T01:00:00+00:00")])
        self.commit(host, "an agent forges the passage")
        self.write_card(host, "card", [self.entry("bet", "2026-10-17T01:00:00+00:00"),
                                       self.entry("doing", "2026-10-17T02:00:00+00:00")], state="doing")
        self.commit(host, "the owner walks the next door, signed", signed_with=owner)
        said = self.checked(host)
        self.assertIn(f"FAIL  {GATE}", said)
        self.assertIn("card.json: the passage to bet is marked by owner, and no commit", said)
        self.assertNotIn("card.json: the passage to doing", said)

    def test_a_door_walked_twice_is_held_by_its_latest_passage_not_its_first_signed_one_N1(self):
        host, owner = self.signed_host()
        bet = self.entry("bet", "2026-10-17T01:00:00+00:00")
        self.write_card(host, "card", [bet])
        self.commit(host, "the owner bets, signed", signed_with=owner)
        flight = {"from": "bet", "to": "in-flight", "at": "2026-10-17T02:00:00+00:00", "by": "dev"}
        self.write_card(host, "card", [bet, flight], state="in-flight")
        self.commit(host, "the agent starts the work")
        parked = dict(self.entry("parked", "2026-10-17T03:00:00+00:00"), **{"from": "in-flight"})
        self.write_card(host, "card", [bet, flight, parked], state="parked")
        self.commit(host, "the owner parks it, signed", signed_with=owner)
        self.assertIn(f"PASS  {GATE}", self.checked(host))
        reshaped = {"from": "parked", "to": "shaped", "at": "2026-10-17T04:00:00+00:00", "by": "dev"}
        again = self.entry("bet", "2026-10-17T05:00:00+00:00")
        self.write_card(host, "card", [bet, flight, parked, reshaped, again], state="bet")
        self.commit(host, "the agent walks the bet again, in the owner's name, unsigned")
        said = self.checked(host)
        self.assertIn(f"FAIL  {GATE}", said, "the first signed bet never covers a later passage")
        self.assertIn("card.json: the passage to bet is marked by owner, and no commit that principal signed", said)
        self.write_card(host, "card", [bet, flight, parked, reshaped, again,
                                       self.entry("bet", "2026-10-17T06:00:00+00:00")], state="bet")
        self.commit(host, "the owner walks the bet again, signed", signed_with=owner)
        self.assertIn(f"PASS  {GATE}", self.checked(host), "a later signed passage covers the unsigned one")

    def test_turning_signing_on_keeps_an_existing_host_green_H5(self):
        def history(host):
            self.commit(host, "the install, with the empty trust root it seeds")
            self.write_card(host, "earlier", [self.entry("bet", "2026-10-02T00:00:00+00:00")])
            self.commit(host, "work done before signing was set up")
        host, _owner = self.signed_host(before=history)
        self.assertIn(f"PASS  {GATE}", self.checked(host),
                      "the baseline is where signing began, not where its empty seed was laid")

    def test_a_card_the_archive_moved_keeps_its_signed_history_H6(self):
        host, owner = self.signed_host()
        self.write_card(host, "closed", [self.entry("bet", "2026-10-17T01:00:00+00:00")])
        self.commit(host, "the owner walks a door, signed", signed_with=owner)
        cards = install_target("delivery", reads_as="cards")
        archived = install_target("delivery", mode="space", validates="card", reads_as=None) + "2026"
        (host / archived).mkdir(parents=True, exist_ok=True)
        self.git(host, "mv", f"{cards}closed.json", f"{archived}/closed.json")
        self.commit(host, "archive: the card moves, byte for byte")
        said = self.checked(host)
        self.assertIn(f"PASS  {GATE}", said)
        self.assertNotIn("closed.json: the passage to bet", said)

    def test_the_declaration_once_signed_is_undone_only_by_a_signer_H7(self):
        host, owner = self.signed_host()
        self.policy(host, lambda body: body.pop("owner_signing"))
        self.write_card(host, "forged", [self.entry("bet", "2026-10-17T01:00:00+00:00")])
        self.commit(host, "an agent removes the declaration, and forges a mark")
        said = self.checked(host)
        self.assertIn(f"FAIL  {GATE}", said)
        self.assertIn("removed owner_signing, and no allowed signer signed it", said)
        self.assertIn("forged.json: the passage to bet is marked by owner, and no commit", said)

        stranger = self.key("stranger")
        line = stranger.with_name("stranger.pub").read_text(encoding="utf-8").split()
        (host / ".agents/project/own_signers").write_text(f'owner namespaces="git" {line[0]} {line[1]}\n',
                                                          encoding="utf-8", newline="\n")
        self.policy(host, lambda body: body.update(owner_signing={"signers": ".agents/project/own_signers"}))
        self.commit(host, "then repoints it at a root of its own, signed by its own key", signed_with=stranger)
        said = self.checked(host)
        self.assertIn(f"FAIL  {GATE}", said)
        self.assertIn("changed owner_signing, and no allowed signer signed it", said)

        self.policy(host, lambda body: body.pop("owner_signing"))
        (host / install_target("delivery", reads_as="cards") / "forged.json").unlink()
        self.commit(host, "the owner turns signing off, signed", signed_with=owner)
        self.assertIn(f"PASS  {GATE}", self.checked(host), "a signer may undo the declaration")


if __name__ == "__main__":
    unittest.main()
