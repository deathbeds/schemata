"mixins.py"
from unittest.signals import installHandler

from . import utils
from .utils import EMPTY


class TypeOps:
    def __add__(cls, *object, **kwargs):
        return type(cls.__name__, (cls,) + object, {})

    add = __add__

    def __radd__(cls, *object):
        return type(cls.__name__, object + (cls,), {})

    def __pos__(cls):
        return cls

    def __neg__(cls):
        from . import Not

        return Not[cls]

    not_ = __neg__

    def __and__(cls, *object):
        from . import AllOf

        return AllOf[(cls,) + object]

    and_ = __and__

    def __or__(cls, *object):
        from . import AnyOf

        return AnyOf[(cls,) + object]

    or_ = __or__

    def __xor__(cls, *object):
        from . import OneOf

        return OneOf[(cls,) + object]

    xor = __xor__

    def __rshift__(cls, object):
        return cls.cast(object)

    def __rrshift__(cls, object):
        from .callables import Cast

        return Cast[object, cls]

    def __lshift__(cls, object):
        from .callables import Do

        return cls >> Do[object]

    do = __lshift__

    def __rlshift__(cls, object):
        from .callables import Do

        return Do[object] >> cls

    def __eq__(cls, object):
        from .types import Schemata

        if isinstance(object, Schemata):
            return int.__eq__(*map(hash, (cls, object)))
        return super().__eq__(object)

    eq = __eq__

    def __hash__(cls):
        return hash(utils.get_hashable(cls))

    hash = __hash__

    def __getattr__(cls, str):
        try:
            return object.__getattribute__(cls, str)
        except AttributeError as e:
            error = e
        if str[0].islower():
            name = utils.uppercase(str)
            if hasattr(cls, name):

                def caller(*args, **kw):
                    if kw:
                        args, kw = (dict(*args, **kwargs),), {}
                    nonlocal cls
                    object = getattr(cls, name)
                    if not args:
                        cls += object
                    elif len(args) == 1:
                        cls += object[args[0]]
                    else:
                        cls += object[args]

                    return cls

                return caller
        raise error

    getattr = __getattr__

    def __dir__(cls):
        object = super().__dir__()
        return object + [
            k[0].lower() + k[1:]
            for k in object
            if k[0].isupper() and isinstance(getattr(cls, k), type)
        ]

    dir = __dir__


class BoolItem:
    def __class_getitem__(cls, object=EMPTY):
        if object is EMPTY:
            object = True
        return super().__class_getitem__(object)


class TupleItem:
    def __class_getitem__(cls, object=EMPTY):
        if isinstance(object, str):
            object = object.split()
        if isinstance(object, (list, set)):
            object = tuple(object)
        return super().__class_getitem__(object)


class DictItem:
    def __class_getitem__(cls, *args, **kwargs):
        args, kwargs = (dict(*args, **kwargs),), {}
        return super().__class_getitem__(*args)


class Array:
    def map(self, callable, *args, **kwargs):
        from . import Any, List, Schemata

        cls = type(self)
        if isinstance(callable, Schemata):
            return cls[callable].cast((callable(x, *args, **kwargs) for x in self))
        return List.cast(callable(x, *args, **kwargs) for x in self)

    def filter(self, callable, *args, **kwargs):
        from .types import Any, Schemata

        cls = type(self)
        return Any(cls((x for x in self if callable(x, *args, **kwargs))))

    def dataframe(self, *args, **kwargs):
        import pandas

        return pandas.DataFrame(self, *args, **kwargs)

    def series(self, *args, **kwargs):
        import pandas

        return pandas.Series(self, *args, **kwargs)

    def append(self, *args):
        list.append(self, *args)
        return self

    def extend(self, *args):
        list.extend(self, *args)
        return self

    def insert(self, *args):
        list.insert(self, *args)
        return self

    def remove(self, *args):
        list.remove(self, *args)
        return self

    def clear(self, *args):
        list.clear(self, *args)
        return self

    def sum(self, start=0):
        from .arrays import List

        if isinstance(start, str):
            from .strings import String

            # usually strings fail to sum on strings.
            return String(start.join(self))
        return List(sum(self, start))

    def sort(self, inplace=True, key=EMPTY, reverse=EMPTY):
        if inplace:
            self.sort(key=key or None, reverse=key or False)
        return type(self).verified(
            [sorted(self, key=EMPTY or None, reverse=EMPTY or False)]
        )

    def __getitem__(self, object):
        if isinstance(object, slice):
            try:
                return super().__getitem__(object)
            except TypeError as e:
                if any(map(callable, (object.start, object.stop, object.step))):
                    if object.start is not None:
                        self = self.filter(object.start)
                    if object.stop is not None:
                        self = self.map(object.start)
                    if object.step is not None:
                        self = self.pipe(object.step)
                    return self
                raise e


class Bunch:

    # only called if k not found in normal places
    def __getattr__(self, k):
        try:
            return object.__getattribute__(self, k)
        except AttributeError:
            try:
                return self[k]
            except KeyError:
                raise AttributeError(k)

    def __setattr__(self, k, v):
        try:
            object.__getattribute__(self, k)
        except AttributeError:
            try:
                self[k] = v
            except:
                raise AttributeError(k)
        else:
            object.__setattr__(self, k, v)

    def __delattr__(self, k):
        try:
            object.__getattribute__(self, k)
        except AttributeError:
            try:
                del self[k]
            except KeyError:
                raise AttributeError(k)
        else:
            object.__delattr__(self, k)
