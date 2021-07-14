"""the basis of schemata that begins defining the type system"""

import abc
import builtins
import collections
import functools
import importlib
import weakref


import functools
import collections

from . import builders, exceptions, mixins, utils, data
from .utils import ANNO, DOC, EMPTY, JSONSCHEMA_SCHEMATA_MAPPING

__all__ = ("Schemata",)


class Schemata(mixins.TypeOps, abc.ABCMeta):
    """a schemaful python type"""

    __annotations__ = utils.merge(data.applicator, data.validation, data.meta_data)
    __validators__ = collections.defaultdict(
        functools.partial(collections.defaultdict, weakref.WeakValueDictionary)
    )
    __types__ = collections.defaultdict(
        functools.partial(collections.defaultdict, weakref.WeakValueDictionary)
    )

    def __new__(cls, name, bases, dict, **annotations):
        dict.setdefault("__annotations__", {})
        dict.update(
            __is_validator__="validator" in dict,
            __is_specification__=bool(annotations),
        )
        dict["__annotations__"].update(annotations)

        if not dict["__is_specification__"]:
            is_object = any(issubclass(x, builtins.dict) for x in bases)
            is_array = any(issubclass(x, (list, set, tuple)) for x in bases)
            if is_object or is_array:
                new = builders.NsBuilder(dict).build()
                if new is not type:
                    bases = bases + (new,)
        return super().__new__(cls, name, bases, dict)

    def value(cls, *key, default=EMPTY):
        """get the corresponding value to the class key"""
        for k in key:
            if isinstance(k, type):
                k = k.__key__

            if k in cls.__annotations__:
                v = cls.__annotations__[k]
                if isinstance(v, utils.Literal):
                    v = str(v)
                return v

        return default

    def __enter__(cls):
        setattr(cls, "_hold_validation", getattr(cls, "_hold_validation", 0))
        cls._hold_validation += 1
        return cls

    def __exit__(cls, *e):
        cls._hold_validation -= 1

    @property
    def __doc__(cls):
        return builders.NumPyDoc(cls).build()

    def __instancecheck__(cls, object):
        if type.__instancecheck__(cls, object):
            return True
        if cls.__annotations__:
            try:
                cls.validate(object)
            except:
                return False
            return True
        return False

    def verified(cls, *args, **kwargs):
        with cls:
            return cls(*args, **kwargs)

    def audit(cls, object, max=10):
        """audit the object against a class returning multiple failures"""
        exception = exceptions.ValidationException(cls, items=max)
        with utils.suppress(BaseException):
            exception.validate(object)
        return exception

    def cast(cls, *args, **kwargs):
        self = cls.verified(*args, **kwargs)
        self.validate(self)
        return self

    def type(cls, *bases, **kwargs):
        if utils.IN_SPHINX:
            kwargs.update(
                {
                    k: utils.Literal(v) if isinstance(v, str) else v
                    for k, v in kwargs.items()
                }
            )
        return type(cls.__name__, bases + (cls,), {}, **kwargs)

    def schema(cls, ravel=None):
        return utils.get_schema(cls, ravel=ravel)

    def validate(cls, object):
        if not getattr(cls, "_hold_validation", 0):
            exceptions.ValidationException(cls).validate(object)
        return object

    @property
    def __signature__(cls):
        return builders.SignatureExporter(cls).build()

    def from_key(cls, key, value=EMPTY):
        from .types import Any

        name = utils.format_capital_key(key)

        data = Schemata.__types__[key]
        v = next(mixins.get_hashable(value))

        nah = hash(EMPTY)
        if nah not in data:
            data[nah] = type(name, (cls,), dict(__key__=key))

        if v not in data:
            return Schemata.register_schemata_types(
                type(name, (data[nah],), {}, **{key: value})
            )
        return data[v]

    def _ep(cls, key, name, *args, **kwargs):
        import importlib.metadata

        for ep in importlib.metadata.entry_points()[key]:
            if name == ep.name:
                return get_import(ep.value)(*args, **kwargs)

        raise AttributeError(f"Schemata has no attribute from_{name}")

    from_ = functools.partialmethod(_ep, "schemata.from")
    to_ = functools.partialmethod(_ep, "schemata.to")

    @classmethod
    def from_alias(cls, object):
        for ep in importlib.metadata.entry_points().get("schemata.schema", []):
            if object == ep.name:
                return get_import(ep.value)

    def register_schemata_types(cls):
        k = cls.__key__
        setattr(Schemata, cls.__name__, cls)
        Schemata.__types__[k][next(mixins.get_hashable(Schemata.value(cls, k)))] = cls
        return cls


def get_import(str):
    name, _, str = str.partition(".")
    object = __import__(name)
    while str:
        tmp, _, str = str.partition(".")
        name += "." + tmp
        if hasattr(object, tmp):
            object = getattr(object, tmp)

        else:
            object = importlib.import_module(name)
    return object
