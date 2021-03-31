from . import base, util


class Ui(base.Form):
    @classmethod
    def form(cls, *args):
        return super().form(*args) if args else f"ui:{util.lowercased(cls.__name__)}"

    def __init_subclass__(cls):
        setattr(Ui, cls.__name__, getattr(Ui, cls.__name__, cls))


class Widget(Ui):
    def __init_subclass__(cls):
        super().__init_subclass__()
        cls.__annotations__["ui:widget"] = util.lowercased(cls.__name__)


class Radio(Widget):
    pass


class Select(Widget):
    pass


class Password(Widget):
    pass


class TextArea(Widget):
    pass


class Color(Widget):
    pass


class ClassNames(Ui):
    pass


class AutoFocus(Ui):
    pass


class Rich(Ui):
    pass


class Interactive(Ui):
    pass


class Rjsf(Ui):
    pass


class Disabled(Ui):
    pass


class EnumDisabled(Ui):
    pass


class Help(Ui):
    pass


class InputType(Ui):
    pass


class Label(Ui):
    pass


class Order(Ui):
    pass


class UpDown(Ui):
    pass


class Range(Ui):
    pass


class Placeholder(Ui):
    pass


class Readonly(Ui):
    pass


class RootFieldId(Ui):
    pass


class Rows(Ui):
    pass


class Description(Ui):
    pass


class Title(Ui):
    pass


class Tree(Widget):
    pass


class Table(Widget):
    pass
