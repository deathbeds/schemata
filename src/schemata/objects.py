import typing

from .arrays import List, Tuple
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

    @classmethod
    def py(cls, ravel=True):

        key = cls.value(Dict.PropertyNames)
        value = cls.value(Dict.Properties)
        # required can be used to populate the typed dict
        required = cls.value(Dict.Required)

        if value:
            return typing.Dict[key or str, typing.Union[tuple(value.values())]]

        if required:
            pass

        value = cls.value(Dict.AdditionalProperties)
        if value:
            return typing.Dict[key or str, value]

        if key:
            return typing.Dict[key, object]
        return dict

    def __class_getitem__(cls, object):
        if isinstance(object, tuple):
            if len(object) is 0:
                return cls
            if len(object) >= 1:
                cls = cls + Dict.PropertyNames[object[0]]
            if len(object) is 2:
                object = object[1]
        if isinstance(object, dict):
            return cls + Dict.Properties[object]
        elif isinstance(object, tuple):
            return cls + Dict.Required[object]
        return cls + Dict.AdditionalProperties[object]

    def items(self, cls=List):
        if not cls:
            return dict.items(self)
        return cls.cast()[
            Tuple[
                type(self).value(Dict.PropertyNames, default=object),
                type(self).value(Dict.AdditionalProperties, default=object),
            ]
        ](dict.items(self))

    def values(self, cls=List):
        if not cls:
            return dict.values(self)
        return cls.cast()[type(self).value(Dict.Properties)](dict.values(self))

    def keys(self, cls=List):
        if not cls:
            return dict.values(self)

        return cls.cast()[type(self).value(Dict.PropertyNames)](dict.keys(self))

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

        def __missing__(self, object):
            self[object] = type(self).value(Dict.AdditionalProperties)()
            return self[object]

    class Required(Any, id="applicator:/properties/required"):
        @validates(dict)
        def is_valid(cls, object):
            required = cls.value(Dict.Required)
            for k in required or {}:
                testing.assertIn(k, object)

    class PatternProperties(Any, id="applicator:/properties/additionalProperties"):
        @validates(dict)
        def is_valid(cls, object):
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
        def is_valid(cls, object):
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
        def is_valid(cls, object):
            testing.assertGreaterEqual(len(object), cls.value(Dict.MinProperties))

    class MaxProperties(Any, id="validation:/properties/maxProperties"):
        @validates(dict)
        def is_valid(cls, object):
            testing.assertLessEqual(len(object), cls.value(Dict.MaxProperties))

    class Dependencies(Any, id="validation:/properties/dependencies"):
        @validates(dict)
        def is_valid(cls, object):
            deps = cls.value(Dict.Dependencies)
            keys = list(object)
            for k, v in dict.items(deps or {}):
                if k in keys:
                    for required in v:
                        testing.assertIn(required, keys)

    def map(self, *input, args=EMPTY, kwargs=EMPTY):
        if len(input) is 0:
            return self
        if len(input) is 1:
            return self.valmap(*input, *(args or ()), **(kwargs or {}))
        if len(input) is 2:
            return self.itemmap(*input, *(args or ()), **(kwargs or {}))
        raise BaseException("at most 2 position arguments allowed")

    def filter(self, *input, args=EMPTY, kwargs=EMPTY):
        if len(input) is 0:
            return self
        if len(input) is 1:
            return self.valfilter(*input, *(args or ()), **(kwargs or {}))
        if len(input) is 2:
            return self.itemfilter(*input, *(args or ()), **(kwargs or {}))
        raise BaseException("at most 2 position arguments allowed")

    def valmap(self, callable=EMPTY, *args, **kwargs):
        if callable:
            cls = type(self)
            if isinstance(cls, MetaType) and isinstance(callable, MetaType):
                cls += callable
            self = cls({k: callable(v, *args, **kwargs) for k, v in self.items()})
        return self

    def itemmap(self, key=EMPTY, value=EMPTY, *args, **kwargs):
        if key or value:
            cls = type(self)
            if isinstance(cls, MetaType) and isinstance(callable, MetaType):
                cls += callable
            self = cls(
                {
                    key(k, *args, **kwargs)
                    if key
                    else k: value(v, *args, **kwargs)
                    if value
                    else v
                    for k, v in self.items()
                }
            )
        return self

    def keymap(self, callable=EMPTY, *args, **kwargs):
        if callable:
            cls = type(self)
            if isinstance(cls, MetaType) and isinstance(callable, MetaType):
                cls += callable
            self = cls({k: callable(v, *args, **kwargs) for k, v in self.items()})
        return self

    def valfilter(self, callable=EMPTY, *args, **kwargs):
        if callable:
            cls = type(self)
            self = cls({k: v for k, v in self.items() if callable(v, *args, **kwargs)})
        return self

    def keyfilter(self, callable=EMPTY, *args, **kwargs):
        if callable:
            cls = type(self)
            self = cls({k: v for k, v in self.items() if callable(k, *args, **kwargs)})
        return self

    def itemfilter(self, key=EMPTY, value=EMPTY, *args, **kwargs):

        if key or value:
            cls = type(self)
            self = cls(
                {
                    k: v
                    for k, v in self.items()
                    if (key(k) if k else True)
                    and (value(v, *args, **kwargs) if v else True)
                }
            )
        return self


JSONSCHEMA_SCHEMATA_MAPPING["object"] = Dict
