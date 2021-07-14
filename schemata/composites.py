import enum
import typing

from . import exceptions, utils
from .types import EMPTY, Any, Schemata, Type

__all__ = "AllOf", "AnyOf", "Else", "If", "Not", "OneOf", "Then"


class AnyOf(Any.from_key("anyOf")):
    @classmethod
    def validate(cls, object):
        type = Schemata.value(cls, AnyOf)
        exception = exceptions.ValidationException(cls, schema="anyOf", items=len(type))
        for i, t in enumerate(type):
            if not isinstance(t, Schemata):
                t = Type[t]
            # t += Any.Parent_[cls]
            with exception:
                with exception.push(schema=i):
                    return t(object)


class Not(Any.from_key("not")):
    @classmethod
    def validate(cls, object):
        exception = exceptions.ValidationException(cls, schema="not")
        nah = Schemata.value(cls, Not)
        with exception:
            exceptions.assertNotIsInstance(object, nah)
        return Any(object)


class AllOf(Any.from_key("allOf")):
    @classmethod
    def validate(cls, object):
        for t in cls.value(AllOf):
            t.validate(object)
        return object


class OneOf(Any.from_key("OneOf")):
    @classmethod
    def validate(cls, object):
        exception = exceptions.ValidationError()
        found = False
        for t in cls.value(OneOf) or ():
            try:
                result = t(object)
            except AssertionError:
                pass
            else:
                if found and "result" in locals():
                    assert False, "more than one condition satisfied"
                found = True
        if found:
            return result
        assert False, f"not one of {any}"


class If(Any.from_key("if")):
    def __class_getitem__(cls, object):
        if isinstance(object, slice):
            types = ()
            if object.start:
                types += (super().__class_getitem__(object.start),)
            if object.stop:
                types += (Else[object.stop],)
            if object.step:
                types += (Then[object.step],)
            return type(cls.__name__, types, {})
        return super().__class_getitem__(object)

    @classmethod
    def validate(cls, object):
        i, e, t = cls.value(If), cls.value(Else), cls.value(Then)
        try:
            i.validate(object)
        except AssertionError:
            return e.validate(object)
        if t:
            return t.validate(object)
        return object


class Else(Any.from_key("else")):
    pass


class Then(Any.from_key("then")):
    pass
