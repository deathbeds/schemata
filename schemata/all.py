"""collections of described and sample types"""

import math

import schemata

EXAMPLES = dict(
    null=(None,),
    boolean=(True, False),
    integer=(-100, 0, 1),
    number=(0.0, math.pi, 1000.0),
    string=("abc", "123"),
    array=([], [1, 2, 3, "abc"]),
    object=({}, dict(a="abc")),
)


def examples(*args):
    return schemata.types.Examples[sum(map(EXAMPLES.get, args), ())]


def negative_examples(*args):
    return schemata.types.Examples[
        sum((v for k, v in EXAMPLES.items() if k not in args), ())
    ]


# we couldn't subclass `type(None)`
class Null(schemata.Null, examples("null")):
    """the null type"""


class NotNull(-Null, negative_examples("null")):
    """non null type"""


# we couldn't subclass bool
class Bool(schemata.Bool, examples("boolean")):
    """the bool type"""


class NotBool(-Bool, negative_examples("boolean")):
    """non bool type"""


class Number(schemata.Number, examples("integer", "number", "boolean")):
    """numeric types"""


class NotNumber(-schemata.Number, negative_examples("integer", "number", "boolean")):
    """non numeric types"""


class ConstrainedNumber(schemata.Number[0:10:2], schemata.types.Examples[0, 2, 10]):
    pass


class NotConstrainedNumber(-ConstrainedNumber, schemata.types.Examples[-2, 1]):
    pass


class String(schemata.String, examples("string")):
    """string types"""


class NotString(-String, negative_examples("string")):
    """non string types"""


class NonemptyNumericString(schemata.String["[0-9]+"].examples(("123",))):
    """a string of only numbers"""


class NotNonemptyNumericString(-NonemptyNumericString, schemata.types.Examples["abc"]):
    """a string containing characters other than strings"""


class List(schemata.List, examples("array")):
    """a list data structure"""


class NotAList(-schemata.List, negative_examples("array")):
    """non list structures"""


class Dict(schemata.Dict, examples("object")):
    """a dict data structure"""


class NotADict(-schemata.Dict, negative_examples("object")):
    """non dict structures"""


def test_times():
    """
    >>> with schemata.Date("2020-01-01"): print(schemata.DateTime())
    2020-01-01T00:00:00
    >>> with schemata.Date("2020-01-01"): print(schemata.Date())
    2020-01-01
    >>> with schemata.Date("2020-01-01"): print(schemata.Time())
    00:00:00
    >>> with schemata.Date("2020-01-01"): print(schemata.Date.when("yesterday"))
    2019-12-31
    """
