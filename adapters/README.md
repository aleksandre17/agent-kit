# Runtime adapters -- published beside the kit, never inside it

Each directory here is ONE complete capability, publishable on its own, and is the only place in
this repository a runtime product's name may appear (ADR-014). The kit core ships the GRAMMAR of a
surface (`kit/schemas/runtime-surface.schema.json`) and the port that serves one; it ships no
instance, and renders and checks green with no adapter taken -- a declared zero.

A host TAKES an adapter the way it takes any capability it did not receive from the kit, into its
take plane beside the pinned kit (ADR-018): `take --path adapters/<id> --approve <who>` (or a
starter), then the id enabled in `.agents/project/project.json` and `init --approve <who>` attests the
pin (ADR-008). Unsigned, its authenticity reads NOT ESTABLISHED.

An adapter may also bring a DETECTOR for its product's own files: a document under the `detector`
contract (`adapters/stack-kit/`). A product whose hook reads a decision on stdout, rather than an exit
code, declares the text in its surface (`hands.refusal.stdout`, `hands.admission.stdout`).

The served projection collects every document whose declaration keeps the `runtime-surface`
contract, from every enabled capability -- so a third product is a third directory, and nothing
in the kit changes.
