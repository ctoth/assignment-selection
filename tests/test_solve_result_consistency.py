"""Tests pinning solve() result-reporting consistency.

solve() must report outcomes consistently as a Result with an accurate
reason rather than raising or returning a misleading reason:

1. Ceiling breach -> Result with an explicit "exceeded ceiling" reason
   (anytime design: never raise).
2. Empty enumeration (nothing was enumerated at all) -> a reason that
   says so, not the no-admissible reason.
3. Genuine no-admissible (candidates exist, all filtered out) -> the
   "no admissible assignments" reason, unchanged.
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from assignment_selection import (
    Assignment,
    Constraint,
    Problem,
    Result,
    SourceAssignment,
    solve,
)


def test_solve_returns_result_on_ceiling() -> None:
    # 5 sources of distinct values over concepts ("x", "y") -> 25 candidates,
    # which exceeds a ceiling of 10.
    problem = Problem(
        concept_ids=("x", "y"),
        sources=tuple(
            SourceAssignment(
                source_id=f"s{i}",
                assignment=Assignment(values={"x": f"x{i}", "y": f"y{i}"}),
            )
            for i in range(5)
        ),
    )

    result = solve(problem, max_candidates=10)

    assert isinstance(result, Result)
    assert result.winners == ()
    assert result.admissible_count == 0
    assert result.reason == "candidate enumeration exceeded ceiling of 10"


def test_solve_empty_enumeration_reason_is_accurate() -> None:
    # Concept "y" is declared but no source observes it: nothing can be
    # enumerated at all. The source references only declared concepts, so
    # the Problem is valid.
    problem = Problem(
        concept_ids=("x", "y"),
        sources=(SourceAssignment("s1", Assignment({"x": 1.0})),),
    )

    result = solve(problem)

    assert result.winners == ()
    assert result.reason == "no candidate assignments to enumerate"


def test_no_admissible_reason_unchanged() -> None:
    # Candidates exist but a constraint that always returns False filters
    # every one of them out.
    problem = Problem(
        concept_ids=("x",),
        sources=(
            SourceAssignment("s1", Assignment({"x": 1.0})),
            SourceAssignment("s2", Assignment({"x": 2.0})),
        ),
        constraints=(
            Constraint(concept_ids=("x",), holds=lambda _assignment: False),
        ),
    )

    result = solve(problem)

    assert result.winners == ()
    assert result.reason == "no admissible assignments"


_st_concept_value = st.integers(min_value=-50, max_value=50)
_st_profile = st.lists(_st_concept_value, min_size=0, max_size=6)


@pytest.mark.property
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(
    profile=_st_profile,
    max_candidates=st.integers(min_value=0, max_value=8),
)
def test_solve_never_raises(profile: list[int], max_candidates: int) -> None:
    problem = Problem(
        concept_ids=("__value__",),
        sources=tuple(
            SourceAssignment(
                source_id=f"s{index}",
                assignment=Assignment(values={"__value__": value}),
            )
            for index, value in enumerate(profile)
        ),
    )

    result = solve(problem, max_candidates=max_candidates)

    assert isinstance(result, Result)
