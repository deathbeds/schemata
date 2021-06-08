import enum
import typing

from schemata.callables import Cast

from . import apis, utils
from .types import ANNO, EMPTY, Any, Const, Default, MetaType, Type
from .utils import get_py, testing, validates

__all__ = ("Dict",)


class Dict(Type["object"], apis.FluentDict, apis.Meaning, dict):
    def __init__(self, *args, **kwargs):
        if all(isinstance(x, dict) for x in args):
            super().__init__(*args, **kwargs)
            args = ()
        else:
            super().__init__(**kwargs)
        cls = type(self)

        from . import callables

        if not self:
            self.update(
                utils.get_default(cls, default=self),
            )

        self.initialize(*args)
        self.validate(self)

    def initialize(self, *args):
        cls = type(self)
        for i, (key, value) in enumerate(
            cls.value(Dict.Properties, default={}).items()
        ):
            if i < len(args):
                self[key] = args[i]

            if key not in self:
                default = utils.get_default(value)
                if default is not EMPTY:
                    self[key] = default

            if key in self:
                if value in type(self[key]).__mro__:
                    key[self] = value(self[key])

        if cls.value(Dict.Dependencies):
            Dict.Dependencies.update_dependencies(self)

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
        def __class_getitem__(cls, object):
            return super().__class_getitem__(object)

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
                    if isinstance(v, type):
                        v.validate(object)
                    else:
                        for required in v:
                            if required == "null":
                                continue
                            testing.assertIn(required, keys)

        def update_dependencies(self, *keys):
            cls = type(self)
            deps = cls.value(Dict.Dependencies) or {}
            for key in keys or tuple(deps):
                d = deps[key]
                if isinstance(d, (tuple, list)):
                    for t in d:
                        if t == "null":
                            if key not in self:
                                dict.__setitem__(self, key, getattr(cls, key)(self))
                                break
                        if t not in self:
                            break
                    else:
                        dict.__setitem__(self, key, getattr(cls, key)(self))

        def __setitem__(self, key, value):
            object = dict.__setitem__(self, key, value)
            Dict.Dependencies.update_dependencies(self)
            return object

    def remove(self, *args):
        for x in args:
            self.pop(x)
        return self


utils.JSONSCHEMA_SCHEMATA_MAPPING["object"] = Dict
