"""base metaclasses, forms, and types for schemata

this module defines the core type constructors for schemata. it does not export any
actual type implementations, these are composed in the types module
"""

import abc
import collections
import functools
import inspect
import typing

from . import exceptions, util


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
    def py(cls):  # pragma: no cover
        return typing.Any

    @abc.abstractclassmethod
    def form(cls):  # pragma: no cover
        pass

    @abc.abstractclassmethod
    def forms(cls, *args):  # pragma: no cover
        pass

    @abc.abstractclassmethod
    def widget(cls, *args):
        import IPython

        return IPython.display.DisplayHandle()


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
                if not (cls.Properties.forms(cls) or cls.Items.forms(cls)):
                    p.update(kwargs.pop(ANNOTATIONS, {}))
        except AttributeError:
            # early on in the module loading we don't have access to List or Dict
            # while we're building the classes. so we pass through the special condition
            # when these objects are not available.
            Dict = List = type(None)
            is_dict = is_list = False

        # we always set a new annotation on the class to avoid and unexpected
        # inheritence confusion.
        kwargs[ANNOTATIONS] = util.Schema(kwargs.get(ANNOTATIONS, {}))

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
                    if isinstance(f, __import__("types").FunctionType):
                        s = inspect.signature(f)
                        for a in s.parameters.values():
                            a = a.annotation
                            if isinstance(a, str):
                                a = (a,)
                            if isinstance(a, (list, tuple, set)):
                                for a in a:
                                    d[k].add(a)

                else:
                    if not issubclass(p[k], cls.Default):
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

        with util.suppress(AttributeError):
            cls.__annotations__ = util.Schema.merge(*cls.__mro__)

        if is_list and t is not None:
            return cls[Generic.type((cls.Dict,) + t)]

        with util.suppress(NameError):
            cls.__init_subclass__()
        return cls

    def __getitem__(cls, x):
        # getitem on types invokes the type method
        if isinstance(x, slice):
            if x.start is x.stop is x.step is None:
                return cls
        return cls.type(x)

    def __add__(cls, object):
        return Generic.type((cls, object))

    def __sub__(cls, object):
        return cls.AllOf[cls, cls.Not[object]]

    def __rshift__(cls, object):
        return Generic.Pipe[cls, object]

    def __lshift__(cls, object):
        return cls >> cls.Do[object]

    def __hash__(cls):
        return hash(cls.schema().hashable())

    def __subclasscheck__(cls, x):
        t = type.__subclasscheck__(cls, x)
        if t:
            return True
        with util.suppress(AttributeError):
            a, b = x.schema(), cls.schema()
            if any(a) and any(b):
                if a in b:
                    return True

        return x in cls.mro()

    def __instancecheck__(cls, object):
        try:
            cls.validate(object)
            return True
        except exceptions.ValidationErrors:
            return False

    def __eq__(cls, object):
        if isinstance(object, Generic):
            return cls.schema() == object.schema()
        with util.suppress(AttributeError):
            if cls.Py in cls.__mro__:
                with util.suppress(IndexError):
                    return object == cls.Py.object.__func__(cls)

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
                return cls + v.type(*x)

            return call
        return object.__getattribute__(cls, k)

    # the pythonic jsonschema of the type
    def schema(cls):  # pragma: no cover
        return cls.__annotations__

    # generate an example of the schemata type
    def example(cls):
        return cls.strategy().example()

    def _attach_parent(cls, x):
        if isinstance(x, (type(None), bool)):
            return x
        with util.suppress(AttributeError):
            x.parent = cls
        return x

    def type(cls, **kwargs):
        if not isinstance(cls, tuple):
            cls = (cls,)
        return type(getattr(cls[0], "__name__", repr(cls[0])), cls, kwargs)


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
        with util.suppress(NotImplementedError):
            return cls.object(*args, **kwargs)
        return cls.validate(*args)

    # the form makes it easy to create new types from class definitions,
    # the annotations take on the form of the cls which defaults to the lowercase name
    def type(cls, *args, **kwargs):
        if not (args or kwargs):
            return cls

        if isinstance(*args, list):
            args = (tuple(*args),)
        return Generic.type(
            cls,
            __annotations__={cls.form(): util.identity(*args)},
            **kwargs,
        )

    @classmethod
    def form(cls):
        n, *_ = cls.__name__.partition("_")
        if n.startswith("At"):
            n = "@" + util.lowercased(n[2:])
        n = util.lowercased(n)
        return n  #  lowercase x

    @classmethod
    def forms(cls, *args):
        x, *_ = args
        if not isinstance(x, type):
            x = type(x)
        if x is not Generic:
            with util.suppress(AttributeError):
                return x.schema().get(cls.form())

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
_python_mapping = {**_type_mapping, **_default_mapping}


