import abc
import builtins
import collections
import functools
import importlib
import inspect
import itertools
import typing
from contextlib import suppress
from functools import partial
from functools import singledispatch as register
from unittest import TestCase

testing = TestCase()
Path = type(__import__("pathlib").Path())
import jsonref
import jsonschema

testing = TestCase()
merge = lambda x: collections.ChainMap(
    *(getattr(y, "__annotations__", {}) for y in x.__mro__)
)

import collections
import enum


class Kind(enum.Enum):
    object = "object"
    int = "int"
    float = "float"
    str = "str"
    tuple = "tuple"
    dict = "dict"


def validates(*types):
    def decorator(callable):
        @functools.wraps(callable)
        def main(cls, object):
            isinstance(object, types) and callable(cls, object)

        return classmethod(main)

    return decorator


def filter_py(x):
    return tuple(
        x
        for x in inspect.getmro(x)
        if not isinstance(x, Definition)
        and x is not object
        and not x.__name__.startswith("abc.")
    )


def enforce_tuple(x):
    if not isinstance(x, tuple):
        return (x,)
    return x


class ValidationError(AssertionError):
    def __init__(self, *args, **kw):
        super().__init__(*args)
        kw.setdefault("exceptions", [])
        for k, v in kw.items():
            setattr(self, k, v)

    def __str__(self):
        import pprint

        if self.exceptions:
            return pprint.pformat(self.exceptions)
        return super().__str__()

    def __enter__(self):

        return

    def __exit__(self, type, exception, traceback):
        if type is exception is traceback is None:
            return
        self.exceptions += (exception,)

    def raises(self):
        if self.exceptions:
            raise self
        return self


def lowercase(s):
    if s.endswith("_" * 2):
        return "@" + lowercase(s[:-1])
    if s.endswith("_"):
        return "$" + lowercase(s[:-1])
    return s[0].lower() + s[1:]


ANNO, NAME = "__annotations__", "__name__"


def is_basic(x):
    if x is object:
        return True
    if len(inspect.getmro(x)) is 2:
        return True
    return False


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


class Definition(abc.ABCMeta):
    """a Definition type that is used to build type definitions."""

    def __new__(cls, name, bases, dict, **kwargs):
        if ANNO in dict:
            # we treat annotations as schema properties for dicts and lists
            property = Properties[dict.pop(ANNO)]
            if any(issubclass(x, List) for x in bases):
                property = Items[Dict + property]
            bases += (property,)

        doc = dict.pop("__doc__", None)
        if doc:
            bases += (Description[doc],)

        dict.setdefault("__doc__", None)

        # initialize empty annotations on every class
        dict.setdefault(ANNO, {})
        # define the kind of type properties
        dict.setdefault("kind", kwargs.pop("kind", Kind.object))

        # define the rank for sorting the subclasses
        dict.setdefault("rank", kwargs.pop("rank", 10000))

        # collection any type definitions in the class
        definitions = []
        for v in dict.values():
            if isinstance(v, Definition):
                definitions += (v,)

        if definitions:
            bases += (Definitions[{x: x for x in definitions}],)

        bases = tuple(sorted(bases, key=lambda x: getattr(x, "rank", 100000)))

        cls = super().__new__(cls, name, bases, dict, **kwargs)
        return cls

    @property
    def created(cls) -> bool:
        """are there annotations defined on the type"""
        return any(cls.__annotations__)

    def key(cls):
        """get the corresponding key to the class"""
        return lowercase(cls.__name__)

    def value(cls, *key):
        """get the corresponding value to the class key"""
        if not key:
            key = (cls.key(),)

        for k in key:
            if isinstance(k, type):
                k = k.key()
            if k in cls.__annotations__:
                return cls.__annotations__[k]

    def py(cls):
        types = ()
        for t in inspect.getmro(cls):
            if (
                not isinstance(t, Definition)
                and t is not object
                and t not in {Mixin.Literal, TestCase}
            ):
                types += (t,)
        if not types:
            for dump in abc._get_dump(cls):
                if isinstance(dump, set) and dump:
                    types += (next(iter(dump))(),)
        if types:
            return typing.Union[types]

    def type(cls, *object, extras=None):
        kw = dict(define=True)
        bases = (cls,) + tuple(extras or tuple())
        if object:
            object = object[0]

            if cls.kind == Kind.tuple and not isinstance(object, tuple):
                object = (object,)
            elif cls.kind == Kind.dict and not isinstance(object, dict):
                object = dict(object)
            if not isinstance(object, getattr(builtins, cls.kind.value)):
                raise BaseException("Invalid type definition")
            kw["value"] = object
            # if isinstance(object, type):
            #     return type(cls.__name__, (object,)+ (cls,), {})
        return type(cls.__name__, bases, {}, **kw)

    def __add__(cls, object):
        """combine two classes"""
        return Combined[cls, object]

    __and__ = __add__

    def __or__(cls, object):
        return AllOf[cls, object]

    def __xor__(cls, object):
        return OneOf[cls, object]

    def __pos__(cls):
        return cls

    def __neg__(cls):
        return Not[cls]


