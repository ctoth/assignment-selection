# assignment-selection

Pure Python assignment-selection merge algorithms and constraint models.

The distribution name is `assignment-selection`; the import package is
`assignment_selection`. The package owns the pure assignment-selection model:
assignments, source assignments, runtime constraints, candidate scoring, and
solver results.

## What It Does

`assignment-selection` solves finite assignment-selection merge problems. A
problem declares concept ids, source assignments over those concepts, optional
runtime constraints, and a merge operator:

- `sigma`: minimize total weighted distance to the sources.
- `max`: minimize the worst weighted distance to unique source assignments.
- `gmax`: lexicographically minimize the sorted worst-distance vector.

Candidate assignments are enumerated from observed source values. Constraints
can filter admissible candidates, and the solver returns all tied winners plus
the sorted scored candidate list.

## Model

### `Assignment`

A frozen mapping of concept id to value. Values are copied into an immutable
mapping at construction. `value_for(concept_id)` returns the value or `None` if
the concept is absent.

### `SourceAssignment`

One weighted source: a `source_id`, an `assignment`, and a `weight`. The
`weight` field defaults to `1.0` and scales the distance from this source in
every operator. A weight that is non-finite (`nan`, `inf`) or negative is
rejected with `ValueError` at construction.

### `Constraint`

A runtime filter over admissible candidates:

- `concept_ids`: the tuple of concept ids the constraint ranges over. It must be
  non-empty and contain no duplicates, or construction raises `ValueError`.
- `holds`: a callable taking an `Assignment` and returning a truthy value. A
  non-callable `holds` is rejected with `TypeError`.
- `description`: an optional human-readable label (`None` by default).

When a constraint is checked, `holds` receives an `Assignment` scoped to exactly
its declared `concept_ids` — concepts outside that set are not visible to the
callable. A `Problem` also rejects constraints (and sources) that reference
concept ids not in the problem's declared `concept_ids`.

### `Problem`

`concept_ids`, `sources`, `constraints` (default empty), and `operator`
(default `MergeOperator.SIGMA`). `concept_ids` must be non-empty and
duplicate-free.

### `Result`

The value returned by `solve`:

- `winners`: the tuple of all tied-best admissible assignments. Empty when the
  problem could not be solved (see `reason`).
- `scored_candidates`: every admissible candidate paired with its score, sorted
  best-first.
- `admissible_count`: the number of candidates that passed all constraints.
- `total_candidate_count`: the number of candidates enumerated (the partial
  count when a ceiling was hit).
- `reason`: `None` on success, otherwise a string explaining the empty result.

## Example

```python
from assignment_selection import Assignment, MergeOperator, Problem, SourceAssignment, solve

problem = Problem(
    concept_ids=("truth_value",),
    sources=(
        SourceAssignment("s1", Assignment({"truth_value": 10.0})),
        SourceAssignment("s2", Assignment({"truth_value": 10.0})),
        SourceAssignment("s3", Assignment({"truth_value": 99.0})),
    ),
    operator=MergeOperator.SIGMA,
)

result = solve(problem, max_candidates=1_000)
winner = result.winners[0]

assert winner.values["truth_value"] == 10.0
assert result.reason is None
```

## Contracts

- Assignment values are copied into immutable mappings.
- `claim_distance` numerically coerces values: a value that can be turned into a
  `float` (including a numeric string) is compared as that number, so `"10"`
  and `10.0` collapse to the same point. Values that cannot be coerced fall back
  to a 0/1 categorical distance. It is therefore a metric only within a
  homogeneous value space — all-numeric or all-categorical — not across a mixed
  one.
- Non-finite numeric distances are rejected (`claim_distance` raises
  `ValueError`) instead of producing empty winner sets with successful-looking
  results.
- `solve(..., max_candidates=N)` does **not** raise when the candidate ceiling
  is breached. It returns a `Result` with empty `winners` and
  `reason="candidate enumeration exceeded ceiling of N"`. It also returns an
  empty-`winners` `Result` with `reason="no candidate assignments to
  enumerate"` when no candidates could be formed, and `reason="no admissible
  assignments"` when candidates exist but every one is filtered out by the
  constraints. On success `reason` is `None`.
- The low-level `enumerate_candidate_assignments(problem, max_candidates=N)`
  enforces the same ceiling but signals a breach differently: it returns an
  `EnumerationExceeded` object (`partial_count`, `max_candidates`) rather than a
  `Result`. `solve` translates that object into the `Result` described above.
- The package ships a `py.typed` marker for inline type consumers.

## References

The merge operators are drawn from the integrity-constraint (IC) belief-merging
literature. Konieczny & Pino-Pérez 2002, *Merging Information Under
Constraints*, is the direct theoretical basis for the `SIGMA` / `MAX` / `GMAX`
operators (Sigma majority, Max quasi-merging, GMax arbitration). See
[`papers/index.md`](papers/index.md) for the full reference collection and
notes.

## Development

```powershell
uv sync
uv run pyright
uv run pytest -vv
```
