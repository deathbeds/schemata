from .utils import EMPTY, enforce_tuple, get_default

from . import utils
from .types import Any, Type

__all__ = "Cast", "Do", "Juxt", "Callable"


class Cast(Any):
    @classmethod
    def preprocess(cls, *args, **kwargs):
        args = utils.enforce_tuple(cls.value(Callable.Args, default=())) + args
        kwargs = {**cls.value(Callable.Kwargs, default={}), **kwargs}

        cast = cls.value(Cast)
        if cast:
            if cast is not True:
                for callable in utils.enforce_tuple(cast):
                    args, kwargs = (callable(*args, **kwargs),), {}
        return args[0]

    class Return(Any):
        ...

    class Args(Any):
        pass

    class Kwargs(Any):
        pass


class Callable(Cast):
    @classmethod
    def validator(cls, object):
        assert callable(object), f"{object} is not callable"

    def __class_getitem__(cls, object):
        if isinstance(object, tuple):
            if len(object) is 1:
                cls += Cast[object[0]]
            if len(object) is 2:
                cls += Callable.Return[object[1]]

        return super().__class_getitem__(enforce_tuple(object))


class Do(Cast):
    def __new__(cls, *args, **kwargs):
        super().__new__(cls, *args, **kwargs)
        if args:
            return args[0]


class Juxt(Type):
    @classmethod
    def call(cls, *args, **kwargs):
        from .utils import enforce_tuple

        args = (cls.value(Callable.Args) or ()) + args
        kwargs = {**(cls.value(Callable.Kwargs) or {}), **kwargs}

        for callable in enforce_tuple(cls.value(Cast)):
            args, kwargs = (callable(*args, **kwargs),), {}
        return args[0]
