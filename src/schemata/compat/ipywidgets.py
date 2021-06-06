from schemata import ui, utils


def get_layout(schema):
    import ipywidgets

    return ipywidgets.Layout(**schema.get("layout", {}))


@utils.register
def get_widget(object):
    return


@get_widget.register
def get_widget_bool(object: bool):
    return


@get_widget.register
def get_widget_int(object: int, **kw):
    import ipywidgets

    schema = object.schema()
    kw.update(
        {
            ipy: schema[s]
            for ipy, s in dict(
                description="description",
                min="minimum exclusiveMinimum",
                max="maximum exclusiveMaximum",
                step="multipleOf",
            ).items()
            for s in s.split()
            if s in schema
        }
    )

    widget = schema.get(str(ui.UiWidget), tuple())

    if "range" in widget:
        cls = ipywidgets.IntRangeSlider
    elif "slider" in widget:
        cls = ipywidgets.IntSlider
    elif "text" in widget:
        cls = ipywidgets.IntText
    else:
        cls = ipywidgets.IntSlider

    return cls(object, **kw, layout=get_layout(schema))


@get_widget.register
def get_widget_float(object: float, **kw):
    import ipywidgets

    schema = object.schema()
    kw.update(
        {
            ipy: schema[s]
            for ipy, s in dict(
                description="description",
                min="minimum exclusiveMinimum",
                max="maximum exclusiveMaximum",
                step="multipleOf",
            ).items()
            for s in s.split()
            if s in schema
        }
    )

    widget = schema.get(str(ui.UiWidget), tuple())

    if "range" in widget:
        cls = ipywidgets.FloatRangeSlider
    elif "slider" in widget:
        cls = ipywidgets.FloatSlider
    elif "text" in widget:
        cls = ipywidgets.FloatText
    else:
        cls = ipywidgets.FloatSlider

    return cls(object, **kw, layout=get_layout(schema))


@get_widget.register
def get_widget_str(object: str, **kw):
    import ipywidgets

    schema = object.schema()
    widget = schema.get(str(ui.UiWidget), "")

    if "textarea" in widget:
        cls = ipywidgets.Textarea
    else:
        cls = ipywidgets.Text

    return cls(object, **kw, layout=get_layout(schema))
