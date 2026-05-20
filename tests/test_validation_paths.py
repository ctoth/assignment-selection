"""Unit tests for constructor guards and the enumeration ceiling."""

from __future__ import annotations

from collections.abc import Callable
from typing import cast

import pytest

from assignment_selection import (
    Assignment,
    Constraint,
    Problem,
    SourceAssignment,
)
from assignment_selection.solver import (
    EnumerationExceeded,
    enumerate_candidate_assignments,
)


def _always_true(_assignment: Assignment) -> bool:
    return True


def _non_callable_holds() -> Callable[[Assignment], bool]:
    """Return a non-callable value typed as the ``holds`` parameter.

    ``Constraint.holds`` is annotated ``Callable[[Assignment], bool]``. To
    exercise the runtime ``TypeError`` guard without scattering ``# type:
    ignore``, a plain ``object`` (here an ``int``) is ``cast`` to that type at
    a single, explicit boundary.
    """
    not_callable: object = 42
    return cast(Callable[[Assignment], bool], not_callable)


@pytest.mark.unit
def test_constraint_rejects_duplicate_concept_ids() -> None:
    with pytest.raises(ValueError):
        Constraint(concept_ids=("x", "x"), holds=_always_true)


@pytest.mark.unit
def test_constraint_rejects_empty_concept_ids() -> None:
    with pytest.raises(ValueError):
        Constraint(concept_ids=(), holds=_always_true)


@pytest.mark.unit
def test_constraint_rejects_non_callable_holds() -> None:
    with pytest.raises(TypeError):
        Constraint(concept_ids=("x",), holds=_non_callable_holds())


def _single_concept_problem() -> Problem:
    return Problem(
        concept_ids=("x",),
        sources=(
            SourceAssignment("s1", Assignment({"x": 0})),
            SourceAssignment("s2", Assignment({"x": 1})),
        ),
    )


@pytest.mark.unit
def test_enumerate_rejects_negative_max_candidates() -> None:
    with pytest.raises(ValueError):
        enumerate_candidate_assignments(_single_concept_problem(), max_candidates=-1)


@pytest.mark.unit
def test_enumerate_zero_max_candidates_returns_exceeded() -> None:
    outcome = enumerate_candidate_assignments(
        _single_concept_problem(), max_candidates=0
    )
    assert isinstance(outcome, EnumerationExceeded)
    assert outcome.partial_count == 0
    assert outcome.max_candidates == 0
