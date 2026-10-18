# Residence — what has no home in this installed surface

> PROJECTION. Do not edit: delete this whole plane and run `render`, and it comes back byte-identical.
> Kit version 0.4.1 · project status accepted.

Nothing on this page is ever removed by the kit. A residence rule NAMES a resident and says where it
belongs; the move is a human act, recorded as such.

## Declared by the kit

### dead-by-location-archive

- matches `(^|/)archive/`
- because vendored superseded text carries no date and no author, so a later reader finds it, cannot tell when it stopped being true, and obeys it.
- belongs in the upstream repository's history, indexed by its changelog -- a chapter worth keeping is not archived, it is current.
- calibrated on `.agents/project/doctrine/archive/superseded-chapter.md`, which it must see, and `.agents/project/doctrine/archived-decisions-and-how-to-read-them.md`, which it must tolerate

### graveyard-by-name-feedback

- matches `(^|/)feedback/`
- because the genre records HOW a rule was learned, which is a lifecycle stage and not a home; a folder named after the intake is a graveyard by construction, and its rows never leave it.
- belongs under the concern it governs -- portable identity in the doctrine plane, environment-conditional doctrine beside the condition it declares, a host incident in the host's own shared knowledge.
- calibrated on `.agents/project/doctrine/feedback/how-we-learned-it.md`, which it must see, and `.agents/project/knowledge/shared/feedback-loops-in-review.md`, which it must tolerate

### vendored-release-record

- matches `(^|/)(UPGRADE-NOTES|CHANGELOG)\.md$`
- because an append-only release record grows with the framework's age rather than this host's needs, so every host would carry the full history of versions it never ran.
- belongs upstream, read at the moment of need: the delta between the version this host has and the version it is moving to is a projection computed at upgrade time, never a vendored artifact.
- calibrated on `.agents/project/UPGRADE-NOTES.md`, which it must see, and `.agents/project/doctrine/upgrade.md`, which it must tolerate

## Declared by this host

_This host has declared no residence rules of its own. That is a state, not a gap: the kit's rules
still hold, and a host adds a genre by declaring one._
