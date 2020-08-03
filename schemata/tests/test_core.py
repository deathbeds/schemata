import pytest
import hypothesis
import jsonschema
import schemata


def test_invalid_schema():
    with pytest.raises(jsonschema.ValidationError):

        class t(schemata.jsonschema):
            type: "whatever"

    with pytest.raises(jsonschema.ValidationError):

        class t(schemata.object):
            properties: []


def test_compare_types():
    assert (schemata.integer <= 10) is (schemata.integer <= 10)
