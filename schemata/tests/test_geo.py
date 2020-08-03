import pytest
import hypothesis
import schemata
from schemata import geo

@hypothesis.given(geo.point.strategy())
def test_point(value):
    geo.point(value)
    assert isinstance(value, geo.point)
    assert isinstance(value, geo.geometry)