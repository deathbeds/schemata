from .types import EMPTY, JSONSCHEMA_SCHEMATA_MAPPING, Any, Const, Default, Type, Value
from .utils import testing, validates

__all__ = "List", "Tuple", "Set"


class Arrays:
    def __class_getitem__(cls, object):
        if isinstance(object, dict):
            from .mappings import Dict

            object = Dict + Dict.Properties[object]
        if isinstance(object, tuple):
            return Tuple + Arrays.Items[object]
        return cls + Arrays.Items[object]

    class Items(Any, id="applicator:/properties/items"):
        @validates(list, tuple, set)
        def validator(cls, object):
            value = cls.value(Arrays.Items)
            if value:
                if isinstance(value, (tuple, list)):
                    for i, (x, y) in enumerate(zip(value, object)):
                        x.validate(y)
                    other = cls.value(Arrays.AdditionalItems)
                    if other:
                        for x in other[i:]:
                            other.validate(x)
                else:
                    for i, x in enumerate(object):
                        value.validate(x)

    class AdditionalItems(Any, id="applicator:/properties/additionalItems"):
        pass

    class MinItems(Any, id="validation:/properties/minItems"):
        @validates(list, tuple, set)
        def validator(cls, object):
            testing.assertGreaterEqual(len(object), cls.value(Arrays.MinItems))

    class MaxItems(Any, id="validation:/properties/maxItems"):
        @validates(list, tuple, set)
        def validator(cls, object):
            testing.assertLessEqual(len(object), cls.value(Arrays.MaxItems))

    class UniqueItems(Any, id="validation:/properties/uniqueItems"):
        @validates(list, tuple, set)
        def validator(cls, object):
            assert len(set(object)) == len(
                object
            ), f"the items of the object are not unique"

    class Contains(Any):
        pass


class List(Arrays, Type["array"], list):
    def __init__(self, object=EMPTY):
        if object is EMPTY:
            object = type(self).value(Default, Const)
        if object is EMPTY:
            super().__init__()
        else:
            super().__init__(object)

    @classmethod
    def validator(cls, object):
        testing.assertIsInstance(object, (tuple, list, set))


class Tuple(Arrays, Type["array"], tuple):
    @classmethod
    def validator(cls, object):
        testing.assertIsInstance(object, tuple)


class Set(Arrays, Type["array"], set):
    @classmethod
    def validator(cls, object):
        testing.assertIsInstance(object, set)


JSONSCHEMA_SCHEMATA_MAPPING["array"] = List
