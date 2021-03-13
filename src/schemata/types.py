import pathlib
import typing

from . import protocols as P
from .base import Any, Generic, ValidationError, ValidationErrors, call

Path = type(pathlib.Path())

del pathlib

Any.annotate(P.RDFS["Resource"], in_place=True)


class Literal(Any, type=P.RDFS["Literal"], vocab=P.PROPS.vocab()):
    """the Literal is the bridge between actual python types and Generic types, they emit concrete
    implementations of python types like int, float, list, dict with they advantage that they may be described
    in rdf notation."""

    @classmethod
    def instance(cls, *args):

        # update the arguments with the defaults or constant if defined
        args = cls.default(*args)

        # map to the schema type
        p = tuple(map(type, args))
        if p in Generic.types:
            p = (Generic.types[p],)

        if issubclass(cls, p):
            return super().instance(*args)
        return call(*p, *args)


class Validate:
    # jsonschema validation
    @classmethod
    def instance(cls, *args, **kwargs):
        value = super().instance(*args, **kwargs)
        if issubclass(cls, Composite):
            # this would have already been validated because now we'd be augmenting the base calsses
            return value
        return cls.validate(value)[0]

    @classmethod
    def validate(cls: typing.Union[Generic, dict], *args):
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
            raise e
        return args


class Const(Any, Generic.Alias):
    # a constant
    def instance(cls, *args, **kwargs):
        return cls.default(*args, **kwargs)[0]


class Default(Const):
    # a default
    pass


class Type(Any, Generic.Alias):
    pass


class Null(Validate, Literal, Type["null"], type=P.RDF["nil"]):
    def instance(cls, *args, **kwargs):
        cls.validate(*cls.default(*args, **kwargs))

    def default(cls, *args, **kwargs):
        return super().default(*args, **kwargs) or (None,)


Null.register(type(None))

Generic.types[
    type(None),
] = Null


class Bool(Validate, Literal, Type["boolean"], type=P.XSD["boolean"]):
    def instance(cls, *args, **kwargs):
        args = cls.default(*args, **kwargs)
        return cls.validate(*args)[0]

    @classmethod
    def default(cls, *args, **kwargs):
        return super().default(*args, **kwargs) or (bool(),)


Generic.types[
    bool,
] = Bool
Bool.register(bool)


class String(Validate, Literal, Type["string"], str, type=P.XSD["string"]):
    @classmethod
    def default(cls, *args, **kwargs):
        return super().default(*args, **kwargs) or (str(),)


Generic.types[
    str,
] = String


class File(Validate, Literal, Type["string"], Path):

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


Generic.types[
    Path,
] = File


class Number(Validate, Literal, Type["number"], float, type=P.XSD["decimal"]):
    @classmethod
    def default(cls, *args, **kwargs):
        return super().default(*args, **kwargs) or (float(),)


Float = (
    Number  # number is canonical, but too many times i reach for float so i aliased it
)
Generic.types[
    float,
] = Number


class Integer(Validate, Literal, Type["integer"], int, type=P.XSD["integer"]):
    @classmethod
    def default(cls, *args, **kwargs):
        return super().default(*args, **kwargs) or (int(),)


Generic.types[
    int,
] = Integer


class List(Validate, Literal, Type["array"], list, type=P.RDF["List"]):
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

    @classmethod
    def instance(cls, *args, **kwargs):
        # build the default
        if args or kwargs:
            args = cls.validate(*args, **kwargs)
        else:
            args = cls.default(*args, **kwargs)
        self = list.__new__(cls)

        list.__init__(self, *args)
        return self.validate(self)[0]


Generic.types[
    list,
] = List


class Tuple(List, type=P.RDF["Alt"]):
    @classmethod
    def new_type(cls, object):
        if Generic.is_empty_slice(object):
            return cls
        if isinstance(object, list):
            object = tuple(object)
        if not isinstance(object, tuple):
            object = (object,)
        return cls + cls.Items[list(object)]


Generic.types[
    tuple,
] = Tuple
Tuple.register(tuple)


class Set(List, type=P.RDF["Bag"]):
    pass


Generic.types[
    set,
] = Set

Set.register(set)