@register
def get_schema(x, *, ravel=True):
    return x


@get_schema.register
def get_schema_type(x: Definition, *, ravel=True):
    return get_schema(x.__annotations__, ravel=ravel)


@get_schema.register
def get_schema_dict(x: dict, *, ravel=True):
    object = {k: get_schema(v, ravel=ravel) for k, v in x.items()}
    return object


@get_schema.register
def get_schema_dict(x: tuple, *, ravel=True):
    return tuple(get_schema(x, ravel=ravel) for x in x)


class Type(metaclass=Definition):
    def __new__(cls, *object):
        if object:
            cls.validate(*object)
        return super().__new__(cls, *object)

    @classmethod
    def object(cls, object):
        cls.validate(object)
        return cls(object)

    def __init_subclass__(cls, value=None, define=None):
        if define:
            cls.__annotations__[cls.key()] = value
        else:
            cls.__annotations__.update(dict(merge(cls)))

        cls.__doc__ = get_docstring(cls)

    @classmethod
    def schema(cls, ravel=False):
        return get_schema(cls, ravel=ravel)

    @classmethod
    def validator(cls, object):
        types = cls.py()
        if types:
            testing.assertIsInstance(object, types)

    @classmethod
    def validate(cls, object: typing.Any) -> None:
        exception = ValidationError()
        for t in inspect.getmro(cls):
            if getattr(t, "created", None):
                with exception:
                    t.validator(object)
        exception.raises()

    def __class_getitem__(cls, object):
        return cls.type(object)


class Title(Type, kind=Kind.str):
    pass


class Description(Type, kind=Kind.str):
    pass


class Default(Type, rank=-1):
    def __new__(cls, *object):
        if not object:
            object = (cls.value(Default, Const),)
        return super().__new__(cls, *object)


class Const(Default):
    @classmethod
    def validator(cls, object):
        value = cls.value(Const)
        if value is not None:
            testing.assertEqual(object, value)


class Combined(Type):
    def __class_getitem__(cls, object):
        object = enforce_tuple(object)
        return type(Type.__name__, object, dict(), define=False)


class Composite(Type):
    def __new__(cls, object=inspect._empty):
        return cls.validator(object)


class Not(Composite, rank=-10000):
    @classmethod
    def validator(cls, object):
        value = cls.value(Not)
        try:
            value.validate(object)
        except AssertionError:
            return object
        assert False, f"{object} is an instance of {value}"


class AllOf(Composite, kind=Kind.tuple):
    @classmethod
    def validator(cls, object):
        exception = ValidationError()
        for type in cls.value(AllOf) or []:
            with exception:
                type.validate(object)
        exception.raises()
        return object


class AnyOf(Composite, kind=Kind.tuple):
    @classmethod
    def validator(cls, object):
        exceptions = ValidationError()
        for type in cls.value(AnyOf) or []:
            with exceptions:
                type.validate(object)
                return object
        raise exceptions.raises()


