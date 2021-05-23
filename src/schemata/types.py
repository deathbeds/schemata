import abc
import builtins
import enum
import inspect
import typing

from .exceptions import ValidationError
from .utils import (
    ANNO,
    EMPTY,
    enforce_tuple,
    get_default,
    get_hash,
    get_schema_dict,
    get_schemata_object,
    get_verified_object,
    testing,
    uppercase,
)

__all__ = (
    "Any",
    "Bool",
    "Cast",
    "Comment_",
    "Const",
    "ContentEncoding",
    "ContentMediaType",
    "Default",
    "Deprecated",
    "Description",
    "Definitions",
    "Enum",
    "Examples",
    "Any",
    "MetaType",
    "Null",
    "ReadOnly",
    "Ref_",
    "Title",
    "Type",
    "Value",
    "ValidationError",
    "Verified",
    "WriteOnly",
)


class MetaType(abc.ABCMeta):
    def __new__(cls, name, bases, dict, value=EMPTY, id=EMPTY, rank=None):
        from .utils import DOC, merge, py_to_json

        # resolve docstrings
        doc = dict.pop(DOC, None)
        if isinstance(doc, (str, type(None))):
            if doc is not None:
                bases += (Description[doc],)
        else:
            dict[DOC] = doc

        # resolve annotations
        if dict.get(ANNO):
            from .mappings import Dict
            from .sequences import Sequence

            property = Dict.Properties[dict[ANNO]]
            if any(issubclass(x, Sequence) for x in bases):
                property = Sequence.Items[property]
            bases += (property,)

        # resolve Meta definitions in the class
        defs = {
            k: v
            for k, v in dict.items()
            if isinstance(v, MetaType) and getattr(v, ANNO, None)
        }
        if defs:
            bases += (Definitions[defs],)

        # update the class dict payload
        key = py_to_json(name)
        if id is not EMPTY:
            dict.setdefault("id", id)
        elif value is not EMPTY:
            dict.setdefault(ANNO, {})
            dict[ANNO].update({key: value})

        dict.setdefault("rank", rank)

        # build
        cls = super().__new__(cls, name, bases, dict)
        cls.__annotations__ = merge(cls)
        return cls

    def key(cls):
        from .utils import py_to_json

        return py_to_json(cls.__name__)

    def value(cls, *key, default=EMPTY):
        """get the corresponding value to the class key"""
        if not hasattr(cls, ANNO):
            return

        for k in key or (cls.key(),):
            if isinstance(k, type):
                k = k.key()

            if k in cls.__annotations__:
                return cls.__annotations__[k]
        if default is EMPTY:
            return EMPTY
        return default

    def __add__(cls, *object):
        return type(cls.__name__, (cls,) + object, {})

    def __pos__(cls):
        return cls

    def __neg__(cls):
        from . import Not

        return Not[cls]

    def __and__(cls, *object):
        from . import AllOf

        return AllOf[(cls,) + object]

    def __or__(cls, *object):
        from . import AnyOf

        return AnyOf[(cls,) + object]

    def __xor__(cls, *object):
        from . import OneOf

        return OneOf[(cls,) + object]

    def __eq__(cls, object):
        if isinstance(object, MetaType):
            return cls.schema() == object.schema()
        return super().__eq__(object)

    def __hash__(cls):
        return get_hash(cls)

    def __getattr__(cls, str):
        try:
            return object.__getattribute__(cls, str)
        except AttributeError as e:
            error = e
        if str[0].islower():
            name = uppercase(str)
            if hasattr(cls, name):

                def caller(*args):
                    object = getattr(cls, name)
                    if not args:
                        return cls + object
                    if len(args) is 1:
                        return cls + object[args[0]]
                    return cls + object[args]

                return caller
        raise error

    @property
    def __doc__(cls):
        """generate docstrings from schema"""
        from .utils import get_docstring

        return get_docstring(cls)

    def __dir__(cls):
        object = super().__dir__()
        return object + [
            k[0].lower() + k[1:]
            for k in object
            if k[0].isupper() and isinstance(getattr(cls, k), type)
        ]


class Any(metaclass=MetaType):
    def __new__(cls, object=EMPTY):
        if not isinstance(object, MetaType):
            object = get_default(cls, object)
            return get_schemata_object(object)
        return object

    @classmethod
    def py(cls):
        return cls

    def __class_getitem__(cls, object):
        return type(cls.__name__, (cls,), {}, value=object)

    @classmethod
    def validate(cls, object: typing.Any) -> None:
        exception = ValidationError()
        for t in inspect.getmro(cls):
            if getattr(t, ANNO, {}):
                with exception:
                    t.is_valid(object)
        exception.raises()

    @classmethod
    def schema(cls, ravel=None):
        from .utils import get_schema

        return get_schema(cls, ravel=ravel)

    @classmethod
    def is_valid(cls, object):
        pass

    def pipe(self, callable, *args, **kwargs):
        return callable(self, *args, **kwargs)

    @classmethod
    def py(cls):
        return object

    @classmethod
    def cast(cls, object=True):
        return cls + Cast[object]

    @classmethod
    def verified(cls, object=EMPTY):
        if object is EMPTY:
            return cls()
        return cls(Verified[object])


