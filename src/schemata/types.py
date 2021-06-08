"""the basis of schemata that begins defining the type system"""

import abc
import builtins
import inspect
import typing
from contextlib import suppress

from . import apis, exceptions, utils
from .utils import ANNO, DOC, EMPTY

__all__ = (
    "Any",
    "Bool",
    "false",
    "Comment_",
    "Const",
    "Default",
    "Deprecated",
    "Description",
    "Definitions",
    "Enum",
    "Examples",
    "Any",
    "MetaType",
    "Null",
    "Optional",
    "ReadOnly",
    "Ref_",
    "Schema_",
    "true",
    "Title",
    "Type",
    "Value",
    "WriteOnly",
)


class MetaType(apis.TypeOps, abc.ABCMeta):
    """a schemaful python type"""

    def __new__(cls, name, bases, dict, value=EMPTY, **kwargs):
        """\
instantiate a new schemata type.

* __annotations__ refer to dictionary properties of like array or object flavor
* __doc__ refers the description of the class
        
        """
        key = utils.normalize_json_key(name)
        dict.setdefault(ANNO, {})
        if value is not EMPTY:
            dict[ANNO].update({key: value})

        # build
        cls = super().__new__(cls, name, bases, dict)
        cls.__annotations__ = utils.merge(cls)

        return cls

    def mro(cls):
        bases = super().mro()

        is_array = any(issubclass(x, (tuple, list, set)) for x in bases)
        is_object = any(issubclass(x, builtins.dict) for x in bases)

        dict = vars(cls)
        if dict.get(DOC):
            bases += (Description[dict[DOC]],)

        comments = inspect.getcomments(cls)
        if comments:
            bases += (Comment_[comments],)

        if is_array or is_object:
            extra = []

            defs, deps = {}, __import__("collections").defaultdict(tuple)
            for k, v in dict.items():
                if isinstance(v, MetaType):
                    if getattr(v, ANNO, None):
                        defs[k] = v
                elif inspect.isfunction(v):
                    sig = inspect.signature(v)

                    if sig.return_annotation != inspect._empty:
                        dict[ANNO].setdefault(k, sig.return_annotation)

                    for i, (key, param) in enumerate(sig.parameters.items()):
                        if isinstance(param.annotation, MetaType):
                            deps.setdefault(k, param.annotation)

                elif callable(v):
                    pass

            for k, v in dict.items():
                if not callable(v) and k in dict[ANNO]:
                    dict[ANNO][k] = dict[ANNO][k].default(v)

            if dict[ANNO]:
                from . import objects

                extra += (objects.Dict.Properties[builtins.dict(dict[ANNO])],)
                dict[ANNO].clear()

            if deps:
                extra += (objects.Dict.Dependencies[deps],)

            if is_array and extra:
                from .arrays import Arrays

                extra = (Arrays.Items[type("Annotations", tuple(extra), {})],)

            if defs:
                extra += (Definitions[defs],)

            id = bases.index(object)
            bases = bases[:id] + list(extra) + bases[id:]
        return bases

    def key(cls):
        return utils.normalize_json_key(cls.__name__)

    def value(cls, *key, default=EMPTY):
        """get the corresponding value to the class key"""
        for k in key or (cls.key(),):
            if isinstance(k, type):
                k = k.key()

            if k in cls.__annotations__:
                v = cls.__annotations__[k]
                if isinstance(v, utils.Literal):
                    v = str(v)
                return v

        return default

    def __str__(cls):
        return cls.key() or super().__str__()

    @property
    def __doc__(cls):
        return utils.get_docstring(cls)


class Any(apis.FluentType, apis.Validate, apis.TypeConversion, metaclass=MetaType):
    @classmethod
    def from_file(cls, file):
        import json

        return cls.from_schema(json.loads(utils.Path(file).read_text()))

    @classmethod
    def from_schema(cls, schema):
        return utils.get_class(schema)

    def __new__(cls, object=EMPTY):
        # fill in the default values if they exist
        object = utils.get_default(cls, default=object)
        if not isinstance(object, Any):
            return utils.get_schemata(object)
        return object

    def __class_getitem__(cls, object):
        return cls.new_type(object)

    @classmethod
    def new_type(cls, value=EMPTY, bases=None, **kwargs):
        if isinstance(value, str):
            value = utils.Literal(value)
        return type(cls.__name__, (cls,) + utils.enforce_tuple(bases), {}, value=value)

    @classmethod
    def schema(cls, ravel=None):
        return utils.get_schema(cls, ravel=ravel)

    @classmethod
    def cast(cls, object=True, *args):
        from . import callables

        if args:
            return callables.Cast[(object,) + args] + cls
        return callables.Cast[object] + cls


