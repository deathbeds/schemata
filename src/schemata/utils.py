import abc
import enum
import functools
import inspect
import re
from contextlib import suppress
from functools import partial, partialmethod
from functools import singledispatch as register
from typing import Type
from unittest import TestCase
from unittest.runner import TextTestResult

testing = TestCase()
import abc
import functools
import json
from pathlib import Path

Path = type(Path())
ANNO, NAME, SCHEMA, DOC, TYPE = (
    "__annotations__",
    "__name__",
    "__schema__",
    "__doc__",
    "@type",
)


class Ø(abc.ABCMeta):
    def __bool__(self):
        return False


class EMPTY(metaclass=Ø):
    """a false sentinel"""

    pass


def validates(*types):
    """a decorator for classmethods that operate on specific types"""

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


def enforce_tuple(x):
    """make sure the input is a tuple"""
    with suppress(TypeError):
        if x in {None, EMPTY}:
            return ()
    if not isinstance(x, tuple):
        return (x,)
    return x


def merge(cls, **schema):
    for type in cls.__mro__:
        for k, v in dict.items(getattr(type, ANNO, {}) or {}):
            if k in ("type", "enum", "cast", "anyOf", "allOf", "oneOf"):
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


def normalize_json_key(s):
    """convert to a string a proper json key based on conventions"""
    if s.startswith("Ui"):
        return "ui:" + lowercase(s[2:])
    if s.endswith("_" * 2):
        return "@" + lowercase(s[:-2])
    if s.endswith("_"):
        return "$" + lowercase(s[:-1])
    s = s.replace("_", "-")
    return lowercase(s)


def uppercase(s):
    return s[0].upper() + s[1:]


@register
def get_schema(x, *, ravel=True):
    """get teh schema from an object"""
    return x


@get_schema.register
def get_schema_str(x: str, *, ravel=True):
    return x


@get_schema.register
def get_schema_enum(x: enum.EnumMeta, *, ravel=True):
    return (ravel and list or tuple)(x.__members__)


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


@get_schema.register(list)
@get_schema.register(tuple)
def get_schema_iter(x, *, ravel=True):
    if ravel:
        return tuple(map(get_schema, x))
    return x


@get_schema.register
def get_schema_re(x: re.Pattern, *, ravel=True):
    return x.pattern


def get_docstring(cls):
    """build a docstring for a schemata type"""
    schema = cls.schema(True)
    docstring = get_santized_comments(inspect.getcomments(cls) or "")
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
                for x in schema["examples"] or []
            )
            + "\n"
        )

    return docstring.rstrip() or ""


def get_santized_comments(x):
    import textwrap

    return textwrap.dedent("".join(x.lstrip("#") for x in x.splitlines(True)))


@register
def get_schemata(x, cls=None):
    from .types import JSONSCHEMA_SCHEMATA_MAPPING, JSONSCHEMA_STR_MAPPING, Any, Type

    if cls and x is EMPTY:
        return cls()

    if isinstance(x, Any):
        return x

    t = get_schemata(type(x))
    if t:
        return t(x)
    return x


@get_schemata.register
def get_schemata_type(x: type, cls=None):
    from .types import (
        JSONSCHEMA_SCHEMATA_MAPPING,
        JSONSCHEMA_STR_MAPPING,
        Any,
        MetaType,
    )

    if isinstance(x, MetaType):
        return x
    if x in JSONSCHEMA_STR_MAPPING:
        return JSONSCHEMA_SCHEMATA_MAPPING[JSONSCHEMA_STR_MAPPING[x]]


@get_schemata.register
def get_schemata_str(x: str, cls=None):
    from .strings import String
    from .types import JSONSCHEMA_SCHEMATA_MAPPING

    if x in JSONSCHEMA_SCHEMATA_MAPPING:
        return JSONSCHEMA_SCHEMATA_MAPPING[x]
    return String


INFER_DICT_TYPES = "properties dependencies".split()


def get_prototypes(x):
    for cls in get_subclasses(x):
        if cls is x:
            continue

        anno = getattr(cls, ANNO, {})
        if len(anno) is 1:
            yield cls


