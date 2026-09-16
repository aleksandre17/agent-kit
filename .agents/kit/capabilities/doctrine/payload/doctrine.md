# doctrine — the carrier, the grammar, and no cardinal

*Vendor. This page explains a mechanism this kit ships; it is replaced wholesale on upgrade and
says nothing about how any host should work.*

## The measure that decided this

Turn one question on a sentence of normative text:

> **Can this sentence become false without the kit changing?**

If it cannot — it could only become false if a mechanism this kit ships changed — the sentence is
**mechanism doctrine**: the meaning of something the kit owns. Its home is beside that mechanism,
version-locked to it, vendored by the capability that ships it. This page is one of those.

If it can — it is a claim about a host's conduct, and only the host can notice it is wrong — the
sentence is **conduct doctrine**: cardinals, protocol, an economy, a risk posture, an environment
chapter. **This kit ships none of it.** It ships the carrier by which a host receives some, the
grammar by which a host answers it, and the surface that states which it has.

## A bundle is an ordinary capability

There is no doctrine plane, no doctrine loader and no second installation grammar. A doctrine
bundle has an id, a semver, `requires`, `provides`, `installs` and `gates`, and the resolver that
composes it is the resolver that composes everything else. `installs` is the write permission and
doctrine gets no exemption from it.

A chapter that applies only in some environments declares `requires: [{ "kind": "fact", "id": …}]`
on a profile fact. The condition therefore lives in the declaration, where a host can read it and
a machine can generate it — never inside an interpreter, which is the one place a host cannot
reach.

A bundle owns its own subtree of the vendor plane and reads the host's answers through the
readable this capability declares. That is the whole coupling: a bundle needs no code here, and
nothing here knows the name of any bundle.

## Four artifacts, four classes

| artifact | class | why |
|---|---|---|
| a distributed cardinal or chapter | **vendor** (of its bundle) | one home, upstream; replaced wholesale; the host never edits it, so it cannot fork |
| the host's stances and its record of what it took | **binding** | the host's own authorship; no upgrade reads it for writing |
| the roll of doctrine in force, with each stance | **projection** | deleted and re-rendered; a reading of the two above, never a third copy |
| a bundle fetched and not installed | **ephemeral** | observed, never owned |

A distributed cardinal is never binding class. Binding means *host-owned after first write* —
which is precisely a fork, taken silently, and a fork can never be spoken about again.

## Amendment without forking

A host never edits a cardinal. It declares a **stance**: the address `bundle@semver#id`, one word
of the declared vocabulary — *adopts · narrows · extends · declares-a-gap · refuses* — what it
has to say in that word, a date and an author.

This is not a second home for the cardinal, because it is a different proposition. The cardinal
states what its publisher holds true; the stance states what this host does with it. Each has one
home, so there is nothing to synchronise and therefore nothing that can drift.

## Citation, not quotation

Every doctrine document is addressed `bundle@semver#id`, and everything that cites doctrine cites
the address. Two hosts on different versions then produce a delta that can be PRINTED — the ids
that moved — instead of two texts that differ in wording and cannot be compared. Old addresses
stay legible forever and are never rewritten. A withdrawn bundle orphans what was said about it
and deletes none of it.

## The zero

A host that has taken no doctrine is a **declared zero**, never a supplied default. `check` is
green; the surface says *THE DOCTRINE IN FORCE IS NONE* in those words. Under no circumstance does
this kit supply a starter cardinal set to be helpful: a default norm is an opinion installed by a
party that was never asked, and a page that simply ended would read exactly like a host whose
doctrine failed to render.
