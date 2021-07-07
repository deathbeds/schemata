import functools
from functools import partial
from re import L

import click

from schemata.objects import Dependencies

from .. import builders, utils

MAPPING = dict(string=click.STRING, integer=click.INT, number=click.FLOAT)


class ClickBuilder(builders.DictBuilder):
    commands: dict
    kwargs: dict

    def Description(self, key, value):
        self["kwargs"]["help"] = value

    def Properties(self, key, value):
        for k, v in value.items():
            self["commands"][k] = CommandBuilder(v).build()

    def Dependencies(self, key, value):
        for k, v in value.items():
            self["commands"].update(ClickBuilder(v).build())

    def wraps(self, callable=None, name=None, command=None, deep=True):
        if callable is None:
            if hasattr(self._type, "__main__"):
                callable = self._type.__main__
            else:
                import rich

                callable = rich.print
        else:
            self["kwargs"].pop("help", None)

        @functools.wraps(callable)
        def main(**kwargs):
            callable(self._type.cast(kwargs))

        props = self.schema.get("properties", {})
        for k in reversed(props):
            v = self.schema["properties"][k]
            main = click.option("--" + k, **self["commands"][k])(main)

        for k in reversed(self.schema.get("required", ())):
            main = click.argument(k, **self["commands"][k])(main)

        group = False
        if command is None:
            deps = self.schema.get("dependencies", {})
            for k in reversed(deps):
                if k not in props:
                    if hasattr(self._type, k):
                        if not group:
                            command = click.group(
                                **self["kwargs"], invoke_without_command=not group
                            )(main)
                        group = True
                        self.wraps(getattr(self._type, k), k, command, False)
            if deep:
                defs = self.schema.get("definitions", {})

                for k in reversed(defs):
                    if not group:
                        command = click.group(
                            **self["kwargs"], invoke_without_command=not group
                        )(main)
                    group = True
                    ClickBuilder(defs[k]).build().wraps(
                        command=command, name=k, deep=True
                    )
        if group:
            return command
        return (command or click).command(name, **self["kwargs"])(main)


def type_to_click(cls):
    if isinstance(cls, type):
        cls = cls.schema()
        cls = cls.get("type")

    if isinstance(cls, (list, tuple)):
        return click.Tuple(tuple(filter(bool, map(type_to_click, cls))))

    if cls in MAPPING:
        return MAPPING[cls]


class CommandBuilder(builders.DictBuilder):
    Title = Optional = builders.DictBuilder.one_for_one

    def Type(self, key, value):
        self["type"] = type_to_click(value)

    def Format(self, key, value):
        self["type"] = click.File()

    def Items(self, key, value):
        if isinstance(value, tuple):
            self["type"] = type_to_click(value)
        else:
            self.update(type=type_to_click, multiple=True)

    def Default(self, key, value):
        self.one_for_one(key, value)
        self.data["show_default"] = True

    def Description(self, key, value):
        self.update(help=value)
