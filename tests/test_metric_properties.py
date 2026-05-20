"""Property tests treating ``claim_distance`` as a metric.

Triangle inequality is tested SEPARATELY for the numeric and the categorical
domains, and deliberately NOT across a mixed domain. ``claim_distance``
numerically coerces its operands: when both coerce to floats it returns their
absolute numeric difference, otherwise it returns ``0.0``/``1.0`` for
categorical equality/inequality. A categorical "detour" between two far-apart
numbers therefore contributes at most distance ``2`` (1 + 1), while the direct
numeric distance between those numbers is unbounded. The triangle inequality
``d(a, c) <= d(a, b) + d(b, c)`` only holds WITHIN a homogeneous value space.
This is a known property of the coercion design, not a bug, so no mixed-domain
triangle test is written here.

Non-negativity holds universally (across mixed values) because every branch of
``claim_distance`` returns a non-negative number.

Symmetry (``d(a, b) == d(b, a)``) and identity (``d(a, a) == 0``) are already
covered by ``test_distance_symmetric`` / ``test_distance_zero_self`` in
``test_assignment_selection_merge.py`` and are intentionally not duplicated here.
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from assignment_selection.solver import claim_distance

st_finite_float = st.floats(
    min_value=-1000,
    max_value=1000,
    allow_nan=False,
    allow_infinity=False,
)
st_category = st.from_regex(r"[a-z]{1,6}", fullmatch=True)
st_mixed_value = st.one_of(st_finite_float, st_category)


@pytest.mark.property
@given(st_mixed_value, st_mixed_value)
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_claim_distance_is_non_negative(a: object, b: object) -> None:
    assert claim_distance(a, b) >= 0


@pytest.mark.property
@given(st_finite_float, st_finite_float, st_finite_float)
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_claim_distance_triangle_inequality_numeric(
    a: float,
    b: float,
    c: float,
) -> None:
    assert claim_distance(a, c) <= claim_distance(a, b) + claim_distance(b, c)


@pytest.mark.property
@given(st_category, st_category, st_category)
@settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_claim_distance_triangle_inequality_categorical(
    a: str,
    b: str,
    c: str,
) -> None:
    assert claim_distance(a, c) <= claim_distance(a, b) + claim_distance(b, c)
