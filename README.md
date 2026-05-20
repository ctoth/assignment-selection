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
```

## Contracts

- Assignment values are copied into immutable mappings.
- Non-finite numeric distances are rejected instead of producing empty winner
  sets with successful-looking results.
- `solve(..., max_candidates=N)` enforces the same anytime candidate ceiling as
  lower-level enumeration.
- The package ships a `py.typed` marker for inline type consumers.

## Development

```powershell
uv sync
uv run pyright
uv run pytest -vv
```
