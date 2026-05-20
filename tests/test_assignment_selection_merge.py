"""Tests extracted from Propstore for pure assignment-selection merge behavior.

Source: C:/Users/Q/code/propstore/tests/test_assignment_selection_merge.py
"""

from __future__ import annotations

from itertools import product

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from assignment_selection import (
    Assignment,
    Constraint,
    MergeOperator,
    Problem,
    SourceAssignment,
    solve,
)
from assignment_selection.solver import (
    assignment_distance,
    assignment_satisfies,
    claim_distance,
    enumerate_candidate_assignments,
)


st_claim_value = st.floats(
    min_value=-1000,
    max_value=1000,
    allow_nan=False,
    allow_infinity=False,
)
st_branch_profile = st.dictionaries(
    keys=st.from_regex(r"branch_[a-z]{1,5}", fullmatch=True),
    values=st_claim_value,
    min_size=2,
    max_size=5,
)
st_small_assignment_value = st.integers(min_value=0, max_value=2)


def _value(assignment: Assignment, concept_id: str) -> object:
    return assignment.values[concept_id]


def _unique_values(profile: dict[str, object]) -> list[object]:
    result: list[object] = []
    for value in profile.values():
        if not any(existing == value for existing in result):
            result.append(value)
    return result


def _sigma_merge(profile: dict[str, object]) -> object:
    candidates = list(profile.values())
    best_value = None
    best_score = float("inf")
    for candidate in candidates:
        score = sum(claim_distance(candidate, value) for value in candidates)
        if score < best_score:
            best_score = score
            best_value = candidate
        elif score == best_score and best_value is not None:
            try:
                if float(candidate) < float(best_value):
                    best_value = candidate
            except (ValueError, TypeError):
                if str(candidate) < str(best_value):
                    best_value = candidate
    return best_value


def _max_merge(profile: dict[str, object]) -> object:
    unique = _unique_values(profile)
    best_value = None
    best_score = float("inf")
    for candidate in unique:
        score = max(claim_distance(candidate, value) for value in unique)
        if score < best_score:
            best_score = score
            best_value = candidate
        elif score == best_score and best_value is not None:
            try:
                if float(candidate) < float(best_value):
                    best_value = candidate
            except (ValueError, TypeError):
                if str(candidate) < str(best_value):
                    best_value = candidate
    return best_value


def _gmax_merge(profile: dict[str, object]) -> object:
    unique = _unique_values(profile)
    best_value = None
    best_vector: list[float] | None = None
    for candidate in unique:
        distances = sorted(
            [claim_distance(candidate, value) for value in unique],
            reverse=True,
        )
        if best_vector is None or distances < best_vector:
            best_vector = distances
            best_value = candidate
        elif distances == best_vector and best_value is not None:
            try:
                if float(candidate) < float(best_value):
                    best_value = candidate
            except (ValueError, TypeError):
                if str(candidate) < str(best_value):
                    best_value = candidate
    return best_value


def _scalar_assignment_selection_merge(
    profile: dict[str, object],
    *,
    operator: MergeOperator | str = MergeOperator.SIGMA,
) -> object:
    dispatch = {
        MergeOperator.SIGMA: _sigma_merge,
        MergeOperator.MAX: _max_merge,
        MergeOperator.GMAX: _gmax_merge,
        "sigma": _sigma_merge,
        "max": _max_merge,
        "gmax": _gmax_merge,
    }
    return dispatch[operator](profile)


def _scalar_profile_problem(
    profile: dict[str, object],
    *,
    operator: MergeOperator | str = MergeOperator.SIGMA,
    constraints: tuple[Constraint, ...] = (),
    concept_id: str = "__value__",
) -> Problem:
    return Problem(
        concept_ids=(concept_id,),
        sources=tuple(
            SourceAssignment(
                source_id=str(source_id),
                assignment=Assignment(values={concept_id: value}),
            )
            for source_id, value in profile.items()
        ),
        constraints=constraints,
        operator=MergeOperator(operator),
    )


def _range_constraint(concept_id: str, lower: object | None, upper: object | None) -> Constraint:
    def _holds(assignment: Assignment) -> bool:
        value = assignment.values[concept_id]
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return False
        if lower is not None and numeric < float(lower):
            return False
        if upper is not None and numeric > float(upper):
            return False
        return True

    return Constraint(concept_ids=(concept_id,), holds=_holds, description="range")


