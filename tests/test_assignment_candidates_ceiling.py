"""Candidate-enumeration ceiling test extracted from Propstore.

Source:
C:/Users/Q/code/propstore/tests/remediation/phase_8_dos_anytime/test_T8_1_assignment_candidates_ceiling.py
"""

from __future__ import annotations

import pytest

from assignment_selection import Assignment, Problem, SourceAssignment
from assignment_selection.solver import EnumerationExceeded, enumerate_candidate_assignments, solve


def test_enumerate_candidate_assignments_returns_enumeration_exceeded_past_ceiling() -> None:
    problem = Problem(
        concept_ids=("x", "y"),
        sources=tuple(
            SourceAssignment(
                source_id=f"s{i}",
                assignment=Assignment(values={"x": f"x{i}", "y": f"y{i}"}),
            )
            for i in range(33)
        ),
    )

    result = enumerate_candidate_assignments(problem, max_candidates=1_000)

    assert isinstance(result, EnumerationExceeded)
    assert result.partial_count == 1_000
    assert result.max_candidates == 1_000


def test_solve_enforces_candidate_ceiling() -> None:
    problem = Problem(
        concept_ids=("x", "y"),
        sources=tuple(
            SourceAssignment(
                source_id=f"s{i}",
                assignment=Assignment(values={"x": f"x{i}", "y": f"y{i}"}),
            )
            for i in range(33)
        ),
    )

    with pytest.raises(RuntimeError, match="candidate enumeration exceeded"):
        solve(problem, max_candidates=1_000)
