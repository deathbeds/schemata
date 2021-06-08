from schemata import ui, utils


def get_layout(schema):
    import ipywidgets

    return ipywidgets.Layout(**schema.get("layout", {}))


@utils.register
def get_widget(object, schema=utils.EMPTY, **kw):
    return


@get_widget.register
def get_widget_int(object: int, schema=utils.EMPTY, **kw):
    import ipywidgets

    schema = schema or object.schema()

    kw.update(
        utils.get_schema(
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
            },
            ravel=True,
        )
    )

    widget = schema.get(str(ui.UiWidget), tuple())

    if schema.get("type") == "boolean" or "checkbox" in widget:
        cls = ipywidgets.Checkbox
    elif "range" in widget:
        cls = ipywidgets.IntRangeSlider
    elif "slider" in widget:
        cls = ipywidgets.IntSlider
    elif "text" in widget:
        cls = ipywidgets.IntText
    else:
        cls = ipywidgets.IntSlider

    return cls(object, **kw, layout=get_layout(schema))


@get_widget.register
def get_widget_float(object: float, schema=utils.EMPTY, **kw):
    import ipywidgets

    schema = schema or object.schema()
    kw.update(
        utils.get_schema(
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
            },
            ravel=True,
        )
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

    return cls(
        object,
        **kw,
        layout=get_layout(schema),
        style=schema.get("style", type(object).value(ui.Style) or {})
    )


@get_widget.register
def get_widget_str(object: str, schema=utils.EMPTY, **kw):
    import ipywidgets

    schema = schema or object.schema()
    widget = schema.get(str(ui.UiWidget), "")

    if "textarea" in widget:
        cls = ipywidgets.Textarea
    else:
        cls = ipywidgets.Text

    return cls(object, **kw, layout=get_layout(schema), style=schema.get("style", {}))


@get_widget.register(list)
@get_widget.register(tuple)
def get_widget_iter(object, schema=utils.EMPTY, **kw):
    import ipywidgets

    schema = schema or object.schema(None)
    widget = schema.get(str(ui.UiWidget), "")

    schema = schema or object.schema()
    kw.update(
        utils.get_schema(
            {
                ipy: schema[s]
                for ipy, s in dict(
                    description="description",
                ).items()
                for s in s.split()
                if s in schema
            },
            ravel=True,
        )
    )

    widget = schema.get(str(ui.UiWidget), tuple())

    if "hbox" in widget:
        cls = ipywidgets.HBox
        object = get_children(object, schema=schema)
    elif "vbox" in widget:
        cls = ipywidgets.VBox
        object = get_children(object)
    elif "select" in widget:
        cls = ipywidgets.Select
    else:
        cls = ipywidgets.Select

    return cls(object, **kw, layout=get_layout(schema), style=schema.get("style", {}))


def get_children(object, schema=utils.EMPTY):
    if schema is utils.EMPTY:
        schema = {}
    typed = []
    if "items" in schema:
        schema = schema["items"]
        if isinstance(schema, (list, tuple)):
            for i, (cls, v) in enumerate(zip(schema, object)):
                if hasattr(cls, "widget"):
                    typed.append(cls.widget(v))
                else:
                    typed.append(get_widget(v, cls.schema()))
            object = object[i:]
            schema = utils.EMPTY
    return typed + [
        x.widget(x) if hasattr(x, "widget") else get_widget(x, schema=schema)
        for x in object
    ]