def _category_constraint(concept_id: str, allowed_values: tuple[object, ...]) -> Constraint:
    return Constraint(
        concept_ids=(concept_id,),
        holds=lambda assignment: assignment.values[concept_id] in allowed_values,
        description="category",
    )


class TestMergeOperatorEnum:
    def test_merge_operator_enum(self) -> None:
        assert MergeOperator.SIGMA == "sigma"
        assert MergeOperator.MAX == "max"
        assert MergeOperator.GMAX == "gmax"


class TestClaimDistance:
    def test_claim_distance_numeric(self) -> None:
        assert claim_distance(3.0, 5.0) == 2.0
        assert claim_distance(5.0, 3.0) == 2.0

    def test_claim_distance_identical(self) -> None:
        assert claim_distance(7.0, 7.0) == 0.0

    def test_claim_distance_categorical(self) -> None:
        assert claim_distance("alpha", "alpha") == 0.0
        assert claim_distance("alpha", "beta") == 1.0

    @pytest.mark.property
    @given(st_claim_value, st_claim_value)
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_distance_symmetric(self, a: float, b: float) -> None:
        assert claim_distance(a, b) == claim_distance(b, a)

    @pytest.mark.property
    @given(st_claim_value)
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_distance_zero_self(self, a: float) -> None:
        assert claim_distance(a, a) == 0.0


