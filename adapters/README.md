# Runtime adapters -- published beside the kit, never inside it

Each directory here is ONE complete capability, publishable on its own, and is the only place in
this repository a runtime product's name may appear (ADR-014). The kit core ships the GRAMMAR of a
surface (`kit/schemas/runtime-surface.schema.json`) and the port that serves one; it ships no
instance, and renders and checks green with no adapter taken -- a declared zero.

A host TAKES an adapter the way it takes any capability it did not receive from the kit: the
directory is placed at `kit/capabilities/<id>/`, a row `{"id": "<id>", "declaration":
"capabilities/<id>/capability.json"}` is added to `kit/MANIFEST.json`, and `init --approve <who>`
pins its digest at the door (ADR-008). Unsigned, its authenticity reads NOT ESTABLISHED.

The served projection collects every document whose declaration keeps the `runtime-surface`
contract, from every enabled capability -- so a third product is a third directory, and nothing
in the kit changes.
