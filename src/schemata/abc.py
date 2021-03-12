import abc, functools


class ValidationError(BaseException):
    pass


ValidationErrors = (ValidationError, __import__("jsonschema").ValidationError)


class Generic(abc.ABCMeta):
    """the Class metaclass introduces meaning through RDF contexts into the python annotations.

    types contain a lot information about their object form that can be interpretted at runtime.
    notebooks work specifically well for this because we can dynamically update the metadata
    contents of the notebooks json document. the Generic types extract type & object metadata in
    the form of json-ld documents to provide resuable metadata.

    i can not think of use case where a developer would subclass Generic or Class, it could be done, however
    in RDF land, everything is a Any so i'd prefer folks to subclass Any as it has better
    user and developer affordances. even in this reference implementation the Py types are derived from
    the Any class.

    when deriving subclasses of semantic types we avoid doing work on the context. the context
    information exists primarily to enrich the descriptions of outputs."""

    def __getattribute__(cls, object):
        import types

        if object.startswith("_"):
            return type.__getattribute__(cls, object)

        try:
            from .protocols import Protocol
        except (AttributeError, ImportError):
            return type.__getattribute__(cls, object)

        try:
            object = type.__getattribute__(cls, object)
        except AttributeError as e:
            if object != "__slots__":
                if Protocol in type.__getattribute__(cls, "__mro__"):
                    return cls[object]
            raise e
        if Protocol in type.__getattribute__(cls, "__mro__"):
            if isinstance(object, types.MemberDescriptorType):
                return cls[object.__name__]

        return object

    types, strategies = {}, {}

    def __new__(cls, name, bases, kwargs, **context):
        for x in vars(Generic).values():
            if isinstance(x, abc.abstractclassmethod):
                k = x.__func__.__name__
                if k in kwargs:
                    v = kwargs[k]
                    if not isinstance(v, classmethod):
                        kwargs[k] = classmethod(v)

        kwargs["__annotations__"] = kwargs.get("__annotations__", {})
        cls = super().__new__(cls, name, bases, kwargs or {}, **context)
        setattr(Generic, cls.__name__, cls)

        return cls

    def new_type(cls, **kwargs):

        if not isinstance(cls, tuple):
            if not kwargs:
                return cls

            cls = (cls,)
        id = cls + tuple(Generic.hash_item(kwargs))

        if id not in Generic.types:
            name = "".join(getattr(x, "__name__", "") for x in cls)

            Generic.types[id] = type(name, cls, kwargs)

            type.__init_subclass__()

        return Generic.types[id]

    @classmethod
    def hash_item(cls, x):
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

    def __getitem__(cls, object):
        return cls.new_type(object)

    @staticmethod
    def ravel_schema(x, parent=None):
        """a schema maybe be comprised of python object, yet to be schemafied.

        we iterate through the schema and expose the schema for objects when we can.
        we strip superfluous json-ld content that may distract new users."""
        from .protocols import LD
        from .util import flatten, flatten_type_schema, get_annotations

        if x is parent:
            return "#"

        if isinstance(x, type):
            parent = x
            x = Generic.types.get((x,), x)
            x = flatten_type_schema(x)

        if isinstance(x, dict):
            x = {
                k: Generic.ravel_schema(v, parent=parent)
                for k, v in x.items()
                if k not in LD.names()
            }

        elif isinstance(x, list):
            x = [Generic.ravel_schema(x, parent=parent) for x in x]
        return x

    @abc.abstractclassmethod
    def alias(cls):
        raise NotImplementedError

    @abc.abstractclassmethod
    def annotate(cls, t=None, in_place=False, **kwargs):
        raise NotImplementedError

    def annotations(cls):
        ANNOTATIONS = "__annotations__"
        if isinstance(object, dict) and ANNOTATIONS in object:
            # we could load a dictionary type that lacks annotations
            # in this case the type could have annotations
            return object.get(ANNOTATIONS, {})
        return getattr(object, ANNOTATIONS, {})

    @abc.abstractclassmethod
    def schema(cls, *args, **kwargs):
        raise NotImplementedError

    @abc.abstractclassmethod
    def default(cls, *args, **kwargs):
        raise NotImplementedError

    @abc.abstractclassmethod
    def instance(cls, *args, **kwargs):
        raise NotImplementedError

    @abc.abstractclassmethod
    def validate(cls, *args):
        raise NotImplementedError

    @abc.abstractclassmethod
    def strategy(cls, *args):
        raise NotImplementedError

    @abc.abstractclassmethod
    def cast(cls, *args):
        raise NotImplementedError

    @abc.abstractclassmethod
    def enter(cls):
        raise NotImplementedError

    @abc.abstractclassmethod
    def exit(cls, *e):
        raise NotImplementedError

    def example(cls):
        return cls.strategy().example()

    @abc.abstractclassmethod
    def mediatype(cls, *args, **kwargs):
        raise NotImplementedError

    def children(cls, deep=True):
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
            a = cls.annotations(x)
            if "enum" in a:
                return a["enum"]
        return []

    # here we add symbolic methods to the type for easier composition
    # we take advantage of the getitem method for this reason
    def __add__(cls, object):
        try:
            return Generic.new_type((cls, object))
        except TypeError:
            return Generic.new_type((object, cls))

    def __sub__(cls, object):
        from .composite import AllOf, Not

        return AllOf[cls, Not[object]]

    def __rshift__(cls, object):
        from .literal import Cast

        return Cast[cls, object]

    def __lshift__(cls, object):
        from .literal import Cast, Do

        return Cast[cls, Do[object]]

    def __enter__(cls):
        cls.enter()

    def __exit__(cls, *a):
        cls.exit(*a)

    def __instancecheck__(cls, object):
        try:
            cls.validate(object)
            return True
        except ValidationErrors:
            return False

    def __lt__(cls, object):
        from . import literal as L

        if issubclass(cls, (L.Integer, L.Float)):
            return cls + L.Number.ExclusiveMaximum[object]
        if issubclass(cls, L.String):
            return cls + L.String.MaxLength[object - 1]
        if issubclass(cls, L.Dict):
            return cls + L.Dict.MaxProperties[object - 1]
        if issubclass(cls, L.List):
            return cls + L.List.MaxItems[object - 1]

        return super().__lt__(object)

    def __le__(cls, object):
        from . import literal as L

        if issubclass(cls, (L.Integer, L.Float)):
            return cls + L.Number.Maximum[object]
        if issubclass(cls, L.String):
            return cls + L.String.MaxLength[object]
        if issubclass(cls, L.Dict):
            return cls + L.Dict.MaxProperties[object]
        if issubclass(cls, L.List):
            return cls + L.List.MaxItems[object]

        return super().__le__(object)

    def __gt__(cls, object):
        from . import literal as L

        if issubclass(cls, (L.Integer, L.Float)):
            return cls + L.Number.ExclusiveMinimum[object]
        if issubclass(cls, L.String):
            return cls + L.String.MinLength[object + 1]
        if issubclass(cls, L.Dict):
            return cls + L.Dict.MinProperties[object + 1]
        if issubclass(cls, L.List):
            return cls + L.List.MinItems[object + 1]

        return super().__gt__(object)

    def __ge__(cls, object):
        from . import literal as L

        if issubclass(cls, (L.Integer, L.Float)):
            return cls + L.Number.Minimum[object]
        if issubclass(cls, L.String):
            return cls + L.String.MinLength[object]
        if issubclass(cls, L.Dict):
            return cls + L.Dict.MinProperties[object]
        if issubclass(cls, L.List):
            return cls + L.List.MinItems[object]

        return super().__ge__(object)

    def __mul__(cls, object):
        from . import literal as L

        if issubclass(cls, L.List):
            if issubclass(cls, L.List.MaxItems):
                if issubclass(cls, L.List.MinItems):
                    return cls[L.List * object]
        if issubclass(cls, L.Dict):
            if issubclass(cls, L.Dict.MaxProperties):
                if issubclass(cls, L.Dict.MinItems):
                    return cls[L.Dict * object]

        return (cls <= object) >= object

    def __xor__(cls, object):
        from .composite import OneOf

        return OneOf[cls, object]

    def __or__(cls, object):
        from .composite import AnyOf

        return AnyOf[cls, object]

    def __and__(cls, object):
        from .composite import AllOf

        return AllOf[cls, object]

    def __neg__(cls):
        from .composite import Not

        return Not[cls]

    def __pos__(cls):
        return cls

    def __i__(cls, op, object):
        cls.__annotations__.update(getattr(cls, f"__{op}__", object).__annotations__)
        return cls

    __rand__ = __and__
    __ror__ = __or__
    __rxor__ = __xor__
    __rneg__ = __neg__
    __rpos__ = __pos__

    for x in ("add", " sub", " rshift", " lshift", " or", " and", " xor", " mul"):
        locals()[f"__i{x}__"] = functools.partialmethod(__i__, x)
    del x

    class Alias:
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
