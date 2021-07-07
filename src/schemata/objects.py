import enum
import functools
import typing

from schemata.callables import Cast

from . import apis, exceptions, mixins, utils
from .types import ANNO, EMPTY, Any, Const, Default, Schemata, Type
from .utils import testing, validates

__all__ = ("Dict", "IDict", "Bunch", "IBunch")


class Dict(Type["object"], apis.FluentDict, apis.Meaning, dict):
    def __class_getitem__(cls, object):
        """
        >>> ...
        """
        from . import builders

        return cls + builders.InstanceBuilder(**build_dict(object)).build()

    @classmethod
    def properties(cls, *args, **kwargs):
        return cls + Properties[dict(*args, **kwargs)]

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.initialize()
        if hasattr(self, "__post_init__"):
            self.__post_init__()

    def initialize(self):
        props = Schemata.value(self, Properties, default={})

        for k, v in props.items():
            if k not in self:
                default = utils.get_default(v)
                if default is not EMPTY:
                    self[k] = default

    def __fluent__(self, key, *args, **kwargs):
        getattr(super(Dict, self), key)(*args, **kwargs)
        return self

    for k in "update append extend insert".split():
        locals().update({k: functools.partialmethod(__fluent__, k)})

    del k


class Properties(Any):
    @validates(dict)
    def validator(cls, object):
        for k, v in (cls.value(Properties) or {}).items():
            if k in object:
                exceptions.ValidationException(v, schema=k, path=k).validate(object[k])


class AdditionalProperties(Any):
    @validates(dict)
    def validator(cls, object):
        pass

    def __missing__(self, object):
        cls = type(self)
        additional = Schemata.value(cls, AdditionalProperties)
        if additional and callable(additional):
            self[object] = additional()
            return self[object]
        raise KeyError(object)


class Required(Any):
    @validates(dict)
    def validator(cls, object):
        required = cls.value(Required)
        missing = [k for k in required or {} if k not in object]
        if missing:
            assert False, f"required keys {missing} are missing from the object"


class PatternProperties(Any):
    @validates(dict)
    def validator(cls, object):
        value = Schemata.value(cls, PatternProperties)
        for k, v in object.items():
            if not isinstance(k, str):
                continue
            for p in value:

                try:
                    testing.assertRegex(k, p)
                except AssertionError:
                    pass
                else:
                    exceptions.ValidationException(value[p], schema=p, path=k).validate(
                        v
                    )


class PropertyNames(Any):
    @validates(dict)
    def validator(cls, object):
        value = cls.value(PropertyNames)
        for k in object:
            exceptions.ValidationException(value, path=k).validate(k)

    def __class_getitem__(cls, object):
        from .strings import String

        if isinstance(object, str):
            object = String[object]
        return super().__class_getitem__(object)


class MinProperties(Any):
    @validates(dict)
    def validator(cls, object):
        testing.assertGreaterEqual(len(object), cls.value(MinProperties))


class MaxProperties(Any):
    @validates(dict)
    def validator(cls, object):
        testing.assertLessEqual(len(object), cls.value(MaxProperties))


class Dependencies(Any):
    @validates(dict)
    def validator(cls, object):
        deps = cls.value(Dependencies)
        keys = list(object)
        for k, v in dict.items(deps or {}):
            if k in object:
                exceptions.ValidationException(v).validate(object[k])

    def __post_init__(self, *keys):
        id = None
        if keys:
            for key in keys:
                try:
                    id = max(id or 0, keys.index(key))
                except IndexError:
                    pass
        else:
            id = 0

        if id is None:
            return

        deps = Schemata.value(self, Dependencies)
        for k in self._ordered_keys[id:]:
            if k in deps:
                if hasattr(self, k):
                    if isinstance(self, deps[k]):
                        dict.update(self, {k: getattr(self, k).__func__(self)})


def remove(self, *args):
    for x in args:
        self.pop(x)
    return self


utils.JSONSCHEMA_SCHEMATA_MAPPING["object"] = Dict


@utils.register
def build_dict(x: type):
    return dict(additionalProperties=x)


@build_dict.register
def build_list_str(x: str):
    return dict(required=tuple(x.split()))


@build_dict.register(int)
@build_dict.register(float)
def build_list_numeric(x):
    if isinstance(x, bool):
        return dict(additionalProperties=x)
    return dict(minProperties=x, maxProperties=x)


@build_dict.register
def build_dict_tuple(x: tuple, **schema):
    for y in x:
        if not isinstance(y, str):
            break
    else:
        return dict(required=x)

    if 0 < len(x) < 3:
        for y in x:
            if not isinstance(y, type):
                break
        else:
            schema["propertyNames"] = x[0]
            if len(x) == 2:
                schema.update(build_dict(x[1]))
            return schema
    raise TypeError(f"dictionaries take at most two properties")


@build_dict.register
def build_dict_dict(x: dict):
    return dict(properties=x)


@build_dict.register
def build_dict_slice(x: slice, **schema):
    if x.start is not None:
        if not isinstance(x.start, (int, float)):
            raise TypeError("slice expects start and stop to be in numeric")
        schema["minProperties"] = x.start
    if x.stop is not None:
        if not isinstance(x.stop, (int, float)):
            raise TypeError("slice expects start and stop to be in numeric")
        schema["maxProperties"] = x.stop
    if x.step is not None:
        schema.update(build_dict(x.step))
    return schema


class IDict(Dict):
    def __setitem__(self, key, value):
        self.update({key: value})

    def update(self, *args, **kwargs):
        args = dict(*args, **kwargs)

        Properties[Schemata.value(self, Properties)].validate(args)

        super().update(args)
        self.__post_init__(*args)
        return self


class Bunch(mixins.Bunch, Dict):
    pass


class IBunch(mixins.Bunch, IDict):
    pass
