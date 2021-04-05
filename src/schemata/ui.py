import contextlib

from . import base, util


class Ui(base.Form):
    @classmethod
    def form(cls):
        return f"ui:{util.lowercased(cls.__name__)}"

    @classmethod
    def widget(cls, *args):
        from .compat.ipywidgets import get_widget_from_value

        return get_widget_from_value(*args, schema=cls.schema())

    def _ipython_display_(self):
        import IPython
        import traitlets

        if not hasattr(self, "_display_handle"):
            self._display_handle = self.widget(self)
            t = base.Title.forms(self)
            if t:

                if isinstance(self._display_handle, traitlets.HasTraits):

                    def handler(delta):
                        IPython.get_ipython().user_ns[t] = delta["new"]

                    self._display_handle.observe(handler, "value")
                    handler(dict(new=self))
            if isinstance(self._display_handle, traitlets.HasTraits):
                IPython.display.display(self._display_handle)
            else:
                self._display_handle.display(self)


class InputType(Ui):
    pass


class Widget(Ui):
    @classmethod
    def form(cls):
        return "ui:widget"


class Radio(Widget["radio"], InputType["radio"]):
    pass


class Select(Widget["select"]):
    pass


class Dropdown(Widget["dropdown"]):
    pass


class Toggle(Widget["toggle"]):
    pass


class Password(Widget["password"], InputType["password"]):
    pass


class Text(Widget["text"], InputType["text"]):
    pass


class Textarea(Widget["textarea"], InputType["password"]):
    pass


class DatePicker(Widget, InputType["date"]):
    pass


class Color(Widget["color"], InputType["color"]):
    pass


class ClassNames(Ui):
    pass


class AutoFocus(Ui):
    pass


class Disabled(Ui):
    pass


class EnumDisabled(Ui):
    pass


class Help(Ui):
    pass


class Checkbox(Widget["checkbox"], InputType["checkbox"]):
    pass


class Label(Ui):
    pass


class Log(Ui):
    pass


class Order(Ui):
    pass


class Updown(Widget["updown"]):
    pass


class Range(Widget["range"], InputType["range"]):
    pass


class Slider(Widget["slider"]):
    pass


class Placeholder(Ui):
    pass


class Readonly(Ui):
    pass


class RootFieldId(Ui):
    pass


class Rows(Ui):
    pass


class Static(Ui):
    def _ipython_display_(self):
        d, md = self._repr_mimebundle_(None, None)
        self._display_handle.display(d, metadata=md, raw=True)


class Ansi(Ui):
    def _repr_mimebundle_(self, *a, **k):
        import rich.jupyter

        from .compat.rich import get_rich

        with util.suppress(AttributeError):
            return rich.jupyter.JupyterMixin._repr_mimebundle_(
                get_rich(self), None, None
            )
        return {"text/html": rich.jupyter.JupyterMixin._repr_html_(get_rich(self))}, {}


class Interactive(Ui):
    def _update_display(self):
        d, md = self._repr_mimebundle_(None, None)
        self._display_handle.update(d, metadata=md, raw=True)

    def _ipython_display_(self):
        import IPython

        if not hasattr(self, "_display_handle"):
            self._display_handle = IPython.display.DisplayHandle()
        try:
            d, md = self._repr_mimebundle_(None, None)
            self._display_handle.display(d, metadata=md, raw=True)
        except AttributeError:
            self._display_handle.display({"text/plain": str(self)}, raw=True)
