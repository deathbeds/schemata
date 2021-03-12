import pathlib
import typing

from . import base as B
from . import literal as L
from . import protocols as P


Path = type(pathlib.Path())

del pathlib

B.Any.annotate(P.RDFS["Resource"], in_place=True)


class Literal(B.Any, type=P.RDFS["Literal"], vocab=P.PROPS.vocab()):
    """the Literal is the bridge between actual python types and Generic types, they emit concrete
    implementations of python types like int, float, list, dict with they advantage that they may be described
    in rdf notation."""

    @classmethod
    def instance(cls, *args):

        # update the arguments with the defaults or constant if defined
        args = cls.default(*args)

        # define p as the prior type of the argument
        p = tuple(map(type, args))
        if p in B.Generic.types:
            p = (B.Generic.types[p],)

        if issubclass(cls, p):
            return super().instance(*args)
        return B.call(*p, *args)

    def __init_subclass__(
        cls, type=None, context=None, vocab=None, base=None, **extras
    ):
        super().__init_subclass__(
            type=type, context=context, vocab=vocab or cls.vocab(), base=base, **extras
        )


class Validate:
    @classmethod
    def instance(cls, *args, **kwargs):
        from .composite import Composite

        value = super().instance(*args, **kwargs)
        if issubclass(cls, Composite):
            # this would have already been validated because now we'd be augmenting the base calsses
            return value
        return cls.validate(value)[0]

    @classmethod
    def validate(cls: typing.Union[B.Generic, dict], *args):
        import jsonschema

        args = cls.default(*args)
        if not isinstance(cls, dict):
            cls = cls.schema()
        try:
            jsonschema.Draft7Validator(
                cls, format_checker=jsonschema.draft7_format_checker
            ).validate(*args)
        except BaseException as e:
            # raise the schemamata validation error to make checking easier
            raise e from B.ValidationError
        return args


class Const(B.Any, B.Generic.Alias):
    def instance(cls, *args, **kwargs):
        return cls.default(*args, **kwargs)[0]


class Default(Const):
    pass


class Null(Validate, Literal, type=P.RDF["nil"]):
    type: "null"

    def instance(cls, *args, **kwargs):
        cls.validate(*cls.default(*args, **kwargs))

    def default(cls, *args, **kwargs):
        return super().default(*args, **kwargs) or (None,)


Null.register(type(None))

B.Generic.types[
    type(None),
] = Null


class Bool(Validate, Literal, type=P.XSD["boolean"]):
    type: "boolean"

    def instance(cls, *args, **kwargs):
        args = cls.default(*args, **kwargs)
        return cls.validate(*args)[0]

    @classmethod
    def default(cls, *args, **kwargs):
        return super().default(*args, **kwargs) or (bool(),)


B.Generic.types[
    bool,
] = Bool
Bool.register(bool)


class String(Validate, Literal, str, type=P.XSD["string"]):
    type: "string"

    @classmethod
    def default(cls, *args, **kwargs):
        return super().default(*args, **kwargs) or (str(),)


B.Generic.types[
    str,
] = String


class File(Validate, Literal, Path):
    type: "string"

    __loader__: String = str
    __dumper__: String = str

    @classmethod
    def _get_value_type(cls, object):
        v = getattr(cls, "value", None)
        if v is None:
            v = type(object)
        return v

    def read(self):
        t = self._get_value_type(self)
        f = lambda x: x
        # if "__loader__" in t.__annotations__:
        #     f = t.__annotations__["__loader__"]
        return f(t.__loader__(self.read_text()))

    def write(self, object):
        return self.write_text(self._get_value_type(self).__dumper__(object))


B.Generic.types[
    Path,
] = File


class Number(Validate, Literal, float, type=P.XSD["decimal"]):
    type: "number"

    @classmethod
    def default(cls, *args, **kwargs):
        return super().default(*args, **kwargs) or (float(),)


Float = (
    Number  # number is canonical, but too many times i reach for float so i aliased it
)
B.Generic.types[
    float,
] = Number