class Dict(Validate, Literal, Type["object"], dict):
    def __missing__(self, key):
        cls = type(self)
        if issubclass(cls, Generic.AdditionalProperties):
            if not issubclass(cls, Generic.Properties):
                dict.__setitem__(
                    self,
                    key,
                    call(cls.schema(0)[Generic.AdditionalProperties.alias()]),
                )
                return self
        return dict.__missing__(self, key)

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
                        args, kwargs = (dict(**kwargs),) + args[i:], {}
        if not all(isinstance(x, dict) for x in args):
            raise ValidationError("can't interpret non-dictionary objects.")

        if not args:
            args = super().default() or (dict(*args, **kwargs),)

        object = args[0]

        s = cls.schema(0)
        p = s.get("properties", {})

        order = list(p)
        if Generic.Dependencies.alias() in s:
            d = s[Generic.Dependencies.alias()]
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

            if isinstance(v, Generic):
                if not issubclass(v, Const):
                    continue

            object[k], *_ = v.default()

            if callable(object[k]):
                try:
                    object[k] = call(object[k])
                except TypeError:
                    object[k] = call(object[k], object)
        x = dict.__new__(cls, object)
        x.update(object)
        return (x,)

    @classmethod
    def instance(cls, *args, **kwargs):
        # build the default
        try:
            self = dict.__new__(cls)
            d = cls.default(*args, **kwargs)
            dict.__init__(self, *d)
            return self.validate(self)[0]
        except (TypeError, ValueError) as e:
            raise ValidationError()

    @classmethod
    def new_type(cls, object):
        if Generic.is_empty_slice(object):
            return cls

        if isinstance(object, dict):
            return cls + Generic.Properties[object]

        if isinstance(object, tuple):
            pass  # allow key types to be defined

        # in jsonschema we can only have string keys
        if issubclass(cls, cls.AdditionalProperties):
            return super().new_type(cls)

        return cls + cls.AdditionalProperties[object]

    @staticmethod
    def _type_to_signature(cls):
        import inspect

        from .types import Cast

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

        from .types import Py

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


