"""the base types for schemata

in this module we introduce the schemata type api
"""

import abc
import collections
import functools
import inspect
import sys
import types
import typing
from contextlib import suppress

try:
    from typing import _ForwardRef as ForwardRef

    _root = True  # pragma: no cover
except ImportError:
    from typing import ForwardRef

    _root = False  # pragma: no cover

Path = type(__import__("pathlib").Path())

from .signatures import Signature


def identity(*args, **kwargs):
    return (args + (None,))[0]


def filter_map(self, *args, **kwargs):
    if self.start is not None:
        args = (filter(self.start, *args),)

    if self.stop is not None:
        args = (map(self.stop, *args),)

    if self.step is not None:
        args = (self.step(*args),)
    return (args + (None,))[0]


class ConsentException(BaseException):
    pass


def forward_strings(*args):
    return tuple(Forward(x)() if isinstance(x, str) else x for x in args)


# a universal call (functor) method for calling schemata objects.
def call(f, *args, **kwargs):

    # lists and dicts dont init properly, mebbe they do now,
    # this function exists because of each cases.
    if callable(f):
        if hasattr(f, "object"):
            return f.object(*args, **kwargs)

        return f(*args, **kwargs)

    if isinstance(f, str):
        return Forward(f)()(*args, **kwargs)
    if isinstance(f, slice):
        return filter_map(f, *args, **kwargs)

    return f


class Forward(ForwardRef, _root=_root):
    # an overloaded forward reference method that allows both strings and literals.
    def __new__(cls, object):
        # only check string Forward References.
        if isinstance(object, str):
            self = super().__new__(cls)
            self.__init__(object)
            return self
        return object

    def consent(self):
        # it would be dangerous too allow any forward reference anytime.
        # consent means that the end user has imported the namespace in sys.modules
        # this will indicate consent
        if isinstance(self.__forward_arg__, str):
            module = self.__forward_arg__.partition(".")[0]
            if module not in sys.modules:
                raise ConsentException(
                    f"Import {module} to consent to making forward references to its attributes."
                )

    def _evaluate(self, force=False, globals=None, locals=None):
        if self.__forward_evaluated__:
            return self.__forward_value__
        if not globals or locals:
            # we've redirected our interests to explicit forward reference off of sys.modules.
            # no errors, just False exceptions
            globals = locals = sys.modules
        self.consent()
        self.__forward_value__ = eval(self.__forward_code__, globals, locals)
        self.__forward_evaluated__ = True
        return self.__forward_value__

    def object(self):
        return self._evaluate()

    __call__ = object


del _root, ForwardRef


def lowercased(x):
    return x[0].lower() + x[1:] if x else x


class ValidationError(BaseException):
    pass


ValidationErrors = (
    ValidationError,
    __import__("jsonschema").ValidationError,
    ValueError,
)


