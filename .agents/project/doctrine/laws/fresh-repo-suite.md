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
