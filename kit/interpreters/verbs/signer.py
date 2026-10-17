"""signer -- set up the owner's signing key, so an owner's mark is a signature and not a name (ADR-025 am. 3).

    python .agents/kit/interpreters/cli.py signer --root .                       # where it stands
    python .agents/kit/interpreters/cli.py signer --setup --root . --principal <who> [--key <path>]

Run by the OWNER, in their own terminal. A key an agent made, or one without a passphrase, proves
nothing: whatever can read it can sign as the owner. So `--setup` refuses without an interactive
terminal, lets `ssh-keygen` itself ask for the passphrase (the kit never sees, stores or passes it),
and refuses a key that opens with an empty one. In order, each step skipped when it already holds:

  1. git verifies SSH signatures (2.34 or later) and ssh-keygen is here
  2. the key: the one at --key, else a new ed25519 key made there (default ~/.ssh/kit_owner_signing)
  3. it is encrypted -- a key that opens with no passphrase is refused
  4. its public half is the principal's line in the host's allowed-signers file, and the host's
     policy declares `owner_signing`; git here is told the format, the file and the key (local config;
     every commit is NOT signed -- an agent's commits go on unsigned, and only the owner's carry marks)
  5. a round trip: a test text signed with the key and verified against the file, before anything
     leans on it
  6. what now holds, and the fingerprint to compare once against the owner's own key

The first registration is trusted on first use, as an SSH host key is: the fingerprint is printed so
the owner can see it is theirs. Every later change to the file holds only in a commit an allowed
signer signed (FF-WORK-SIGNED).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import collection
import lifecycle as lifecycle_module
import signing
from errors import KitError

SUMMARY = "set up the owner's signing key, so an owner's mark is a signature -- the owner's own act"
MUTATES = True
REQUIRES_APPROVED_HOST = True
ARGUMENTS = [
    ("--setup", {"action": "store_true", "help": "walk the setup, in order (the owner, in their own terminal)"}),
    ("--principal", {"default": None, "help": "the name the owner signs as -- the name their marks carry"}),
    ("--key", {"default": None, "help": "the private key's path (default: ~/.ssh/kit_owner_signing)"}),
]
#: The payload the delivery capability seeds the allowed-signers file from.
SEED = "allowed_signers"
MINIMUM_GIT = (2, 34)


class SignerError(KitError):
    """A signing setup that cannot be taken honestly."""

    code = "KIT0091"


def interactive(stdin=None, stdout=None) -> bool:
    """Whether a person sits at this run: both ends a terminal. An agent's shell has neither."""
    stdin, stdout = stdin or sys.stdin, stdout or sys.stdout
    return bool(getattr(stdin, "isatty", lambda: False)() and getattr(stdout, "isatty", lambda: False)())


def git_version(said: str) -> tuple:
    found = re.search(r"(\d+)\.(\d+)", said or "")
    return (int(found.group(1)), int(found.group(2))) if found else (0, 0)


def opens_without_passphrase(key: Path, run=subprocess.run) -> bool:
    """True when the key opens with an empty passphrase -- then anything that reads it signs with it."""
    done = run(["ssh-keygen", "-y", "-P", "", "-f", str(key)], capture_output=True)
    return done.returncode == 0


def _places(ctx):
    capabilities = ctx.enabled_capabilities()
    governed = lifecycle_module.the_governed(capabilities, collection.read_all(ctx, capabilities))
    seed = next((i for i in governed.capability.installs if i.get("mode") == "seed"
                 and str(i.get("source", "")).endswith("/" + SEED)), None)
    policy = next((i for i in governed.capability.installs if i.get("reads_as") == "policy"), None)
    if seed is None or policy is None:
        raise SignerError("the delivery capability declares no allowed-signers seed or no policy: nothing to set up")
    declared = (governed.policy or {}).get("owner_signing") or {}
    return governed, declared.get("signers") or seed["target"], policy["target"]


def _status(ctx) -> int:
    governed, signers, _policy = _places(ctx)
    declared = (governed.policy or {}).get("owner_signing")
    text = ctx.workspace.read_text(signers) if ctx.workspace.exists(signers) else ""
    who = signing.principals(text)
    print(f"signer: owner signing is {'DECLARED' if declared else 'not declared'}; {signers} names "
          f"{', '.join(who) if who else 'nobody'}")
    if not declared or not who:
        print("signer: to set it up, the owner runs in their own terminal:\n"
              "  python <kit>/interpreters/cli.py signer --setup --root . --principal <the name you sign as>")
    return 0


