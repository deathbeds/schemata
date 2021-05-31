from .types import Any

from . import base, util


class Ui(base.Form):
    @classmethod
    def form(cls):
        return f"ui:{util.lowercased(cls.__name__)}"

class Ui(Any):
    pass


class UiWidget(Ui):
    pass


class UiOptions(Ui):
    pass


class Checkbox(UiWidget["checkbox"]):
    pass


class Select(UiWidget["select"]):
    pass


class Radio(UiWidget["radio"]):
    pass


class Range(UiWidget["range"]):
    pass


class Slider(UiWidget["slider"]):
    pass


class Dropdown(UiWidget["dropdown"]):
    pass


class Text(UiWidget["text"]):
    pass


class Textarea(UiWidget["text"]):
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


from .arrays import Arrays
from .numbers import Numeric
from .objects import Dict
from .strings import String
from .types import Bool, Enum

SCHEMATA_TO_UI_TYPES = {
    Bool: [Checkbox, Select, Radio],
    Numeric: [Text, Updown, Range, Slider],
    String: [Text, Textarea, Password, Color],
    Arrays: [Dropdown, Range, Select],
    Dict: [],
    Enum: [Range, Select, Dropdown, Radio],
}
for k, v in SCHEMATA_TO_UI_TYPES.items():
    for v in v:
        setattr(k, v.__name__, v)

del k, v