class Type(Form):
    @classmethod
    def concrete_type(cls):
        return _python_mapping.get(cls.Type.forms(cls))

    def py(cls):  # pragma: no cover
        return cls.concrete_type()

    def __init__(self, *args, **kwargs):
        # short circuit initialization below this point and execute it ourselves
        # in the object methods
        pass

    def object(cls, *args, **kwargs):
        if not (args or kwargs) and issubclass(cls, cls.Default):
            f = cls.Default.forms(cls)
            if callable(f):
                args, kwargs = (f(*args, **kwargs),), {}

        if (args or kwargs) and not issubclass(cls, cls.Dict):
            args, kwargs = (cls.validate(*args, **kwargs),), {}

        t = cls.concrete_type()
        if t in {type(None), bool}:
            if not args:
                try:
                    args = (super().object(),)
                except:
                    args = (t(),)
            return args[0]
        with util.suppress(AttributeError):
            if not (args or kwargs):
                args = (super().object(),)
        if t is not None:
            self = t.__new__(cls, *args, **kwargs)
            try:
                t.__init__(self, *args, **kwargs)
            except TypeError:
                t.__init__(self)
            return self
        return args[0]


class Const(Form):
    # a constant
    def object(cls, *args, **kwargs):
        return Const.forms(cls)


class Default(Form):
    def object(cls, *args, **kwargs):
        x = Default.forms(cls)
        if callable(x):
            return util.call(x, *args, **kwargs)
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
    def forms(cls, *args):  # pragma: no cover
        return super().forms(*args) or ()


class AtType(Plural):
    pass


class Numeric(Form):
    pass


class Nested(Plural):
    @classmethod
    def type(cls, object):
        x = super().type(object)
        v = ()
        for y in cls.forms(x):
            if issubclass(y, cls):
                v += cls.forms(y)
            else:
                v += (y,)
        x.__annotations__[cls.form()] = v
        return x


class Value(Plural):
    @classmethod
    def form(cls):
        return "value"


class Mapping(Form):
    @classmethod
    def forms(cls, *args):  # pragma: no cover
        return super().forms(*args) or {}


# json schema formes


class MinLength(Numeric):
    pass


class MaxLength(Numeric):
    pass


class Pattern(Form):
    @classmethod
    def type(cls, *x):
        import re

        if isinstance(*x, str):
            x = (re.compile(*x),)
        return super().type(*x)

    def py(cls):
        return typing.Pattern


class Format(Form):
    pass


class MultipleOf(Numeric):
    pass


class Minimum(Numeric):
    pass


class Maximum(Numeric):
    pass


class ExclusiveMaximum(Numeric):
    pass


class ExclusiveMinimum(Numeric):
    pass


class Items(Form):
    pass


class Contains(Form):
    pass


class AdditionalItems(Form):
    pass


class MinItems(Numeric):
    pass


class MaxItems(Numeric):
    pass


class UniqueItems(Form):
    pass


class Properties(Mapping):
    pass


class AdditionalProperties(Form):
    def __missing__(self, key):
        cls = type(self)
        p = AdditionalProperties.forms(cls)
        if p:
            self.update({key: util.call(p)})
        return self[key]


class Dependencies(Mapping):
    pass


class Required(Plural):
    pass


class PropertyNames(Mapping):
    pass


class MinProperties(Numeric):
    pass


class MaxProperties(Numeric):
    pass


class PatternProperties(Mapping):
    pass


class Keys(Form):
    pass


class ContentMediaType(Form):
    def __init_subclass__(cls):
        t = cls.ContentMediaType.forms(cls)
        for e in cls.FileExtension.forms(cls) if t else ():
            __import__("mimetypes").add_type(t, e)

    def _repr_mimebundle_(self, include=None, exclude=None):
        return {
            "text/plain": str(self),
            ContentMediaType.forms(self): self,
        }, {}


class Examples(Plural):
    pass


class Title(Form):
    pass


class Description(Form):
    pass


# schemata specific formes


class Optional(Form):
    pass


class FileExtension(Plural):
    pass


class Args(Plural):
    pass


class Kwargs(Mapping):
    pass


class AtContext(Mapping):
    pass


class AtVocab(Form):
    pass


class AtBase(Form):
    pass


class AtLanguage(Form):
    pass


class AtId(Form):
    pass


class AtGraph(Plural):
    pass


class Literal:
    @classmethod
    def type(cls, *x):
        return cls.default(*x)


class UpdateDisplay:
    def _update_display(self):
        if hasattr(self, "_display_handle"):
            try:
                d, md = self._repr_mimebundle_(None, None)
                self._display_handle.update(d, metadata=md, raw=True)
            except AttributeError:
                self._display_handle.update({"text/plain": str(self)}, raw=True)

    def _ipython_display_(self):
        import IPython

        if not hasattr(self, "_display_handle"):
            self._display_handle = IPython.display.DisplayHandle()
        try:
            d, md = self._repr_mimebundle_(None, None)
            self._display_handle.display(d, metadata=md, raw=True)
        except AttributeError:
            self._display_handle.display({"text/plain": str(self)}, raw=True)
