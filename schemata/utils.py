import abc
import builtins
import enum
import functools
import inspect
import operator
import re
import sys
from contextlib import suppress
from functools import partial, partialmethod
from functools import singledispatch as register
from typing import Type
from unittest import TestCase
from unittest.runner import TextTestResult

from numpy.lib.arraysetops import isin

IN_SPHINX = "sphinx" in sys.modules
try:
    from typing import _ForwardRef as ForwardRef

    _root = True  # pragma: no cover
except ImportError:
    from typing import ForwardRef

    _root = False  # pragma: no cover


Pattern = type(re.compile(""))

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

    def __repr__(cls):
        return cls.__name__

    def __hash__(self):
        return hash(None)


class EMPTY(metaclass=Ø):
    """a false sentinel"""

    pass


def validates(*types):
    """a decorator for classmethods that operate on specific types"""

    def decorator(callable):
        @functools.wraps(callable)
        def main(cls, object, *args, **kwargs):
            if isinstance(object, types):
                return callable(cls, object, *args, **kwargs)

        return classmethod(main)

    return decorator


def enforce_tuple(x):
    """make sure the input is a tuple"""
    with suppress(TypeError):
        if x in {None, EMPTY}:
            return ()
    if isinstance(x, (list, set)):
        x = tuple(x)
    if not isinstance(x, tuple):
        return (x,)
    return x


@register
def merge(object, **schema):
    return schema


@merge.register
def merge_type(object: type, **schema):
    """merge multiple schema together"""
    for type in object.__mro__:
        schema = merge_dict(getattr(type, ANNO, {}) or {}, **schema)
    return schema


@merge.register
def merge_dict(object: dict, **schema):
    """merge multiple schema together"""
    for k, v in object.items():
        if k in ("type", "enum", "cast", "anyOf", "allOf", "oneOf", "ui:widget"):
            if k in schema:
                for y in enforce_tuple(v):
                    if y == schema[k]:
                        continue
                    if y in schema[k]:
                        continue
                    schema[k] = enforce_tuple(schema[k]) + (y,)

        schema.setdefault(k, v)
    return schema


@merge.register(tuple)
@merge.register(list)
def merge_iter(object, **schema):
    """merge multiple schema together"""
    for object in object:
        schema.update(merge(object, **schema))
    return schema


def merge(a, b=None, *c):
    while c:
        b = merge(b, c[0])
        c = c[1:]
    if isinstance(a, dict):
        if b:
            if isinstance(b, type):
                return b
            for k, v in b.items():
                if k in a:
                    if isinstance(a[k], dict):
                        a[k] = merge(a[k], v)
                    elif isinstance(a, (list, set, tuple)):
                        a[k].extend(v)

                else:
                    a[k] = v
    return a


class types:
    class null(abc.ABC):
        pass

    null.register(type(None))

    class boolean(abc.ABC):
        pass

    boolean.register(bool)

    class integer(abc.ABC):
        pass

    integer.register(int)

    class number(integer):
        pass

    number.register(float)

    class array(abc.ABC):
        pass

    array.register(list)
    array.register(set)
    array.register(tuple)

    class object(abc.ABC):
        pass

    object.register(dict)


def lowercase(s):
    """return a lower string"""
    if s:
        return s[0].lower() + s[1:]
    return ""


def format_capital_key(str):
    if str.startswith("$"):
        return uppercase(str[1:]) + "_"

    if str.startswith("@"):
        return uppercase(str[1:]) + "__"

    return uppercase(str)


def normalize_json_key(s):
    """convert to a string a proper json key based on conventions

    * one trailing `_` refers to a `$` key
    * two trailing `__` refers to a `@` key
    * names leading with Ui are given spinal case
    """
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
    """get the schema from an object"""
    return x


@get_schema.register
def get_schema_enum(x: enum.EnumMeta, *, ravel=True):
    return (ravel and list or tuple)(x.__members__)


@get_schema.register
def get_schema_type(x: type, *, ravel=True):
    from .objects import Dict
    from .types import Schemata, Type

    if not isinstance(x, Schemata):
        x = Type[x]

    data = getattr(x, ANNO, {})

    if ravel is None:
        return get_schema(data, ravel=False)
    if ravel:
        return get_schema(data, ravel=ravel)
    return x


