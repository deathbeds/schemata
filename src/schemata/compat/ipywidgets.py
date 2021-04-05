import enum
import functools
import types

from schemata import base, ui, util

from .ipython import get_names_in_main

mapping = dict(
    min=base.Minimum,
    max=base.Maximum,
    step=base.MultipleOf,
    description=base.Title,
    disabled=ui.Disabled,
    placeholder=ui.Placeholder,
    options=base.Generic.Enum,
)


mapping = {v.form(): k for k, v in mapping.items()}


def get_kwargs_from_schema(s, **kwargs):
    for k, v in s.items():
        if k in mapping:
            kwargs[mapping[k]] = v
    return kwargs


def get_widget_schema(s):
    if s.get("enum"):
        return get_widget_from_enum(s)
    if s.get("type") in {"number", "integer"}:
        return get_widget_from_number(s)

    if s.get("type") in {"string"}:
        return get_widget_from_string(s)


def get_widget_from_number(s):
    import ipywidgets

    if s.get("ui:widget") == "range":
        attr = "{}Slider"
    else:
        if any(
            x in s
            for x in ("maximum", "minimum", "exclusiveMinimum", "exclusiveMaximum")
        ):
            attr = "Bounded{}Text"
        else:
            attr = "{}Text"
    return getattr(
        ipywidgets, attr.format(dict(integer="Int", number="Float")[s["type"]])
    )


def get_widget_from_bool(s):
    import ipywidgets

    if s.get("ui:widget") == "checkbox":
        return ipywidgets.Checkbox
    return ipywidgets.ToggleButton


def get_widget_from_string(s):
    import ipywidgets

    if s.get("ui:widget") == "textarea":
        return ipywidgets.Textarea
    elif s.get("ui:widget") == "password":
        return ipywidgets.Password
    elif s.get("contentMediaType") == "text/html":
        return ipywidgets.HTML
    elif s.get("contentMediaType") == "imgae":
        return ipywidgets.Image
    elif s.get("format") == "date":
        return ipywidgets.DatePicker
    elif s.get("ui:widget") == "color":
        return ipywidget.ColorPicker

    return ipywidgets.Text


def get_widget_from_enum(s):
    import ipywidgets

    if s.get("ui:widget") == "select":
        return ipywidgets.Select
    elif s.get("ui:widget") == "radio":
        return ipywidgets.RadioButtons
    elif s.get("ui:widget") == "range":
        return ipywidgets.SelectionSlider
    elif s.get("ui:widget") == "toggle":
        return ipywidgets.ToggleButtons
    elif s.get("ui:widget") == "dropdown":
        return ipywidgets.Dropdown

    return ipywidgets.Select


def get_widget_from_value(*args, schema=None):
    if schema is None:
        schema = x.schema()

    widget = get_widget_schema(schema)
    kwargs = get_kwargs_from_schema(schema)
    if args:
        kwargs["value"] = util.identity(*args)
    w = widget(**kwargs)
    if args:
        names, annotations = get_names_in_main(*args)

        def handler(delta):
            nonlocal names
            m = __import__("__main__")
            for name in names:
                setattr(m, name, delta["new"])

        w.observe(handler, "value")
    return w
