"""the basis of schemata that begins defining the type system"""

import abc
import builtins
import enum
import inspect
import os
import typing

from numpy.lib.arraysetops import isin

import schemata

from . import builders, exceptions, mixins, utils
from .utils import ANNO, DOC, EMPTY

__all__ = ("Any", "Bool", "Const", "Enum", "Envvar", "Any", "Schemata", "Null", "Type")


def get_bases(cls, bases, dict):
    """build the underlying schemata types for python class syntaxes"""
    is_array = any(issubclass(cls, (tuple, list, set)) for cls in bases)
    is_object = any(issubclass(cls, builtins.dict) for cls in bases)

    schema = {}

    if dict.get(DOC):
        schema["description"] = dict[DOC]

    if is_array or is_object:
        # for lists and dicts, collect schema features from python lanuage features
        schema.update(
            properties=builtins.dict(dict[ANNO]),
            required=(),
            dependencies={},
            definitions={},
        )
        dict[ANNO].clear()

        ignore = set(sum(map(dir, bases), []))
        for k, v in dict.items():
            if callable(v):
                if isinstance(v, Schemata):
                    if getattr(v, ANNO, None):
                        schema["definitions"][k] = v
                elif inspect.isfunction(v):
                    sig = inspect.signature(v)

                    if sig.return_annotation is not inspect._empty:
                        schema["properties"][k] = sig.return_annotation

                    if (
                        next(iter(sig.parameters.values())).annotation
                        is not inspect._empty
                    ):
                        schema["dependencies"].update({k: builders.from_signature(v)})
            elif k in schema["properties"]:
                schema["properties"][k] += Default[v]

    schema = {k: v for k, v in schema.items() if v}

    if schema:
        schema = Schemata.from_schema(schema)
        if is_array:
            schema = Schemata.from_schema(items=schema)

        return (schema,)
    return ()


def get_ordered_keys(cls):
    schema = cls.schema(1)
    order = list(schema.get("required", []))
    order += list(schema.get("properties", {}))
    for k, v in schema.get("dependencies", {}).items():
        if k in order:
            i = order.index(k)
            order = order[:i] + list(v.get("required", [])) + order[i:]
    return sorted(set(order), key=order.index)


class Schemata(mixins.TypeOps, abc.ABCMeta):
    """a schemaful python type"""

    def __new__(cls, name, bases, dict, value=EMPTY):
        """\
instantiate a new schemata type.

* __annotations__ refer to dictionary properties of like array or object flavor
* __doc__ refers the description of the class
        
        """
        # ensure annotations on the class
        dict.setdefault(ANNO, {})
        if value is not EMPTY:
            dict[ANNO].update({utils.normalize_json_key(name): value})

        cls = super().__new__(cls, name, bases + get_bases(cls, bases, dict), dict)
        cls.__annotations__ = utils.merge(cls)

        comments = inspect.getcomments(cls)
        if comments:
            cls.__annotations__["$comment"] = comments

        with utils.suppress(NameError):
            setattr(Any, cls.__name__, getattr(Any, cls.__name__, cls))

        if issubclass(cls, builtins.dict):
            with utils.suppress(ImportError):
                cls._ordered_keys = get_ordered_keys(cls)

        return cls

    def key(cls):
        return utils.normalize_json_key(cls.__name__)

    def value(cls, *key, default=EMPTY):
        """get the corresponding value to the class key"""
        for k in key or (Schemata.key(cls),):
            if isinstance(k, type):
                k = k.key()

            if k in cls.__annotations__:
                v = cls.__annotations__[k]
                if isinstance(v, utils.Literal):
                    v = str(v)
                return v

        return default

    def __enter__(cls):
        setattr(cls, "_hold_validation", getattr(cls, "_hold_validation", 0))
        cls._hold_validation += 1
        return cls

    def __exit__(cls, *e):
        cls._hold_validation -= 1

    @classmethod
    def from_file(cls, file):
        from .files import File

        return cls.from_schema(File(file).load())

    @classmethod
    def from_schema(cls, *args, **kwargs):
        return builders.InstanceBuilder(*args, **kwargs).build()

    @classmethod
    def from_signature(cls, callable):
        return builders.SignatureBuilder(callable).build()

    @property
    def __doc__(cls):
        return builders.NumPyDoc(cls).build()

    def __instancecheck__(cls, object):
        try:
            cls.validate(object)
        except:
            return False
        return True

    def verified(cls, *args, **kwargs):
        with cls:
            return cls(*args, **kwargs)

    def audit(cls, object, max=10):
        """audit the object against a class returning multiple failures"""
        exception = exceptions.ValidationException(cls, items=max)
        with utils.suppress(BaseException):
            exception.validate(object)
        return exception

    def cast(cls, *args, **kwargs):
        self = cls.verified(*args, **kwargs)
        self.validate(self)
        return self

    def new_type(cls, value=EMPTY, bases=None):
        if utils.IN_SPHINX and isinstance(value, str):
            value = utils.Literal(value)
        return type(cls.__name__, (cls,) + utils.enforce_tuple(bases), {}, value=value)

    def schema(cls, ravel=None):
        return utils.get_schema(cls, ravel=ravel)

    def validate(cls, object):
        if not getattr(cls, "_hold_validation", 0):
            exceptions.ValidationException(cls).validate(object)
        return object

    def validator(cls, object):
        pass

    def __signature__(cls):
        return builders.SignatureBuilder(cls).build()

    def to_doctest(cls):
        import doctest
        import types

        module = types.ModuleType(cls.__module__)
        setattr(module, "__test__", {cls.__name__: cls})
        return doctest.DocTestSuite(module)

    def to_unittest(cls):
        import unittest

        suite = unittest.TestSuite()
        suite.addTests(Schemata.to_doctest(cls))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromTestCase(cls + unittest.TestCase)
        )
        return suite

    def to_test_results(cls):
        import unittest

        result = unittest.TestResult()
        Schemata.to_unittest(cls).run(result)
        return result