class Integer(Validate, Literal, int, type=P.XSD["integer"]):
    type: "integer"

    @classmethod
    def default(cls, *args, **kwargs):
        return super().default(*args, **kwargs) or (int(),)


B.Generic.types[
    int,
] = Integer


class List(Validate, Literal, list, type=P.RDF["List"]):
    type: "array"

    @classmethod
    def default(cls, *args, **kwargs):
        return super().default(*args, **kwargs) or ([],)

    @classmethod
    def new_type(cls, object):
        if isinstance(object, dict):
            object = Dict[object]
        if isinstance(object, (list, tuple)):
            return Tuple[list(object)]
        return cls + cls.Items[object]


B.Generic.types[
    bool,
] = Bool


class Tuple(List, type=P.RDF["Alt"]):
    @classmethod
    def new_type(cls, object):
        if B.Generic.is_empty_slice(object):
            return cls
        if isinstance(object, list):
            object = tuple(object)
        if not isinstance(object, tuple):
            object = (object,)
        return cls + cls.Items[list(object)]


B.Generic.types[
    tuple,
] = Tuple


class Set(List, type=P.RDF["Bag"]):
    pass


B.Generic.types[
    set,
] = Set


class Dict(Validate, Literal, dict):
    type: "object"

    @classmethod
    def default(cls, *args, **kwargs):
        import inspect

        if args:
            if all(isinstance(x, dict) for x in args):
                pass
            else:
                sig = inspect.signature(cls)
                if sig != inspect.signature(Dict):
                    if sig.parameters:
                        for i, p in enumerate(sig.parameters.values()):
                            if i == len(args):
                                break
                            if p.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD:
                                kwargs[p.name] = args[i]
                        args, kwargs = dict(**kwargs) + args[i:], {}
        if not all(isinstance(x, dict) for x in args):
            raise B.ValidationError("can't interpret non-dictionary objects.")

        if not args:
            args = super().default() or (dict(*args, **kwargs),)

        object = args[0]

        s = cls.schema(0)
        p = s.get("properties", {})

        order = list(p)
        if "dependencies" in s:
            d = s["dependencies"]
            o = set(list(d) + sum(d.values(), []))
            order = [x for x in order if x not in d]
            rank = {k: sum(map(list(d).__contains__, v)) for k, v in d.items()}
            order += sorted(rank, key=rank.get)

        for k in order:
            # after initializing a dict we have all of the defaults on
            # the properties in the schema and we call them direcly from the types.
            if k in object:
                continue

            v = p[k]

            if isinstance(v, B.Generic):
                if not issubclass(v, Const):
                    continue

            object[k], *_ = v.default()

            if callable(object[k]):
                try:
                    object[k] = B.call(object[k])
                except TypeError:
                    object[k] = B.call(object[k], object)
        x = dict.__new__(cls, object)
        x.update(object)
        return (x,)

    @classmethod
    def instance(cls, *args, **kwargs):
        # build the default
        try:
            return super().instance(*cls.default(*args, **kwargs))
        except (TypeError, ValueError) as e:
            raise B.ValidationError()

    @classmethod
    def new_type(cls, object):
        if B.Generic.is_empty_slice(object):
            return cls

        if isinstance(object, dict):
            return B.Generic.new_type(cls, __annotations__=object)

        if isinstance(object, tuple):
            pass  # allow key types to be defined
        # in jsonschema we can only have string keys
        if issubclass(cls, cls.AdditionalProperties):
            return super().new_type(cls)
        return cls + cls.AdditionalProperties[object]

    @staticmethod
    def _type_to_signature(cls):
        import inspect

        from .literal import Cast

        s = cls.schema(0)

        p = s.get("properties", {})

        a = []
        required = s.get("required", [])
        for k in required:
            try:
                a += (
                    inspect.Parameter(
                        k,
                        inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        annotation=p[k],
                    ),
                )
            except (ValueError, TypeError):
                return inspect.signature(Dict)

        for k in p:
            if k in required:
                continue

            v = p[k]
            if isinstance(v, type) and issubclass(v, Const):
                d, *_ = v.default()
                if not callable(d):
                    a += (
                        inspect.Parameter(
                            k,
                            inspect.Parameter.KEYWORD_ONLY,
                            annotation=p[k],
                            default=d,
                        ),
                    )
                continue

            a += (
                inspect.Parameter(
                    k,
                    inspect.Parameter.KEYWORD_ONLY,
                    annotation=p[k],
                ),
            )

        return inspect.Signature(a)

    @classmethod
    def _infer_dependencies(cls):
        import collections
        import inspect

        from .literal import Py

        # accumulate dependencies and required schema values in this method
        deps, required = collections.defaultdict(set), []

        deps.update(
            {k: set(v) for k, v in cls.schema().get("dependencies", {}).items()}
        )

        props = cls.schema(0).get("properties", {})

        for k in props:
            if not hasattr(cls, k):
                if isinstance(props[k], type):
                    if not issubclass(props[k], Default):
                        required += (k,)

            else:
                if isinstance(props[k], type):
                    if not issubclass(props[k], Default):
                        props[k] += Default[getattr(cls, k)]
                else:
                    props[k] += Default[getattr(cls, k)]

        for k in dir(cls):

            try:
                # get the atttribute value
                v = getattr(cls, k)
            except AttributeError:
                continue

            if not callable(v):
                # ignore callables, but we should probably treat these as defaults
                continue

            try:
                # get the signature of the callable.
                s = inspect.signature(v)
            except ValueError:
                continue

            n = k

            if s.return_annotation in props:
                if s.return_annotation in required:
                    required.pop(required.index(s.return_annotation))
                    props[s.return_annotation] += Default[v]
                    n = s.return_annotation

            for x in s.parameters.values():
                if x.annotation == inspect._empty:
                    continue

                if isinstance(x.annotation, str):
                    deps[n].add(x.annotation)

                elif isinstance(x.annotation, (tuple, list)):
                    [deps[n].add(x) for x in x.annotation]

            deps.pop(inspect._empty, None)
            if len(deps):
                cls.__annotations__["dependencies"] = {
                    k: list(v) for k, v in deps.items() if k in props
                }

            if required:
                cls.__annotations__["required"] = required

            # the first parameter to self tells up what the
            # return type depends on

            # the return type tells us the default that we can append

    def __init_subclass__(cls, **kwargs):
        ANNOTATIONS = "__annotations__"

        # we should change the vocab here
        super().__init_subclass__(**kwargs)
        hold = dict(properties={}, dependencies={}, required=[])
        body = {}
        for x in reversed(cls.__mro__):
            a = getattr(x, ANNOTATIONS, {})
            for h in hold:
                if h in a:
                    if isinstance(hold[h], dict):
                        hold[h].update(a[h])
                    elif isinstance(hold[h], list):
                        hold[h].append(a[h])

        for k, v in hold.items():
            if v:
                cls.__annotations__[k] = v

        cls._infer_dependencies()
        cls.__signature__ = cls._type_to_signature(cls)


