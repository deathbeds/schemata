from .types import Form, Py, suppress


class App(Py):
    @classmethod
    def suppress(cls):
        ipy = False
        if "IPython" in sys.modules:
            ipy = bool(sys.modules["IPython"].get_ipython())
        return suppress(*(ipy and (SystemExit,) or ()))

    @classmethod
    def run(cls, argv=None):
        if isinstance(argv, str):
            argv = argv.split()
        with cls.suppress():
            return cls()(argv)

    @classmethod
    def help(cls):
        return cls.run("-h")


class Test(App["unittest.main"]):
    """run doc and unit tests"""

    def object(cls, *args, **k):
        main, (_, *v) = super().object(), Form.AtType.form(cls)
        k["module"] = __import__("__main__")

        def load_tests(loader, tests, ignore):
            nonlocal k
            tests.addTests(__import__("doctest").DocTestSuite(k["module"]))
            return tests

        k["module"].load_tests = load_tests

        if args and len(args) == 1 and isinstance(args[0], str):
            args = args[0].split()

        k["argv"] = args or ["discover"]

        try:
            with suppress(SystemExit):
                return main(**k)
        finally:
            del k["module"].load_tests


class Typer(App["typer.Typer"]):
    @staticmethod
    def wrap(f):
        def wrap(*args, **kwargs):
            x = call(f, *args, **kwargs)
            if not isinstance(x, (type(None), int)):
                try:
                    from rich import print
                except:
                    pass
                print(x)

        wrap.__signature__ = Signature.from_type(f).to_typer()

        return wrap

    def object(cls, *args, **kwargs):
        kwargs["name"] = kwargs.get("name", cls.Title.form(cls) or cls.__name__)
        kwargs["add_completion"] = False
        context_settings = dict(help_option_names=["-h", "--help"])
        kwargs["context_settings"] = context_settings

        app, (_, *v) = super().object()(*args, **kwargs), Form.AtType.form(cls)
        for i, v in v:
            name, help = v.__name__, None
            if isinstance(v, Generic):

                if issubclass(v, App):
                    app.add_typer(v.object())
                    continue
                elif issubclass(v, Sys):
                    x = v
                    while issubclass(x, Sys):
                        u = x.values()
                        if u:
                            x = u[0]
                        else:
                            break
                        name = x.__name__
                else:
                    s = v.schema()
                    name = cls.Title.form(cls) or name
                    help = cls.Description.form(cls) or help

            name = name[0].lower() + name[1:]
            app.command(name, context_settings=context_settings, help=help)(cls.wrap(v))

        return app


class Chain(Typer):
    def object(cls, *args, **kwargs):
        return super().object(*args, **kwargs, chain=True)
