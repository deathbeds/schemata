from .forms import Form, lowercased


class Ui(Form):
    @classmethod
    def form(cls, *args):
        return super().form(*args) if args else f"ui:{lowercased(cls.__name__)}"

    def __init_subclass__(cls):
        setattr(Ui, cls.__name__, getattr(Ui, cls.__name__, cls))


class Widget(Ui):
    def __init_subclass__(cls):
        super().__init_subclass__()
        cls.__annotations__["ui:widget"] = lowercased(cls.__name__)


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
    def _ipython_display_(self):
        import rich
        rich.print(self)
        
    def __rich__(x, t=None):
        import typing

        import rich.tree

        from .base import Generic, Path

        if t is None:
            if isinstance(type(x), Generic):
                t = type(x)

                mt = t.schema().get("contentMediaType")
                if mt == "text/markdown":
                    import rich.markdown

                    return rich.markdown.Markdown(x)

            if isinstance(x, (str, Path)):
                return x
            if not isinstance(x, (typing.Iterable)):
                return x

            t = rich.tree.Tree(repr(type(x)))

        if isinstance(x, dict):
            for k, v in x.items():
                u = t.add(k)
                Rich.__rich__(v, u)
        elif isinstance(x, (str, Path)):
            t.add(str(x))

        elif isinstance(x, (list, typing.Iterable)):
            for v in x:
                if v is not x:
                    Rich.__rich__(v, t)
        else:
            t.add(str(x))
        return t


class Interactive(Ui):
    def _update_display(self):
        try:
            h = object.__getattribute__(self, "_display_handle")
            d, md = self._repr_mimebundle_()

            h.update(d, metadata=md, raw=True)
        except AttributeError:
            pass

        return self

    def _ipython_display_(self):
        import IPython

        try:
            self._display_handle = object.__getattribute__(self, "_display_handle")
        except AttributeError:
            self._display_handle = IPython.display.DisplayHandle()
        d, md = self._repr_mimebundle_()
        self._display_handle.display(d, metadata=md, raw=True)


class Rjsf(Ui):
    def object(cls, *args, **kwargs):
        import wxyz.json_schema_form

        args = (dict(*args, **kwargs),)
        s = cls.schema().ravel()
        for k, v in s["properties"].items():
            s["properties"][k]["default"] = v
        v, *_ = args
        return wxyz.json_schema_form.JSONSchemaForm(
            schema=cls.schema().ravel(), ui_schema=cls.ui_schema(), value=v
        )

    def _ipython_display_(self):
        import IPython

        IPython.display.display(Rjsf.object.__func__(self))


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
    def __rich__(x, tree=None):
        import rich.tree

        if not isinstance(tree, rich.tree.Tree):
            tree = rich.tree.Tree(tree or type(x).__name__)

        if isinstance(x, dict):
            [Tree.__rich__(v, tree.add(rich.tree.Tree(k))) for k, v in x.items()]
        elif isinstance(x, (list, tuple)):
            [Tree.__rich__(x, tree) for x in x]
        else:
            if not isinstance(x, str):
                x = str(x)
            tree.add(x)

        return tree


class Table(Widget):
    def __rich__(x):
        import rich.table

        t = rich.table.Table()
        p = Generic.Properties.form(type(x))
        if isinstance(x, list):
            for y in x:
                if not p:
                    p = dict(zip(y, y))
                    for k, v in p.items():
                        t.add_column(k)

                t.add_row(*map(Generic.Literals.__rich__, map(y.get, p)))
        return t
