from __future__ import annotations

import pytest

from assignment_selection import Assignment, Problem, SourceAssignment, solve
from assignment_selection.solver import claim_distance


@pytest.mark.parametrize(
    "left,right",
    [
        (2**53, 2**53 + 1),
        (2**63 - 2, 2**63 - 1),
        (-(2**53), -(2**53) - 1),
        (-(2**63), -(2**63) + 1),
    ],
)
def test_adjacent_large_integers_have_unit_distance(left: int, right: int) -> None:
    assert claim_distance(left, right) == 1.0
    assert claim_distance(right, left) == 1.0


@pytest.mark.parametrize("majority", [2**53, -(2**63)])
def test_sigma_selects_the_majority_of_adjacent_large_integers(majority: int) -> None:
    minority = majority + 1
    sources = tuple(
        SourceAssignment(str(index), Assignment({"x": value}))
        for index, value in enumerate((majority, majority, minority))
    )

    result = solve(Problem(("x",), sources))

    assert tuple(winner.value_for("x") for winner in result.winners) == (majority,)
    assert tuple(
        (candidate.assignment.value_for("x"), candidate.score)
        for candidate in result.scored_candidates
    ) == ((majority, 1.0), (minority, 2.0))
