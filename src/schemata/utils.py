import abc
import builtins
import collections
import functools
import importlib
import inspect
import itertools
import re
import typing
from contextlib import suppress
from functools import partial, partialmethod
from functools import singledispatch as register
from unittest import TestCase

testing = TestCase()
import abc
import functools
import json
from pathlib import Path

Path = type(Path())
ANNO, NAME, SCHEMA, DOC = "__annotations__", "__name__", "__schema__", "__doc__"


class Ø(abc.ABCMeta):
    def __bool__(self):
        return False


class EMPTY(metaclass=Ø):
    pass


def validates(*types):
    def decorator(callable):
        @functools.wraps(callable)
        def main(cls, object):
            if types:
                if isinstance(object, types):
                    return callable(cls, object)
            else:
                return callable(cls, object)

        return classmethod(main)

    return decorator


def not_format(cls, object):
    cls = type(object)
    return f"{object} is not a validate {cls.value()} format."


def resolve(pointer, object):
    if pointer.startswith("#"):
        return resolve_ref(pointer, object)
    import jsonpointer

    return jsonpointer.resolve_pointer(object, pointer)


def resolve_ref(ref, object):
    return resolve(ref.lstrip("#"), object)


def enforce_tuple(x):
    if x is None:
        return ()
    if not isinstance(x, tuple):
        return (x,)
    return x


def merge(cls, **schema):
    for type in cls.__mro__:
        for k, v in dict.items(getattr(type, ANNO, {}) or {}):
            if k in ("type", "enum"):
                if k in schema:
                    for y in enforce_tuple(v):
                        if y == schema[k]:
                            continue
                        if y in schema[k]:
                            continue
                        v = enforce_tuple(schema[k]) + (y,)

                schema[k] = v
            else:
                schema[k] = v
    return schema


def lowercase(s):
    if s:
        return s[0].lower() + s[1:]
    return ""


def py_to_json(s):
    if s.startswith("Ui"):
        return "ui:" + lowercase(s[2:])
    if s.endswith("_" * 2):
        return "@" + lowercase(s[:-1])
    if s.endswith("_"):
        return "$" + lowercase(s[:-1])
    return lowercase(s)


def uppercase(s):
    return s[0].upper() + s[1:]


def json_to_py(s):
    if s.startswith("$"):
        return uppercase(s[1:]) + "_"
    if s.startswith("@"):
        return uppercase(s[1:]) + "__"
    return s[0].upper() + s[1:]


@register
def get_schema(x, *, ravel=True):
    return x


@get_schema.register
def get_schema_str(x: str, *, ravel=True):
    return x


@get_schema.register
def get_schema_type(x: type, *, ravel=True):
    from .objects import Dict

    if ravel is None:
        return get_schema(getattr(x, ANNO, {}), ravel=True)
    if ravel:
        return get_schema(getattr(x, ANNO, {}), ravel=ravel)
    return x


@get_schema.register
def get_schema_dict(x: dict, *, ravel=True):
    if ravel:
        return {k: get_schema(v, ravel=ravel) for k, v in x.items()}
    return x


@get_schema.register
def get_schema_re(x: re.Pattern, *, ravel=True):
    return x.pattern


def get_docstring(cls):
    schema = cls.schema(True)
    docstring = """"""
    if "title" in schema:
        docstring += schema["title"] + "\n" * 2
    if "description" in schema:
        docstring += schema["description"] + "\n" * 2

    if "$comment" in schema:

        docstring += f"""\
Notes
--------
{schema["$comment"]}

"""

    if "examples" in schema:

        docstring += (
            f"""\
Examples
--------
"""
            + "\n".join(
                f"""\
 >>> {cls.__name__}({F'"{x}"' if isinstance(x, str) else x})
 """
                + ("" if x is None else f"'{x}'" if isinstance(x, str) else str(x))
                for x in schema["examples"]
            )
            + "\n"
        )

    return docstring.rstrip() or None


@get_schema.register
def get_schema_dict(x: tuple, *, ravel=True):
    return tuple(get_schema(x, ravel=ravel) for x in x)


def get_default(cls, object=EMPTY, default=EMPTY):
    from .types import Const, Default

    if object is EMPTY:
        object = cls.value(Default, Const)

    if object is EMPTY:
        if default is not EMPTY:
            return default
    return object


def get_schemata_object(x, cls=None):
    from .types import JSONSCHEMA_SCHEMATA_MAPPING, JSONSCHEMA_STR_MAPPING, Any, Type

    if cls and x is EMPTY:
        return cls()

    if isinstance(x, Any):
        return x

    t = type(x)
    if t in JSONSCHEMA_STR_MAPPING:
        t = JSONSCHEMA_SCHEMATA_MAPPING[JSONSCHEMA_STR_MAPPING[t]]
        return t(x)
    return x


@register
def get_py(x):
    if hasattr(x, "py"):
        return x.py()
    return x


@get_py.register
def get_py_dict(x: dict):
    return {k: get_py(v) for k, v in x.items()}


@get_py.register(tuple)
@get_py.register(list)
def get_py_iter(x):
    return type(x)(map(get_py, x))


def get_verified_object(x):
    from .types import Verified

    if isinstance(x, type) and issubclass(x, Verified):
        return True, x.value(Verified)
    return False, x


@register
def get_hash(x):
    return hash(x)


@get_hash.register
def get_hash_dict(x: dict):
    return hash(zip(x.keys(), map(get_hash, x.values())))


@get_hash.register
def get_hash_type(x: type):
    return get_hash(getattr(x, ANNO, {}))