class Type(Any):
    id = "validation:/properties/type"

    def __new__(cls, object=EMPTY, *args, **kw):
        if object is EMPTY:
            object = utils.get_default(cls, object)

        from .callables import Cast

        type, cast = cls.value(Type), cls.value(Cast)

        # when the type is a tuple iterate through allowing
        # for conformations like ("integer", "string") which are valid jsonschema
        if isinstance(type, tuple):
            exception = exceptions.ValidationError()
            for t in type:
                with exception:
                    return Type[t].cast(cast)(object, *args, **kw)
            exception.raises()

        # update the arguments
        if object is not EMPTY:
            args = (object,) + args

        if not cast:
            args = args or (super(Any, cls).__new__(cls),)
            cls.validate(*args)

        if type:
            self = super(Any, cls).__new__(cls, *args, **kw)
        else:
            return super().__new__(cls, *args, **kw)

        return self

    @classmethod
    def validator(cls, object):
        exception = exceptions.ValidationError()

        for value in utils.enforce_tuple(cls.value(Type)):
            if value is EMPTY:
                continue
            if isinstance(value, str):
                if value in utils.JSONSCHEMA_SCHEMATA_MAPPING:
                    with exception:
                        utils.JSONSCHEMA_SCHEMATA_MAPPING[value].validator(object)
                else:
                    "we'll consider these forward references"

            elif isinstance(value, type):
                with exception:
                    exceptions.assertIsInstance(object, value)
            else:
                assert False, f"don't know how to enfore type: {value}"

        exception.raises()

    @classmethod
    def py(cls):
        type = cls.value(Type)
        if isinstance(type, tuple):
            return typing.Union[tuple(Type[x].py() for x in type)]
        if type:
            return utils.JSONSCHEMA_PY_MAPPING[type]
        return object

    def __class_getitem__(cls, object):
        if object in utils.JSONSCHEMA_STR_MAPPING:
            object = utils.JSONSCHEMA_STR_MAPPING[object]
        if object in utils.JSONSCHEMA_SCHEMATA_MAPPING:
            return utils.JSONSCHEMA_SCHEMATA_MAPPING[object]

        return Any.__class_getitem__.__func__(cls, object)


class Const(Any):
    id = "validation:/properties/const"

    @classmethod
    def validator(cls, object):
        exceptions.assertEqual(object, cls.value(Const))

    def map(x, f):
        cls = type(x)
        if isinstance(f, type):
            return cls[type](list(map(f, x)))
        return cls(list(map(f, x)))

    def filter(x, f):
        return type(x)(list(filter(f, x)))

    def groupby(x, f):
        import itertools


class Schema_(Any):
    pass


class Comment_(Any):
    id = "core:/properties/$comment"
    pass


class Default(Any):
    id = "metadata:/properties/default"
    pass


class Definitions(Any):
    id = "core:/properties/$defs"
    pass


class Deprecated(Any):
    id = "metadata:/properties/default"
    pass


class Description(Any):
    id = "metadata:/properties/description"
    pass


class Examples(Any):
    id = "metadata:/properties/examples"
    pass


class Optional(Any):
    pass


class ReadOnly(Any):
    id = "metadata:/properties/default"
    pass


class Ref_(Any):
    id = "core:/properties/$ref"
    pass


class Title(Any):
    id = "metadata:/properties/title"
    pass


class Value(Any):
    pass


class WriteOnly(Any):
    id = "metadata:/properties/default"


class Null(Type["null"]):
    def __new__(cls, object=EMPTY):
        if object is EMPTY:
            object = utils.get_default(cls, None)

        if object is EMPTY:
            return

        cls.validate(object)

    @classmethod
    def validator(cls, object):
        exceptions.assertIs(object, None)


Null.register(type(None))


class Bool(Type["boolean"], int):
    def __new__(cls, object=EMPTY):
        if object is EMPTY:
            object = utils.get_default(cls, bool())
        Bool.validator(object)
        try:
            return [false, true][object]
        except NameError:
            return super().__new__(cls, object)

    @classmethod
    def validator(cls, object):
        assert object in (True, False)

    def __repr__(self):
        return repr([False, True][self])


Bool.register(bool)


# the enum type
class Enum(Type):
    id = "validation:/properties/enum"

    def __new__(cls, object=EMPTY):
        enum = cls.value(Enum)
        if object is EMPTY:
            object = next(iter(enum.__members__))
        return enum(object)

    def __class_getitem__(cls, object):
        if isinstance(object, str) and object:
            object = tuple(object.split())
        if not isinstance(object, dict):
            object = utils.enforce_tuple(object)
            object = dict(zip(map(str, object), object))
        return super().__class_getitem__(utils.make_enum(cls, object))

    @classmethod
    def validator(cls, object):
        cls.value(Enum)(object)
        return object

    @classmethod
    def py(cls):
        return cls.value(Enum)


Any.Comment_ = Comment_
Any.Const = Const
Any.Default = Default
Any.Definitions = Definitions
Any.Deprecated = Deprecated
Any.Description = Description
Any.Enum = Enum
Any.Examples = Examples
Any.Optional = Optional
Any.ReadOnly = ReadOnly
Any.Ref_ = Ref_
Any.Title = Title
Any.WriteOnly = WriteOnly


# map a jsonschema to the schemata type
utils.JSONSCHEMA_SCHEMATA_MAPPING.update(
    null=Null,
    boolean=Bool,
    enum=Enum,
)

false, true = Bool(), Bool(True)
