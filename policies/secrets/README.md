# secrets -- the one catalogue of what a secret looks like

This policy's edit-gate document is THE catalogue of secret shapes for every tool that judges a host,
not one judge among several. The edit hook and the commit gate apply it here; a tool that scans the
whole tree and its history reads the same file by path instead of keeping a list of its own, so there
is one list to extend, calibrated once, and two judges cannot disagree about what a secret is.

## Where it is, and its contract

| what | path |
| --- | --- |
| the catalogue, as published | `policies/secrets/payload/edit-gates.json` |
| the catalogue, in a host that took it | `.agents/taken/secrets/payload/edit-gates.json` (vendored), or the published path inside the host's own copy of the kit (referenced, ADR-024 decision 18) |
| its contract (JSON Schema 2020-12 subset) | `kit/schemas/edit-gate.schema.json` (`$id: edit-gate`) |

A reader needs only these fields of each row of `gates[]`:

| field | meaning |
| --- | --- |
| `id` | the rule's stable name, quoted in every refusal |
| `paths` | a regular expression over the host-relative POSIX path; `.*` for every file |
| `forbids` | the pattern of a secret: a regular expression, matched MULTILINE over the text a change introduces |
| `proves` | `{path, text}` -- a specimen the rule MUST flag |
| `admits` | `{path, text}` -- a lookalike the rule MUST NOT flag (a placeholder, a public key) |
| `because`, `instead` | why it is refused, and what to do instead -- for the message |

The patterns use only syntax Python `re`, PCRE and RE2 read alike (non-capturing groups, `\b`, classes,
counted repetition). A reader calibrates before it trusts: a row whose `forbids` does not flag its
`proves` text, or flags its `admits` text, is not applied -- the kit's `check` (FF-EDIT-GATE) holds every
row to exactly that, and so should any other reader.

## The bridge to a tree-and-history scanner

stack-kit's `scan` reads this catalogue through the path a host declares in its `stack-kit.json` under
`security.secretPatterns` -- one of the two paths above. The bridge is declared by the stack-kit adapter
(`adapters/stack-kit`); the kit core names no scanner and imports nothing from one.
