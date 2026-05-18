"""Assignment-selection merge models and algorithms."""

from assignment_selection.model import (
    Assignment,
    CandidateScore,
    Constraint,
    MergeOperator,
    Problem,
    Result,
    SourceAssignment,
)
from assignment_selection.solver import solve

__all__ = [
    "Assignment",
    "CandidateScore",
    "Constraint",
    "MergeOperator",
    "Problem",
    "Result",
    "SourceAssignment",
    "solve",
]