@get_schema.register
def get_schema_forward(x: ForwardRef, *, ravel=True):
    """get the schema from an object"""
    if ravel:
        return x.__forward_code__
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
def get_schema_re(x: Pattern, *, ravel=True):
    return x.pattern


def get_docstring(cls, docstring=""):
    """build a docstring for a schemata type"""
    schema = cls.schema(True)
    docstring = """"""
    if "title" in schema:
        docstring += schema["title"] + "\n" * 2
    if "description" in schema:
        docstring += schema["description"] + "\n" * 2

    if "$comment" in schema:

        docstring += f"""\
Notes
-----
{schema["$comment"]}

"""

    if "examples" in schema:

        docstring += f"""\
Examples
--------

{get_examples(cls, schema)}
"""

    return docstring.rstrip() or ""


def get_examples(cls, schema):
    schema = schema or {}
    doctests = """"""
    for x in schema.get("examples", ()) or ():
        doctests += (
            f"""\
>>> {cls.__name__}({F'"{x}"' if isinstance(x, str) else x})
"""
            + ("" if x is None else f"'{x}'" if isinstance(x, str) else str(x))
            + "\n"
        )

    if "not" in schema:
        for x in schema["not"].get("examples", ()) or ():
            doctests += f"""\
>>> with __import__("pytest").raises(BaseException): {cls.__name__}({F'"{x}"' if isinstance(x, str) else x})
"""
    return doctests


def get_santized_comments(x):
    import textwrap

    return textwrap.dedent("".join(x.lstrip("#") for x in x.splitlines(True)))


@register
def get_schemata(x, cls=None):
    from .types import Any, Type

    if cls and x in (EMPTY, None):
        return None

    if isinstance(x, Any):
        return x

    t = get_schemata(type(x))
    if t:
        return t(x)
    return x


@get_schemata.register
def get_schemata_type(x: type, cls=None):
    from .types import Any, Schemata

    if isinstance(x, Schemata):
        return x
    if x in JSONSCHEMA_STR_MAPPING:
        return JSONSCHEMA_SCHEMATA_MAPPING[JSONSCHEMA_STR_MAPPING[x]]


@get_schemata.register
def get_schemata_str(x: str, cls=None):
    from .strings import String

    if x in JSONSCHEMA_SCHEMATA_MAPPING:
        return JSONSCHEMA_SCHEMATA_MAPPING[x]
    return String(x)


INFER_DICT_TYPES = "properties dependencies".split()


def get_prototypes(x):
    """the prototypes are individual class definitions that can be verified."""
    for cls in get_subclasses(x):
        if cls is x:
            continue

        anno = getattr(cls, ANNO, {})
        if len(anno) == 1:
            yield cls


def get_subclasses(x):
    """iterate through all the subclasses of an object"""
    for cls in x.__subclasses__():
        yield cls
        yield from get_subclasses(cls)


@register
def get_hashable(x):
    return x


@get_hashable.register
def get_hashable_dict(x: dict):
    return tuple(
        sorted(
            (
                (k, get_hashable(v))
                for k, v in x.items()
                if k not in {"description", "$comment"}
            ),
            key=lambda x: x[0],
        )
    )


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
    if len(anno) == 1:
        return x
    return False


def is_validator(x):
    from .types import Any, Type

    if x is Type:
        return True
    anno = getattr(x, ANNO, {})

    if len(anno) == 1:
        if x.validator is not Any.validator:
            return True
    return False


def is_prototype(x):
    if not hasattr(x, ANNO):
        return False
    if len(x.__annotations__) == 0:
        return True
    return False