class OneOf(Composite, kind=Kind.tuple):
    @classmethod
    def validator(cls, object):
        found = False
        for type in cls.value(OneOf) or []:
            try:
                type.validator(object)
                if found:
                    raise ValidationError(
                        "object is more than one type", parent=cls, exceptions=[]
                    )
                found = False
            except BaseException as error:
                pass
        if found:
            return object
        raise ValidationError("not one of", exceptions=[], parent=cls)


class Mixin:
    class Literal:
        rank = -10

        def __class_getitem__(cls, object):
            return cls.type(Default[object])


class Null(Type["null"], Mixin.Literal):
    def __new__(cls, *object):
        object = object or (None,)
        cls.validate(*object)


Null.register(type(None))


class Bool(Type["boolean"], Mixin.Literal):
    def __class_getitem__(cls, object):
        return Const[object] + cls

    def __new__(cls, *object):
        object = object or (bool(),)
        cls.validate(*object)
        return object[0]


Bool.register(bool)


class Integer(Type["integer"], int, Mixin.Literal):
    @classmethod
    def validator(cls, object):
        testing.assertNotIsInstance(object, bool)
        super().validator(object)


class Float(Type["number"], float, Mixin.Literal):
    pass


class String(Type["string"], str, Mixin.Literal):
    pass


class Items(Type):
    @classmethod
    def validator(cls, object):
        value = cls.value(Items)
        if value:
            if isinstance(value, (tuple, list)):
                for i, (x, y) in enumerate(zip(value, object)):
                    x.validate(y)
                other = cls.value(AdditionalItems)
                if other:
                    for x in other[i:]:
                        other.validate(x)
            else:
                for i, x in enumerate(object):
                    value.validate(x)


class List(Type["array"], list):
    def __class_getitem__(cls, object):
        if isinstance(object, dict):
            object = Dict + Properties[object]
        if isinstance(object, tuple):
            return Tuple + Items[object]
        return cls + Items[object]

    @classmethod
    def object(cls, object):
        cls.validate(object)
        self = list.__new__(cls)
        list.__init__(self, object)
        return self


class Tuple(Type["array"], tuple):
    def __class_getitem__(cls, object):
        return cls + Items[object]

    @classmethod
    def object(cls, object):
        cls.validate(object)
        self = tuple.__new__(cls)
        tuple.__init__(self, object)
        return self


class AdditionalProperties(Type):
    pass


class Dict(Type["object"], dict, kind=Kind.dict):
    def __class_getitem__(cls, object):
        if isinstance(object, dict):
            return cls + Properties[object]
        elif isinstance(object, tuple):
            return cls + Required[object]
        return cls + AdditionalProperties[object]

    @classmethod
    def object(cls, object):
        cls.validate(object)
        self = dict.__new__(cls)
        dict.__init__(self, object)
        return self


class Enum(Type, kind=Kind.tuple):
    pass


class Examples(Type, kind=Kind.tuple):
    pass


class Dependencies(Type, kind=Kind.dict):
    @validates(dict)
    def validator(cls, object):
        for k, v in (cls.value(Dependencies) or {}).items():
            if k in object:
                missing = list(v)
                for x in list(missing):
                    if x in object:
                        missing.remove(x)
                if missing:
                    assert missing, f"{k} key requires missing keys {missing}"


class Properties(Type, kind=Kind.dict):
    @validates(dict)
    def validator(cls, object):
        if isinstance(object, dict):
            for k, v in (cls.value(Properties) or {}).items():
                if k in object:
                    v.validate(object[k])


class Comment_(Type, kind=Kind.str):
    pass


class Test(Type):
    @classmethod
    def run(cls, exit=False, **kw):
        import importlib
        import unittest

        name = cls.value() or "__main__"
        module = importlib.import_module(name)
        setattr(module, "load_tests", cls.load_tests)
        return unittest.main(name, argv=["discover"], exit=exit, **kw)

    @classmethod
    def load_tests(cls, loader, tests, ignore):
        import doctest

        tests.addTests(
            doctest.DocTestSuite(importlib.import_module(cls.value() or "__main__"))
        )
        return tests


class ContentMediaType(Type):
    def _repr_mimebundle_(self, include=None, exclude=None):
        return {type(self).value(ContentMediaType): self}, {}


