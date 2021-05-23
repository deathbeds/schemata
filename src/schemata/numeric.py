from .types import (
    EMPTY,
    JSONSCHEMA_SCHEMATA_MAPPING,
    Any,
    Default,
    Type,
    UiWidget,
    testing,
)
from .utils import validates

__all__ = "Integer", "Float"


class Numeric:
    def __new__(cls, object=EMPTY):
        from .utils import get_default

        object = get_default(cls, object, super().__new__(cls))

        return super().__new__(cls, object)

    def __class_getitem__(cls, object):
        return cls + Default[object]

    class Minimum(Any, id="validation:/properties/minimum"):
        @validates(int, float)
        def is_valid(cls, object):
            testing.assertGreaterEqual(object, cls.value(Numeric.Minimum))

    class Maximum(Any, id="validation:/properties/maximum"):
        @validates(int, float)
        def is_valid(cls, object):
            testing.assertLessEqual(object, cls.value(Numeric.Maximum))

    class ExclusiveMinimum(Any, id="validation:/properties/exclusiveMinimum"):
        @validates(int, float)
        def is_valid(cls, object):
            testing.assertGreater(object, cls.value(Numeric.ExclusiveMinimum))

    class ExclusiveMaximum(Any, id="validation:/properties/exclusiveMaximum"):
        @validates(int, float)
        def is_valid(cls, object):
            testing.assertLess(object, cls.value(Numeric.ExclusiveMaximum))

    class MultipleOf(Any, id="validation:/properties/multipleOf"):
        @validates(int, float)
        def is_valid(cls, object):
            mul, offset = cls.value(Numeric.MultipleOf), cls.value(
                Numeric.Offset, default=0
            )
            print(offset)
            assert not ((object - offset) % mul), f"{object} is not a multiple of {mul}"

    class Offset(Any):
        pass

    class Text(UiWidget["text"]):
        pass

    class UpDown(UiWidget["updown"]):
        pass

    class Range(UiWidget["range"]):
        pass

    class Slider(UiWidget["slider"]):
        pass


class Integer(Numeric, Type["integer"], int):
    @classmethod
    def is_valid(cls, object):
        testing.assertNotIsInstance(object, bool)
        testing.assertIsInstance(object, int)


class Float(Numeric, Type["number"], float):
    @classmethod
    def is_valid(cls, object):
        testing.assertIsInstance(object, float)


JSONSCHEMA_SCHEMATA_MAPPING.update(dict(integer=Integer, number=Float))
