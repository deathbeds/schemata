from schemata.utils import enforce_tuple, get_default

from .types import Any, Type

__all__ = "Callable", "Compose", "Juxt"


class Callable(Type):
    def __class_getitem__(cls, object):
        if isinstance(object, tuple):
            return cls + Callable.Funcs[object[0]] + Callable.Args[object[1:]]
        elif isinstance(object, dict):
            return cls + Callable.Kwargs[object]
        return cls + Callable.Funcs[object]

    @classmethod
    def is_valid(cls, object):
        assert callable(object), "{object} is not callable"

    def __new__(cls, *args, **kwargs):
        from .utils import enforce_tuple

        args = enforce_tuple(cls.value(Callable.Args, default=())) + args
        kwargs = {**cls.value(Callable.Kwargs, default={}), **kwargs}

        for callable in enforce_tuple(cls.value(Callable.Funcs)):
            args, kwargs = (callable(*args, **kwargs),), {}
        return args[0]

    class Funcs(Any):
        pass

    class Args(Any):
        pass

    class Kwargs(Any):
        pass


class Compose(Callable):
    def __class_getitem__(cls, object):
        return cls + Callable.Funcs[enforce_tuple(object)]


class Juxt(Type):
    def __new__(cls, *args, **kwargs):
        from .utils import enforce_tuple

        args = (cls.value(Callable.Args) or ()) + args
        kwargs = {**(cls.value(Callable.Kwargs) or {}), **kwargs}

        for callable in enforce_tuple(cls.value(Callable.Funcs)):
            args, kwargs = (callable(*args, **kwargs),), {}
        return args[0]
