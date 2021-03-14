import abc
import functools


class ValidationError(BaseException):
    pass


ValidationErrors = (ValidationError, __import__("jsonschema").ValidationError)


class ABC:
    # the ABC represents all of the bespoke type api features we provide through schemata.

    # types and strategies are caches for types and hypothesis strategies
    types, strategies = {}, {}

    @abc.abstractclassmethod
    def alias(cls):  # pragma: no cover
        pass

    @abc.abstractclassmethod
    def schema(cls, *args, **kwargs):  # pragma: no cover
        pass

    @abc.abstractclassmethod
    def default(cls, *args, **kwargs):  # pragma: no cover
        pass

    @abc.abstractclassmethod
    def instance(cls, *args, **kwargs):  # pragma: no cover
        pass

    @abc.abstractclassmethod
    def validate(cls, *args):  # pragma: no cover
        pass

    @abc.abstractclassmethod
    def strategy(cls, *args):  # pragma: no cover
        pass

    @abc.abstractclassmethod
    def cast(cls, *args):  # pragma: no cover
        pass

    @abc.abstractclassmethod
    def enter(cls):  # pragma: no cover
        pass

    @abc.abstractclassmethod
    def exit(cls, *e):  # pragma: no cover
        pass

    def example(cls):
        return cls.strategy().example()

    @abc.abstractclassmethod
    def mediatype(cls, *args, **kwargs):  # pragma: no cover
        pass

    def new_type(cls, **kwargs):
        # new_type is our alias for making a new type.
        if not isinstance(cls, tuple):
            if not kwargs:
                return cls

            # we always treat classes as tuples
            cls = (cls,)

        # our types our cached for easier comparison, here we hash the new type
        id = cls + tuple(Generic.hash_item(kwargs))

        if id not in Generic.types:
            # if the hash id doesn't exist then we create it.
            name = "".join(getattr(x, "__name__", "") for x in cls)

            Generic.types[id] = type(name, cls, kwargs)

        return Generic.types[id]

    @classmethod
    def hash_item(cls, x):
        # hash items for caching types we create
        if not isinstance(x, type):
            x = type(x), x
        if not isinstance(x, tuple):
            x = (x,)
        for y in x:
            if isinstance(y, dict):
                for k, v in y.items():
                    yield k
                    yield from Generic.hash_item(v)

            elif isinstance(y, (set, list, tuple)):
                yield from tuple(map(Generic.hash_item, y))

            else:
                yield y

    # type annotation methods
    def annotations(cls):
        return getattr(object, "__annotations__", {})

    def annotate(cls, t=None, in_place=False, **kwargs):
        TYPE = "@type"
        if t is not None:
            kwargs["@type"] = t
        if in_place:
            cls.__annotations__.update(kwargs)
            return cls
        return Generic.new_type(cls, **kwargs)

    # type classmethods
    def children(cls, deep=True):  # pragma: no cover
        from .protocols import Protocol

        if not deep:
            yield from cls.__subclasses__()
            return
        yield cls

        for cls in cls.__subclasses__():
            if issubclass(cls, Protocol):
                continue
            if hasattr(cls, "children"):
                v = getattr(cls, "children")
                if callable(v):
                    yield from cls.children()

    def vocab(cls):
        CONTEXT, VOCAB = "@context", "@vocab"
        for x in cls.__mro__:
            a = Generic.annotations(x)
            if CONTEXT in a:
                if VOCAB in a[CONTEXT]:
                    return a[CONTEXT][VOCAB]

    def choices(cls):
        for x in cls.__mro__:
            a = Generic.annotations(x)
            if "enum" in a:
                return a["enum"]
        return []

    # staticmethods
    @staticmethod
    def flatten_schema(cls):
        import collections

        ANNOTATIONS = "__annotations__"
        return dict(
            collections.ChainMap(*(getattr(x, ANNOTATIONS, {}) for x in cls.__mro__))
        )

    @staticmethod
    def ravel_schema(x, parent=None):
        """a schema maybe be comprised of python object, yet to be schemafied.

        we iterate through the schema and expose the schema for objects when we can.
        we strip superfluous json-ld content that may distract new users."""
        from .protocols import LD

        if x is parent:
            return "#"  # pragma: no cover

        if isinstance(x, type):
            parent = x
            x = Generic.types.get((x,), x)
            x = Generic.flatten_schema(x)

        if isinstance(x, dict):
            x = {
                k: Generic.ravel_schema(v, parent=parent)
                for k, v in x.items()
                if k not in LD.names()
            }

        elif isinstance(x, list):
            x = [Generic.ravel_schema(x, parent=parent) for x in x]
        return x

    def _attach_parent(cls, x):
        if isinstance(x, (type(None), bool)):
            return x
        x.parent = cls
        return x