Generic.types[
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


class Sys(Any):
    """forward reference to python objects."""

    def __init_subclass__(cls, **kwargs):
        import inspect

        super().__init_subclass__(**kwargs)
        if hasattr(cls, "value"):
            try:
                cls.__signature__ = inspect.signature(cls.value[0])
            except ValueError:
                pass

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
        return Generic.new_type(len(x) is 1 and cls or Cast, value=x)


class Py(Sys):
    # forces the import
    pass


class Cast(Py):
    @classmethod
    def instance(cls, *args, **kwargs):
        args = cls.default(*args)

        for i, f in enumerate(cls.value):
            args, kwargs = (call(f, *args, **kwargs),), {}

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

        return Generic.new_type(cls, value=(value,), args=args, kwargs=kwargs)


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
            a["value"] = tuple(
                Juxt.new_type((isinstance(k, str) and k.format or k, v))
                for k, v in object.items()
            )

        return Generic.new_type(cls, **a)

    @classmethod
    def instance(cls, *args, **kwargs):

        if hasattr(cls, "type"):
            if isinstance(cls.value, typing.Iterable):
                return cls.type(call(x, *args, **kwargs) for x in cls.value)
            return cls.type(cls.value)

        if callable(cls.value):
            return call(cls.value, *args, **kwargs)
        return cls.value


from . import aliases, aliases as A  # isort:skip

aliases.Type = Type


class Uri(String, Generic.Format["uri"], type=P.XSD["anyURI"]):
    def get(*args, **kwargs):
        return __import__("requests").get(self, *args, **kwargs)


# at this point we have everything we need to build other string and number types.
from .strings import *  # isort:skip
from .numbers import *  # isort:skip


class Enum(Validate, Literal, Generic.Plural, type=P.XSD["enumeration"]):
    """
    >>> Enum[1, 2](10)
    ...

    """

    pass
    # we need a strategy for extensible type bases.
    # maybe can get them from all instances.


class Pointer(String, String.Format["json-pointer"]):
    @classmethod
    def instance(cls, *args):
        if len(args) > 1:
            args = (__import__("jsonpointer").JsonPointer.from_parts(args).path,)
        return super().instance(*args)

    def apply(self, object):
        # a pointer can be called against an object to resolve
        return __import__("jsonpointer").resolve_pointer(object, self)

    def __truediv__(self, object):
        return Pointer(self + "/" + object)


class Composite(Literal):
    """a schemaless alias type mixin, the name of the class is used to derive others"""

    @classmethod
    def validate(cls, object):
        # composites use the instance creation for typing checking
        return cls.instance(object)


class Nested:
    @classmethod
    def new_type(cls, object):
        # post process the created type to avoid nesting in the
        # schema representation.
        self = super().new_type(object)
        s = self.schema(0)
        n = cls.alias()
        order = []
        for x in s[n]:
            if isinstance(x, type) and issubclass(x, cls):
                order += x.schema(0)[n]
            elif x not in order:
                order.append(x)
        self.__annotations__[n] = order
        return self

    @classmethod
    def _attach_parent(cls, x):
        if isinstance(x, (type(None), bool)):
            return x
        x.parent = cls
        return x


class AnyOf(Nested, Composite, Generic.Plural):
    @classmethod
    def instance(cls, *args):
        import typing

        args = cls.default(*args)
        schema = cls.schema(False)
        p = schema[AnyOf.alias()]
        for t in p:
            try:
                x = call(t, *args)
                return cls._attach_parent(x)
            except ValidationErrors:
                if t is p[-1]:
                    raise ValidationError()


class AllOf(Nested, Composite, Generic.Plural):
    @classmethod
    def instance(cls, *args):

        args = cls.default(*args)
        schema = cls.schema(False)
        result = {}
        for t in schema[AllOf.alias()]:
            result.setdefault("x", call(t, *args))

        x = result.get("x", args[0])

        return cls._attach_parent(x)


class OneOf(Nested, Composite, Generic.Plural):
    @classmethod
    def instance(cls, *args, **kwargs):
        args = cls.default(*args)
        schema = cls.schema(False)
        i, x = 0, None
        for t in schema[OneOf.alias()]:
            try:
                if i:
                    call(t, *args, **kwargs)
                else:
                    x = call(t, *args, **kwargs)
                i += 1
            except ValidationErrors as e:
                continue

            if i > 1:
                break

        if i == 1:
            return cls._attach_parent(x)

        raise ValidationError()


class Not(Generic.Alias, Composite):
    @classmethod
    def instance(cls, *args):
        try:
            super().instance(*args)
        except ValidationErrors:
            x, *_ = args

            return cls._attach_parent(x)


class If(Literal):
    @classmethod
    def instance(cls, *args):

        args = cls.default(*args)
        s = cls.schema(False)
        i, t, e = s.get(If.alias()), s.get("then"), s.get("else")
        if isinstance(*args, i):
            e = t
        if isinstance(e, Generic):
            if issubclass(e, cls):
                return super().instance(*args)
            return e.instance(*args)
        return Literal.__new__(e, *args)

    def new_type(cls, object):

        payload = {}
        if isinstance(object, slice):
            if object.start is not None:
                payload[If.alias()] = object.start
            if object.stop is not None:
                payload["then"] = object.stop
            if object.step is not None:
                payload["else"] = object.step
        if payload:
            return Generic.new_type(cls, __annotations__=payload)
        return cls


class Json(
    List ^ Dict ^ String ^ Number ^ Bool ^ Null,
    Generic.ContentMediaType["application/json"],
):
    import json

    loader = json.loads
    dumper = json.dumps
    del json


# json patching methods
class Patch:
    """the patch class implements the json patch protocol, for lazy updating and validation to lists and dictionaries"""

    ADD = dict(op="add")
    REMOVE = dict(op="remove")
    REPLACE = dict(op="replace")
    COPY = dict(op="copy")
    MOVE = dict(op="move")
    TEST = dict(op="test")

    _depth = 0
    _push_mode = 0

    @staticmethod
    def pointer(x):
        import jsonpointer

        if isinstance(x, str):
            if x.startswith("/"):
                return jsonpointer.JsonPointer(x).path
            x = (x,)
        if isinstance(x, tuple):
            return jsonpointer.JsonPointer.from_parts(x).path
        raise BaseException("dunno")

    def __enter__(self):
        self._depth += 1
        return self

    def __exit__(self, *e):
        self._depth -= 1
        if not self._depth:
            # a depth indicates we should collect our patches, verify and apply them.
            self.verify()

    def verify(self):
        with self.push_mode():
            x = self.inc()

        try:
            self.validate(x)
        except ValidationErrors as e:
            self.reset()
            raise e

        self.apply_patch()

    def push_mode(self):
        """enter a push mode state where the dictionary can apply standard changes,
        otherwise we only record the patches"""
        import contextlib

        @contextlib.contextmanager
        def push_mode():
            self._push_mode += 1
            yield self
            self._push_mode -= 1

        return push_mode()

    def apply_patch(self):
        """apply the stored json patches to the object"""
        import jsonpatch

        with self.push_mode():
            jsonpatch.apply_patch(self, self._patches, in_place=True)
            self.reset()
        return self

    def inc(self):
        """created a temporary instance of the patched object"""
        import jsonpatch

        t = type(self)
        t = [list, dict][issubclass(t, dict)]
        with self.push_mode():
            self._tmp = jsonpatch.apply_patch(t(self), self._patches, in_place=False)
        return self._tmp

    def resolve(self, x):
        import jsonpointer

        with self.push_mode():
            self = jsonpointer.resolve_pointer(self, Patch.pointer(x))
        return self

    def patches(self, *patch):
        if not hasattr(self, "_patches"):
            self._patches, self._applied_patches = [], []

        for p in patch:
            if "from" in p:
                p["from"] = Patch.pointer(p["from"])
            p["path"] = Patch.pointer(p["path"])
            self._patches.append(p)

        return self

    def add(self, key, value):
        return self.patches(dict(path=key, value=self[key], **self.ADD))

    def remove(self, key, *default):
        return self.patches(dict(path=key, value=self[key], **self.REMOVE))

    def move(self, key, target):
        return self.patches(dict(path=target, **{"from": key}, **self.MOVE))

    def copy(self, key, target):
        return self.patches(dict(path=target, **{"from": key}, **self.COPY))

    def replace(self, key, value):
        return self.patches(dict(path=key, value=value, **self.REPLACE))

    def reset(self):
        self._depth = self._push_mode = 0
        for x in (self._patches, self._applied_patches, self._tmp):
            while x:
                if isinstance(x, list):
                    x.pop()
                elif isinstance(x, dict):
                    x.popitem()


from .objects import *  # isort:skip
from .arrays import *  # isort:skip


class Pipe(Py):
    # this is used as an instance, not a type, it falls back to pipe
    @classmethod
    def new_type(cls, x):
        if not isinstance(x, tuple):
            x = (x,)

        return cls.append(x)

    @classmethod
    def instance(cls, *args):
        self = super().instance()
        self.value = tuple(args)
        return self

    def append(*args):
        if not args:
            return Pipe()
        self, *args = args

        if issubclass(type(self), Pipe):
            self.value += tuple(args)
            return self
        return Pipe().append(*args)

    __add__ = __sub__ = __getitem__ = __rshift__ = append

    def map(self, value):
        return self.append(functools.partial(map, value))

    __mul__ = __imul__ = map

    def filter(self, value):
        return self.append(functools.partial(filter, value))

    __truediv__ = __itruediv__ = filter

    def reduce(self, value):
        init = None
        if isinstance(value, tuple):
            value, init = value
        if init:
            return self.append(lambda x: functools.reduce(value, x, init))
        return self.append(functools.partial(functools.reduce, value))

    __floordiv__ = reduce

    def groupby(self, value):
        import itertools

        return self.append(
            lambda v: {x: list(y) for x, y in itertools.groupby(v, value)}
        )

    __matmul__ = groupby

    def do(self, object):
        return self.append(Do[Juxt[object]])

    __lshift__ = do

    def iff(self, object):
        p = object
        if isinstance(object, (tuple, type)):
            p = lambda x: isinstance(x, object)
        return Iff[self.append(p)]

    def ifthen(self, object):
        return IfThen[self, object]

    def ifnot(self, object):
        return IfNot[self, object]

    def excepts(self, object):
        return Excepts[self, object]

    def complement(self):
        return Pipe(Not[self])

    def pipe(self):
        return Cast[self.value]

    def __call__(self, *args, **kwargs):
        return self.pipe()(*args, **kwargs)


class X(BaseException):
    def __bool__(self):
        return False


class Conditional:
    @classmethod
    def new_type(cls, object):
        p, v = object, tuple()
        if isinstance(p, tuple):
            p, v, *_ = p
        cls = super().new_type(object)
        cls.predicate, cls.value = p, v
        return cls

    @classmethod
    def instance(cls, *args, **kwargs):
        args = cls.default(*args)
        return call(cls.predicate, *args, **kwargs)


class Iff(Conditional, Pipe):
    @classmethod
    def instance(cls, *args, **kwargs):
        x = super().instance(*args, **kwargs)
        if x:
            return call(cls.value, *args, **kwargs)
        return args[0]


class IfThen(Conditional, Pipe):
    @classmethod
    def instance(cls, *args, **kwargs):
        x = super().instance(*args, **kwargs)
        if x:
            return call(cls.value, x)
        return args[0]


class IfNot(Conditional, Pipe):
    @classmethod
    def instance(cls, *args, **kwargs):
        x = super().instance(*args, **kwargs)
        if x:
            return args[0]
        return call(cls.value, *args, **kwargs)


class Excepts(Conditional, Instance):
    @classmethod
    def instance(cls, *args, **kwargs):
        try:
            return super().instance(*args, **kwargs)
        except cls.value or () as e:
            return X(e)


class Not(Instance):
    @classmethod
    def instance(cls, *args, **kwargs):
        return not cls.instance(*args, **kwargs)