class TestAssignmentSelectionSolver:
    @pytest.mark.parametrize("bad_value", [float("nan"), float("inf"), float("-inf")])
    def test_solve_rejects_non_finite_numeric_claim_values(self, bad_value: float) -> None:
        problem = _scalar_profile_problem(
            {"b1": bad_value, "b2": 1.0},
            operator=MergeOperator.SIGMA,
        )

        with pytest.raises(ValueError, match="non-finite"):
            solve(problem)

    def test_enumerates_observed_candidate_assignments(self) -> None:
        problem = Problem(
            concept_ids=("x", "y"),
            sources=(
                SourceAssignment("s1", Assignment({"x": 0, "y": "a"})),
                SourceAssignment("s2", Assignment({"x": 1, "y": "b"})),
            ),
        )

        assert enumerate_candidate_assignments(problem) == (
            Assignment({"x": 0, "y": "a"}),
            Assignment({"x": 0, "y": "b"}),
            Assignment({"x": 1, "y": "a"}),
            Assignment({"x": 1, "y": "b"}),
        )

    def test_assignment_distance_sums_concept_distances(self) -> None:
        assignment = Assignment({"x": 1.0, "y": "hot"})
        source = SourceAssignment("s1", Assignment({"x": 4.0, "y": "cold"}))

        assert assignment_distance(assignment, source) == 4.0

    def test_sigma_majority_wins(self) -> None:
        profile = {"b1": 10.0, "b2": 10.0, "b3": 10.0, "b4": 99.0}

        result = solve(_scalar_profile_problem(profile, operator=MergeOperator.SIGMA))

        assert _value(result.winners[0], "__value__") == 10.0

    def test_max_minimizes_worst_case(self) -> None:
        profile = {"b1": 0.0, "b2": 10.0, "b3": 100.0}

        result = solve(_scalar_profile_problem(profile, operator=MergeOperator.MAX))

        assert _value(result.winners[0], "__value__") == 10.0

    def test_gmax_refines_max(self) -> None:
        profile = {"b1": 0.0, "b2": 10.0, "b3": 5.0}

        result = solve(_scalar_profile_problem(profile, operator=MergeOperator.GMAX))

        assert _value(result.winners[0], "__value__") == _gmax_merge(profile)

    def test_tiebreak_is_deterministic(self) -> None:
        profile = {"b1": 0.0, "b2": 2.0}

        result = solve(_scalar_profile_problem(profile, operator=MergeOperator.SIGMA))

        assert tuple(_value(winner, "__value__") for winner in result.winners) == (0.0, 2.0)
        assert _value(result.scored_candidates[0].assignment, "__value__") == 0.0

    def test_no_admissible_assignment_reports_reason(self) -> None:
        problem = _scalar_profile_problem(
            {"b1": 1.0, "b2": 2.0},
            constraints=(
                Constraint(
                    concept_ids=("__value__",),
                    holds=lambda assignment: False,
                    description="unsatisfiable",
                ),
            ),
        )

        result = solve(problem)

        assert result.winners == tuple()
        assert result.admissible_count == 0
        assert result.reason == "no admissible assignments"

    def test_cross_concept_runtime_constraint_changes_winner_set(self) -> None:
        problem = Problem(
            concept_ids=("x", "y"),
            sources=(
                SourceAssignment("s1", Assignment({"x": 0.0, "y": 0.0})),
                SourceAssignment("s2", Assignment({"x": 0.0, "y": 1.0})),
                SourceAssignment("s3", Assignment({"x": 1.0, "y": 0.0})),
            ),
            constraints=(
                Constraint(
                    concept_ids=("x", "y"),
                    holds=lambda assignment: assignment.values["x"] + assignment.values["y"] == 1.0,
                    description="x and y must sum to exactly 1",
                ),
            ),
            operator=MergeOperator.SIGMA,
        )

        result = solve(problem)

        assert result.winners == (
            Assignment({"x": 0.0, "y": 1.0}),
            Assignment({"x": 1.0, "y": 0.0}),
        )

    def test_custom_constraint_is_scoped_to_declared_concepts(self) -> None:
        problem = Problem(
            concept_ids=("x", "y", "z"),
            sources=(
                SourceAssignment("s1", Assignment({"x": 0, "y": 0, "z": 0})),
                SourceAssignment("s2", Assignment({"x": 1, "y": 1, "z": 1})),
            ),
            constraints=(
                Constraint(
                    concept_ids=("x", "y"),
                    holds=lambda assignment: set(assignment.values) == {"x", "y"},
                ),
            ),
            operator=MergeOperator.SIGMA,
        )

        result = solve(problem)

        assert result.winners
        assert result.admissible_count == 8

    def test_range_constraint_filters_admissible_winners(self) -> None:
        problem = _scalar_profile_problem(
            {"b1": 5.0, "b2": 10.0, "b3": 50.0},
            operator=MergeOperator.SIGMA,
            constraints=(_range_constraint("__value__", 0.0, 20.0),),
        )

        result = solve(problem)

        assert [winner.values["__value__"] for winner in result.winners] == [10.0]
        assert result.admissible_count == 2

    def test_category_constraint_rejects_non_member_values(self) -> None:
        problem = _scalar_profile_problem(
            {"b1": "speech", "b2": "whisper", "b3": "song"},
            operator=MergeOperator.MAX,
            constraints=(_category_constraint("__value__", ("speech", "whisper")),),
        )

        result = solve(problem)

        assert result.winners
        assert all(winner.values["__value__"] in {"speech", "whisper"} for winner in result.winners)
        assert result.admissible_count == 2

    def test_problem_rejects_source_assignment_outside_declared_concepts(self) -> None:
        with pytest.raises(ValueError, match="unknown concept ids"):
            Problem(
                concept_ids=("x", "y"),
                sources=(SourceAssignment("s1", Assignment({"x": 0.0, "z": 1.0})),),
            )

    def test_problem_rejects_duplicate_concept_ids(self) -> None:
        with pytest.raises(ValueError, match="duplicate concept ids"):
            Problem(
                concept_ids=("x", "x"),
                sources=(SourceAssignment("s1", Assignment({"x": 0.0})),),
            )

    @pytest.mark.property
    @given(st_branch_profile, st.sampled_from(list(MergeOperator)))
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_unconstrained_single_concept_matches_scalar_dispatch(
        self,
        profile: dict[str, float],
        operator: MergeOperator,
    ) -> None:
        result = solve(_scalar_profile_problem(profile, operator=operator))

        assert result.scored_candidates
        assert result.scored_candidates[0].assignment.values["__value__"] == _scalar_assignment_selection_merge(
            profile,
            operator=operator,
        )

    @pytest.mark.property
    @given(st_branch_profile)
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_winners_always_satisfy_range_constraint(self, profile: dict[str, float]) -> None:
        ordered_values = sorted(profile.values())
        upper = ordered_values[len(ordered_values) // 2]
        constraint = _range_constraint("__value__", ordered_values[0], upper)
        problem = _scalar_profile_problem(
            profile,
            operator=MergeOperator.SIGMA,
            constraints=(constraint,),
        )

        result = solve(problem)

        assert result.winners
        assert all(assignment_satisfies(problem, winner) for winner in result.winners)

    @pytest.mark.property
    @given(st_branch_profile, st.sampled_from(list(MergeOperator)))
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_source_renaming_does_not_change_best_assignment(
        self,
        profile: dict[str, float],
        operator: MergeOperator,
    ) -> None:
        renamed = {f"renamed_{index}": value for index, value in enumerate(profile.values())}

        original = solve(_scalar_profile_problem(profile, operator=operator))
        renamed_result = solve(_scalar_profile_problem(renamed, operator=operator))

        assert original.scored_candidates
        assert renamed_result.scored_candidates
        assert (
            original.scored_candidates[0].assignment.values["__value__"]
            == renamed_result.scored_candidates[0].assignment.values["__value__"]
        )

    @pytest.mark.property
    @given(
        st.lists(
            st.tuples(st_small_assignment_value, st_small_assignment_value),
            min_size=2,
            max_size=5,
        ),
        st.sampled_from(list(MergeOperator)),
    )
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_multiconcept_source_order_does_not_change_winners(
        self,
        source_pairs: list[tuple[int, int]],
        operator: MergeOperator,
    ) -> None:
        forward = Problem(
            concept_ids=("x", "y"),
            sources=tuple(
                SourceAssignment(f"s{index}", Assignment({"x": x, "y": y}))
                for index, (x, y) in enumerate(source_pairs)
            ),
            operator=operator,
        )
        reversed_problem = Problem(
            concept_ids=("x", "y"),
            sources=tuple(
                SourceAssignment(f"r{index}", Assignment({"x": x, "y": y}))
                for index, (x, y) in enumerate(reversed(source_pairs))
            ),
            operator=operator,
        )

        forward_result = solve(forward)
        reversed_result = solve(reversed_problem)

        assert forward_result.winners == reversed_result.winners
        assert [
            (dict(item.assignment.values), item.score)
            for item in forward_result.scored_candidates
        ] == [
            (dict(item.assignment.values), item.score)
            for item in reversed_result.scored_candidates
        ]

    @pytest.mark.property
    @given(
        st.lists(
            st.tuples(st.integers(min_value=0, max_value=2), st.integers(min_value=0, max_value=2)),
            min_size=2,
            max_size=5,
        ),
        st.integers(min_value=0, max_value=4),
        st.sampled_from(list(MergeOperator)),
    )
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_cross_concept_winners_always_satisfy_runtime_constraint(
        self,
        source_pairs: list[tuple[int, int]],
        max_sum: int,
        operator: MergeOperator,
    ) -> None:
        x_values = {x for x, _ in source_pairs}
        y_values = {y for _, y in source_pairs}
        assume(any(x + y <= max_sum for x, y in product(x_values, y_values)))

        problem = Problem(
            concept_ids=("x", "y"),
            sources=tuple(
                SourceAssignment(f"s{index}", Assignment({"x": x, "y": y}))
                for index, (x, y) in enumerate(source_pairs)
            ),
            constraints=(
                Constraint(
                    concept_ids=("x", "y"),
                    holds=lambda assignment, limit=max_sum: assignment.values["x"] + assignment.values["y"] <= limit,
                    description="sum-bounded cross-concept admissibility",
                ),
            ),
            operator=operator,
        )

        result = solve(problem)

        assert result.winners
        assert all(assignment_satisfies(problem, winner) for winner in result.winners)

    @pytest.mark.property
    @given(st_branch_profile, st.sampled_from(list(MergeOperator)))
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_renaming_concept_ids_preserves_winner_values(
        self,
        profile: dict[str, float],
        operator: MergeOperator,
    ) -> None:
        original = solve(_scalar_profile_problem(profile, operator=operator, concept_id="x"))
        renamed = solve(_scalar_profile_problem(profile, operator=operator, concept_id="renamed_x"))

        assert [winner.values["x"] for winner in original.winners] == [
            winner.values["renamed_x"] for winner in renamed.winners
        ]
