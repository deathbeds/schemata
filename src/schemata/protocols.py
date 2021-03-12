from . import base as B


class Protocol(B.Any):
    prefix = suffix = ""

    @classmethod
    def new_type(cls, object):
        return (cls.vocab() or "") + cls.prefix + object + cls.suffix

    @classmethod
    def add(cls, *args):
        cls.__slots__ += tuple(
            map(("{}" + cls.suffix).format, map(cls.prefix.__add__, args))
        )
        return cls

    @classmethod
    def names(cls, *args):
        return cls.__slots__


class Strict(Protocol):
    pass
    # requires annotations to exist


class Closed(Protocol):
    @classmethod
    def new_type(cls, object):
        if object in cls.names():
            return super().new_type(object)
        raise B.ValidationError(f"{object} not in {cls}")


class RDFS(Closed, vocab="http://www.w3.org/1999/02/22-rdf-syntax-ns#"):
    __slots__ = (
        "Resource",
        "Class",
        "subClassOf",
        "subPropertyOf",
        "comment",
        "label",
        "domain",
        "range",
        "seeAlso",
        "isDefinedBy",
        "Literal",
        "Container",
        "ContainerMembershipProperty",
        "member",
        "Datatype",
    )


class RDF(Closed, vocab="http://www.w3.org/2000/01/rdf-schema#"):
    __slots__ = (
        "RDF",
        "Description",
        "ID",
        "about",
        "parseGeneric",
        "resource",
        "li",
        "nodeID",
        "datatype",
        "Seq",
        "Bag",
        "Alt",
        "Statement",
        "Property",
        "List",
        "PlainLiteral",
        "subject",
        "predicate",
        "object",
        "type",
        "value",
        "first",
        "rest",
        "nil",
        "XMLLiteral",
        "HTML",
        "langString",
    )


class PROPS(Closed, vocab="http://json-schema.org/draft-07/schema#/properties/"):
    __slots__ = (
        "title",
        "description",
        "default",
        "readOnly",
        "examples",
        "multipleOf",
        "maximum",
        "exclusiveMaximum",
        "minimum",
        "exclusiveMinimum",
        "maxLength",
        "minLength",
        "pattern",
        "additionalItems",
        "items",
        "maxItems",
        "minItems",
        "uniqueItems",
        "contains",
        "maxProperties",
        "minProperties",
        "required",
        "additionalProperties",
        "definitions",
        "properties",
        "patternProperties",
        "dependencies",
        "propertyNames",
        "const",
        "enum",
        "type",
        "format",
        "contentMediaGeneric",
        "contentEncoding",
        "if",
        "then",
        "else",
        "allOf",
        "anyOf",
        "oneOf",
        "not",
    )


PROPS.add(
    *map(
        "$".__add__,
        (
            "id",
            "schema",
            "ref",
            "comment",
        ),
    )
)


class LD(Protocol, vocab="jsonld://"):
    __slots__ = ()
    prefix = "@"


LD.add(
    "context",
    "vocab",
    "type",
    "id",
    "base",
    "language",
    "graph",
)


class XSD(Protocol, vocab="http://www.w3.org/2001/XMLSchema#"):
    pass


class Dunder(Protocol, vocab=""):
    __slots__ = ()
    prefix = suffix = "__"
