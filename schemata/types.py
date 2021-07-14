"""the basis of schemata that begins defining the type system"""

import abc
import builtins
import collections
import enum
import functools
import inspect
import os
import importlib
from re import S
import typing
import sys
import weakref


import functools
import collections

from numpy.lib.arraysetops import isin
import schemata
from .schemata import Schemata
from . import builders, exceptions, mixins, utils, data, meta

from .utils import ANNO, DOC, EMPTY, get_hashable

__all__ = ("Any", "Bool", "Const", "Enum", "Envvar", "Any", "Schemata", "Null", "Type")


class Any(mixins.Methods, metaclass=Schemata):
    def __init_subclass__(cls):
        cls.__annotations__ = utils.merge(
            *(
                x.__annotations__.copy()
                for x in cls.__mro__
                if hasattr(x, "__annotations__")
                and x.__annotations__ is not Schemata.__annotations__
            ),
        )
        k = getattr(cls, "__key__", None)
        if k is not None:
            if not cls.__annotations__ or cls.__is_validator__:
                cls.register_schemata_types()

    def __new__(cls, *args, **kwargs):
        if issubclass(cls, dict):
            args, kwargs = (dict(*args, **kwargs),), {}
        if not args:
            default = utils.get_default(cls)
            if default is not EMPTY:
                args = (default,)
        if args:
            cls.validate(*args[:1])
        else:
            return super(Any, cls).__new__(cls, *args, **kwargs)

        if utils.get_first_builtin_type(cls):
            return super(Any, cls).__new__(cls, *args, **kwargs)
        else:
            if args:
                t = meta.meta_types.__types__.get(type(*args[:1]))
                if t is not None:
                    return Type[t.__name__].verified(*args, **kwargs)

        return args[0] if args else None

    def __class_getitem__(cls, object):
        return Schemata.from_key(cls, cls.__key__, object)

    @classmethod
    def schema(cls, ravel=None):
        return Schemata.schema(cls, ravel)

    @classmethod
    def validate(cls, object):
        return Schemata.validate(cls, object)


tuple(map(Any.from_key, Schemata.__annotations__["properties"]))


class Type(Any.from_key("type")):
    @classmethod
    def validator(cls, object, *types):
        for x in utils.enforce_tuple(Schemata.value(cls, "type")):
            if isinstance(x, type):
                types += (x,)
            elif x in meta.types.__dict__:
                types += (meta.types.__dict__[x],)
        exceptions.assertIsInstance(object, types)


class Const(Any.from_key("const")):
    @classmethod
    def validator(cls, object):
        """
        >>> Const[1](1)
        1
        """
        exceptions.assertEqual(object, cls.value(Const))


@Schemata.register_schemata_types
class Null(Type["null"]):
    def __new__(cls, *args, **kwargs):
        cls.validate(*args or (None,))


Null.register(type(None))


@Schemata.register_schemata_types
class Bool(Type["boolean"], int):
    def __new__(cls, *args, **kwargs):
        return bool(super().__new__(cls, *args, **kwargs))


Bool.register(bool)


class Enum(Any.from_key("enum")):
    def __new__(cls, object=EMPTY):
        enum = cls.value(Enum)
        if object is EMPTY:
            object = next(iter(enum.__members__))
        return enum(object)

    def __class_getitem__(cls, object):
        """
        >>> Enum["a b"].schema(1)
        {'enum': ['a', 'b']}

        >>> Enum[1, 2].schema(1)
        {'enum': ['1', '2']}

        >>> Enum[dict(a=1, b=2)].schema(1)
        {'enum': ['a', 'b']}

        >>> Integer.enum((1, 2)).schema(1)
        {'type': 'integer', 'enum': ['1', '2']}
        """
        if isinstance(object, str) and object:
            object = tuple(object.split())
        if not isinstance(object, dict):
            object = utils.enforce_tuple(object)
            object = dict(zip(map(str, object), object))
        return super().__class_getitem__(utils.make_enum(cls, object))

    @classmethod
    def validator(cls, object):
        Schemata.value(cls, Enum)(object)
        return object


class Envvar(Any.from_key("envvar")):
    def __new__(cls, *args, **kwargs):
        return os.getenv(Schemata.value(cls, Envvar))

    @classmethod
    def list(cls):
        return list(os.environ)
