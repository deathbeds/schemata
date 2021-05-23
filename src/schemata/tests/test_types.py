import copy
import math
import string

import hypothesis
import pytest

from schemata import *


class ANull(Null, Examples[None]):
    """A Null type"""


class NotANull(-ANull, Examples[True, 1, math.pi, string.ascii_letters, [], {}]):
    """Non-Null types"""


class ABool(Bool, Examples[True, False]):
    """A Bool type"""


class NotABool(-ABool, Examples[None, 2, math.pi, string.ascii_letters, [], {}]):
    """Non-Bool type"""


class AnInteger(Integer, Examples[-100, 0, 1, 10]):
    """An Integer type"""


class NotAnInteger(
    -Integer, Examples[None, True, math.pi, string.ascii_letters, [], {}]
):
    """Non-Integer type"""


class AFloat(Float, Examples[math.pi, math.tau, math.pi, 0.0, 1.0]):
    """An Float type"""


class NotAFloat(
    -Float,
    Examples[None, True, 0, 1, string.ascii_letters, [], {}],
):
    """Non-Float type"""


class AString(String, Examples[string.ascii_letters, "abc", "123"]):
    """A String type"""


class NotAString(-String, Examples[None, True, 1, math.pi, [], {}]):
    "A String type"


class APattern(
    String["^a"],
    Examples["abc", "a", string.ascii_letters],
):
    """A Pattern string"""


class NotAPattern(
    -APattern,
    Examples["", "123", string.ascii_uppercase],
):
    """Invalid string Patterns"""


class AList(List, Examples[[], list("abc")]):
    """A List"""


class NotAList(-AList, Examples[None, True, 0, 1, string.ascii_letters, {}]):
    """Non List types"""


class ADict(Dict, Examples[{}, dict(foo="bar")]):
    """A Dict"""


class NotADict(
    -ADict,
    Examples[None, True, 0, 1, string.ascii_letters, []],
):
    """Non Dict types"""


class ADictWithProperties(Dict):
    """\
>>> assert issubclass(ADictWithProperties, Dict.Properties)
>>> assert ADictWithProperties.value(Dict.Properties)["foo"] is Integer
    """

    foo: Integer


class AListWithItems(List):
    """\
>>> assert issubclass(AListWithItems, List.Items)
>>> assert issubclass(AListWithItems.value(List.Items), Dict.Properties)
    """

    foo: Integer


def test_uri():
    uri = Uri["https://api.github.com/users{/user}"]
    assert uri(user="tonyfast") == "https://api.github.com/users/tonyfast"


def test_uuid():
    assert Uuid() == "00000000-0000-0000-0000-000000000000"
    assert Uuid[1]
    assert Uuid[3]
    assert Uuid[4]
    assert Uuid[5]


@pytest.mark.parametrize(
    "type, value", ((String, 1), (Integer, "1"), (Float, "1.2"), (Dict, [("a", 1)]))
)
def test_casting(type, value):
    x, y = copy.copy(value), copy.copy(value)
    with pytest.raises(AssertionError):
        type(value)
    assert type.cast()(x) == type.py()(y)


def test_casting_list():
    iter = lambda: map(type, range(10))
    with pytest.raises(AssertionError):
        List(iter())
    assert List.cast()(iter()) == List.py()(iter())
