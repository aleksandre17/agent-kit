# Packet — link L3a: the host tree meets the drawn floor (decided, not yet built)

*Kind: proposal. It binds nothing until it lands. The orchestrator decided it on 2026-09-13 at HEAD
`ad73054` (full suite 261/261). Three dispatches from a national-accounts session were refused as
"out of scope for this repository", so this is run from a session rooted HERE (ADR-015 "one body":
the framework runs its own development).*

**Artifact:** zero rows `pending: L3` in `kit/capabilities/governance/host-layout.json`; FF-HOST-FLOOR
green on host #0 (re-delivered) and on the host #2 clone; the full suite green.

**Decided design:**
1. **Flatten.** The pinned copy lives AT `.agents/kit/`, and its lock at `.agents/project/kit.lock.json`.
   `pin.py` reads and writes the lock there. The separate vendor installs of the doctrine pages and
   `HOST-LAYOUT.json` are removed, and readers use the in-tree files, so a host carries those bytes once.
2. **The old shape upgrades cleanly.** `upgrade` on a host carrying `.agents/kit/pinned/` moves it to the
   flat shape as one planned act (`--plan` shows it). One acceptance test covers it.
3. **Adapters contribute floor rows.** A capability declaration may carry `floor` rows. FF-HOST-FLOOR
   evaluates governance's rows plus those of every ENABLED capability. `adapters/claude-code` and
   `adapters/codex` declare `.claude/` and `.codex/`. kit/ stays free of product names.
4. **Re-point, never a placeholder:** `project/roster.json` → pending F · `generated/INDEX.md` →
   pending L3b · `runtime/{telemetry,ground,guards}/` → pending C · `runtime/receipts/` becomes the
   receipts target if receipts already live under `runtime/`, and otherwise pending C.
5. `generated/{roles/,runtimes/}` become directory render targets. If that ripples wider than the render
   targets and their tests, re-point them to pending L3b instead.
6. New refusals get diagnostic codes, and `kit/kit.lock.json` is regenerated.

**Verification:** run the touched files while working, and the FULL suite once at the end, to a file,
reading only its summary and `^FAILED` lines.