B.Generic.types[
    dict,
] = Dict


class Forward(typing.ForwardRef, _root=False):
    def __new__(cls, object):
        if isinstance(object, str):
            self = super().__new__(cls)
            self.__init__(object)
            return self

    def _evaluate(self, force=False, globals=None, locals=None):
        if self.__forward_evaluated__:
            return self.__forward_value__
        if not globals or locals:
            # we've redirected our interests to explicit forward reference off of sys.modules.
            # no errors, just False exceptions
            globals = locals = __import__("sys").modules
        self.__forward_value__ = eval(self.__forward_code__, globals, locals)
        self.__forward_evaluated__ = True
        return self.__forward_value__

    def instance(self):
        return self._evaluate()

    __call__ = instance


class ForwardInstance(Forward, _root=False):
    def __call__(cls, *args, **kwargs):
        return super().__call__()(*args, **kwargs)


class Sys(B.Any):
    """forward reference to python objects."""

    def __init_subclass__(cls, **kwargs):
        import inspect

        super().__init_subclass__(**kwargs)
        if hasattr(cls, "value"):
            cls.__signature__ = inspect.signature(cls.value[0])

    @classmethod
    def validate(cls, *args):
        return cls.value[0].validate(*args)

    @classmethod
    def schema(cls, ravel=True):
        v = cls.value[0]
        if hasattr(v, "schema"):
            return v.schema(ravel)
        return v

    @classmethod
    def instance(cls, *args, **kwargs):
        import typing

        self = super().instance(*args)
        if hasattr(self, "value"):
            if isinstance(self.value, typing.Iterable):
                object = self.value[0]
            else:
                object = self.value
        else:
            object = self
        if isinstance(object, Forward):
            if not isinstance(object, type):
                object = object.instance()
        return object

    @classmethod
    def new_type(cls, x):
        if isinstance(x, str):
            x = Forward(x)
        if not isinstance(x, tuple):
            if isinstance(x, list):
                x = tuple(x)
            else:
                x = (x,)
        return B.Generic.new_type(len(x) is 1 and cls or Cast, value=x)


