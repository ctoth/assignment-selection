"""Tests pinning SourceAssignment.weight validation.

A non-finite (nan, inf, -inf) or negative weight silently corrupts merge
results, so constructing such a SourceAssignment must raise ValueError.
weight == 0.0 and positive finite weights remain valid.
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from assignment_selection import (
    Assignment,
    MergeOperator,
    Problem,
    SourceAssignment,
    solve,
)


def _assignment() -> Assignment:
    return Assignment(values={"__value__": 1.0})


@pytest.mark.unit
@pytest.mark.parametrize(
    "weight",
    [float("nan"), float("inf"), float("-inf"), -1.0, -0.001],
)
def test_source_assignment_rejects_invalid_weight(weight: float) -> None:
    with pytest.raises(ValueError):
        SourceAssignment(
            source_id="s1",
            assignment=_assignment(),
            weight=weight,
        )


@pytest.mark.unit
def test_source_assignment_accepts_zero_weight() -> None:
    source = SourceAssignment(
        source_id="s1",
        assignment=_assignment(),
        weight=0.0,
    )

    assert source.weight == 0.0


@pytest.mark.unit
def test_source_assignment_accepts_positive_finite_weight() -> None:
    source = SourceAssignment(
        source_id="s1",
        assignment=_assignment(),
        weight=2.5,
    )

    assert source.weight == 2.5


st_concept_value = st.integers(min_value=-1000, max_value=1000)
st_source_weight = st.floats(
    min_value=0.0,
    max_value=1000.0,
    allow_nan=False,
    allow_infinity=False,
)
st_weighted_profile = st.lists(
    st.tuples(st_concept_value, st_source_weight),
    min_size=2,
    max_size=5,
)


@pytest.mark.property
@given(st_weighted_profile, st.sampled_from(list(MergeOperator)))
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_admissible_implies_winners(
    profile: list[tuple[int, float]],
    operator: MergeOperator,
) -> None:
    problem = Problem(
        concept_ids=("__value__",),
        sources=tuple(
            SourceAssignment(
                source_id=f"s{index}",
                assignment=Assignment(values={"__value__": value}),
                weight=weight,
            )
            for index, (value, weight) in enumerate(profile)
        ),
        operator=operator,
    )

    result = solve(problem)

    if result.admissible_count >= 1:
        assert result.winners
