import typing

from . import apis, utils
from .types import (
    ANNO,
    EMPTY,
    JSONSCHEMA_SCHEMATA_MAPPING,
    Any,
    Const,
    Default,
    MetaType,
    Type,
)
from .utils import get_py, testing, validates

__all__ = ("Dict",)


class Dict(Type["object"], apis.FluentDict, dict):
    def __new__(cls, *args, **kwargs):
        if not (args or kwargs):
            args = (utils.get_default(cls, {}),)

        if kwargs:
            args = (dict(*args, **kwargs),)
        cast = cls.value(callables.Cast)
        if cast:
            args = utils.enforce_tuple((dict if cast is True else cast)(*args, **kwargs))
        else:
            cls.validate(*args)

        self = dict.__new__(cls)
        dict.__init__(self, *args)
        if cast:
            cls.validate(self)
        return self

    def __init__(self, object=EMPTY, **kwargs):
        if object is EMPTY:
            object = type(self).value(Default, Const)

        if object is EMPTY:
            object = {}

        if object is EMPTY:
            super().__init__()
        else:
            super().__init__(object, **kwargs)

    @classmethod
    def default(cls, object=EMPTY, **kwargs):
        return cls + Default[dict(*object or {}, **kwargs)]

    @classmethod
    def py(cls, ravel=True):

        key = cls.value(Dict.PropertyNames)
        value = cls.value(Dict.Properties)
        # required can be used to populate the typed dict
        required = cls.value(Dict.Required)

        if value:
            return typing.Dict[
                key and key.py() or str,
                typing.Union[tuple(x.py() for x in value.values())],
            ]

        if required:
            pass

        value = cls.value(Dict.AdditionalProperties)
        if value:
            return typing.Dict[key and key.py() or str, value.py()]

        if key:
            return typing.Dict[key.py(), object]
        return dict

    def __class_getitem__(cls, object):
        from .builders import build_dict

        return cls.add(*utils.enforce_tuple(build_dict(object)))

    @classmethod
    def validator(cls, object):
        testing.assertIsInstance(object, dict)

    @classmethod
    def properties(cls, *args, **kwargs):
        return cls + Dict.Properties[dict(*args, **kwargs)]

    class Properties(Any, id="applicator:/properties/properties"):
        @validates(dict)
        def validator(cls, object):
            for k, v in (cls.value(Dict.Properties) or {}).items():
                if k in object:
                    v.validate(object[k])

    class AdditionalProperties(Any, id="applicator:/properties/additionalProperties"):
        @validates(dict)
        def validator(cls, object):
            pass

        def __missing__(self, object):
            self[object] = type(self).value(Dict.AdditionalProperties)()
            return self[object]

    class Required(Any, id="applicator:/properties/required"):
        @validates(dict)
        def validator(cls, object):
            required = cls.value(Dict.Required)
            for k in required or {}:
                testing.assertIn(k, object)

    class PatternProperties(Any, id="applicator:/properties/additionalProperties"):
        @validates(dict)
        def validator(cls, object):
            value = cls.value(Dict.PatternProperties)
            for k, v in dict.items(value and object or {}):
                for p in value:
                    try:
                        testing.assertRegex(k, p)
                    except AssertionError:
                        pass
                    else:
                        value[p].validate(v)

    class PropertyNames(Any, id="validation:/properties/propertyNames"):
        @validates(dict)
        def validator(cls, object):
            value = cls.value(Dict.PropertyNames)
            for k in value and object or ():
                value.validate(k)

        def __class_getitem__(cls, object):
            from .strings import String

            if isinstance(object, str):
                object = String[object]
            return super().__class_getitem__(object)

    class MinProperties(Any, id="validation:/properties/minProperties"):
        @validates(dict)
        def validator(cls, object):
            testing.assertGreaterEqual(len(object), cls.value(Dict.MinProperties))

    class MaxProperties(Any, id="validation:/properties/maxProperties"):
        @validates(dict)
        def validator(cls, object):
            testing.assertLessEqual(len(object), cls.value(Dict.MaxProperties))

    class Dependencies(Any, id="validation:/properties/dependencies"):
        @validates(dict)
        def validator(cls, object):
            deps = cls.value(Dict.Dependencies)
            keys = list(object)
            for k, v in dict.items(deps or {}):
                if k in keys:
                    for required in v:
                        testing.assertIn(required, keys)


JSONSCHEMA_SCHEMATA_MAPPING["object"] = Dict
