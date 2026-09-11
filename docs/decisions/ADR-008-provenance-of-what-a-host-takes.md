# ADR-008 — Provenance of what a host takes: integrity pinned at a door, authenticity delegated and never assumed

- **Status**: Accepted
- **Date**: 2026-09-11
- **Amends**: ADR-004, by closing what it left OPEN — *provenance, signature and fetch for a
  third-party bundle* — for provenance and signature. **Fetch stays open** (see Consequences).
  ADR-002 gains one field on the estate; ADR-005 gains one code (`KIT0032`); ADR-006 gains one
  floor gate. Nothing in ADR-001…007 is overturned.
- **Rules on**: `kit/interpreters/provenance.py` (new), `kit/interpreters/gates/taken.py` (new),
  `kit/capabilities/governance/provenance.json` (new document) and
  `kit/schemas/provenance.schema.json` (new, registered in `kit/MANIFEST.json`), the optional
  `provenance` claim on `capability.schema.json`, the optional `taken` list on
  `estate.schema.json`, one `seed` install (`.agents/project/allowed_signers`, from `kit/seeds/allowed_signers`) and one gate
  (`FF-PROVENANCE-PINNED`, floor `enforce`) on the governance capability, one phase (`provenance`)
  in `init`, and `lockfile.closure` — the declaration walker, now one function used twice.

## The situation

The kit accounts for its OWN bytes (`kit.lock.json`) and a host records what it was GIVEN
(`estate.json`). A capability that did not come from the kit — a doctrine bundle a company
publishes is the first case — fell between the two: a declaration a human had placed in a kit.
Nothing recorded where it came from, nothing could tell the bytes its publisher released from
bytes altered on the way, and nothing stopped a host silently receiving an older release. The
blueprint called release signing and provenance the biggest trust hole. Two facts bound the answer:
the kit is **standard library only**, and the standard library has **no asymmetric signature
primitive** — `hashlib` and `hmac`, no ed25519, no RSA verify. Hand-rolling one is how trust holes
are made.

## The field

- **npm / Subresource Integrity** — `integrity: sha512-…` pins CONTENT; says nothing of who.
- **Go `go.sum` + checksum database** — content pinned at first use (`h1:` dirhash), and the first
  use itself made auditable by a transparency log. Trust-on-first-use, recorded.
- **Cargo.lock / Nix / Bazel** — content addressing: the name of a thing is its digest.
- **git SSH signing** — `ssh-keygen -Y verify` against an `allowed_signers` file the verifier
  OWNS: asymmetric verification delegated to a tool on almost every machine, with the trust root
  held by the party that verifies, not the party that signs.
- **sigstore / cosign + Rekor** — keyless identity signing plus a transparency log.
- **SLSA** — levels of build provenance (who built what, from what, how).
- **TUF** — separated roles, threshold signatures, and explicit defences against ROLLBACK (never
  accept older than seen) and FREEZE (never accept stale as current).
- **OPA signed bundles** — policy bundles carry a signature the engine verifies before loading.

The convergent reading: **integrity and authenticity are two propositions with two mechanisms**.
Content is pinned at first contact (go.sum, SRI, Cargo); identity is verified against a trust root
the VERIFIER holds (git allowed_signers, TUF root, OPA keys); and a version high-water mark stops
rollback (TUF). The questions and their answers here:

| question | answer |
|---|---|
| what is pinned | CONTENT (an `h1:` digest) and VERSION, both, per taken capability |
| what is trusted at first contact | nothing by a machine; a named human walks a door and the pin records who and when |
| who holds the trust root | the HOST, in a file it authors (`.agents/project/allowed_signers`, seeded naming nobody) |
| what stops a rollback | the pinned version is a high-water mark; older is refused and no door opens it |
| where asymmetric verification lives | in a delegated tool the kit declares as data; its absence is a named state |

## The decision

### ① A taken capability is MEASURED, not claimed

A capability is *taken* when its declaration is not a path in the kit's own lock. The lock is the
kit's reading of itself; a capability cannot declare itself kit-issued. Nothing is privileged —
no publisher, no id, no word `doctrine`.

### ② INTEGRITY — a content pin at a door, in the estate, never re-taken

