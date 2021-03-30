import inspect


class Signature(inspect.Signature):
    def __init__(cls, object):
        if isinstance(object, list):
            parameters, return_annotation = object, inspect._empty

        else:
            tmp = inspect.signature(object)
            parameters, return_annotation = (
                list(tmp.parameters.values()),
                tmp.return_annotation,
            )

        super().__init__(parameters, return_annotation=return_annotation)

    def to_schema(self):
        pass

    def align_args(self, *args, **kwargs):
        p = [
            x
            for x in self.parameters.values()
            if x.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
        ]
        if not p:
            return args, kwargs
        for i, p in enumerate(p):
            if i == len(args):
                break
            kwargs[p.name] = args[i]
        return (kwargs,) + args[i + 1 :], {}

    @classmethod
    def from_schema(cls, s):
        import inspect

        from .base import Default

        p = s.get("properties", {})

        a = []
        required = s.get("required", [])
        for k in required:
            try:
                a += (
                    inspect.Parameter(
                        k,
                        inspect.Parameter.POSITIONAL_OR_KEYWORD,
                        annotation=p.get(k, inspect._empty),
                    ),
                )
            except (ValueError, TypeError):
                return inspect.signature(cls)

        for k in p:
            if k in required:
                continue

            v = p[k]
            if isinstance(v, type) and issubclass(v, Default):
                d = Default.form(v)
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

            try:
                a += (
                    inspect.Parameter(
                        k,
                        inspect.Parameter.KEYWORD_ONLY,
                        annotation=p[k],
                    ),
                )
            except ValueError:
                pass

        additional = s.get("additionalProperties", True)
        if not additional:
            a += (
                (
                    inspect.Parameter(
                        "kwargs",
                        inspect.Parameter.VAR_KEYWORD,
                        annotation=inspect._empty
                        if isinstance(additional, bool)
                        else additional,
                    ),
                ),
            )
        return cls(a)

    @classmethod
    def from_type(cls, object):
        if hasattr(object, "schema"):
            return cls.from_schema(object.schema())
        return cls(object)

    @classmethod
    def from_re(cls, object):
        return Signature(
            [
                inspect.Parameter("string", inspect.Parameter.POSITIONAL_ONLY),
                *(
                    inspect.Parameter(x, inspect.Parameter.KEYWORD_ONLY)
                    for x in sorted(object.groupindex)
                ),
                inspect.Parameter("kwargs", inspect.Parameter.VAR_KEYWORD),
            ]
        )

    # create a concrete type from the signature using the schemata as an intermediate.
    def to_type(self):
        s, additional = {}, None
        required = ()
        for p in self.parameters.values():
            if p.annotation == inspect._empty:
                continue
            t = p.annotation
            if p.kind == inspect.Parameter.VAR_KEYWORD:
                additional = Generic.AdditionalProperties[p.annotation]
                continue

            if p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                required += (p.name,)

            elif p.kind == inspect.Parameter.KEYWORD_ONLY:
                pass

            else:
                raise BaseException(f"can't integer {p.kind}")

            if p.default != inspect._empty:
                t = t + Default[t.default]

            s[p.name] = t

        t = Dict[s]
        if additional is not None:
            t = t + additional
        return t

    def to_typer(self):
        # change the default value to a typer.Option or typer.Argument
        # change the annotation to a typer compliant type
        return Signature(list(map(get_typer_parameter, self.parameters.values())))


def get_typer_parameter(p):
    import functools
    import typing

    import typer

    from .abc import Generic

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


def get_non_schemata_types(cls):
    import abc

    from schemata import Container, Display, Generic, call

    from .base import Any, Form, Plural

    try:
        t = list(filter(bool, map(call, abc._get_dump(cls)[0])))
    except AttributeError:
        t = []
    return t + [
        x
        for x in cls.__mro__
        if x is not object
        and not issubclass(x, (Container, Form, Plural, Any, Display))
    ]