def get_subclasses(x):
    for cls in x.__subclasses__():
        yield cls
        yield from get_subclasses(cls)


def get_schema_type_cache(x=EMPTY):
    from .types import Any

    return dict(
        prototypes={
            hash(x): x
            for x in get_prototypes(x or Any)
            if len(getattr(x, ANNO, {})) is 1
        },
        keys={
            x.key(): x
            for x in get_prototypes(x or Any)
            if len(getattr(x, ANNO, {})) is 0
        },
    )


@get_schemata.register
def get_schemata_dict(schema: dict, cache=None):
    from .composites import AllOf, AnyOf, Not, OneOf
    from .types import Any, MetaType

    cache = cache or get_schema_type_cache()

    id = (("type", schema["type"]),)
    if "type" in schema and id in cache["prototypes"]:
        cls = cache["prototypes"][hash(id)]
    else:
        cls = Any
    for k, v in schema.items():
        if k == "type":
            continue

        if isinstance(v, MetaType):
            cls += v
            continue

        id = hash(((k, v),))

        if id in cache["prototypes"]:
            cls = cls + cache["prototypes"][id]
        elif k in cache["keys"]:
            cls = cls + cache["keys"][k][v]
    return cls


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
def get_hashable(x):
    return x


@get_hashable.register
def get_hashable_dict(x: dict):
    return tuple(zip(x.keys(), map(get_hashable, x.values())))


@get_hashable.register
def get_hashable_type(x: type):
    return get_hashable(getattr(x, ANNO, {}))


@get_hashable.register(list)
@get_hashable.register(tuple)
def get_hashable_type(x):
    return tuple(map(get_hashable, x))


def make_time(x):
    return x.rpartition(".")[0].replace(".", ":") + "00:00"


def is_type_definition(x):
    anno = getattr(x, ANNO, {})
    if len(anno) is 1:
        return x
    return False


def is_validator(x):
    from .types import Any

    anno = getattr(x, ANNO, {})
    if len(anno) is 1:
        if x.validator is not Any.validator:
            return True
    return False


def is_prototype(x):
    if not hasattr(x, ANNO):
        return False
    if len(x.__annotations__) is 0:
        return True
    return False


def make_enum(cls, members):
    return enum.Enum(
        cls.__name__, members, module=cls.__module__, qualname=cls.__qualname__
    )


def is_metadata(x):
    from . import types

    return issubclass(
        x,
        (
            types.Description,
            types.Comment_,
            types.Title,
            types.Optional,
            types.Examples,
            types.Optional,
            types.ReadOnly,
            types.WriteOnly,
        ),
    )


@register
def get_default(object, default=EMPTY):
    return object


@get_default.register
def get_default_null(object: Ø, default=EMPTY):
    if object is EMPTY:
        return default
    return object


@get_default.register
def get_default_type(cls: type, default=EMPTY):
    from . import objects, types

    object = cls.value(types.Default, types.Const)
    if object is EMPTY:
        object = cls.value(types.Enum)
        if isinstance(object, tuple):
            object = object[0]
    if object is EMPTY:
        if issubclass(cls, objects.Dict):
            props = cls.value(objects.Dict.Properties, default={})
            next = {}
            for k, v in props.items():
                v = get_default(v)
                if v is not EMPTY:
                    next[k] = v
            return next
    return get_default(object, default=default)


def get_cast(cls, *args, **kwargs):
    from .callables import Cast

    cast = cls.value(Cast)
    if cast:
        if cast is True:
            return cls(*args, **kwargs)
        if callable(cast):
            return cast(*args, **kwargs)
    raise TypeError("cant cast")


"""
Args (alias of Parameters)

Arguments (alias of Parameters)
Attention
Attributes
Caution
Danger
Error
Example
Examples
Hint
Important
Keyword Args (alias of Keyword Arguments)
Keyword Arguments
Methods
Note
Notes
Other Parameters
Parameters
Return (alias of Returns)
Returns
Raise (alias of Raises)
Raises
References
See Also
Tip
Todo
Warning
Warnings (alias of Warning)
Warn (alias of Warns)
Warns
Yield (alias of Yields)
Yields
"""
