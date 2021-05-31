import ast

import IPython
import traitlets

from schemata import *

from .. import exceptions, types, ui, util


class Display(traitlets.HasTraits):
    """an general interactive display object for widgets and non-widgets.

    widgets abide the `ipywidgets` convention, and the non-widgets are displayed using the display handler.
    """

    value = traitlets.Any(help="the value to be displayed.")
    type = traitlets.Type(help="the type of the value that may carry schema.")
    description = traitlets.Any(help="the name of the object")
    _display = traitlets.Any(help="the display object")

    @traitlets.observe("value")
    def _change_value(self, delta):
        """a handler to update the display when the value changes."""
        if isinstance(self._display, IPython.display.DisplayHandle):
            # update the non-widget object
            d, md = IPython.get_ipython().display_formatter.format(delta["new"])
            self._display.update(d, metadata=md, raw=True)
        elif isinstance(self._display, traitlets.HasTraits):
            # update the widget object
            self._display.value = delta["new"]

    def _ipython_display_(self):
        """an ipython display protocol for interactive updating objects."""
        if self._display is None:
            # seed the display object if it doesn't exist
            self._display = self.type.widget(self.value)
            if hasattr(self._display, "description") and self.description:
                self._display.description = self.description

                def handler(delta):
                    IPython.get_ipython().user_ns[self.description] = delta["new"]

                self._display.observe(handler, "value")
                handler(dict(new=self._display.value))

        if isinstance(self._display, IPython.display.DisplayHandle):
            # display the non-widgets objects
            d, md = IPython.get_ipython().display_formatter.format(self.value)
            self._display.display(d, metadata=md, raw=True)
        else:
            # display a widget object
            IPython.display.display(self._display)


class AnnotationDisplay(traitlets.HasTraits):
    """a manager for displaying annotations in the notebook.

    the annotation display interprets annotations as visual elements. when
    there an annotation we display the value below the cell. the behavior
    can be circumvented by using private names.
    """

    cell_annotations = traitlets.List()
    parent = traitlets.Any()
    annotations = traitlets.Dict()
    displays = traitlets.Dict()

    def load(self):
        """load the annotation display mechanism"""
        self.unload()
        # register IPython events
        self.parent.events.register("pre_execute", self.pre_execute)
        self.parent.events.register("post_execute", self.post_execute)

        # register ast transformers
        self.parent.ast_transformers.append(AnnotationDisplay.Discovery(self))

    def unload(self):
        """unload the annotation display mechanism"""
        with util.suppress(ValueError):
            # unregister the ipython events
            self.parent.events.unregister("pre_execute", self.pre_execute)
            self.parent.events.unregister("post_execute", self.post_execute)
        # remove the ast transformer
        self.parent.ast_transformers = [
            x
            for x in self.parent.ast_transformers
            if not isinstance(x, AnnotationDisplay.Discovery)
        ]

    def pre_execute(self):
        self.cell_annotations.clear()

    def post_execute(self):
        main = self.parent.user_ns
        annotations = main.get("__annotations__", {})
        for key, annotation in annotations.items():
            if not key[0].isalpha():
                continue
            if "title" not in annotation.schema():
                annotation = annotation + types.Title[key]

            if key in self.annotations:
                if self.annotations[key] != annotation:
                    for v in (self.annotations, self.displays):
                        with util.suppress(KeyError):
                            del v[key]

            if key not in self.annotations:
                self.annotations[key] = annotation

            if key in main:
                args = (main[key],)
            else:
                args = ()

            value = util.identity(*args)

            if key not in self.displays:
                self.displays[key] = Display(
                    value=value, type=annotations[key], description=key
                )

            if key in self.cell_annotations:
                IPython.display.display(self.displays[key])
            else:
                self.displays[key]._change_value(dict(new=value))

    class Discovery(ast.NodeTransformer):
        """an ast transformer that captures the annotation definitions."""

        def __init__(self, parent):
            self.parent = parent

        def visit_FunctionDef(self, node):
            return node

        visit_ClassDef = visit_FunctionDef

        def visit_AnnAssign(self, node):
            self.parent.cell_annotations.append(node.target.id)
            return node


display_extension = None


def load_ipython_extension(shell):
    global display_extension
    if display_extension is None:
        display_extension = AnnotationDisplay(parent=shell)
    display_extension.load()


def unload_ipython_extension(shell):
    global display_extension
    if display_extension is not None:
        display_extension.unload()
