import traitlets

from .. import exceptions, ui, util


def get_names_in_main(x):
    m = __import__("__main__")
    return [k for k, v in vars(m).items() if v is x], getattr(m, "__annotations__", {})


import ast

import IPython
import traitlets

from schemata import *


class AnnotationDiscovery(ast.NodeTransformer):
    def __init__(self, parent):
        self.parent = parent

    def visit_FunctionDef(self, node):
        return node

    visit_ClassDef = visit_FunctionDef

    def visit_AnnAssign(self, node):
        self.parent.cell_annotations.append(node.target.id)
        return node


class AnnotationDisplay(traitlets.HasTraits):
    parent = traitlets.Any()
    cell_annotations = traitlets.List()
    annotations = traitlets.Dict()
    state = traitlets.Dict()
    displays = traitlets.Dict()

    def load(self):
        self.unload()
        self.parent.events.register("pre_execute", self.pre_execute)
        self.parent.events.register("post_execute", self.post_execute)
        self.parent.ast_transformers.append(AnnotationDiscovery(self))

    def unload(self):
        with util.suppress(ValueError):
            self.parent.events.unregister("pre_execute", self.pre_execute)
            self.parent.events.unregister("post_execute", self.post_execute)
        self.parent.ast_transformers = [
            x
            for x in self.parent.ast_transformers
            if not isinstance(x, AnnotationDiscovery)
        ]

    def pre_execute(self):
        self.cell_annotations.clear()

    def post_execute(self):
        main = self.parent.user_ns
        annotations = main.get("__annotations__", {})
        for key, annotation in annotations.items():
            if "title" not in annotation.schema():
                annotation = annotation + base.Title[key]

            if key in self.annotations:
                if self.annotations[key] != annotation:
                    for v in (self.annotations, self.displays, self.state):
                        with util.suppress(KeyError):
                            del v[key]

            if key not in self.annotations:
                self.annotations[key] = annotation

            if key in main:
                args = (main[key],)
            else:
                args = ()

            try:
                value = annotation(*args)
            except exceptions.ValidationErrors as e:
                print(e)
                continue

            if key not in self.displays:
                self.displays[key] = annotation.widget(value)

                if isinstance(self.displays[key], traitlets.HasTraits):

                    def handler(delta):
                        nonlocal key
                        m = __import__("__main__")
                        setattr(m, key, delta["new"])

                    self.displays[key].observe(handler, "value")

            if key in self.cell_annotations:
                if isinstance(self.displays[key], traitlets.HasTraits):
                    IPython.display.display(self.displays[key])
                elif isinstance(self.displays[key], IPython.display.DisplayHandle):
                    self.displays[key].display(value)

            if isinstance(self.displays[key], traitlets.HasTraits):
                if self.displays[key].value != value:
                    self.displays[key].value = value
            elif isinstance(self.displays[key], IPython.display.DisplayHandle):
                if key not in self.state or self.state[key] != value:
                    self.displays[key].update(value)
                self.state[key] = value


disp = None


def load_ipython_extension(shell):
    global disp
    if disp is None:
        disp = AnnotationDisplay(parent=shell)
    disp.load()


def unload_ipython_extension(shell):
    global disp
    if disp is not None:
        disp.unload()
