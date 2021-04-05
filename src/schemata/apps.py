import functools
import inspect
import re
import sys
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
        v = base.Value.forms(cls)
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

            with util.suppress(SystemExit):
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
        from .compat.typer import get_typer

        def wrap(*args, **kwargs):
            x = util.call(f, *args, **kwargs)
            if not isinstance(x, (type(None), int)):
                print(x)

        wrap.__signature__ = get_typer(f)

        return wrap

    def object(cls, *args, **kwargs):
        import typer

        kwargs["name"] = kwargs.get("name", cls.Title.forms(cls) or cls.__name__)
        kwargs["add_completion"] = False
        default_context_settings = dict(help_option_names=["-h", "--help"])
        kwargs["context_settings"] = default_context_settings

        # split the application and things it is going to call.
        app, *to = util.forward_strings(*cls.Value.forms(cls))
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
                        u = cls.Value.forms(x)
                        if u:
                            x = u[0]
                        else:
                            break
                        n = x.__name__
                else:
                    n = cls.Title.forms(cls) or n
                    help = cls.Description.forms(cls) or help

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