class ContentEncoding(Type):
    pass


class Image(ContentEncoding["base64"], String):
    def __new__(cls, object):
        import base64

        if isinstance(object, bytes):
            object = base64.b64encode(object).decode()
        return super().__new__(cls, object)


class Png(ContentMediaType["image/png"], Image):
    pass


class Jpeg(ContentMediaType["image/jpeg"], Image):
    pass


class Markdown(String, ContentMediaType["text/markdown"]):
    pass


class Pattern(String):
    def __class_getitem__(cls, object):
        import re

        return Type.__class_getitem__.__func__(cls, re.compile(object))

    @validates(str)
    def validator(cls, object):
        value = cls.value(Pattern)
        if isinstance(value, typing.Pattern):
            testing.assertRegex(object, value)


def not_format(cls, object):
    cls = type(object)
    return f"{object} is not a validate {cls.value()} format."


class Format(Type):
    pass


class Uri(Format["uri"], String):
    @validates(str)
    def validator(cls, object):
        import rfc3986

        assert rfc3986.uri_reference(object).validator(require_scheme=True), not_format(
            cls, object
        )


class UriReference(Format["uri-reference"], Uri):
    pass


class Dir(Type, Path):
    pass


class File(Type, Path):
    pass


class Email(Format["email"]):
    pass


class MinLength(Type, kind=Kind.int):
    @validates(list, tuple)
    def validator(cls, object):
        if isinstance(object, str):
            testing.assertGreaterEqual(len(object), cls.value(MinLength))


class MaxLength(Type, kind=Kind.int):
    @validates(list, tuple)
    def validator(cls, object):
        if isinstance(object, str):
            testing.assertLessEqual(len(object), cls.value(MaxLength))


class Regex(Format["regex"], String):
    @validates(str)
    def validator(cls, object):
        import re

        re.compile(object)


class MultipleOf(Type, kind=Kind.float):
    @validates(int, float)
    def validator(cls, object):
        if isinstance(object, (int, float)):
            value = cls.value(MultipleOf)
            assert not object % value, f"{object} is not a multiple of {value}"


class Minimum(Type, kind=Kind.float):
    @validates(int, float)
    def validator(cls, object):
        if isinstance(object, (int, float)):
            testing.assertGreaterEqual(object, cls.value(Minimum))


class Maximum(Type, kind=Kind.float):
    @validates(int, float)
    def validator(cls, object):
        if isinstance(object, (int, float)):
            testing.assertLessEqual(object, cls.value(Maximum))


class ExclusiveMinimum(Type, kind=Kind.float):
    @validates(int, float)
    def validator(cls, object):
        if isinstance(object, (int, float)):
            testing.assertGreater(object, cls.value(ExclusiveMinimum))


class ExclusiveMaximum(Type, kind=Kind.float):
    @validates(int, float)
    def validator(cls, object):
        if isinstance(object, (int, float)):
            testing.assertLess(object, cls.value(ExclusiveMaximum))


class Contains(Type):
    pass


class AdditionalItems(Type):
    pass


class MinItems(Type, kind=Kind.int):
    @validates(list)
    def validator(cls, object):
        if isinstance(object, (tuple, list)):
            testing.assertGreaterEqual(len(object), cls.value(MinItems))


class MaxItems(Type, kind=Kind.int):
    @validates(list)
    def validator(cls, object):
        if isinstance(object, (tuple, list)):
            testing.assertLessEqual(len(object), cls.value(MaxItems))


class UniqueItems(Type):
    pass


class AdditionalProperties(Type):
    pass


class PropertyNames(Type):
    pass


class MinProperties(Type, kind=Kind.int):
    @validates(dict)
    def validator(cls, object):
        if isinstance(object, str):
            testing.assertGreaterEqual(len(object), cls.value(MinProperties))


class MaxProperties(Type, kind=Kind.int):
    @validates(dict)
    def validator(cls, object):
        if isinstance(object, str):
            testing.assertLessEqual(len(object), cls.value(MaxProperties))


class PatternProperties(Type, kind=Kind.dict):
    pass