class Cast(Any):
    pass


class Verified(Any):
    pass


class Type(Any, id="validation:/properties/type"):
    def __new__(cls, object=EMPTY):
        object = get_default(cls, object)

        if object is EMPTY:
            return super().__new__(cls)

        cast = cls.value(Cast)
        cast or cls.validate(object)
        t = Type.py.__func__(cls)
        self = t.__new__(cls, object)
        cast and cls.validate(self)
        return self

    @classmethod
    def is_valid(cls, object):
        from .utils import enforce_tuple, testing

        with ValidationError() as exceptions:
            for value in enforce_tuple(cls.value(Type)):
                if value is EMPTY:
                    continue
                if isinstance(value, str):
                    if value in JSONSCHEMA_SCHEMATA_MAPPING:
                        JSONSCHEMA_SCHEMATA_MAPPING[value].is_valid(object)
                    else:
                        "we'll consider these forward references"

                elif isinstance(value, type):
                    testing.assertIsInstance(object, value)
                else:
                    assert False, f"don't know how to enfore type: {value}"

        exceptions.raises()

    @classmethod
    def py(cls, expand=True):
        type = cls.value(Type)
        if type:
            return JSONSCHEMA_PY_MAPPING[type]
        return object

    @classmethod
    def strategy(cls):
        import hypothesis_jsonschema

        return hypothesis_jsonschema.from_schema(cls.schema(True))

    def print(self):
        import pprint

        if isinstance(self, str):
            print(self)
        else:
            pprint.pprint(self)


class Null(Type["null"]):
    def __new__(cls, object=EMPTY):
        object = get_default(cls, object, None)

        if object is EMPTY:
            return

        cls.validate(object)

    @classmethod
    def is_valid(cls, object):
        testing.assertIs(object, None)


class Title(Any, id="metadata:/properties/title"):
    pass


class Description(Any, id="metadata:/properties/description"):
    pass


class Examples(Any, id="metadata:/properties/examples"):
    pass


class Default(Any, id="metadata:/properties/default"):
    pass


class Deprecated(Any, id="metadata:/properties/default"):
    pass


class ReadOnly(Any, id="metadata:/properties/default"):
    pass


class WriteOnly(Any, id="metadata:/properties/default"):
    pass


class Value(Any):
    @classmethod
    def key(cls):
        return "value"


class ContentMediaType(Any, id="content:/properties/contentMediaType"):
    def _repr_mimebundle_(self, include=None, exclude=None):
        cls = type(self)
        return dict({cls.value(ContentMediaType, "text/plain"): self})


class ContentEncoding(Any, id="content:/properties/contentEncoding"):
    pass


class Const(Type, id="validation:/properties/const"):
    @classmethod
    def is_valid(cls, object):
        testing.assertEqual(object, cls.value(Const))


class Ref_(Any, id="core:/properties/$ref"):
    pass


class Comment_(Any, id="core:/properties/$comment"):
    pass


class Definitions(Any, id="core:/properties/$defs"):
    pass


class Ui(Any):
    pass


class UiWidget(Ui):
    pass

class UiOptions(Ui):
    pass

class Bool(Type["boolean"]):
    def __new__(cls, object=EMPTY):
        object = get_default(cls, object, bool())
        cls.validate(object)
        return object

    @classmethod
    def is_valid(cls, object):
        testing.assertIsInstance(object, bool)


class Enum(Type, id="validation:/properties/enum"):
    def __class_getitem__(cls, object):
        if isinstance(object, str):
            object = tuple(object.split())
        return super().__class_getitem__(object)

    @classmethod
    def is_valid(cls, object):
        testing.assertIn(object, cls.value(Enum))

    @classmethod
    def py(cls):
        data = cls.value(Enum)
        if not isinstance(data, dict):
            data = dict(zip(*map(enforce_tuple, (data, data))))
        return EnumeratedType

    class Radio(UiWidget["updown"]):
        pass


Any.Cast = Cast
Any.Comment_ = Comment_
Any.Const = Const
Any.ContentEncoding = ContentEncoding
Any.ContentMediaType = ContentMediaType
Any.Default = Default
Any.Definitions = Definitions
Any.Deprecated = Deprecated
Any.Description = Description
Any.Enum = Enum
Any.Examples = Examples
Any.ReadOnly = ReadOnly
Any.Ref_ = Ref_
Any.Title = Title
Any.UiWidget = UiWidget
Any.WriteOnly = WriteOnly

JSONSCHEMA_SCHEMATA_MAPPING = dict(
    null=Null,
    boolean=Bool,
)


JSONSCHEMA_PY_MAPPING = dict(
    null=type(None),
    boolean=bool,
    string=str,
    integer=int,
    number=float,
    array=list,
    object=dict,
)


JSONSCHEMA_STR_MAPPING = dict(map(reversed, JSONSCHEMA_PY_MAPPING.items()))