class Schema(dict):
    def __init__(self, object=None):
        if isinstance(object, type):
            object = getattr(object, "__annotations__", {})

        super().__init__(object)

    def merge(*args):
        next = {}

        types = dict(
            **{
                x.form(): {}
                for x in Generic.Mapping.__subclasses__()
                if x is not Generic.Mapping
            },
            **{
                x.form(): ()
                for x in Generic.Plural.__subclasses__()
                + Generic.Nested.__subclasses__()
                if x is not (Generic.Plural, Generic.Nested)
            },
        )
        for x in args:
            for k, v in Schema(x).items():
                if k in types:
                    next.setdefault(k, types[k])
                    if isinstance(types[k], dict):
                        next[k].update(v)
                    elif isinstance(next[k], tuple):
                        for u in v:
                            if isinstance(u, str):
                                if u in next[k]:
                                    continue
                            next[k] += (u,)
                else:
                    next[k] = v

        for k in sorted(next):
            if k in types:
                v = next[k]
                if isinstance(v, dict):
                    o = sorted(v)
                    v = dict(zip(o, map(v.get, o)))

        return Schema(next)

    def new(x, pointer=None):
        if pointer is None:
            pointer = ""
        import jsonpointer

        t = None
        schema = jsonpointer.resolve_pointer(x, pointer)
        types = {
            y.form(): y
            for x in (Generic.Form, Generic.Plural, Generic.Mapping, Generic.Nested)
            for y in x.__subclasses__()
        }
        m = dict(
            boolean=Generic.Bool,
            null=Generic.Null,
            integer=Generic.Integer,
            number=Generic.Number,
            array=Generic.List,
            object=Generic.Dict,
        )
        for k, v in schema.items():
            if k in types:
                if k == "type":
                    v = m.get(k, v)

                if t is None:
                    t = types[k][v]
                else:
                    t = t + types[k][v]
        return t

    def validate(self, x):
        import jsonschema

        jsonschema.Draft7Validator(
            self.ravel(), format_checker=jsonschema.draft7_format_checker
        ).validate(x)
        return x

    def ravel(self):
        if isinstance(self, typing.Pattern):
            return self.pattern
        if isinstance(self, dict):
            d = Schema(zip(self, map(Schema.ravel, self.values())))
            for k in list(d):
                if callable(d[k]):
                    del d[k]

                if k == "enum":
                    v = d[k]
                    if len(v) is 1 and isinstance(*v, dict):
                        d[k] = list(*v)
            return d
        if isinstance(self, (tuple, list)):
            return list(map(Schema.ravel, self))

        if isinstance(self, Generic):
            return Schema.ravel(self.schema())

        return self

    def __contains__(self, x):
        if isinstance(x, dict):
            for k, v in x.items():
                if self.get(k, object()) != v:
                    break
            else:
                return True
            return False

        return dict.__contains__(self, x)

    def hashable(x, t=None):
        if t is None:
            t = ()
        if isinstance(x, type):
            if x not in t:
                t += (x,)
            return x
        if isinstance(x, dict):
            if not isinstance(x, Schema):
                x = Schema(x)

            return tuple((k, Schema.hashable(v, t)) for k, v in x.items())

        if isinstance(x, slice):
            return slice, x.start, x.stop, x.step

        if isinstance(x, list):
            x = tuple(x)

        if isinstance(x, tuple):
            return tuple(Schema.hashable(x, t) for x in x)

        return x


