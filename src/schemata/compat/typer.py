import inspect
import typing

from .. import types
from . import get_signature


def get_typer(x):
    return inspect.Signature(
        list(map(get_typer_parameter, get_signature(x).parameters.values()))
    )


def get_typer_parameter(p):
    import typer

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
        if isinstance(t, types.Generic):
            a = t.py()
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
    try:
        return inspect.Parameter(
            p.name, p.kind, annotation=a, default=f(k.pop("default"), **k)
        )
    except ValueError:
        return inspect.Parameter(p.name, p.kind, annotation=a, **k)
