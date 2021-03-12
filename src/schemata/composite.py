from . import base as B
from . import literal as L
from . import literal as P


class Composite(L.Literal):
    """a schemaless alias type mixin, the name of the class is used to derive others"""

    @classmethod
    def validate(cls, object):
        # composites use the instance creation for typing checking
        return cls.instance(object)


class Nested:
    @classmethod
    def new_type(cls, object):
        # post process the created type to avoid nesting in the
        # schema representation.
        self = super().new_type(object)
        s = self.schema(0)
        n = cls.alias()
        order = []
        for x in s[n]:
            if isinstance(x, type) and issubclass(x, cls):
                order += x.schema(0)[n]
            elif x not in order:
                order.append(x)
        self.__annotations__[n] = order
        return self

    @classmethod
    def _attach_parent(cls, x):
        import typing

        if isinstance(x, typing.Hashable):
            if x not in {None, True, False}:
                # we can't modify values that aren't ours
                x.parent = cls
        else:
            x.parent = cls
        return x


class AnyOf(Nested, Composite, B.Generic.Plural):
    @classmethod
    def instance(cls, *args):
        import typing

        args = cls.default(*args)
        schema = cls.schema(False)
        p = schema[AnyOf.alias()]
        for t in p:
            try:
                x = B.call(t, *args)
                return cls._attach_parent(x)
            except B.ValidationErrors:
                if t is p[-1]:
                    raise B.ValidationError()


class AllOf(Nested, Composite, B.Generic.Plural):
    @classmethod
    def instance(cls, *args):

        args = cls.default(*args)
        schema = cls.schema(False)
        result = {}
        for t in schema[AllOf.alias()]:
            result.setdefault("x", B.call(t, *args))

        x = result.get("x", args[0])

        return cls._attach_parent(x)


class OneOf(Nested, Composite, B.Generic.Plural):
    @classmethod
    def instance(cls, *args, **kwargs):
        args = cls.default(*args)
        schema = cls.schema(False)
        i, x = 0, None
        for t in schema[OneOf.alias()]:
            try:
                if i:
                    B.call(t, *args, **kwargs)
                else:
                    x = B.call(t, *args, **kwargs)
                i += 1
            except B.ValidationErrors as e:
                continue

            if i > 1:
                break

        if i == 1:
            return cls._attach_parent(x)

        raise B.ValidationError()


class Not(B.Generic.Alias, Composite):
    @classmethod
    def instance(cls, *args):
        try:
            super().instance(*args)
        except B.ValidationErrors:
            x, *_ = args

            return cls._attach_parent(x)


class If(L.Literal):
    @classmethod
    def instance(cls, *args):

        args = cls.default(*args)
        s = cls.schema(False)
        i, t, e = s.get(If.alias()), s.get("then"), s.get("else")
        if isinstance(*args, i):
            e = t
        if isinstance(e, B.Generic):
            if issubclass(e, cls):
                return super().instance(*args)
            return e.instance(*args)
        return L.Literal.__new__(e, *args)

    def new_type(cls, object):

        payload = {}
        if isinstance(object, slice):
            if object.start is not None:
                payload[If.alias()] = object.start
            if object.stop is not None:
                payload["then"] = object.stop
            if object.step is not None:
                payload["else"] = object.step
        if payload:
            return B.Generic.new_type(cls, __annotations__=payload)
        return cls
