# 14. Review protocol -- defects and opportunities, found and recorded
- **Trace the whole line** a change touches, as the host declares it (its chapter names its own chain, e.g.
  source -> adapter -> rule -> storage -> permission -> response -> view -> export -> audit -> rollback).
- **Smells to look for on the line:** implicit coupling · a rule duplicated · a hardcoded id · an unfixed
  time-zone assumption · enforcement only in the UI · an unbounded query · interpolated SQL · leaked exception
  text · a missing audit row.
- **Four axes:** structure · semantics · execution · governance. **Four views:** domain correctness · systems
  correctness · engineering quality · organisational operability.
- **Record everything found in the same session** (priority, owner, status); a review ENDS in an improvement
  record -- what was found, the invariant added, the test proving it -- never only PASS/FAIL. A case without
  answers stays DISCOVERY_REQUIRED.