def run(ctx, args) -> int:
    if not getattr(args, "setup", False):
        return _status(ctx)
    if not interactive():
        raise SignerError("signer --setup is the owner's own act, in their own terminal: this run has no "
                          "interactive terminal, so nothing was done. A key made here would be known to "
                          "whatever made it")
    principal = getattr(args, "principal", None) or getattr(args, "approve", None)
    if not principal or not re.fullmatch(r"[A-Za-z0-9._@+-]+", principal):
        raise SignerError("signer --setup needs --principal <the name you sign as> -- the name your marks "
                          "carry (`--approve <that name>`), letters, digits and . _ @ + - only")
    governed, signers, policy_rel = _places(ctx)

    print("signer: 1/6  git and ssh-keygen")
    said = subprocess.run(["git", "version"], capture_output=True, text=True).stdout
    if git_version(said) < MINIMUM_GIT:
        raise SignerError(f"git {said.strip() or '(none)'} cannot verify SSH signatures: 2.34 or later is needed")
    if shutil.which("ssh-keygen") is None:
        raise SignerError("ssh-keygen is not on this machine's PATH (it ships with OpenSSH and with Git for Windows)")

    key = Path(getattr(args, "key", None) or Path.home() / ".ssh" / "kit_owner_signing").expanduser()
    public = key.with_name(key.name + ".pub")
    print(f"signer: 2/6  the key: {key}")
    if not key.exists():
        key.parent.mkdir(parents=True, exist_ok=True)
        print("        ssh-keygen asks for a passphrase now -- choose one nobody else knows, and do not add the "
              "key to ssh-agent")
        made = subprocess.run(["ssh-keygen", "-t", "ed25519", "-C", f"{principal} (owner marks)", "-f", str(key)])
        if made.returncode != 0 or not key.exists():
            raise SignerError("ssh-keygen did not make the key; nothing else was done")
    if not public.exists():
        raise SignerError(f"{public} is not there: the public half is what the host records")

    print("signer: 3/6  the key is encrypted")
    if opens_without_passphrase(key):
        raise SignerError(f"{key} opens with no passphrase, so anything that can read it can sign as you. Give it "
                          f"one (ssh-keygen -p -f {key}) and run this again")

    print(f"signer: 4/6  {signers} and the host's policy")
    line = signing.signers_line(principal, public.read_text(encoding="utf-8"))
    present = ctx.workspace.read_text(signers) if ctx.workspace.exists(signers) else ""
    scoped = ctx.workspace.scoped(governed.capability.targets())
    if line not in present.splitlines():
        scoped.write_text(signers, present.rstrip("\n") + ("\n" if present.strip() else "") + line + "\n")
    policy = ctx.workspace.read_json(policy_rel)
    if (policy.get("owner_signing") or {}).get("signers") != signers:
        scoped.write_json(policy_rel, dict(policy, owner_signing={"signers": signers}))
    for name, value in (("gpg.format", "ssh"), ("gpg.ssh.allowedSignersFile", ctx.workspace.path(signers).as_posix()),
                        ("user.signingkey", key.as_posix())):
        subprocess.run(["git", "-C", str(ctx.workspace.root), "config", "--local", name, value], check=True)

    print("signer: 5/6  a round trip -- ssh-keygen asks for the passphrase once more")
    with tempfile.TemporaryDirectory() as scratch:
        text = Path(scratch) / "round-trip"
        text.write_text("kit owner signing round trip\n", encoding="utf-8")
        signed = subprocess.run(["ssh-keygen", "-Y", "sign", "-f", str(key), "-n", "git", str(text)])
        if signed.returncode != 0:
            raise SignerError("the key could not sign the test text; the host's file and config are written, the "
                              "round trip is not -- run this again")
        with open(text, "rb") as data:
            verified = subprocess.run(["ssh-keygen", "-Y", "verify", "-f", str(ctx.workspace.path(signers)),
                                       "-I", principal, "-n", "git", "-s", str(text) + ".sig"], stdin=data,
                                      capture_output=True)
        if verified.returncode != 0:
            raise SignerError("a signature by this key did not verify against the host's file: nothing leans on it")

    fingerprint = subprocess.run(["ssh-keygen", "-lf", str(public)], capture_output=True, text=True).stdout.strip()
    print(f"signer: 6/6  {principal} signs with {fingerprint}")
    print(f"        compare it once with your own: ssh-keygen -lf {public}")
    print(f"        then commit the setup, signed:  git add {signers} {policy_rel} && git commit -S -m \"owner signing\"")
    print("        from now on a door you walk holds in a commit you sign: git commit -S")
    return 0
