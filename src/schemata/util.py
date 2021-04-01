"""schemata utility functions and classes.

functions and non-schemata classes live in this module.
"""

__all__ = (
    "identity",
    "filter_map",
    "forward_strings",
    "call",
    "lowercased",
    "to_pydantic",
    "Schema",
    "Forward",
    "suppress",
    "Path",
)

import functools
import sys
import typing
import inspect
from contextlib import suppress

from .exceptions import ConsentException

try:
    from typing import _ForwardRef as ForwardRef

    _root = True  # pragma: no cover
except ImportError:
    from typing import ForwardRef

    _root = False  # pragma: no cover

Path = type(__import__("pathlib").Path())


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


def get_typer_parameter(p):
    import functools
    import typing

    import typer

    from .base import Generic

    k = {}
    if p.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD:
        f = typer.Argument

    else:
        f = typer.Option

    k["default"] = ...
    if p.default is not inspect._empty:
        k["default"] = p.default

    a = t = typing.Any
    if p.annotation is not inspect._empty:
        import enum

        a = t = p.annotation
        if isinstance(t, Generic):
            a, *_ = get_non_schemata_types(t) + [typing.Any]
            s = t.schema()
            if a is enum.Enum:
                c = t.choices()
                if not isinstance(c, dict):
                    c = dict(zip(c, c))
                a = enum.Enum(t.__name__, c)
            for e in ["", "Exclusive"]:
                for m in ["maximum", "minimum"]:
                    n = m + e
                    if n in s:
                        k[n[:3]] = s[n]

                        if e == "Exclusive":
                            k["clamp"] = True

            if "description" in s:
                k["help"] = s["description"]

    return inspect.Parameter(
        p.name, p.kind, annotation=a, default=f(k.pop("default"), **k)
    )


class Schema(dict):
    def __init__(self, object=None):
        if isinstance(object, type):
            object = getattr(object, "__annotations__", {})

        super().__init__(object)

    def merge(*args):
        from .base import Generic

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

        for k in next:
            if k in types:
                v = next[k]
                if isinstance(v, dict):
                    o = sorted(v)
                    v = dict(zip(o, map(v.get, o)))

        return Schema(next)

    def new(x, pointer=None):
        from .base import Generic

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
        from .base import Generic

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

        if "parse" in sys.modules:
            if isinstance(self, sys.modules["parse"].Parser):
                self = self._match_re

        if isinstance(self, typing.Pattern):
            return self.pattern

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


def to_pydantic_annotations(cls):
    import pydantic
    import typing_extensions

    fields = {
        "title": "title",
        "description": "description",
        "const": "const",
        "gt": "minimumExclusive",
        "ge": "minimum",
        "lt": "maximumExclusive",
        "le": "maximum",
        "multipleOf": "multipleOf",
        "minItems": "minItems",
        "maxItems": "maxItems",
        "minLength": "minLength",
        "maxLength": "maxLength",
        "regex": "regex",
    }

    a = {}
    for k, v in cls.Properties.form(cls).items():
        s = v.schema()
        a[k] = typing_extensions.Annotated[
            cls.Type.pytype.__func__(v),
            pydantic.Field(
                s.get("default", ...),
                **{
                    fields.get(k, k): v
                    for k, v in s.items()
                    if k not in {"type", "default"}
                },
            ),
        ]
    return a


def to_pydantic(cls):
    import pydantic

    return type(
        cls.__name__,
        (pydantic.BaseModel,),
        dict(
            __annotations__=to_pydantic_annotations(cls),
            Config=type("Config", (), dict(schema_extra=cls.schema().ravel())),
        ),
    )


def dispatch(f):

    f = functools.singledispatch(f)
    r = f.register

    @functools.wraps(r)
    def register(g):
        nonlocal r
        for i, p in enumerate(inspect.signature(g).parameters.values()):
            if not i:
                a = p.annotation
                if isinstance(a, (list, tuple)):
                    [r(x)(g) for x in a]
                else:
                    r(a)(g)

        return g

    f.register = register
    return f

