"""signer -- set up the owner's signing key, so an owner's mark is a signature and not a name (ADR-025 am. 3).

    python .agents/kit/interpreters/cli.py signer --root .                       # where it stands
    python .agents/kit/interpreters/cli.py signer --setup --root . --principal <who> [--key <path>]

Run by the OWNER, in their own terminal. A key an agent made, or one without a passphrase, proves
nothing: whatever can read it can sign as the owner. So `--setup` refuses without an interactive
terminal, lets the key tool itself ask for the passphrase (the kit never sees, stores or passes it),
and refuses a key that opens with an empty one. The trust root and the key tool are the ones the
host's declared verifier names (ADR-008): one root, one program, for every signature. In order, each
step skipped when it already holds:

  1. version control verifies SSH signatures (git 2.34 or later) and the declared key tool is here
  2. the key: the one at --key, else a new ed25519 key made there (default ~/.ssh/kit_owner_signing)
  3. it is encrypted -- a key that opens with no passphrase is refused
  4. its public half is the principal's line in the host's trust root, and the host's policy declares
     `owner_signing`; version control here is told the format, the file and the key (local config;
     every commit is NOT signed -- an agent's commits go on unsigned, and only the owner's carry marks)
  5. a round trip: a test text signed with the key and verified against the file, before anything
     leans on it
  6. what now holds, and the fingerprint to compare once against the owner's own key

The first registration is trusted on first use, as an SSH host key is: the fingerprint is printed so
the owner can see it is theirs. Every later change to the file holds only in a commit an allowed
signer signed -- the delivery capability's gate over owner marks says so on every `check`.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import collection
import hostlock
import lifecycle as lifecycle_module
import provenance
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
MINIMUM_GIT = (2, 34)
#: The namespace commits are signed in -- the one an owner's line in the trust root is restricted to.
NAMESPACE = "git"


class SignerError(KitError):
    """A signing setup that cannot be taken honestly."""

    code = "KIT0091"


def interactive(stdin=None, stdout=None) -> bool:
    """Whether a person sits at this run: both ends a terminal. An agent's shell has neither."""
    stdin, stdout = stdin or sys.stdin, stdout or sys.stdout
    return bool(getattr(stdin, "isatty", lambda: False)() and getattr(stdout, "isatty", lambda: False)())


def opens_without_passphrase(tool: str, key: Path, run=subprocess.run) -> bool:
    """True when the key opens with an empty passphrase -- then anything that reads it signs with it."""
    done = run([tool, "-y", "-P", "", "-f", str(key)], capture_output=True)
    return done.returncode == 0


def global_warnings(setting, key: Path) -> list:
    """What the owner's GLOBAL version-control settings would undo (`setting(name)` -> its value, "" when
    unset): signing every commit, or this key as every repository's signing key, signs an agent's commits
    on this machine as the owner -- the very thing the setup keeps apart."""
    warnings = []
    if setting("commit.gpgsign").strip().lower() == "true":
        warnings.append("your global configuration signs EVERY commit (commit.gpgsign=true): a commit an agent "
                        "makes on this machine is then signed as you -- unset it globally and sign your own "
                        "commits by hand (commit -S)")
    configured = setting("user.signingkey").strip()
    if configured:
        def same(a: Path, b: Path) -> bool:
            try:
                return a.expanduser().resolve() == b.expanduser().resolve()
            except OSError:
                return False
        if any(same(Path(configured), held) for held in (key, key.with_name(key.name + ".pub"))):
            warnings.append(f"your global user.signingkey is this key ({configured}): every repository on this "
                            f"machine signs with it -- keep it in this host's own configuration only")
    return warnings


def _places(ctx):
    """(governed, the trust root, the key tool, the capability that seeds the root, the policy's path)."""
    capabilities = ctx.enabled_capabilities()
    governed = lifecycle_module.the_governed(capabilities, collection.read_all(ctx, capabilities))
    rooted = signing.trust_root(capabilities)
    policy = next((i for i in governed.capability.installs if i.get("reads_as") == "policy"), None)
    if rooted is None or rooted[2] is None or policy is None:
        raise SignerError("no capability declares a verifier with a seeded trust root, or no delivery policy: "
                          "nothing to set up")
    declared = (governed.policy or {}).get("owner_signing") or {}
    root, checks, owner = rooted
    return governed, declared.get("signers") or root, checks, owner, policy["target"]


def _status(ctx) -> int:
    governed, signers, _checks, _owner, _policy = _places(ctx)
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
    hostlock.arrive(ctx, args)  # one writer per host: a hold another run keeps refuses this one, by name
    if not getattr(args, "setup", False):
        return _status(ctx)
    return hostlock.held(ctx, args, lambda: _setup(ctx, args))


