import enum
import functools
import types

import ipywidgets
import traitlets

from schemata import types, ui, util

mapping = dict(
    min=types.Minimum,
    max=types.Maximum,
    step=types.MultipleOf,
    description=types.Title,
    disabled=ui.Disabled,
    placeholder=ui.Placeholder,
    options=types.Generic.Enum,
)


mapping = {v.form(): k for k, v in mapping.items()}


def get_kwargs_from_schema(s, **kwargs):
    for k, v in s.items():
        if k in mapping:
            kwargs[mapping[k]] = v
    return kwargs


def make_object_widget(layout, **kwargs):
    pass


def get_widget_from_object(s):
    import ipywidgets

    widgets = {}

    def widget(**kwargs):
        children = []
        if s.has("properties"):
            for key, value in s["properties"].items():
                S = s["properties"][key].schema()
                widget = get_widget_from_schema(S)

                k = get_kwargs_from_schema(S)
                k["description"] = key
                if key in kwargs.get("value", {}):
                    k["value"] = kwargs["value"][key]
                children.append(widget(**k))
        return ValueContainer(
            container=ipywidgets.HBox(children=children), value=kwargs["value"]
        )

    return widget


def get_widget_from_schema(s):
    if s.has("enum"):
        return get_widget_from_enum(s)
    if s.has("type", "integer", "number"):
        return get_widget_from_number(s)
    if s.has("type", "string"):
        return get_widget_from_string(s)
    if s.has("type", "object"):
        return get_widget_from_object(s)


def get_widget_from_number(s):
    import ipywidgets

    if s.has("ui:widget", "range"):
        attr = "{}Slider"
    else:
        if any(
            map(s.has, ("maximum", "minimum", "exclusiveMinimum", "exclusiveMaximum"))
        ):
            attr = "Bounded{}Text"
        else:
            attr = "{}Text"
    return getattr(
        ipywidgets, attr.format(dict(integer="Int", number="Float")[s["type"][0]])
    )


def get_widget_from_bool(s):
    import ipywidgets

    if s.has("ui:widget", "checkbox"):
        return ipywidgets.Checkbox
    return ipywidgets.ToggleButton


def get_widget_from_string(s):
    import ipywidgets

    if s.has("ui:widget", "textarea"):
        return ipywidgets.Textarea
    elif s.has("ui:widget", "password"):
        return ipywidgets.Password
    elif s.has("contentMediaType", "text/html"):
        return ipywidgets.HTML
    elif s.has("contentMediaType", "image"):
        return ipywidgets.Image
    elif s.has("format", "date"):
        return ipywidgets.DatePicker
    elif s.has("ui:widget", "color"):
        return ipywidgets.ColorPicker

    return ipywidgets.Text


def get_widget_from_enum(s):
    import ipywidgets

    if s.has("ui:widget", "select"):
        return ipywidgets.Select
    elif s.has("ui:widget", "radio"):
        return ipywidgets.RadioButtons
    elif s.has("ui:widget", "range"):
        return ipywidgets.SelectionSlider
    elif s.has("ui:widget", "toggle"):
        return ipywidgets.ToggleButtons
    elif s.has("ui:widget", "dropdown"):
        return ipywidgets.Dropdown

    return ipywidgets.Select


def get_widget_from_value(*args, schema=None, **kwargs):
    """create widgets from an object conforming to a schema.

    Args:
        schema ([type], optional): [description]. Defaults to None.

    Returns:
        [type]: [description]
    """
    if args:
        kwargs["value"] = util.identity(*args)

    if schema is None:
        schema = kwargs["value"].schema()

    widget = get_widget_from_schema(schema)
    kwargs.update(get_kwargs_from_schema(schema))
    return widget(**kwargs)


class ValueContainer(traitlets.HasTraits):
    container = traitlets.Any()
    value = traitlets.Any()

    def _ipython_display_(self):
        import IPython

        IPython.display.display(self.container)

    @traitlets.observe("value")
    def _change_value(self, delta):
        for child in self.container.children:
            if child.description in delta["new"]:
                child.value = delta["new"][child.description]