class Any(metaclass=Schemata):
    def __new__(cls, *args, **kwargs):
        if issubclass(cls, dict):
            args, kwargs = (dict(*args, **kwargs),), {}
        if not args:
            args = (utils.get_default(cls, default=object),)

        if args:
            args = (cls.validate(*args[:1]),)

        if not utils.get_first_builtin_type(cls):
            if isinstance(*args[:1], Any):
                return args[0]

            cls = Type[type(*args[:1])]
        return super(Any, cls).__new__(cls, *args, **kwargs)

    def __class_getitem__(cls, object):
        return cls.new_type(object)

    def pipe(self, callable, *args, **kwargs):
        args = (self,) + args
        for f in utils.enforce_tuple(callable):
            args, kwargs = (f(*args, **kwargs),), {}
        return args[0]

    def print(self):
        try:
            import rich

            return rich.print(self)
        except ModuleNotFoundError:
            import pprint

            if isinstance(self, str):
                print(self)
            else:
                pprint.pprint(self)

    @classmethod
    def schema(cls, ravel=None):
        return Schemata.schema(cls, ravel)

    @classmethod
    def validate(cls, object):
        return Schemata.validate(cls, object)

    @classmethod
    def validator(cls, object):
        return Schemata.validator(cls, object)


class Type(Any):
    @classmethod
    def to_pytype(cls):
        types = Schemata.value(cls, Type)
        if not types:
            return type
        result = ()
        for t in utils.enforce_tuple(types):
            if isinstance(t, str):
                if t in utils.JSONSCHEMA_PY_MAPPING:
                    t = utils.JSONSCHEMA_PY_MAPPING[t]

            result += utils.enforce_tuple(t)
        return result

    @classmethod
    def validator(cls, object):
        exceptions.assertIsInstance(object, cls.to_pytype())

    def __class_getitem__(cls, object):
        """Type item getter methods

        Examples
        --------

        >>> Type["integer", "number"].schema()
        {'type': ('integer', 'number')}

        >>> Type["integer"]
        schemata.numbers.Integer

        >>> assert Type["integer"] is Type[int]
        """

        if object in utils.JSONSCHEMA_STR_MAPPING:
            object = utils.JSONSCHEMA_STR_MAPPING[object]

        if object in utils.JSONSCHEMA_SCHEMATA_MAPPING:
            return utils.JSONSCHEMA_SCHEMATA_MAPPING[object]

        return Any.__class_getitem__.__func__(cls, object)


class Const(Any):
    @classmethod
    def validator(cls, object):
        """
        >>> Const[1](1)
        1
        """
        exceptions.assertEqual(object, cls.value(Const))


class Schema_(Any):
    pass


class Parent_(Any):
    pass


class Comment_(Any):
    pass


class Default(Any):
    pass


class Definitions(Any):
    pass


class Deprecated(Any):
    pass


class Description(Any):
    pass


class Examples(Any):
    pass


class Optional(Any):
    pass


class ReadOnly(Any):
    pass


class Ref_(Any):
    pass


class Title(Any):
    pass


class WriteOnly(Any):
    pass


class Null(Type["null"]):
    def __new__(cls, object=EMPTY):
        if object is EMPTY:
            object = utils.get_default(cls, None)

        if object is EMPTY:
            return

        cls.validate(object)


Null.register(type(None))


class Bool(Type["boolean"], int):
    @classmethod
    def validator(cls, object):
        assert object in (True, False)


Bool.register(bool)


class Enum(Type):
    def __new__(cls, object=EMPTY):
        enum = cls.value(Enum)
        if object is EMPTY:
            object = next(iter(enum.__members__))
        return enum(object)

    def __class_getitem__(cls, object):
        """
        >>> Enum["a b"].schema(1)
        {'enum': ['a', 'b']}

        >>> Enum[1, 2].schema(1)
        {'enum': ['1', '2']}

        >>> Enum[dict(a=1, b=2)].schema(1)
        {'enum': ['a', 'b']}

        >>> Integer.enum((1, 2)).schema(1)
        {'type': 'integer', 'enum': ['1', '2']}
        """
        if isinstance(object, str) and object:
            object = tuple(object.split())
        if not isinstance(object, dict):
            object = utils.enforce_tuple(object)
            object = dict(zip(map(str, object), object))
        return super().__class_getitem__(utils.make_enum(cls, object))

    @classmethod
    def validator(cls, object):
        Schemata.value(cls, Enum)(object)
        return object


# map a jsonschema to the schemata type
utils.JSONSCHEMA_SCHEMATA_MAPPING.update(
    null=Null,
    boolean=Bool,
    enum=Enum,
)


class Envvar(Any):
    def __new__(cls, *args, **kwargs):
        return os.getenv(Schemata.value(cls, Envvar))

    @classmethod
    def list(cls):
        return list(os.environ)
