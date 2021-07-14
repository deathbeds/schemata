from . import exceptions, utils
from .types import EMPTY, Any, Schemata, Type

__all__ = "Integer", "Float", "Number"


class Numeric(Any):
    def __class_getitem__(cls, object):
        """

        >>> Number[1:10].schema()
        {'type': ('integer', 'number'), 'minimum': 1, 'maximum': 10}"""
        from . import builders

        if not isinstance(object, type):
            object = builders.InstanceBuilder(build_number(object)).build()
        return cls + object


@Schemata.register_schemata_types
class Number(Numeric, Type["integer", "number"]):
    pass


class Minimum(Any.from_key("minimum")):
    @utils.validates(int, float)
    def validator(cls, object):
        exceptions.assertGreaterEqual(object, Schemata.value(cls, Minimum))


class Maximum(Any.from_key("maximum")):
    @utils.validates(int, float)
    def validator(cls, object):
        exceptions.assertLessEqual(object, Schemata.value(cls, Maximum))


class ExclusiveMinimum(Any.from_key("exclusiveMinimum")):
    @utils.validates(int, float)
    def validator(cls, object):
        exceptions.assertGreater(object, Schemata.value(cls, ExclusiveMinimum))


class ExclusiveMaximum(Any.from_key("exclusiveMaximum")):
    @utils.validates(int, float)
    def validator(cls, object):
        exceptions.assertLess(object, Schemata.value(cls, ExclusiveMaximum))


class MultipleOf(Any.from_key("multipleOf")):
    @utils.validates(int, float)
    def validator(cls, object):
        mul, offset = Schemata.value(cls, MultipleOf), Schemata.value(
            cls, Offset, default=0
        )
        assert not ((object - offset) % mul), f"{object} is not a multiple of {mul}"


class Offset(Any.from_key("offset")):
    pass


@Schemata.register_schemata_types
class Integer(Type["integer"], int):
    pass


Type.from_key("integer").register(int)


@Schemata.register_schemata_types
class Float(Type["number"], float):
    pass


Type.from_key("number").register(float)

utils.JSONSCHEMA_SCHEMATA_MAPPING.update(dict(integer=Integer, number=Float))


@utils.register
def build_number(x: type):
    return dict(items=x)


@build_number.register(int)
@build_number.register(float)
def build_number_numeric(x):
    return dict(default=x)


@build_number.register
def build_number_slice(x: slice, **schema):
    if x.start is not None:
        schema["minimum"] = x.start
    if x.stop is not None:
        schema["maximum"] = x.stop
    if x.step is not None:
        schema["multipleOf"] = x.step
    return schema
