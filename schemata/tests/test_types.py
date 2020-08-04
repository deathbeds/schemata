import pytest
import hypothesis
import jsonschema
import schemata


@hypothesis.given(schemata.string.strategy())
def test_string(value):
    schemata.string(value)
    assert isinstance(value, schemata.string)


@hypothesis.given(schemata.integer.strategy())
def test_integer(value):
    schemata.integer(value)
    assert isinstance(value, schemata.number)
    assert isinstance(value, schemata.integer)


@hypothesis.given(
    hypothesis.strategies.one_of(
        schemata.integer.strategy(), schemata.number.strategy()
    )
)
def test_number(value):
    schemata.number(value)
    assert isinstance(value, schemata.number)


@hypothesis.given(schemata.array.strategy())
def test_array(value):
    schemata.array(value)
    assert isinstance(value, schemata.array)


@hypothesis.given(schemata.object.strategy())
def test_object(value):
    schemata.object(value)
    assert isinstance(value, schemata.object)


def test_template():
    assert schemata.template(dict(x={"$eval": "foo + 2"}))(dict(foo=4)) == dict(x=6)

# test complex schema
def test_anyof():
    anyof = schemata.jsonschema[dict(anyOf=[schemata.integer, schemata.string])]
    with pytest.raises(jsonschema.ValidationError):
        anyof({})
    with pytest.raises(jsonschema.ValidationError):
        anyof(1.1)

    assert anyof(10)
    assert anyof("abc")



stringOrInteger = schemata.jsonschema[
    dict(anyOf=[schemata.integer, schemata.string], title="stringOrInteger")
]


@hypothesis.given(stringOrInteger.strategy())
def test_anyof_strategy(value):
    assert isinstance(value, stringOrInteger)

