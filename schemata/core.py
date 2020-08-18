"""Core types for schemata."""
import abc
import typing
import builtins
import functools
import inspect
import pathlib
import rdflib
import schemata
from . import checker, data, mutable, util, ops, rdf, translate

_ = translate.get_translation("en").gettext


__all__ = "jsonschema", 


class specification(ops.unary, ops.binary, abc.ABCMeta):
    """An abstract base class for building and validating types."""

    # A cache of types.
    __types__ = {}

    def __init_subclass__(cls):
        util.merge_annotations(cls)

        # Derive a fluent api for enriching schema.
        for property in cls.__annotations__.get("properties", {}):
            setattr(
                cls,
                property.lstrip("$"),
                functools.partialmethod(cls._property_attribute, property),
            )

    def _property_attribute(cls, key, object, **schema):
        return cls[{key: object, **schema}]

    def __new__(cls, name, bases, kwargs, language=None):
        # ensure we're adding annotations.
        a = kwargs["__annotations__"] = kwargs.get("__annotations__", {})
        if language:
            a["@context"] = a.get("@context", {})
            a["@context"].update({"@language": language})

        # assign a concrete type the base classes based on URIs.
        base_type = cls.to_type(a, *bases)
        if base_type not in (bool, builtins.type(None), None):
            bases += (base_type,)

        # Finally create the type.
        self = super().__new__(cls, a.get("title", name), bases, kwargs)

        # The annotations are frozen
        # Access an equivalent cached type if it exists.
        if (self.__name__, self.__annotations__) in cls.__types__:
            prior = cls.__types__[self.__name__, self.__annotations__]

            del self
            return prior

        # cache the type.
        cls.__types__[self.__name__, self.__annotations__] = self
        return self

    @staticmethod
    def to_type(annotation, *bases):
        """URIs are used for type discovery, to_type discovers types."""
        # has a new type been defined?
        if "@type" in annotation:
            type = rdflib.URIRef(annotation["@type"])
            if type in rdf.types:
                return rdf.types[type]

        # Look through the base class for the canonical type.
        for cls in bases:
            for cls in inspect.getmro(cls):
                if hasattr(cls, "__schema__") and "@type" in cls.__schema__:
                    type = rdflib.URIRef(cls.__schema__.get("@type"))
                    if type in rdf.types:
                        return rdf.types[type]

    def __instancecheck__(cls, object):
        try:
            return cls.validate(object) or True
        except:
            return super().__instancecheck__(object)


class implementation:
    """A concrete implementation of an ABC for specific types.."""

    __annotations__ = {}
    __init_subclass__ = util.merge_annotations


class applicator:
    __annotations__ = getattr(
        data, "https://json-schema.org/draft/2019-09/meta/applicator"
    )


class content:
    __annotations__ = getattr(
        data, "https://json-schema.org/draft/2019-09/meta/content"
    )


class core:
    __annotations__ = getattr(data, "https://json-schema.org/draft/2019-09/meta/core")


class format:

    __annotations__ = getattr(data, "https://json-schema.org/draft/2019-09/meta/format")


class hyper_schema:
    __annotations__ = getattr(
        data, "https://json-schema.org/draft/2019-09/meta/hyper-schema"
    )


class meta_data:
    __annotations__ = getattr(
        data, "https://json-schema.org/draft/2019-09/meta/meta-data"
    )


class validation:
    __annotations__ = getattr(
        data, "https://json-schema.org/draft/2019-09/meta/validation"
    )


class meta_schema(
    content,
    core,
    format,
    hyper_schema,
    meta_data,
    validation,
    applicator,
    specification,
):
    """The meta_schema is a composition of the core jsonschema specifications."""


class jsonschema(implementation, metaclass=meta_schema):
    @classmethod
    def __new_anyof__(cls, object):
        for schema in cls.__schema__["anyOf"]:
            try:
                return jsonschema[schema](object)
            except:
                ...
        cls.validate(object)

    def __new_oneof__(cls, object):
        for i, schema in enumerate(cls.__schema__["oneOf"]):
            try:
                self = jsonschema[schema](object)
                break
            except:
                ...
        else:
            cls.validate(object)

        for schema in cls.__schema__["oneOf"][i:]:
            try:
                jsonschema[schema](object)
                cls.validate(object)
            except:
                ...
        return self

    def __new__(cls, object=None):
        if object is None:
            object = cls.__schema__.get(_("default"), object)
            if object is None:
                object = cls.__schema__.get(_("examples"), [object])[0]
        if "anyOf" in cls.__schema__:
            return cls.__new_anyof__(object)
        if "oneOf" in cls.__schema__:
            return cls.__new_oneof__(object)

        cls.validate(object)
        if issubclass(builtins.type(object), (bool, builtins.type(None))):
            return object
        return super().__new__(cls, object)

    def __init_subclass__(cls):
        util.merge_annotations(cls)
        cls.__schema__ = util.unfreeze(
            util.schema_from_annotations(cls.__annotations__)
        )

        language = cls.__schema__.get("@context", {}).get("@language", "en")

        __import__("jsonschema").validate(
            cls.__schema__,
            translate.translate(type(cls).__annotations__, language),
            cls=checker.localize_validator(language),
            format_checker=checker.checker,
        )

    @classmethod
    def validate(cls, object: typing.Any):
        """Validate an  object against a schema."""
        language = cls.__schema__.get("@context", {}).get("@language", "en")

        __import__("jsonschema").validate(
            object, cls.__schema__, cls=checker.localize_validator(language)
        )

    # IPython display features
    def _repr_data_(self) -> typing.Dict[str, str]:
        """Return a valid MimeBundle for the IPython display system."""
        schema = self.__schema__
        if _("contentMediaType") in schema:
            return {schema[_("contentMediaType")]: self}
        return {"text/plain": repr(self)}

    def _repr_meta_(self) -> typing.Union[typing.List, typing.Dict[str, typing.Any]]:
        """Return expanded/compacted linked data."""
        return {}

    def _repr_mimebundle_(
        self, include=None, exclude=None
    ) -> typing.Tuple[typing.Dict, typing.Dict]:
        """Separate the data and metadata representations into separate functions."""
        return self._repr_data_(), self._repr_meta_()

    # Example generation from schema.
    @classmethod
    def strategy(
        cls, filter=None
    ) -> typing.ForwardRef("hypothesis.strategies.Strategy"):
        """Generate testing strategies from a schema."""
        from hypothesis import strategies

        schema = cls.__schema__
        strategy = __import__("hypothesis_jsonschema").from_schema(schema)
        if "default" in schema or "examples" in schema:
            strategy = (strategy,)
            if "default" in schema:
                strategy += strategies.just(schema["default"])
            if "examples" in schema:
                strategy += (strategies.one_of(schema["examples"]),)
            return strategies.one_of(*strategy)
        return strategy.filter(filter) if filter else strategy

    @classmethod
    def example(cls: "T", filter: typing.Callable = None) -> "T":
        """Generate an example from a strategy"""
        if filter is not None and not callable(filter):
            raise TypeError("filter must be a callable.")
        return cls(cls.strategy(filter).example())