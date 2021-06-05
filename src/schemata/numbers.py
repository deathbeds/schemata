from . import apis, exceptions, utils
from .types import EMPTY, Any, Default, Type

__all__ = "Integer", "Float", "Numeric"


class Numeric(apis.FluentNumber):
    def __class_getitem__(cls, object):
        if isinstance(object, slice):
            if object.start is not None:
                cls += Numeric.Minimum[object.start]
            if object.stop is not None:
                cls += Numeric.Maximum[object.stop]
            if object.step is not None:
                cls += Numeric.MultipleOf[object.step]
            return cls
        if isinstance(object, type):
            return cls + object
        return cls + Default[object]

    class Minimum(Any, id="validation:/properties/minimum"):
        @utils.validates(int, float)
        def validator(cls, object):
            exceptions.assertGreaterEqual(object, cls.value(Numeric.Minimum))

    class Maximum(Any, id="validation:/properties/maximum"):
        @utils.validates(int, float)
        def validator(cls, object):
            exceptions.assertLessEqual(object, cls.value(Numeric.Maximum))

    class ExclusiveMinimum(Any, id="validation:/properties/exclusiveMinimum"):
        @utils.validates(int, float)
        def validator(cls, object):
            exceptions.assertGreater(object, cls.value(Numeric.ExclusiveMinimum))

    class ExclusiveMaximum(Any, id="validation:/properties/exclusiveMaximum"):
        @utils.validates(int, float)
        def validator(cls, object):
            exceptions.assertLess(object, cls.value(Numeric.ExclusiveMaximum))

    class MultipleOf(Any, id="validation:/properties/multipleOf"):
        @utils.validates(int, float)
        def validator(cls, object):
            mul, offset = cls.value(Numeric.MultipleOf), cls.value(
                Numeric.Offset, default=0
            )
            assert not ((object - offset) % mul), f"{object} is not a multiple of {mul}"

    class Offset(Any):
        pass


class Integer(Numeric, Type["integer"], int):
    @classmethod
    def validator(cls, object):
        exceptions.assertNotIsInstance(object, bool)
        exceptions.assertIsInstance(object, int)


class Float(Numeric, Type["number"], float):
    @classmethod
    def validator(cls, object):
        exceptions.assertIsInstance(object, float)


utils.JSONSCHEMA_SCHEMATA_MAPPING.update(dict(integer=Integer, number=Float))
