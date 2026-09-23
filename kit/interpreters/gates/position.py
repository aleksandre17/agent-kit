"""What a bounded position artifact says about its own losses -- the reading, and a count of it.

A write-ahead eviction preserves the text it removes and states where that text landed, or states
that it landed nowhere (ADR-020 decision 2). `null` there is legal and is never refused: an
ordinary editorial cut has nowhere to land, and a gate that fired on ordinary work would be off
within a week. What it is NOT is free. Every removal that was curated nowhere is a piece of the
record that survives only in a log, and the number of them is a fact about the corpus that a host
can undertake to hold and bring down.

So this module publishes that number as a MEASURE and no verdict whatsoever. Whether the count is
too high is a ceiling; a ceiling is a number; and every number is the host's, declared as a budget
row in its own map and judged by the ratchet this kit already carries. No second ratchet is built
here, and this module names no ceiling, no artifact and no path.

It knows no KIND either, deliberately. The subject of this reading is the FIELD -- any document
that declares an unlanded count is counted, whatever it calls itself and wherever it lives -- so a
host with two bounded artifacts, or with one it has not classed yet, is measured exactly as it
stands. An interpreter that filtered by a vocabulary word would have made one kind of artifact
privileged, and the next bounded surface would have needed the framework's permission to be read.
"""

from __future__ import annotations

import corpus
import eviction


def _unlanded(ctx, params) -> "int | None":
    """How many removals this corpus preserved and curated nowhere -- the number, and nothing
    about it.

    `None`, not 0, where nothing declares the count: a host whose position artifact carries no
    counter has not got zero unlanded removals, it has an unasked question, and a measure that
    answered 0 there would report a corpus nobody looked at as a corpus that has lost nothing
    (Cardinal V). The ratchet prints that state in its own words and holds nobody to it.
    """
    reading = corpus.read(ctx, params)
    if reading.nothing_read():
        return None
    declaring = [r for r in reading.residents if r.declares(eviction.UNLANDED) is not None]
    if not declaring:
        return None
    return sum(eviction.count(r.declares(eviction.UNLANDED), r.path) for r in declaring)


#: What this module can be held to a BUDGET on (ADR-019 decision 9), published in the module that
#: owns the reading and discovered by the same registry that finds a gate kind. The name is the
#: word a host writes in its map, and it is the field's own spelling -- one word, one meaning, at
#: both ends of the boundary between a declaration and the count it caps.
MEASURES = {eviction.UNLANDED: _unlanded}
