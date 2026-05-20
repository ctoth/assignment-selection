from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Any, overload

from assignment_selection.model import (
    Assignment,
    CandidateScore,
    Constraint,
    MergeOperator,
    Problem,
    Result,
    SourceAssignment,
)


@dataclass(frozen=True)
class EnumerationExceeded:
    partial_count: int
    max_candidates: int


def claim_distance(a: Any, b: Any) -> float:
    """Distance between two claim values."""
    try:
        return abs(float(a) - float(b))
    except (ValueError, TypeError):
        return 0.0 if a == b else 1.0


def _unique_sources(
    sources: tuple[SourceAssignment, ...],
) -> tuple[SourceAssignment, ...]:
    result: list[SourceAssignment] = []
    for source in sources:
        if not any(
            existing.assignment.values == source.assignment.values
            and existing.weight == source.weight
            for existing in result
        ):
            result.append(source)
    return tuple(result)


def _assignment_tiebreak_key(
    assignment: Assignment,
    concept_ids: tuple[str, ...],
) -> tuple[tuple[int, float | str], ...]:
    key: list[tuple[int, float | str]] = []
    for concept_id in concept_ids:
        value: Any = assignment.value_for(concept_id)
        try:
            key.append((0, float(value)))
        except (TypeError, ValueError):
            key.append((1, repr(value)))
    return tuple(key)


def _score_sort_key(score: float | tuple[float, ...]) -> tuple[float, ...]:
    if isinstance(score, tuple):
        return score
    return (score,)


@overload
def enumerate_candidate_assignments(problem: Problem) -> tuple[Assignment, ...]: ...


@overload
def enumerate_candidate_assignments(
    problem: Problem,
    *,
    max_candidates: None,
) -> tuple[Assignment, ...]: ...


@overload
def enumerate_candidate_assignments(
    problem: Problem,
    *,
    max_candidates: int,
) -> tuple[Assignment, ...] | EnumerationExceeded: ...


def enumerate_candidate_assignments(
    problem: Problem,
    *,
    max_candidates: int | None = None,
) -> tuple[Assignment, ...] | EnumerationExceeded:
    """Enumerate observed assignments with an anytime candidate ceiling."""

    if max_candidates is not None and max_candidates < 0:
        raise ValueError("max_candidates must be non-negative")

    domains: list[list[object]] = []
    for concept_id in problem.concept_ids:
        values: list[object] = []
        for source in problem.sources:
            if concept_id in source.assignment.values and not any(
                existing == source.assignment.value_for(concept_id)
                for existing in values
            ):
                values.append(source.assignment.value_for(concept_id))
        if not values:
            return tuple()
        domains.append(values)

    result: list[Assignment] = []
    for choice in product(*domains):
        if max_candidates is not None and len(result) >= max_candidates:
            return EnumerationExceeded(
                partial_count=len(result),
                max_candidates=max_candidates,
            )
        assignment = Assignment(
            values={
                concept_id: value
                for concept_id, value in zip(problem.concept_ids, choice, strict=True)
            }
        )
        if not any(existing.values == assignment.values for existing in result):
            result.append(assignment)
    return tuple(result)


def assignment_distance(assignment: Assignment, source: SourceAssignment) -> float:
    """Distance between a candidate assignment and one source assignment."""
    distance = 0.0
    for concept_id, value in assignment.values.items():
        if concept_id not in source.assignment.values:
            continue
        distance += claim_distance(value, source.assignment.value_for(concept_id))
    return distance


def _constraint_scope_assignment(
    assignment: Assignment,
    constraint: Constraint,
) -> Assignment:
    return Assignment(
        {
            concept_id: assignment.value_for(concept_id)
            for concept_id in constraint.concept_ids
        }
    )


def _constraint_holds(assignment: Assignment, constraint: Constraint) -> bool:
    return bool(constraint.holds(_constraint_scope_assignment(assignment, constraint)))


def assignment_satisfies(problem: Problem, assignment: Assignment) -> bool:
    """Whether an assignment satisfies every runtime constraint in the problem."""
    return all(_constraint_holds(assignment, constraint) for constraint in problem.constraints)


def _score_assignment(
    problem: Problem,
    assignment: Assignment,
) -> float | tuple[float, ...]:
    operator = MergeOperator(problem.operator)
    if operator == MergeOperator.SIGMA:
        return sum(
            source.weight * assignment_distance(assignment, source)
            for source in problem.sources
        )

    scored_sources = (
        _unique_sources(problem.sources)
        if operator in (MergeOperator.MAX, MergeOperator.GMAX)
        else problem.sources
    )
    distances = tuple(
        source.weight * assignment_distance(assignment, source)
        for source in scored_sources
    )
    if operator == MergeOperator.MAX:
        return max(distances, default=0.0)
    if operator == MergeOperator.GMAX:
        return tuple(sorted(distances, reverse=True))
    raise ValueError(f"Unknown merge operator: {problem.operator}")


def solve(problem: Problem) -> Result:
    """Solve one assignment-level assignment-selection merge problem."""
    candidates = enumerate_candidate_assignments(problem)
    if isinstance(candidates, EnumerationExceeded):
        raise RuntimeError("candidate enumeration exceeded during solve")

    admissible = tuple(
        candidate
        for candidate in candidates
        if all(_constraint_holds(candidate, constraint) for constraint in problem.constraints)
    )
    if not admissible:
        return Result(
            winners=tuple(),
            scored_candidates=tuple(),
            admissible_count=0,
            total_candidate_count=len(candidates),
            reason="no admissible assignments",
        )

    scored = sorted(
        (
            CandidateScore(
                assignment=assignment,
                score=_score_assignment(problem, assignment),
            )
            for assignment in admissible
        ),
        key=lambda item: (
            _score_sort_key(item.score),
            _assignment_tiebreak_key(item.assignment, problem.concept_ids),
        ),
    )
    best_score = scored[0].score
    winners = tuple(item.assignment for item in scored if item.score == best_score)
    return Result(
        winners=winners,
        scored_candidates=tuple(scored),
        admissible_count=len(admissible),
        total_candidate_count=len(candidates),
    )
