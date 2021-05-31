import typing

from schemata import *
from schemata.utils import Path


def test_dict_py():

    assert Dict.py() is dict
    assert Dict[Integer].py() == typing.Dict[str, int]
    assert Dict[List].py() == typing.Dict[str, list]
    assert Dict.propertyNames(Integer).py() == typing.Dict[int, object]
    assert Dict[Integer, String].py() == typing.Dict[int, str]


def test_file_py():
    assert File.py() is Path


def test_list_py():
    assert List.py() is list
    assert Tuple.py() is tuple
    assert Set.py() is set
    assert List[Integer].py() == typing.List[Integer]
    assert List[Integer, String].py() == typing.Tuple[int, str]
    assert Tuple[Integer, String].py() == typing.Tuple[int, str]


def test_composite_py():
    assert (Integer | Float).py() == typing.Union[int, float]
    assert (Integer & Float).py() == (Integer & Float)
    assert (Integer ^ Float).py() == typing.Union[int, float]
    assert Not[Integer].py() == Not[Integer]
