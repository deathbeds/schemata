import functools
import typing

from . import base as B
from . import literal as P


class Function(P.Py):
    # this is used as an instance, not a type, it falls back to pipe
    @classmethod
    def new_type(cls, x):
        if not isinstance(x, tuple):
            x = (x,)

        return cls.append(x)

    @classmethod
    def instance(cls, *args):
        self = super().instance()
        self.value = tuple(args)
        return self

    def append(*args):
        if not args:
            return Function()
        self, *args = args

        if issubclass(type(self), Function):
            self.value += tuple(args)
            return self
        return Function().append(*args)

    __add__ = __sub__ = __getitem__ = __rshift__ = append

    def map(self, value):
        return self.append(functools.partial(map, value))

    __mul__ = __imul__ = map

    def filter(self, value):
        return self.append(functools.partial(filter, value))

    __truediv__ = __itruediv__ = filter

    def reduce(self, value):
        init = None
        if isinstance(value, tuple):
            value, init = value
        if init:
            return self.append(lambda x: functools.reduce(value, x, init))
        return self.append(functools.partial(functools.reduce, value))

    __floordiv__ = reduce

    def groupby(self, value):
        import itertools

        return self.append(
            lambda v: {x: list(y) for x, y in itertools.groupby(v, value)}
        )

    __matmul__ = groupby

    def do(self, object):
        return self.append(Do[Juxt[object]])

    __lshift__ = do

    def iff(self, object):
        p = object
        if isinstance(object, (tuple, type)):
            p = lambda x: isinstance(x, object)
        return Iff[self.append(p)]

    def ifthen(self, object):
        return IfThen[self, object]

    def ifnot(self, object):
        return IfNot[self, object]

    def excepts(self, object):
        return Excepts[self, object]

    def complement(self):
        return Function(Not[self])

    def pipe(self):
        return P.Cast[self.value]

    def __call__(self, *args, **kwargs):
        return self.pipe()(*args, **kwargs)


class X(BaseException):
    def __bool__(self):
        return False


class Conditional:
    @classmethod
    def new_type(cls, object):
        p, v = object, tuple()
        if isinstance(p, tuple):
            p, v, *_ = p
        cls = super().new_type(object)
        cls.predicate, cls.value = p, v
        return cls

    @classmethod
    def instance(cls, *args, **kwargs):
        args = cls.default(*args)
        return B.call(cls.predicate, *args, **kwargs)


class Iff(Conditional, Function):
    @classmethod
    def instance(cls, *args, **kwargs):
        x = super().instance(*args, **kwargs)
        if x:
            return B.call(cls.value, *args, **kwargs)
        return args[0]


class IfThen(Conditional, Function):
    @classmethod
    def instance(cls, *args, **kwargs):
        x = super().instance(*args, **kwargs)
        if x:
            return B.call(cls.value, x)
        return args[0]


class IfNot(Conditional, Function):
    @classmethod
    def instance(cls, *args, **kwargs):
        x = super().instance(*args, **kwargs)
        if x:
            return args[0]
        return B.call(cls.value, *args, **kwargs)


class Excepts(Conditional, P.Instance):
    @classmethod
    def instance(cls, *args, **kwargs):
        try:
            return super().instance(*args, **kwargs)
        except cls.value or () as e:
            return X(e)


class Not(P.Instance):
    @classmethod
    def instance(cls, *args, **kwargs):
        return not cls.instance(*args, **kwargs)
