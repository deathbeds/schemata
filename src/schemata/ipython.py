import traitlets

from .base import get_compact_graph, get_compact_id, get_graph, get_id


class Trait(traitlets.HasTraits):
    parent = traitlets.Any()
    enabled = traitlets.Bool(True)
    register_keys = "pre_execute pre_run_cell post_run_cell post_execute".split()

    def register(self):
        for key in self.register_keys:
            if hasattr(self, key):
                self.parent.events.register(key, getattr(self, key))

    def toggle(self, object: bool):
        self.enabled = bool(object if object is None else not self.enabled)


class MetadataFormatter(Trait):
    buffer = traitlets.List()

    def flush(self):
        graph = []
        while self.buffer:
            graph += (self.buffer.pop(0),)
        return graph

    def add(self, *object):
        for x in object:
            self.buffer.extend(get_graph(x))

        return self


import IPython


class MultiFormatter(IPython.core.formatters.DisplayFormatter):
    display = traitlets.List()

    def format(self, object, include=None, exclude=None):
        for f in self.formatters:
            if hasattr(f, "_ipython_display_"):
                return f._ipython_display_(self)
            if hasattr(f, "_repr_mimebundle_"):
                return f._repr_mimebundle_(self, include, exclude)

        return super().format(object)


class Rich(Display):
    def _ipython_display_(self):
        import rich

        rich.print(self)


class Live(Display):
    def _ipython_display_(self):
        pass
        # live traitlets, widgets blah


class Formatter(IPython.core.formatters.DisplayFormatter):
    mdf = traitlets.Instance(MetadataFormatter, tuple())

    def format(self, object, include=None, exclude=None):
        d, md = super().format(object)
        self.mdf.add(object)
        md = get_compact_graph(self.mdf.flush() + [md])
        md.pop("@context", None)
        return {"@id": get_compact_id(get_id(object)), **d}, md


def load_ipython_extension(shell):
    if "_prior_formatter" not in globals():
        globals()["_prior_formatter"] = shell.display_formatter
    shell.display_formatter = DisplayFormatter(
        **globals()["_prior_formatter"]._trait_values
    )
    shell.user_ns["format"] = shell.display_formatter.format


def unload_ipython_extension(shell):
    if "_prior_formatter" in globals():
        shell.display_formatter = globals()["_prior_formatter"]
