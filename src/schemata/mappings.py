from .types import EMPTY, JSONSCHEMA_SCHEMATA_MAPPING, Any, Const, Default, Type
from .utils import testing, validates

__all__ = ("Dict",)


class Dict(Type["object"], dict):
    def __init__(self, object=EMPTY, **kwargs):
        if object is EMPTY:
            object = type(self).value(Default, Const)

        if object is EMPTY:
            object = {}

        if object is EMPTY:
            super().__init__()
        else:
            super().__init__(object, **kwargs)

    def __class_getitem__(cls, object):
        if isinstance(object, dict):
            return cls + Dict.Properties[object]
        elif isinstance(object, tuple):
            return cls + Dict.Required[object]
        return cls + Dict.AdditionalProperties[object]

    @classmethod
    def is_valid(cls, object):
        testing.assertIsInstance(object, dict)

    class Properties(Any, id="applicator:/properties/properties"):
        @validates(dict)
        def is_valid(cls, object):
            for k, v in (cls.value(Dict.Properties) or {}).items():
                if k in object:
                    v.validate(object[k])

    class AdditionalProperties(Any, id="applicator:/properties/additionalProperties"):
        @validates(dict)
        def is_valid(cls, object):
            pass

    class PatternProperties(Any, id="applicator:/properties/additionalProperties"):
        @validates(dict)
        def is_valid(cls, object):
            pass

    class PropertyNames(Any, id="validation:/properties/propertyNames"):
        @validates(dict)
        def is_valid(cls, object):
            pass

    class MinProperties(Any, id="validation:/properties/minProperties"):
        @validates(dict)
        def is_valid(cls, object):
            testing.assertGreaterEqual(len(object), cls.value(Dict.MinProperties))

    class MaxProperties(Any, id="validation:/properties/maxProperties"):
        @validates(dict)
        def is_valid(cls, object):
            testing.assertLessEqual(len(object), cls.value(Dict.MaxProperties))

    class Dependencies(Any, id="validation:/properties/dependencies"):
        @validates(dict)
        def is_valid(cls, object):
            pass


JSONSCHEMA_SCHEMATA_MAPPING["object"] = Dict
