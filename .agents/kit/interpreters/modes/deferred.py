"""Install modes a LATER step of the run carries out, never the install loop.

`render` recomputes the projections; `record` measures what this host was given once everything
else has landed. A record taken in the middle of the writes would be a reading of a half-installed
host, stating a moment that described nothing.
"""

from __future__ import annotations

from installmodes import Mode

MODES = {
    "projection": Mode("render"),
    "estate": Mode("record"),
}
