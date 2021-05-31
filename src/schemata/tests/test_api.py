import math
import string

import hypothesis
import pytest

from schemata import *


def _test_api(t, contains):
    keys = dir(t)
    assert all(map(keys.__contains__, keys))


# TODO: i might have missed some keys
not_keys = "max min desc ex".split()
type_keys = "description default examples title comment_".split()
numbers_keys = "minimum maximum exclusiveMinimum exclusiveMaximum".split()
string_keys = "pattern maxLength minLength format".split()
list_keys = "items additionalItems minItems maxItems contains".split()
dict_keys = (
    "properties additionalProperties minProperties maxProperties PropertyNames".split()
)


@pytest.mark.parametrize(
    "type, contains",
    [
        (Type, type_keys),
        (Integer, numbers_keys + type_keys),
        (Float, numbers_keys + type_keys),
        (String, string_keys + type_keys),
        (List, list_keys + type_keys),
        (Dict, dict_keys + type_keys),
    ],
)
def test_api(type, contains):
    keys = dir(type)
    assert all(map(keys.__contains__, contains))
    assert not any(map(keys.__contains__, not_keys))


# def test_infer():
#     self = Integer.minimum(1).maximum(10)

#     assert Any.infer(self.schema()) is not self
#     assert Any.infer(self.schema()) == self