class Py(Sys):
    # forces the import
    pass


class Cast(Py):
    @classmethod
    def instance(cls, *args, **kwargs):
        args = cls.default(*args)

        for i, f in enumerate(cls.value):
            args, kwargs = (B.call(f, *args, **kwargs),), {}

        return args[0]


class Instance(Py):
    # force the import
    # so many schema have a thing, this is ours
    @classmethod
    def instance(cls, *args, **kwargs):
        """kind of like a functor."""
        f = super().instance()
        if callable(f):
            import functools

            return functools.partial(f, *cls.args, **cls.kwargs)(*args, **kwargs)

        return f

    @classmethod
    def new_type(cls, object):
        if not isinstance(object, tuple):
            object = (object,)

        args, kwargs = (), {}
        value, *object = object
        if isinstance(value, str):
            value = ForwardInstance(value)

        for arg in object:
            if isinstance(arg, slice):
                kwargs[arg.start] = arg.stop
                # use the step as a signature
            else:
                args += (arg,)

        return B.Generic.new_type(cls, value=(value,), args=args, kwargs=kwargs)


class Kwargs(Instance):
    @classmethod
    def instance(cls, *args, **kwargs):
        """kind of like a functor."""
        return super().instance(**dict(*args, **kwargs))


class Do(Instance):
    # so many schema have a thing, this is ours
    @classmethod
    def instance(cls, *args, **kwargs):
        """kind of like a functor."""
        super().instance(*args, **kwargs)
        return args[0]


class Juxt(Py):
    @classmethod
    def new_type(cls, object):
        from .callables import Function

        a = dict()
        if callable(object):
            return object

        elif isinstance(object, str):
            return ForwardInstance(object)

        elif isinstance(object, slice):
            f = Function()
            if object.start:
                f = f.filter(object.start)
            if object.stop:
                f = f.map(object.stop)
            if object.step:
                f = f.append(object.step)
            return f

        elif isinstance(object, (typing.Sequence, typing.Set)):
            a["type"] = type(object)
            a["value"] = list(map(Juxt.new_type, object))

        elif isinstance(object, typing.Container):
            a["type"] = type(object)
            a["value"] = list(map(Juxt.new_type, object.items()))

        return B.Generic.new_type(cls, **a)

    @classmethod
    def instance(cls, *args, **kwargs):

        if hasattr(cls, "type"):
            if isinstance(cls.value, typing.Iterable):
                return cls.type(B.call(x, *args, **kwargs) for x in cls.value)
            return cls.type(cls.value)

        if callable(cls.value):
            return B.call(cls.value, *args, **kwargs)
        return cls.value


from . import alias  # isort:skip


class Uri(Validate, Literal, B.Generic.Format["uri"], str, type=P.XSD["anyURI"]):
    type: "string"

    def get(self, *args, **kwargs):
        import requests
        import requests_cache

        requests_cache.install_cache("xxx")
        return requests.get(self, *args, **kwargs)


class Enum(Validate, Literal, B.Generic.Plural, type=P.XSD["enumeration"]):
    """
    >>> Enum[1, 2](10)
    ...

    """

    pass
    # we need a strategy for extensible type bases.
    # maybe can get them from all instances.


del typing
