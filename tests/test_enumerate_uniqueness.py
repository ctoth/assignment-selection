"""Property test pinning the uniqueness invariant of candidate enumeration.

`enumerate_candidate_assignments` builds per-concept value domains that are
already de-duplicated, then iterates `product(*domains)` to build candidate
`Assignment`s. The Cartesian product of distinct-valued domains is itself
all-distinct, so the enumeration result can never contain two assignments with
equal `.values`. This test pins that invariant so the dead append-time dedup
guard can be removed safely.
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from assignment_selection import (
    Assignment,
    Problem,
    SourceAssignment,
)
from assignment_selection.solver import enumerate_candidate_assignments

_CONCEPT_IDS = ("x", "y", "z")
st_concept_value = st.integers(min_value=0, max_value=3)


@st.composite
def st_problem(draw: st.DrawFn) -> Problem:
    """Generate a Problem whose sources collectively observe every concept.

    Each source assigns a value to every concept in `_CONCEPT_IDS`, so every
    per-concept domain is non-empty and the enumeration is the full Cartesian
    product of the observed values.
    """
    source_rows: list[tuple[int, ...]] = draw(
        st.lists(
            st.tuples(*(st_concept_value for _ in _CONCEPT_IDS)),
            min_size=1,
            max_size=6,
        )
    )
    sources = tuple(
        SourceAssignment(
            source_id=f"s{index}",
            assignment=Assignment(
                values=dict(zip(_CONCEPT_IDS, row, strict=True))
            ),
        )
        for index, row in enumerate(source_rows)
    )
    return Problem(concept_ids=_CONCEPT_IDS, sources=sources)


def _expected_product_count(problem: Problem) -> int:
    """Product of the per-concept distinct observed-value counts."""
    total = 1
    for concept_id in problem.concept_ids:
        observed: set[object] = {
            source.assignment.value_for(concept_id)
            for source in problem.sources
            if concept_id in source.assignment.values
        }
        total *= len(observed)
    return total


class TestEnumerateUniqueness:
    @pytest.mark.property
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    @given(st_problem())
    def test_enumerated_candidates_are_pairwise_distinct(
        self,
        problem: Problem,
    ) -> None:
        candidates = enumerate_candidate_assignments(problem)
        assert isinstance(candidates, tuple)

        distinct_value_mappings = {
            tuple(sorted(candidate.values.items())) for candidate in candidates
        }
        # No two enumerated candidates share the same `.values`.
        assert len(candidates) == len(distinct_value_mappings)

        # The enumeration is exactly the Cartesian product of observed values,
        # independently confirming no element was dropped by any dedup pass.
        assert len(candidates) == _expected_product_count(problem)
