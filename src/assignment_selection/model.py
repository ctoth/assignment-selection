from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class MergeOperator(StrEnum):
    SIGMA = "sigma"
    MAX = "max"
    GMAX = "gmax"


@dataclass(frozen=True)
class Assignment:
    values: Mapping[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", dict(self.values))

    def value_for(self, concept_id: str) -> object:
        return self.values.get(concept_id)


@dataclass(frozen=True)
class SourceAssignment:
    source_id: str
    assignment: Assignment
    weight: float = 1.0


@dataclass(frozen=True)
class Constraint:
    concept_ids: tuple[str, ...]
    holds: Callable[[Assignment], bool]
    description: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "concept_ids", tuple(self.concept_ids))
        if not self.concept_ids:
            raise ValueError("Constraint requires at least one concept id")
        if len(set(self.concept_ids)) != len(self.concept_ids):
            raise ValueError("Constraint has duplicate concept ids")
        if not callable(self.holds):
            raise TypeError("Constraint.holds must be callable")


@dataclass(frozen=True)
class Problem:
    concept_ids: tuple[str, ...]
    sources: tuple[SourceAssignment, ...]
    constraints: tuple[Constraint, ...] = ()
    operator: MergeOperator = MergeOperator.SIGMA

    def __post_init__(self) -> None:
        object.__setattr__(self, "concept_ids", tuple(self.concept_ids))
        object.__setattr__(self, "sources", tuple(self.sources))
        object.__setattr__(self, "constraints", tuple(self.constraints))
        object.__setattr__(self, "operator", MergeOperator(self.operator))
        if not self.concept_ids:
            raise ValueError("Problem requires at least one concept id")
        if len(set(self.concept_ids)) != len(self.concept_ids):
            raise ValueError("Problem has duplicate concept ids")

        declared_concepts = set(self.concept_ids)
        for source in self.sources:
            unknown_concepts = tuple(
                concept_id
                for concept_id in source.assignment.values
                if concept_id not in declared_concepts
            )
            if unknown_concepts:
                joined = ", ".join(sorted(unknown_concepts))
                raise ValueError(
                    f"Problem source {source.source_id!r} references unknown concept ids: {joined}"
                )

        for constraint in self.constraints:
            unknown_concepts = tuple(
                concept_id
                for concept_id in constraint.concept_ids
                if concept_id not in declared_concepts
            )
            if unknown_concepts:
                joined = ", ".join(sorted(unknown_concepts))
                raise ValueError(
                    f"Problem constraint references unknown concept ids: {joined}"
                )


@dataclass(frozen=True)
class CandidateScore:
    assignment: Assignment
    score: float | tuple[float, ...]


@dataclass(frozen=True)
class Result:
    winners: tuple[Assignment, ...]
    scored_candidates: tuple[CandidateScore, ...]
    admissible_count: int
    total_candidate_count: int
    reason: str | None = None


JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | tuple["JsonValue", ...] | Mapping[str, Any]
