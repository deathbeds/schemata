import hypothesis
import pytest

from schemata import Default, Not
from schemata.tests import strategies


@hypothesis.given(strategies.draw_type_value(strategies.draw_schemata()))
@hypothesis.settings(suppress_health_check=[hypothesis.HealthCheck.too_slow])
def test_types(pair):
    global cls, value
    cls, value = pair

    assert cls(value) == value
    assert (cls + Default[value])() == value

    with pytest.raises(AssertionError):
        Not[cls](value)
