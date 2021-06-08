from . import utils
from .types import Any, Type


class Ui(Any):
    pass


class UiWidget(Ui):
    def __class_getitem__(cls, object):
        current = cls.value(UiWidget)
        if current:
            object = utils.enforce_tuple(current) + utils.enforce_tuple(object)
        return super().__class_getitem__(object)

    @classmethod
    def widget(cls, object=utils.EMPTY):
        from .compat import ipywidgets

        return ipywidgets.get_widget(object, schema=utils.merge((cls, type(object))))

    def _ipython_display_(self, schema=utils.EMPTY):
        if not hasattr(self, "_display_handle"):
            from .compat import ipywidgets

            self._display_handle = self.widget(self)
        self._display_handle._ipython_display_()


class UiOptions(Ui):
    pass


class Checkbox(UiWidget["checkbox"]):
    pass


class Select(UiWidget["select"]):
    pass


class Radio(UiWidget["radio"]):
    pass


# https://react-jsonschema-form.readthedocs.io/en/latest/usage/widgets/#for-number-and-integer-fields
class Range(UiWidget["range"]):
    pass


class Slider(UiWidget["slider"]):
    pass


class Dropdown(UiWidget["dropdown"]):
    pass


class Text(UiWidget["text"]):
    pass


class Textarea(UiWidget["textarea"]):
    pass


class Password(UiWidget["password"]):
    pass


class Updown(UiWidget["updown"]):
    pass


class Color(UiWidget["color"]):
    pass


class Picker(UiOptions):
    pass


class Multiple(UiOptions):
    pass


class HBox(UiWidget["hbox"]):
    pass


class VBox(UiWidget["vbox"]):
    pass


from .arrays import Arrays
from .numbers import Numeric
from .objects import Dict
from .strings import String, UriTemplate
from .types import Bool, Enum

SCHEMATA_TO_UI_TYPES = {
    Bool: [Checkbox, Select, Radio],
    Numeric: [Checkbox, Text, Updown, Range, Slider],
    String: [Text, Textarea, Password, Color],
    Arrays: [Dropdown, Range, Select],
    Dict: [],
    Enum: [Range, Select, Dropdown, Radio],
}
for k, v in SCHEMATA_TO_UI_TYPES.items():
    for v in v:
        setattr(k, v.__name__, v)

del k, v


class Layout(Any):
    pass


class Style(Any):
    pass
