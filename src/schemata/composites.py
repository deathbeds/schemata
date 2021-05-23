from functools import partial

from .types import EMPTY, Any, Default, ValidationError, testing, typing
from .utils import get_py

__all__ = "AllOf", "AnyOf", "Else", "If", "Not", "OneOf", "Then"


class _Composite:
    def __new__(cls, object=EMPTY):
        if object is EMPTY:
            object = None
            if issubclass(cls, Default):
                object = cls.value(Default)
            else:
                pass
        return cls.validate(object)


class Not(_Composite, Any, id="applicator:/properties/not"):
    @classmethod
    def validate(cls, object):
        testing.assertRaises(AssertionError, partial(cls.value(Not).validate, object))
        return object


class AllOf(_Composite, Any, id="applicator:/properties/allOf"):
    @classmethod
    def validate(cls, object):
        for t in cls.value(AllOf):
            t.validate(object)
        return object


class AnyOf(_Composite, Any, id="applicator:/properties/anyOf"):
    @classmethod
    def validate(cls, object):
        exception = ValidationError()
        for t in cls.value(AnyOf):
            with exception:
                return t(object)
        exception.raises()
        assert False, "empty anyof"

    @classmethod
    def py(cls):
        return typing.Union[get_py(cls.value(AnyOf)) or (object,)]


class OneOf(_Composite, Any, id="applicator:/properties/oneOf"):
    @classmethod
    def validate(cls, object):
        exception = ValidationError()
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


class If(_Composite, Any, id="applicator:/properties/if"):
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
            e and e.validate(object)
        else:
            t and t.validate(object)
        return object


class Else(_Composite, Any, id="applicator:/properties/else"):
    pass


class Then(_Composite, Any, id="applicator:/properties/then"):
    pass
