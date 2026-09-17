# Instructions for `tests/acceptance/fresh-repo/` and everything below it

> **Generated. Do not edit.** Served to the runtime `claude-code` at the path its surface
> `claude-code` reads for a directory, and rebuilt from scratch on every render · kit 0.1.6.
> These laws bind ONLY inside `tests/acceptance/fresh-repo/`; the repository-wide instructions still apply here.
> Declared once, by the scope `fresh-repo-suite` in this host's law-scope declaration -- that
> declaration and the page it names are where a change is made. An edit here is refused by the
> next render and reported by `check` under `FF-KIT-PROJECTION`.

The kit's acceptance suite: how a test may know the kit, and what it may never name, bind here and nowhere else.

## Scoped laws -- binding in this directory and below it

# Laws of `tests/acceptance/fresh-repo/` -- binding here and below

> Host-authored. Every law below restates, in words, what this suite already DECLARES about
> itself; the declaration named beside each law is its home. Amend the declaration first; this
> page follows it.

1. **A test keeps no copy of the kit's vocabulary.** Every path, field, surface, view and code a
   test uses is READ from the declaration or the module that owns it -- a capability, a schema,
   `kit/diagnostics.json`, an error class's `code`. A suite that spells its own copy goes on
   passing after the interpreter has moved.
   *Declared in `harness.py` and the docstring of every acceptance module.*
2. **No named subject in a test.** No runtime product, stack, role or host instance is named in
   a test's own assertions; a product appears only where an adapter declares it and is reached
   through that declaration.
   *Declared by ADR-001 point 2 (T1, the name test).*
3. **The boundary's rules are read, never restated.** `boundary.json` holds them, and each rule
   carries the specimen it must flag and the lookalike it must admit, so the sensor is measured
   before the tree is. A new rule is a row there, not a test here.
   *Declared in `boundary.json` and `test_boundary.py`.*
4. **The harness asserts nothing.** It measures the host or parses what the kit said; judgement
   lives in the suites.
   *Declared in `harness.py`.*

