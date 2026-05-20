"""Property tests pinning ``solve`` / ``Result`` invariants.

Each strategy builds ``Problem``s with no constraints, so enumeration always
yields a non-empty admissible set: every generated problem produces a
non-empty ``Result``. Source weights are finite and non-negative, as required
by ``SourceAssignment``.
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from assignment_selection import (
    Assignment,
    MergeOperator,
    Problem,
    Result,
    SourceAssignment,
    solve,
)
from assignment_selection.solver import assignment_satisfies

st_concept_value = st.integers(min_value=-50, max_value=50)
st_weight = st.floats(
    min_value=0.0,
    max_value=100.0,
    allow_nan=False,
    allow_infinity=False,
)
st_positive_scale = st.floats(
    min_value=1e-3,
    max_value=1e3,
    allow_nan=False,
    allow_infinity=False,
)
st_operator = st.sampled_from(list(MergeOperator))


@st.composite
def st_source_rows(
    draw: st.DrawFn,
    concept_ids: tuple[str, ...],
) -> list[tuple[dict[str, int], float]]:
    """Draw a non-empty list of (value-mapping, weight) rows for the concepts."""
    rows: list[tuple[dict[str, int], float]] = draw(
        st.lists(
            st.tuples(
                st.fixed_dictionaries(
                    {cid: st_concept_value for cid in concept_ids}
                ),
                st_weight,
            ),
            min_size=1,
            max_size=5,
        )
    )
    return rows


def _build_problem(
    concept_ids: tuple[str, ...],
    rows: list[tuple[dict[str, int], float]],
    operator: MergeOperator,
    *,
    weight_scale: float = 1.0,
) -> Problem:
    return Problem(
        concept_ids=concept_ids,
        sources=tuple(
            SourceAssignment(
                source_id=f"s{index}",
                assignment=Assignment(values=dict(values)),
                weight=weight * weight_scale,
            )
            for index, (values, weight) in enumerate(rows)
        ),
        operator=operator,
    )


@st.composite
def st_problem(draw: st.DrawFn) -> Problem:
    """A single- or multi-concept, unconstrained ``Problem``."""
    concept_ids = draw(st.sampled_from([("a",), ("a", "b")]))
    rows = draw(st_source_rows(concept_ids))
    operator = draw(st_operator)
    return _build_problem(concept_ids, rows, operator)


def _score_tuple(score: float | tuple[float, ...]) -> tuple[float, ...]:
    if isinstance(score, tuple):
        return score
    return (score,)


@pytest.mark.property
@given(st_problem())
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_solve_is_idempotent(problem: Problem) -> None:
    first = solve(problem)
    second = solve(problem)
    assert first == second


@pytest.mark.property
@given(st_problem())
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_result_counts_are_consistent(problem: Problem) -> None:
    result: Result = solve(problem)
    assert result.admissible_count <= result.total_candidate_count
    assert len(result.winners) <= result.admissible_count
    if result.winners:
        assert len(result.scored_candidates) == result.admissible_count


@pytest.mark.property
@given(st_problem())
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_scored_candidates_are_sorted(problem: Problem) -> None:
    result = solve(problem)
    scores = [_score_tuple(item.score) for item in result.scored_candidates]
    assert scores == sorted(scores)


@pytest.mark.property
@given(st_problem())
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_winners_are_best_and_admissible(problem: Problem) -> None:
    result = solve(problem)
    assert result.winners
    best_score = result.scored_candidates[0].score
    scored_by_assignment = {
        item.assignment: item.score for item in result.scored_candidates
    }
    for winner in result.winners:
        assert winner in scored_by_assignment
        assert scored_by_assignment[winner] == best_score
        assert assignment_satisfies(problem, winner)


@pytest.mark.property
@given(st.data())
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_uniform_weight_scaling_preserves_winners(data: st.DataObject) -> None:
    concept_ids = data.draw(st.sampled_from([("a",), ("a", "b")]))
    rows = data.draw(st_source_rows(concept_ids))
    operator = data.draw(st_operator)
    k = data.draw(st_positive_scale)

    base = _build_problem(concept_ids, rows, operator)
    scaled = _build_problem(concept_ids, rows, operator, weight_scale=k)

    assert solve(base).winners == solve(scaled).winners
