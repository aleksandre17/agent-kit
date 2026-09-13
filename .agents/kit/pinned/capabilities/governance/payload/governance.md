# Governance — the four-class seam

This file is VENDOR. It is framework payload: never edited downstream, replaced wholesale on upgrade.
If you need it to say something else here, that belongs in the BINDING plane, not in this file.

Every path under `.agents/` is exactly one of:

- **VENDOR** — framework payload. Replaced wholesale. Never hand-edited.
- **BINDING** — this host's own truth. Created once if absent; never written by an upgrade.
- **PROJECTION** — derived from VENDOR + BINDING. Deletable at any moment; `render` rebuilds it
  byte-identically. A projection that can be edited and survive is a second home, and a second home
  is a system that speaks with confidence and lies.
- **EPHEMERAL** — observed state. Never committed, never upgraded, safely deletable.

The class is **declared** in a capability's `installs`, never inferred from the folder name.

Two rules follow, and they are the whole seam:

1. A capability may write only inside the targets it declared. The `Workspace` port refuses
   everything else — the write scope is the declaration, so the two cannot drift.
2. A reading of the environment states *when* it was taken. A reading that cannot be dated cannot
   be contradicted, only believed.
