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


@dataclass(frozen=True)
class Problem:
    concept_ids: tuple[str, ...]
    sources: tuple[SourceAssignment, ...]
    constraints: tuple[Constraint, ...] = ()
    operator: MergeOperator = MergeOperator.SIGMA


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
