def to_pydantic_annotations(cls):
    import pydantic
    import typing_extensions

    fields = {
        "title": "title",
        "description": "description",
        "const": "const",
        "gt": "minimumExclusive",
        "ge": "minimum",
        "lt": "maximumExclusive",
        "le": "maximum",
        "multipleOf": "multipleOf",
        "minItems": "minItems",
        "maxItems": "maxItems",
        "minLength": "minLength",
        "maxLength": "maxLength",
        "regex": "regex",
    }

    a = {}
    for k, v in cls.Properties.form(cls).items():
        s = v.schema()
        a[k] = typing_extensions.Annotated[
            cls.Type.pytype.__func__(v),
            pydantic.Field(
                s.get("default", ...),
                **{
                    fields.get(k, k): v
                    for k, v in s.items()
                    if k not in {"type", "default"}
                },
            ),
        ]
    return a


def to_pydantic(cls):
    import pydantic

    return type(
        cls.__name__,
        (pydantic.BaseModel,),
        dict(
            __annotations__=to_pydantic_annotations(cls),
            Config=type("Config", (), dict(schema_extra=cls.schema().ravel())),
        ),
    )
