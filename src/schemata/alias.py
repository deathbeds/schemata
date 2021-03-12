from .base import Any, Generic


class MinLength(Any, Generic.Alias):
    pass


class MaxLength(Any, Generic.Alias):
    pass


class Format(Any, Generic.Alias):
    pass


class MultipleOf(Any, Generic.Alias):
    pass


class Minimum(Any, Generic.Alias):
    pass


class Maximum(Any, Generic.Alias):
    pass


class ExclusiveMaximum(Any, Generic.Alias):
    pass


class ExclusiveMinimum(Any, Generic.Alias):
    pass


class Items(Any, Generic.Alias):
    pass


class Contains(Any, Generic.Alias):
    pass


class AdditionalItems(Any, Generic.Alias):
    pass


class MinItems(Any, Generic.Alias):
    pass


class MaxItems(Any, Generic.Alias):
    pass


class UniqueItems(Any, Generic.Alias):
    pass


class AdditionalProperties(Any, Generic.Alias):
    pass


class Required(Any, Generic.Plural):
    pass


class PropertyNames(Any, Generic.Alias):
    pass


class MinProperties(Any, Generic.Alias):
    pass


class MaxProperties(Any, Generic.Alias):
    pass


class Dependencies(Any, Generic.Alias):
    pass


class PatternProperties(Any, dict, Generic.Alias):
    pass


class ContentMediaType(Any, Generic.Alias):
    pass


class Examples(Any, Generic.Plural):
    @classmethod
    def examples(cls, *args):
        if not args:
            return cls.schema(False).get("examples", [])
        cls.__annotations__["examples"] = cls.__annotations__.get("examples", [])
        for v in args:
            cls.__annotations__["examples"].append(v)
        return cls


class Title(Any, Generic.Alias):
    ...


class Description(Any, Generic.Alias):
    ...
