# assignment-selection review

## 2026-05-20 — initial survey

### What the project is
Pure-Python belief-merge / "assignment-selection" library extracted from propstore.
- `src/assignment_selection/model.py` — frozen dataclasses: `Assignment`, `SourceAssignment`,
  `Constraint`, `Problem`, `CandidateScore`, `Result`; `MergeOperator` StrEnum (SIGMA/MAX/GMAX).
  Also `JsonScalar`/`JsonValue` type aliases.
- `src/assignment_selection/solver.py` — `claim_distance`, `enumerate_candidate_assignments`
  (anytime ceiling, returns `EnumerationExceeded`), `assignment_distance`, `assignment_satisfies`,
  `solve`.
- tests/: 3 files. `test_assignment_selection_merge.py` carries reference scalar merge impls +
  Hypothesis property tests; `test_assignment_candidates_ceiling.py`; `test_packaging.py`.

### Baseline
- TODO: run `uv run pytest` + `uv run pyright` for clean baseline.

### Observations (verified by reading source)
- `enumerate_candidate_assignments` dedup is O(n^2) (`any(existing == ...)`), same for
  `_unique_sources`.
- `solve` RAISES `RuntimeError` on `EnumerationExceeded` — inconsistent with the anytime design
  (the enumerator returns a value; solve throws). Could return a `Result` with `reason`.
- `JsonScalar`/`JsonValue` declared in model.py, not exported in `__all__`, not used anywhere yet.
- Property tests good but gaps: `weight` rarely exercised; no Result-invariant properties
  (winners subset of scored, scored sorted, counts ordered, determinism/idempotence).

### Papers — done
Evidence for selection: propstore `docs/ic-merge.md` names Konieczny-Pino-Perez 2002
as the literature behind SIGMA/MAX/GMAX. Copied 8 full dirs into ./papers/:
7 from belief-set/papers (Konieczny_2002, Alchourron_1985, Grove_1988,
Gardenfors_1988, Hansson_1989, Booth_2006, Spohn_1988) + Coste-Marquis_2007 from
argumentation/papers. Skipped propstore/papers (204) — argumentation/provenance,
not merge theory. gitignore verified: 45 md/yaml/json tracked, all pdf/png ignored.

### Tasks
1. [done] .gitignore (+ *.pdf *.png .hypothesis/) — committed 526b184
2. [done] copy useful papers (8 dirs)
3. write papers/index.md, commit papers
4. deep review writeup (pending)
5. Hypothesis-heavy test additions (pending Q sign-off)
