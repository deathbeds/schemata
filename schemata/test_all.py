from schemata import *


def test_any():

    assert isinstance(type(Any()), Schemata)

    assert issubclass(type(Any(None)), type(None))

    assert issubclass(type(Any(True)), bool)

    assert issubclass(type(Any(False)), bool)

    assert issubclass(type(Any(1)), Integer)

    assert issubclass(type(Any(1.1)), Float)

    assert issubclass(type(Any("abc")), String)

    assert issubclass(type(Any([])), List)

    assert issubclass(type(Any({})), Dict)
