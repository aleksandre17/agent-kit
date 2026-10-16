# Developing the kit

## Where to change it

Change the kit in its own repository, never inside a host that runs it referenced. A referenced kit
that changes under a host blocks every edit in that host, by design.

## Before you push

1. In a fresh clone, activate the commit gate on the kit's own host (`activate --surface git-commit`).
2. Run the unit suite: `python -B -m pytest -p no:cacheprovider tests/unit -q`.
3. Run the acceptance suite: `python -I -B tests/acceptance/fresh-repo/parallel.py [modules]`.
4. On the kit's own host, run `lock --root .` and then `upgrade --root .`.
5. Run `audit`.

## Versions, addresses and refusal codes

- **A capability whose bytes change gets a new version.**
- **A bundle's document addresses carry that version** (`bundle@x.y.z#id`). A new version therefore
  re-addresses its documents, and hosts that cite them move with it.
- **A new refusal gets a KIT code** in `kit/diagnostics.json`; bump `issued`.

## How a host takes the change

1. Fast-forward the host's submodule.
2. If a capability has a new version, take it again with `take --path <dir>`.
3. Run `upgrade --mode referenced`.
