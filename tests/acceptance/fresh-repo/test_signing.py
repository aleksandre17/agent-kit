"""An owner's mark is a signature, not a name, where the host declares it (ADR-025 amendment 3) -- on a
real repository, with real keys: a mark in a commit the owner signed holds; the same mark committed
unsigned, or signed by a key the host does not allow, fails; a door walked again in a signed commit
holds; a mark not yet committed is reported and not failed; a mark that stood before signing was set
up holds as it was; and a change to who may sign holds only when an allowed signer signed it."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import unittest

from harness import KIT, Fixtures, install_target

GATE = "FF-WORK-SIGNED"


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
        signers = ".agents/project/delivery/allowed_signers"
        public = owner.with_name("owner.pub").read_text(encoding="utf-8").split()
        (host / signers).write_text(f'owner namespaces="git" {public[0]} {public[1]}\n', encoding="utf-8", newline="\n")
        policy = host / install_target("delivery", reads_as="policy")
        body = json.loads(policy.read_text(encoding="utf-8"))
        policy.write_text(json.dumps({**body, "owner_signing": {"signers": signers}}, indent=2) + "\n",
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


if __name__ == "__main__":
    unittest.main()