class Generic(ABC, abc.ABCMeta):
    # the generic base case is the metaclass for all of schemata's typess and protocols
    # in this specific definition we only add magic method definitions to the types

    def __new__(
        cls,
        name,
        bases,
        kwargs,
        context=None,
        vocab=None,
        base=None,
        language=None,
        **annotations,
    ):
        VOCAB, BASE, LANGUAGE, CONTEXT, ANNOTATIONS = (
            "@vocab",
            "@base",
            "@language",
            "@context",
            "__annotations__",
        )

        for x in vars(ABC).values():
            # since we've defined our base class completely, we enforce our abstract methods
            # to be classmethods. we have to do this before object creation otherwise
            # we lose track of our class methods and would have to attach them to
            # the type method afterwards
            if isinstance(x, abc.abstractclassmethod):
                k = x.__func__.__name__
                if k in kwargs:
                    v = kwargs[k]
                    if not isinstance(v, classmethod):
                        kwargs[k] = classmethod(v)

        # we make a special conditions for list & dictionary types. for subclasses of list or dictionaries
        # the annotations are meaningful and obey different semantics.
        properties = {}
        try:
            from .types import Dict, List

            if any(issubclass(x, (List, Dict)) for x in bases):
                properties = kwargs.pop("__annotations__", {})
        except (AttributeError, ImportError):
            # early on in the module loading we don't have access to List or Dict
            # while we're building the classes. so we pass through the special condition
            # when these objects are not available.
            pass

        # we always set a new annotation on the class to avoid and unexpected
        # inheritence confusion.
        kwargs[ANNOTATIONS] = kwargs.get(ANNOTATIONS, {})

        # build the linked context before instantiating the type
        # this includes keywords for vocab, base, and language (type is missing atm)
        if context is None:
            context = {}

        if vocab:
            context[VOCAB] = str(vocab)

        if base:
            context[BASE] = str(base)

        if language:
            context[LANGUAGE] = language

        if context:
            kwargs[ANNOTATIONS].update({CONTEXT: context})

        # finally we make the type
        cls = super().__new__(cls, name, bases, kwargs or {})

        # put the type on the Generic so it is easier to get to.
        setattr(Generic, cls.__name__, getattr(Generic, cls.__name__, cls))

        # use our symbollic logic to tend to the properties if we found any.
        # we'll never have properties somethign other than lists or dicts
        if properties:
            return cls[properties]
        return cls

    def __getitem__(cls, x):
        # getitem on types invokes the new_type method
        if isinstance(x, slice):
            if x.start is x.stop is x.step is None:
                return cls
        return cls.new_type(x)

    # here we add symbolic methods to the type for easier composition
    # we take advantage of the getitem method for this reason
    def __add__(cls, object):
        return Generic.new_type((cls, object))

    def __sub__(cls, object):
        from .types import AllOf, Not

        return AllOf[cls, Not[object]]

    # bit shift operators
    def __rshift__(cls, object):
        from .types import Cast

        return Cast[cls, object]

    def __lshift__(cls, object):
        from .types import Cast, Do

        return Cast[cls, Do[object]]

    # context manager operators
    def __enter__(cls):
        # alias entering the type context with the enter classmethod
        cls.enter()

    def __exit__(cls, *a):
        cls.exit(*a)

    # class checking
    def __instancecheck__(cls, object):
        try:
            cls.validate(object)
            return True
        except ValidationErrors:
            return False

    # total ordering
    # we do overload __eq__ because we need for the comparison
    # if we do overload __eq__ then we can compare on annotations and cls mebbe
    # this way we wouldn't have to cache
    # otherwise we overload lt, le, gt, ge
    def __lt__(cls, object):
        from . import types as T

        if issubclass(cls, (T.Integer, T.Float)):
            return cls + T.Number.ExclusiveMaximum[object]
        if issubclass(cls, T.String):
            return cls + T.String.MaxLength[object - 1]
        if issubclass(cls, T.Dict):
            return cls + T.Dict.MaxProperties[object - 1]
        if issubclass(cls, T.List):
            return cls + T.List.MaxItems[object - 1]

        return super().__lt__(object)

    def __le__(cls, object):
        from . import types as T

        if issubclass(cls, (T.Integer, T.Float)):
            return cls + T.Number.Maximum[object]
        if issubclass(cls, T.String):
            return cls + T.String.MaxLength[object]
        if issubclass(cls, T.Dict):
            return cls + T.Dict.MaxProperties[object]
        if issubclass(cls, T.List):
            return cls + T.List.MaxItems[object]

        return super().__le__(object)

    def __gt__(cls, object):
        from . import types as T

        if issubclass(cls, (T.Integer, T.Float)):
            return cls + T.Number.ExclusiveMinimum[object]
        if issubclass(cls, T.String):
            return cls + T.String.MinLength[object + 1]
        if issubclass(cls, T.Dict):
            return cls + T.Dict.MinProperties[object + 1]
        if issubclass(cls, T.List):
            return cls + T.List.MinItems[object + 1]

        return super().__gt__(object)

    def __ge__(cls, object):
        from . import types as T

        if issubclass(cls, (T.Integer, T.Float)):
            return cls + T.Number.Minimum[object]
        if issubclass(cls, T.String):
            return cls + T.String.MinLength[object]
        if issubclass(cls, T.Dict):
            return cls + T.Dict.MinProperties[object]
        if issubclass(cls, T.List):
            return cls + T.List.MinItems[object]

        return super().__ge__(object)

    def __mul__(cls, object):
        from . import types as T

        if issubclass(cls, T.List):
            if issubclass(cls, T.List.MaxItems):
                if issubclass(cls, T.List.MinItems):
                    return cls[T.List * object]
        if issubclass(cls, T.Dict):
            if issubclass(cls, T.Dict.MaxProperties):
                if issubclass(cls, T.Dict.MinItems):
                    return cls[T.Dict * object]

        return (cls <= object) >= object

    # conditional operations
    def __xor__(cls, object):
        from .types import OneOf

        return OneOf[cls, object]

    def __or__(cls, object):
        from .types import AnyOf

        return AnyOf[cls, object]

    def __and__(cls, object):
        from .types import AllOf

        return AllOf[cls, object]

    # unary operations
    def __neg__(cls):
        from .types import Not

        return Not[cls]

    def __pos__(cls):
        return cls

    # incremental operations
    def __i__(cls, op, object):
        cls.__annotations__.update(getattr(cls, f"__{op}__", object).__annotations__)
        return cls

    for x in ("add", " sub", " rshift", " lshift", " or", " and", " xor", " mul"):
        locals()[f"__i{x}__"] = functools.partialmethod(__i__, x)
    del x

    # right sided operations
    __rand__ = __and__
    __ror__ = __or__
    __rxor__ = __xor__
    __rneg__ = __neg__
    __rpos__ = __pos__


class Alias:
    # the alias makes it easy to create new types from class definitions,
    # the annotations take on the alias of the cls which defaults to the lowercase name
    @classmethod
    def new_type(cls, object=None):

        c = Generic.new_type(cls, __annotations__={cls.alias(): object})

        return c


class Plural(Alias):
    @classmethod
    def new_type(cls, object=None):
        if not isinstance(object, tuple):
            object = (object,)
        return super().new_type(object)


Generic.Alias, Generic.Plural = Alias, Plural
