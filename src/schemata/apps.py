import re
import sys
import inspect
import typing

from . import base, types, util


class App(types.Instance):
    # suppress SystemExit in IPython
    @classmethod
    def suppress(cls):
        ipy = False
        if "IPython" in sys.modules:
            ipy = bool(sys.modules["IPython"].get_ipython())
        return util.suppress(*(ipy and (SystemExit,) or ()))

    @classmethod
    def type(cls, *args):
        if not args:
            return cls
        v = base.Value.form(cls)
        if isinstance(args[0], (tuple, list)):
            args = v + args[0]
        else:
            args = (v + args,)
        return super().type(*args)


class Test(App["unittest.main"]):
    """run doc and unit tests"""

    def object(cls, *args, **k):
        # k holds the keywords passed to unittest.man
        # args are the sys args
        k["module"] = k.get("module", __import__("__main__"))

        def load_tests(loader, tests, ignore):
            nonlocal k
            import doctest

            tests.addTests(
                doctest.DocTestSuite(k["module"], optionflags=doctest.ELLIPSIS)
            )
            return tests

        k["module"].load_tests = load_tests

        if args and len(args) == 1 and isinstance(args[0], str):
            args = args[0].split()

        # default to this cause it works and i dont know why
        k["argv"] = args or ["discover"]

        try:

            with suppress(SystemExit):
                return super().object(**k)
        finally:
            del k["module"].load_tests


class Typer(App["typer.Typer"]):
    @classmethod
    def run(cls, argv=None):
        if isinstance(argv, str):
            argv = argv.split()
        with cls.suppress():
            return cls()(argv)

    @classmethod
    def help(cls):
        return cls.run("-h")

    @staticmethod
    def wrap(f):
        def wrap(*args, **kwargs):
            x = util.call(f, *args, **kwargs)
            if not isinstance(x, (type(None), int)):
                print(x)

        wrap.__signature__ = get_typer(f)

        return wrap

    def object(cls, *args, **kwargs):
        import typer

        kwargs["name"] = kwargs.get("name", cls.Title.form(cls) or cls.__name__)
        kwargs["add_completion"] = False
        default_context_settings = dict(help_option_names=["-h", "--help"])
        kwargs["context_settings"] = default_context_settings

        # split the application and things it is going to call.
        app, *to = util.forward_strings(*cls.Value.form(cls))
        app = app(**kwargs)
        for i, x in enumerate(to):
            n, help = x.__name__, None
            if isinstance(x, base.Generic):

                if issubclass(x, App):
                    app.add_typer(x)
                    continue
                elif issubclass(x, cls.Py):
                    y = x
                    while issubclass(x, cls.Py):
                        u = cls.Value.form(x)
                        if u:
                            x = u[0]
                        else:
                            break
                        n = x.__name__
                else:
                    n = cls.Title.form(cls) or n
                    help = cls.Description.form(cls) or help

            n = cls.String.lowercased(n)
            app.command(
                n,
                context_settings=default_context_settings,
                help=help,
            )(cls.wrap(x))

        return app


class Chain(Typer):
    def object(cls, *args, **kwargs):
        return super().object(*args, **kwargs, chain=True)


@util.dispatch
def get_signature(x):
    return inspect.signature(x)

@get_signature.register
def _get_signature_from_schema(x:base.Generic):
    return get_signature(x.schema())

@get_signature.register
def _get_signature_from_schema(x:re.Pattern):
    return inspect.Signature(
            [
                # inspect.Parameter("string", inspect.Parameter.POSITIONAL_ONLY),
                *(
                    inspect.Parameter(x, inspect.Parameter.KEYWORD_ONLY)
                    for x in sorted(x.groupindex)
                ),
                inspect.Parameter("kwargs", inspect.Parameter.VAR_KEYWORD),
            ]
        )
@get_signature.register
def _get_signature_from_schema(s:dict):
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
            if isinstance(v, type) and issubclass(v, base.Default):
                d = base.Default.form(v)
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
        return inspect.Signature(a)

def get_typer(x):
    return inspect.Signature(list(map(get_typer_parameter, get_signature(x).parameters.values())))

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
        if isinstance(t, base.Generic):
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

    return inspect.Parameter(
        p.name, p.kind, annotation=a, default=f(k.pop("default"), **k)
    )

