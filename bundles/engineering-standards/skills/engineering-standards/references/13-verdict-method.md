# 13. Verdict method -- judging a design against a benchmark
A benchmark is the definition of *better*, fixed before a design is chosen; its test is whether an
independent reviewer can judge two candidates against it without inventing a criterion. Best is the
strongest justified invariants at the lowest justified complexity, with the safest evolution.
- **Gate 1 -- invariants, binary.** Each is HOLDS · VIOLATED · NOT_DEMONSTRATED. Any VIOLATED -> REJECTED;
  any NOT_DEMONSTRATED -> NOT READY. The only override is an approved, time-bounded ADR (scope, owner,
  risk, compensating control, expiry, removal task) -- an agent never approves its own override. Fail-closed, non-additive.
- **Gate 2 -- criteria, evidence-bound.** PASS · PARTIAL · FAIL · N/A (N/A needs a substantive reason). Evidence
  is bound to revision, command, environment and exit code; historical, partial, mocked or documentation-only
  evidence never raises a verdict above PARTIAL.
- **Gate 3 -- quality attributes, rated then compared.** Where candidates trade attributes, the DECISION
  HIERARCHY decides, in writing; a comparison that names no rank is a preference.
- **Decision hierarchy (generic order, a host restates it):** proven requirements > recovered intent of existing
  behaviour > explicit invariants > external obligations and contracts > domain correctness > security and
  privacy > transactional correctness > reproducibility and auditability > schema/data integrity > performance
  and bounded resources > failure and recovery > evolvability > conceptual simplicity > maintainability and
  operability > existing implementation convenience -- **last, always**.
- **Output:** CANDIDATE (revision) · INVARIANTS n/n/n · CRITERIA n/n/n/n · QUALITY ATTRIBUTES vs threshold ·
  REJECTION CRITERIA triggered · VERDICT (ACCEPTED | ACCEPTED-WITH-BOUNDED-EXCEPTIONS | NOT READY | REJECTED) ·
  UNRESOLVED questions. ACCEPTED never implies production readiness.
- **Falsify the benchmark itself:** observation -> hypothesis -> evidence -> falsification attempt -> conclusion
  -> confidence -> decision, on its riskiest claims.