The capability's bytes are the closure of its declaration by the kit's one walker
(`lockfile.closure`), less the paths the kit issued (the kit's lock pins those) and less the
signature its publisher claims (a digest cannot contain the signature over itself). They digest to
Go's `h1:` dirhash, adopted whole. The pin lives in exactly ONE record, the estate's `taken` list —
because it is the same proposition as `files` one step further upstream: *what this host was
given*. It carries `capability`, `version`, `digest`, `pinned_by`, `pinned_at`, `authenticity`, and
`supersedes` when it replaced an earlier pin.

Each measured state's meaning is DATA in `provenance.json`, not code:

| state | disposition | meaning |
|---|---|---|
| pinned | hold | the bytes and version are the pin |
| withdrawn | carry | no longer taken; the pin is kept, so the capability can never return older |
| first-contact | door | never pinned; a named person takes it, and the pin records it |
| advanced | door | newer than the pin; new bytes from a publisher, met as first contact is |
| drifted | refuse | same version, different bytes; never re-pinned |
| rolled-back | refuse | older than the pin; refused whoever signed it |

The judgement runs as a declared `init` phase before any write (and therefore under `upgrade`,
which hands its verdict to `init`), and as the gate `FF-PROVENANCE-PINNED` on every `check`, whose
stance is a **floor**: no host may lower its own integrity. A refusal is `KIT0032` and no approval
opens it. An estate written before this ADR carries no `taken`; that is read as NO pin — never as
a pass — and the check says `first-contact`.

### ③ AUTHENTICITY — delegated, declared, and absent by name

A publisher may CLAIM a signature in its declaration (`provenance: {verifier, signer,
signature}`). A claim establishes nothing. The kit declares an OPEN registry of verifiers as data —
argv with whole-token placeholders, a namespace, and where the host keeps its trust root — with one
row today, `ssh-keygen -Y verify`. At the door, the signed statement (declared template:
`{capability}@{version} {digest}`) is handed to the verifier the claim names. The outcome is one
declared word, recorded on the pin with its moment:

- `signature-verified` — **established**; the pin also records the signer and the digest of the trust root.
- `unsigned`, `signature-missing`, `unknown-verifier`, `no-trust-root`, `verifier-absent` — **not
  established**, each saying why. A trust root with no line but comments (the prefix is declared
  on the verifier row) names nobody: `no-trust-root`, an absence of trust, never a refutation. The surface prints `authenticity NOT ESTABLISHED: <word>`.
- `signature-refuted` — evidence AGAINST: refused (`KIT0032`), nothing pinned. Never recorded as an absence.

Authenticity is a reading taken ONCE, at the door, and dated. Integrity is what carries it forward:
`check` re-measures the digest and does not re-run the verifier, so a later check depends on no
tool and no trust root — the pin is exactly what makes that unnecessary.

## Rejected alternatives

1. **Verify signatures in-process (vendored ed25519, or a crypto dependency).** A dependency is
   forbidden by the kit's own boundary; a hand-rolled or vendored primitive is unaudited
   cryptography inside a trust mechanism — the exact trust hole this closes, relocated.
2. **Authenticity only, no content pin (OPA-signed-bundle-alone).** Makes every run depend on a
   verifier and a trust root being present, and turns their absence into either a hard stop for
   every host or a silent pass. It also gives no drift or rollback defence between signatures.
3. **Re-pin on drift, or let `--approve` accept a changed digest at the same version.** A pin that
   a door can re-take pins nothing; this is precisely the attack go.sum refuses.
4. **Trust by default what a human placed in the kit (status quo).** The surface would print a
   capability as though its origin were known when nothing was measured — a success that was not
   observed.
5. **A separate `provenance` capability owning its own record.** A host could disable it and lower
   a floor, and the pin would get a second home beside the estate that already states what a host
   received. The mechanism is the estate's, so it lives on the estate's capability.
6. **Detect "foreign" by a self-declared publisher field.** A claim cannot establish its own
   standing; the kit's lock can, because the kit wrote it.

7. **A `space` the host fills with trust roots.** Measured wrong: an empty directory is not a
   file, so a host that took governance could not be shown to hold its declared targets. A SEED
   that names nobody is a present, honest zero.

## Consequences

- **Named absences, not built.** FETCH (retrieval by a URL/registry) stays open — a bundle is
  still placed in a kit by a human. There is no TRANSPARENCY LOG (Go sumdb / Rekor): first contact
  is recorded, not globally auditable. There is no FREEZE defence (TUF timestamp role): a
  capability that is never updated is never known to be stale. There is no THRESHOLD or ROLE
  separation (TUF): one signer suffices. A host cannot yet DECLARE that it requires authenticity
  (a stance refusing `not established` pins). A DELIBERATE downgrade has no door; today it needs
  the host to edit its own estate — the host is not the adversary this defends against. SLSA
  build provenance is not captured. The kit's OWN lock is not signed: the kit is the one capability
  whose provenance this mechanism does not yet establish, and the same verifier registry is the
  way to establish it.
- A new verifier (cosign, minisign, gpg) is a registry row, not an interpreter edit.
- Every kit change here is a new lock; a fixture kit is copied from the lock.

## Fitness functions

`tests/acceptance/fresh-repo/test_provenance.py`, `test_202`…`test_211`: first contact is a
recorded door; unsigned is printed NOT ESTABLISHED and never established; drift fails check and is
refused and not re-pinned; rollback is refused under approval; an advance is a door and records
what it supersedes; kit-issued capabilities are never taken and the zero is printed; a record
without pins fails check; a claim with no trust root is a named absence; and against a REAL
`ssh-keygen` — a trusted signature is recorded verified, an untrusted one is refused (skipped with
a declared reason where no usable verifier is measured on the machine).
