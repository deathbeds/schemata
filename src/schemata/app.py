from . import base as B
from . import literal as L
from . import literal as P


class IPython(L.Py["IPython.get_ipython()"]):
    pass


class Action(L.Py["doit.action.CmdAction"], B.Generic.Alias):
    # Also cwd happens a lot
    # That also breaks work Path on windows unless cast to a string
    @classmethod
    def instance(cls, *args, **kwargs):
        action = super().instance()(cls.__annotations__[cls.alias()], shell=False)
        e = action.execute

        def execute():
            nonlocal e
            e()
            return action.result

        action.execute = execute
        return action


class ArgParse:
    pass


class Nox:
    # https://gist.github.com/tonyfast/bacfb0c2d81b1ceba7794385a7882049
    pass


class Voila:
    pass


class Doit(L.Instance["doit.run"], B.Generic.Alias):
    @classmethod
    def instance(cls, object):
        return super().instance()(object)


class Pydantic(L.Py["pydantic.BaseModel"], B.Generic.Alias):
    @classmethod
    def new_type(cls, object):
        return type(
            object.__name__,
            (super().instance(),),
            dict(Config=type("Config", (), dict(schema_extra=object.schema()))),
        )


class Logging(L.Py["structlog.get_logger()"], B.Generic.Alias):
    @classmethod
    def instance(cls, object):
        return super().instance().msg(cls.__name__, **object)


class Typer(L.Py.Instance["typer.Typer"], B.Generic.Alias):
    # use an alias so we don't collide with the existing value
    def __init_subclass__(cls, **kwargs):
        import inspect

        super().__init_subclass__(**kwargs)
        cls.__signature__ = inspect.signature(cls.__annotations__[cls.alias()])

    @classmethod
    def help(cls):
        cls.runner().run("--help")

    @classmethod
    def _pythonic_signature(cls) -> L.Py["inspect.Signature"]:
        # convert class signature to something typer understands
        import inspect

        return inspect.Signature(
            [
                inspect.Parameter(
                    b.name,
                    b.kind,
                    annotation=B.Generic.types.get((b.annotation, b.annotation)),
                    default=b.default,
                )
                for b in cls.__signature__.parameters.values()
            ]
        )

    @classmethod
    def runner(cls, **kwargs):
        import inspect
        import typer

        def runner(*args, **kwargs):
            B.call(cls.__annotations__[cls.alias()], *args, **kwargs)

        runner.__signature__ = cls._pythonic_signature()

        app = super().instance(**kwargs)
        app.command()(runner)
        return typer.main.get_command(app)

    @classmethod
    def instance(cls, *args, **kwargs) -> L.Py["click.Command"]:
        import sys

        args = args or None
        if IPython():
            args = args or ()

        if args:
            if len(args) == 1 and isinstance(args[0], str):
                args = args[0].split()

        try:
            # typer get keywards and we pass as sys arg
            cls.runner(**kwargs).main(args, standalone_mode=args is None)
        except () if args is None else (SystemExit,):
            pass
