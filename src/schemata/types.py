"""the basis of schemata that begins defining the type system"""

import abc
import builtins
import inspect
import typing
from contextlib import suppress


from . import apis, exceptions, utils
from .utils import ANNO, DOC, EMPTY, PYVER

__all__ = (
    "Any",
    "Bool",
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
        # resolve docstrings
        if DOC in dict and isinstance(dict[DOC], (str, type(None))):
            doc = dict.pop(DOC)
            if doc and isinstance(doc, str):
                bases += (Description[doc],)

        if ANNO in dict:
            anno = dict.pop(ANNO)
            from . import arrays, objects

            for k, v in anno.items():
                if k in dict:
                    anno[k] = anno[k].default(dict[k])
            if any(issubclass(x, arrays.Arrays) for x in (cls,) + bases):
                bases += (arrays.Arrays.Items[objects.Dict[anno]],)
            elif any(issubclass(x, objects.Dict) for x in (cls,) + bases):
                bases += (objects.Dict.Properties[anno],)

        # update the class dict payload
        key = utils.normalize_json_key(name)
        dict.setdefault(ANNO, {})
        if value is not EMPTY:
            dict[ANNO].update({key: value})

        # build
        cls = super().__new__(cls, name, bases, dict)
        cls.__annotations__ = utils.merge(cls)

        return cls

    def key(cls):
        return utils.normalize_json_key(cls.__name__)

    def value(cls, *key, default=EMPTY):
        """get the corresponding value to the class key"""
        if not hasattr(cls, ANNO):
            return

        for k in key or (cls.key(),):
            if isinstance(k, type):
                k = k.key()

            if k in cls.__annotations__:
                return cls.__annotations__[k]
        return default

    @property
    def __doc__(cls):
        """generate docstrings from schema"""
        return utils.get_docstring(cls)

    def __str__(cls):
        return cls.key() or super().__str__()

class Any(apis.FluentType, apis.Validate, apis.TypeConversion, metaclass=MetaType):
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

        self = super(Any, cls).__new__(cls, *args, **kw)

        return self

    @classmethod
    def validator(cls, object):
        exception = exceptions.ValidationError()

        for value in utils.enforce_tuple(cls.value(Type)):
            if value is EMPTY:
                continue
            if isinstance(value, str):
                if value in JSONSCHEMA_SCHEMATA_MAPPING:
                    with exception:
                        JSONSCHEMA_SCHEMATA_MAPPING[value].validator(object)
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
            return JSONSCHEMA_PY_MAPPING[type]
        return object

    def __class_getitem__(cls, object):
        with suppress(NameError):
            if object in JSONSCHEMA_STR_MAPPING:
                object = JSONSCHEMA_STR_MAPPING[object]
            if object in JSONSCHEMA_SCHEMATA_MAPPING:
                return JSONSCHEMA_SCHEMATA_MAPPING[object]
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


class Bool(Type["boolean"]):
    def __new__(cls, object=EMPTY):
        if object is EMPTY:
            object = utils.get_default(cls, bool())
        cls.validate(object)
        return object

    @classmethod
    def validator(cls, object):
        exceptions.assertIsInstance(object, bool)


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

JSONSCHEMA_SCHEMATA_MAPPING = dict(
    null=Null,
    boolean=Bool,
    enum=Enum,
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