def _setup(ctx, args) -> int:
    if not interactive():
        raise SignerError("signer --setup is the owner's own act, in their own terminal: this run has no "
                          "interactive terminal, so nothing was done. A key made here would be known to "
                          "whatever made it")
    principal = getattr(args, "principal", None) or getattr(args, "approve", None)
    if not principal or not re.fullmatch(r"[A-Za-z0-9._@+-]+", principal):
        raise SignerError("signer --setup needs --principal <the name you sign as> -- the name your marks "
                          "carry (`--approve <that name>`), letters, digits and . _ @ + - only")
    governed, signers, checks, root_owner, policy_rel = _places(ctx)
    tool = checks[0]

    print(f"signer: 1/6  version control and {tool}")
    have = ctx.workspace.vcs_version()
    if have < MINIMUM_GIT:
        raise SignerError(f"version control {'.'.join(map(str, have))} cannot check SSH signatures: git 2.34 or "
                          f"later is needed")
    if shutil.which(tool) is None:
        raise SignerError(f"{tool} is not on this machine's PATH (it ships with OpenSSH and with Git for Windows)")

    key = Path(getattr(args, "key", None) or Path.home() / ".ssh" / "kit_owner_signing").expanduser()
    public = key.with_name(key.name + ".pub")
    print(f"signer: 2/6  the key: {key}")
    if not key.exists():
        key.parent.mkdir(parents=True, exist_ok=True)
        print(f"        {tool} asks for a passphrase now -- choose one nobody else knows, and do not load the "
              f"key into an agent")
        made = subprocess.run([tool, "-t", "ed25519", "-C", f"{principal} (owner marks)", "-f", str(key)])
        if made.returncode != 0 or not key.exists():
            raise SignerError(f"{tool} did not make the key; nothing else was done")
    if not public.exists():
        raise SignerError(f"{public} is not there: the public half is what the host records")

    print("signer: 3/6  the key is encrypted")
    if opens_without_passphrase(tool, key):
        raise SignerError(f"{key} opens with no passphrase, so anything that can read it can sign as you. Give it "
                          f"one ({tool} -p -f {key}) and run this again")

    print(f"signer: 4/6  {signers} and the host's policy")
    line = signing.signers_line(principal, public.read_text(encoding="utf-8"))
    present = ctx.workspace.read_text(signers) if ctx.workspace.exists(signers) else ""
    if line not in present.splitlines():
        ctx.workspace.scoped(root_owner.targets()).write_text(
            signers, present.rstrip("\n") + ("\n" if present.strip() else "") + line + "\n")
    policy = ctx.workspace.read_json(policy_rel)
    if (policy.get("owner_signing") or {}).get("signers") != signers:
        ctx.workspace.scoped(governed.capability.targets()).write_json(
            policy_rel, dict(policy, owner_signing={"signers": signers}))
    # the private key's path: version control hands it to the key tool, which asks for the passphrase --
    # a public key's path would send it to an agent, which the owner was told not to load it into
    done, why = ctx.workspace.configure_vcs({"gpg.format": "ssh",
                                             "gpg.ssh.allowedSignersFile": ctx.workspace.path(signers).as_posix(),
                                             "user.signingkey": key.as_posix()})
    if done is None:
        raise SignerError(f"version control here could not be told how to sign: {why}")
    for warning in global_warnings(ctx.workspace.global_vcs_setting, key):
        print(f"        WARNING: {warning}")

    print(f"signer: 5/6  a round trip -- {tool} asks for the passphrase once more")
    with tempfile.TemporaryDirectory() as scratch:
        text = Path(scratch) / "round-trip"
        text.write_text("kit owner signing round trip\n", encoding="utf-8")
        signed = subprocess.run([tool, "-Y", "sign", "-f", str(key), "-n", NAMESPACE, str(text)])
        if signed.returncode != 0:
            raise SignerError("the key could not sign the test text; the host's file and config are written, the "
                              "round trip is not -- run this again")
        # checked by the declared verifier's own argv (ADR-008), in the namespace commits are signed in
        argv = provenance.filled(checks, {"trust_root": str(ctx.workspace.path(signers)), "signer": principal,
                                          "namespace": NAMESPACE, "signature": str(text) + ".sig"})
        with open(text, "rb") as data:
            accepted = subprocess.run(argv, stdin=data, capture_output=True)
        if accepted.returncode != 0:
            raise SignerError("a signature by this key was not accepted against the host's trust root: nothing "
                              "leans on it")

    fingerprint = subprocess.run([tool, "-lf", str(public)], capture_output=True, text=True).stdout.strip()
    print(f"signer: 6/6  {principal} signs with {fingerprint}")
    print(f"        compare it once with your own: {tool} -lf {public}")
    print(f"        then commit the setup, signed:  git add {signers} {policy_rel} && git commit -S -m \"owner signing\"")
    print("        from now on a door you walk holds in a commit you sign: git commit -S")
    return 0
