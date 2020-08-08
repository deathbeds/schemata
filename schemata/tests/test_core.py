import pytest
import hypothesis
import jsonschema
import schemata


def test_metaschema():
    assert {"definitions", "dependencies"} == set(
        jsonschema.Draft7Validator.META_SCHEMA["properties"]
    ) - set(schemata.core.meta_schema.__annotations__["properties"])
    assert {
        "$anchor",
        "$defs",
        "$recursiveAnchor",
        "$recursiveRef",
        "$vocabulary",
        "base",
        "contentSchema",
        "dependentRequired",
        "dependentSchemas",
        "deprecated",
        "links",
        "maxContains",
        "minContains",
        "unevaluatedItems",
        "unevaluatedProperties",
        "writeOnly",
    } == set(schemata.core.meta_schema.__annotations__["properties"]) - set(
        jsonschema.Draft7Validator.META_SCHEMA["properties"]
    )


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


def test_fluent_integer():
    assert isinstance(
        9, schemata.integer.minimum(0).maximum(10).title("Between 0 and 10")
    ) ^ isinstance(
        99, schemata.integer.minimum(0).maximum(10).title("Between 0 and 10")
    )
