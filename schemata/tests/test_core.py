import pytest
import hypothesis
import jsonschema
import schemata


def test_invalid_schema():
    with pytest.raises(jsonschema.ValidationError):

        class s(schemata.jsonschema):
            type: "whatever"

        s

    with pytest.raises(jsonschema.ValidationError):

        class t(schemata.object):
            properties: []

        t


def test_compare_types():
    assert (schemata.integer <= 10) is (schemata.integer <= 10)