def make_enum(cls, members):
    return enum.Enum(
        cls.__name__, members, module=cls.__module__, qualname=cls.__qualname__
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
def get_default_null(object: dict, default=EMPTY):
    if object is EMPTY:
        return default
    return object.get("default", default)


@get_default.register
def get_default_type(cls: type, default=EMPTY):
    from . import arrays, objects, types

    object = cls.value(types.Any.Default, types.Any.Const)
    if object is EMPTY:
        object = cls.value(types.Enum)
        if isinstance(object, tuple):
            object = object[0]
    if object is EMPTY or issubclass(cls, dict):
        if issubclass(cls, objects.Dict):
            props = cls.value(objects.Dict.Properties, default={})
            next = {}
            for k, v in props.items():
                v = get_default(v)
                if v is not EMPTY:
                    next[k] = v
            return next
        if issubclass(cls, arrays.Tuple):
            return tuple(map(get_default, cls.value(arrays.Arrays.Items)))

    return get_default(object, default=default)


# map a jsonschema to the python type
JSONSCHEMA_PY_MAPPING = dict(
    null=type(None),
    boolean=bool,
    string=str,
    integer=int,
    number=float,
    array=(set, list, tuple),
    object=dict,
)

# map a python type to its jsonschema key
JSONSCHEMA_STR_MAPPING = dict(map(reversed, JSONSCHEMA_PY_MAPPING.items()))

JSONSCHEMA_SCHEMATA_MAPPING = {}


def get_prototype_mapping(cls=None):
    from .types import Any

    return {x.key(): x for x in filter(is_prototype, get_subclasses(cls or Any))}


@register
def get_class(schema, cls=EMPTY, types=EMPTY):
    return schema


@get_class.register
def get_class_dict(schema: dict, cls=EMPTY, types=EMPTY):
    types = types or get_prototype_mapping()
    if not cls and "type" in schema:
        if isinstance(schema["type"], str):
            cls = get_schemata(schema["type"])
        else:
            cls = Type[schema["type"]]
    for key, value in schema.items():
        if key in {"type"}:
            continue
        if key in types:
            if isinstance(value, dict):
                cls = cls.new_type(
                    {k: get_class(v, types=types) for k, v in value.items()}, types[key]
                )
            else:
                cls = cls.new_type(value, types[key])
    return cls


@get_class.register(tuple)
@get_class.register(list)
def get_class_iter(schema, cls=EMPTY, types=EMPTY):
    return type(schema)(map(partial(get_class, types=types), schema))


class Literal(ForwardRef, _root=_root):
    # an overloaded forward reference method that allows both strings and literals.
    def __new__(cls, object):
        # only check string Forward References.
        if isinstance(object, str):
            self = ForwardRef.__new__(cls)
            return self
        return object

    def __init__(self, object):
        self.__forward_evaluated__ = True
        self.__forward_value__ = self.__forward_arg__ = self.__forward_code__ = object

    def _evaluate(self, force=False, globals=None, locals=None):
        return self.__forward_code__

    def __str__(self):
        return self.__forward_arg__

    __repr__ = __str__

    def __contains__(self, object):
        return object in self.__forward_value__

    def __repr__(self):
        return repr(self.__forward_value__)


# class Forward(ForwardRef, _root=_root):
#     # an overloaded forward reference method that allows both strings and literals.
#     def __new__(cls, object):
#         # only check string Forward References.
#         if isinstance(object, str):
#             self = ForwardRef.__new__(cls)
#             self.__init__(object)
#             return self
#         return object

#     def consent(self):
#         # it would be dangerous too allow any forward reference anytime.
#         # consent means that the end user has imported the namespace in sys.modules
#         # this will indicate consent
#         if isinstance(self.__forward_arg__, str):
#             module = self.__forward_arg__.partition(".")[0]
#             if module not in sys.modules:
#                 raise ConsentException(
#                     f"Import {module} to consent to making forward references to its attributes."
#                 )

#     def _evaluate(self, force=False, globals=None, locals=None):
#         if self.__forward_evaluated__:
#             return self.__forward_value__
#         if not globals or locals:
#             # we've redirected our interests to explicit forward reference off of sys.modules.
#             # no errors, just False exceptions
#             globals = locals = sys.modules
#         self.consent()
#         self.__forward_value__ = eval(self.__forward_code__, globals, locals)
#         self.__forward_evaluated__ = True
#         return self.__forward_value__

#     def object(self):
#         return self._evaluate()

#     __call__ = object

del _root


def get_first_builtin_type(cls):
    from . import Schemata

    for cls in reversed(inspect.getmro(cls)):
        if cls is object:
            continue
        if cls in vars(builtins).values():
            return cls
        if isinstance(cls, Schemata):
            break


def get_doctest(cls):
    import doctest
    import importlib

    doctest_suite = doctest.DocTestSuite()
    test_case = doctest.DocTestParser().get_doctest(
        inspect.getdoc(cls) or "",
        vars(importlib.import_module(cls.__module__)),
        cls.__module__,
        cls.__module__,
        1,
    )
    test_case.examples and doctest_suite.addTest(
        doctest.DocTestCase(test_case, doctest.ELLIPSIS)
    )
    return doctest_suite