# the Interface represents all of the bespoke type api features we provide through schemata.
class Interface:
    @abc.abstractclassmethod
    def object(cls, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractclassmethod
    def validate(cls, *args):  # pragma: no cover
        return cls.schema().validate(*args)

    @abc.abstractclassmethod
    def strategy(cls, *args):  # pragma: no cover
        pass

    @abc.abstractclassmethod
    def type(cls, **kwargs):  # pragma: no cover
        pass

    @abc.abstractclassmethod
    def pytype(cls, *args):  # pragma: no cover
        if args:
            return type(*args)
        return typing.Any


class Generic(Interface, abc.ABCMeta):
    # the generic base case is the metaclass for all of schemata's typess and protocols
    # in this specific definition we only add magic method definitions to the types

    def __new__(
        cls,
        name,
        bases,
        kwargs,
        **annotations,
    ):
        ANNOTATIONS = "__annotations__"

        # we make a special conditions for list & dictionary types. for subclasses of list or dictionaries
        # the annotations are meaningful and obey different semantics.
        p = {}
        try:
            is_list = any(cls.List in x.__mro__ for x in bases)
            is_dict = any(cls.Dict in x.__mro__ for x in bases)
            if is_list or is_dict:
                if not (cls.Properties.form(cls) or cls.Items.form(cls)):
                    p.update(kwargs.pop(ANNOTATIONS, {}))
        except AttributeError:
            # early on in the module loading we don't have access to List or Dict
            # while we're building the classes. so we pass through the special condition
            # when these objects are not available.
            Dict = List = type(None)
            is_dict = is_list = False

        # we always set a new annotation on the class to avoid and unexpected
        # inheritence confusion.
        kwargs[ANNOTATIONS] = Schema(kwargs.get(ANNOTATIONS, {}))

        for k in tuple(
            k
            for k, v in vars(Interface).items()
            if isinstance(v, abc.abstractclassmethod)
        ):
            if k in kwargs:
                if not isinstance(kwargs[k], classmethod):
                    kwargs[k] = classmethod(kwargs[k])
        t = None
        if p:
            r, d = (), collections.defaultdict(set)
            for k in p:
                if k in kwargs:
                    f = kwargs[k]
                    p[k] = p[k] + cls.Default[f]
                    if isinstance(f, types.FunctionType):
                        s = inspect.signature(f)
                        for a in s.parameters.values():
                            a = a.annotation
                            if isinstance(a, str):
                                a = (a,)
                            if isinstance(a, (list, tuple, set)):
                                for a in a:
                                    d[k].add(a)

                else:
                    if not issubclass(p[k], Default):
                        r += (k,)

            t = (cls.Properties[p],)
            if r:
                t += (cls.Required[r],)

            if d:
                t += (cls.Dependencies[dict(zip(d, map(sorted, d.values())))],)

            if is_dict:
                bases += t

        # finally we make the type
        cls = super().__new__(cls, name, bases, kwargs or {})

        # attach all new types to the Generic so they are easy to access
        setattr(Generic, cls.__name__, getattr(Generic, cls.__name__, cls))

        with suppress(AttributeError):
            cls.__annotations__ = Schema.merge(*cls.__mro__)

        if is_list and t is not None:
            return cls[Generic.type((cls.Dict,) + t)]

        with suppress(NameError):
            cls.__init_subclass__()
        return cls

    def __getitem__(cls, x):
        # getitem on types invokes the type method
        if isinstance(x, slice):
            if x.start is x.stop is x.step is None:
                return cls
        return cls.type(x)

    # here we add symbolic methods to the type for easier composition
    # we take advantage of the getitem method for this reason
    def __add__(cls, object):
        return Generic.type((cls, object))

    def __sub__(cls, object):
        return cls.AllOf[cls, cls.Not[object]]

    # bit shift operators
    def __rshift__(cls, object):
        return Generic.Pipe[cls, object]

    def __lshift__(cls, object):
        return Generic.Pipe[cls, cls.Do[object]]

    def __hash__(cls):
        return hash(cls.schema().hashable())

    def __subclasscheck__(cls, x):
        t = type.__subclasscheck__(cls, x)
        if t:
            return True
        with suppress(AttributeError):
            a, b = x.schema(), cls.schema()
            if any(a) and any(b):
                if a in b:
                    return True

        return x in cls.mro()

    def __instancecheck__(cls, object):
        try:
            cls.validate(object)
            return True
        except ValidationErrors:
            return False

    def __eq__(cls, object):
        if isinstance(object, Generic):
            return cls.schema() == object.schema()
        return type.__eq__(cls, object)

    # conditional operations
    def __xor__(cls, object):
        return cls.OneOf[cls, object]

    def __or__(cls, object):
        return cls.AnyOf[cls, object]

    def __and__(cls, object):
        return cls.AllOf[cls, object]

    # unary operations
    def __neg__(cls):
        return cls.Not[cls]

    def __pos__(cls):
        return cls

    def __r__(cls, op, object):
        return getattr(Generic, f"__{op}__")(object, cls)

    for x in ("add", "sub", "rshift", "lshift", "or", "and", "xor", "mul"):
        locals()[f"__r{x}__"] = functools.partialmethod(__r__, x)

    del x

    # right sided operations
    __rand__ = __and__
    __ror__ = __or__
    __rxor__ = __xor__
    __rneg__ = __neg__
    __rpos__ = __pos__

    def __getattr__(cls, k):

        if k[0].islower():
            k = k[0].upper() + k[1:]
            v = object.__getattribute__(cls, k)

            @functools.wraps(v)
            def call(*x):
                return cls + v[x[0]]

            return call
        return object.__getattribute__(cls, k)

    # the pythonic jsonschema of the type
    def schema(cls):  # pragma: no cover
        return cls.__annotations__

    # generate an example of the schemata type
    def example(cls):
        return cls.strategy().example()

    # generate all the children of a schemata type
    def children(cls, deep=True):  # pragma: no cover

        if not deep:
            yield from cls.__subclasses__()
            return
        yield cls

        for cls in cls.__subclasses__():
            if hasattr(cls, "children"):
                if callable(cls.children):
                    yield from cls.children()

    def attach_parent(cls, x):
        if isinstance(x, (type(None), bool)):
            return x
        with suppress(AttributeError):
            x.parent = cls
        return x

    def type(cls, **kwargs):
        if not isinstance(cls, tuple):
            cls = (cls,)
        return type(cls[0].__name__, cls, kwargs)


class Form(metaclass=Generic):
    hypothesis_strategies = {}

    @classmethod
    def schema(cls):
        return Generic.schema(cls)

    @classmethod
    def validate(cls, *args):
        return cls.schema().validate(*args)

    def __new__(cls, *args, **kwargs):
        # schemata types bubble up instances from the bottom rather than top down.
        with suppress(NotImplementedError):
            return cls.object(*args, **kwargs)
        return cls.validate(*args)

    # the form makes it easy to create new types from class definitions,
    # the annotations take on the form of the cls which defaults to the lowercase name
    def type(cls, object=None, **kwargs):
        if isinstance(object, list):
            object = tuple(object)
        return Generic.type(
            cls,
            __annotations__={cls.form(): object},
            **kwargs,
        )

    @classmethod
    def form(cls, *args):  # pragma: no cover
        n, *_ = cls.__name__.partition("_")
        if n.startswith("At"):
            n = "@" + lowercased(n[2:])
        if cls.__name__.endswith("_"):
            n = "$" + lowercased(n)
        n = lowercased(n)
        if not args:
            return n  #  lowercase x
        x, *_ = args
        if not isinstance(x, type):
            x = type(x)
        if x is not Generic:
            with suppress(AttributeError):
                return x.schema().get(n)

    @classmethod
    def strategy(cls):

        # our default strategy is to create strategies from the schema on
        # all of the objects.
        import hypothesis

        if cls not in cls.hypothesis_strategies:
            # these definitely need to be cached to avoid redundancies in testing.
            cls.hypothesis_strategies[cls] = __import__(
                "hypothesis_jsonschema"
            ).from_schema(cls.schema().ravel())
        return cls.hypothesis_strategies[cls]


_type_mapping = dict(number=float, integer=int, string=str, array=list, object=dict)
_default_mapping = dict(null=type(None), boolean=bool)


class Type(Form):
    def __init__(self, *args, **kwargs):
        # short circuit initialization below this point and execute it ourselves
        # in the object methods
        pass

    @classmethod
    def type(cls, *args):
        cls = super().type(*args)
        e = _type_mapping.get(Type.form(cls)) or ()
        if e:
            return Generic.type((cls, e))
        return cls

    def object(cls, *args, **kwargs):
        if not (args or kwargs) and issubclass(cls, cls.Default):
            f = cls.Default.form(cls)
            if callable(f):
                args, kwargs = (f(*args, **kwargs),), {}

        if (args or kwargs) and not issubclass(cls, cls.Dict):
            args, kwargs = (cls.validate(*args, **kwargs),), {}

        pytype = cls.pytype()
        if pytype in {type(None), bool}:
            if not args:
                try:
                    args = (super().object(),)
                except:
                    args = (pytype(),)
            return args[0]
        with suppress(AttributeError):
            if not (args or kwargs):
                args = (super().object(),)
        if pytype is not None:
            self = pytype.__new__(cls, *args, **kwargs)
            try:
                pytype.__init__(self, *args, **kwargs)
            except TypeError:
                pytype.__init__(self)
            return self
        return args[0]

    @classmethod
    def pytype(cls):
        return {**_type_mapping, **_default_mapping}.get(cls.Type.form(cls))


class Sys(Type):
    """ reference to python objects."""

    def object(cls, *args, **kwargs):
        return cls.pytype()

    def validate(cls, *args):
        return args

    def type(cls, *args, **kwargs):
        if not args:
            return cls
        x, *_ = args

        cls = cls + cls.AtType[x]
        with suppress(ConsentException, ValueError, TypeError):
            t = cls.pytype()
            cls.__signature__ = inspect.signature(t)
        return cls

    def pytype(cls):
        return forward_strings(*cls.AtType.form(cls)[:1])[0]


class Const(Form):
    # a constant
    def object(cls, *args, **kwargs):
        return Const.form(cls)


class Default(Form):
    def object(cls, *args, **kwargs):
        x = Default.form(cls)
        if callable(x):
            return call(x, *args, **kwargs)
        return x


class Plural(Form):
    def type(cls, *args):
        if not args:
            return cls

        if not isinstance(*args, tuple):
            if isinstance(*args, list):
                args = (tuple(*args),)
            else:
                args = (args,)

        return Form.type.__func__(cls, *args)

    @classmethod
    def form(cls, *args):  # pragma: no cover
        return super().form(*args) or ()


class AtType(Plural):
    pass
