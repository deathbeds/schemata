"""the base types for schemata

in this module we introduce the schemata type api
"""

from .abc import Generic, ValidationErrors, ValidationError
import typing
import functools


def call(f, *args, **kwargs):
    if hasattr(f, "instance"):
        return f.instance(*args, **kwargs)
    return f(*args, **kwargs)


class Any(metaclass=Generic):
    """everything is a Any, this is your interface to rdf land.

    rdf descriptions allow for multiple vocabularies and schema to cooperate.
    our Any type is jsonschema aware allowing for more flexible type descriptions
    than python."""

    # relative to pydantic:
    # pydantic only care about jsonschema, we care about jsonschema and rdf schema.

    # relative to traitlets/params
    # these tools define schema for runtime objects in python.
    # they reduce to jsonschema with work, but still lack general metadata
    # descriptions that enabled improved searches.

    # a near term goal is to generate pydantic, traitlets, and params translations of our types and vice versa.
    def __new__(cls, *args, **kwargs):
        # for ease of execution and testing we define the instance classmethod as the way types are created.
        return cls.instance(*args, **kwargs)

    def __init_subclass__(cls, type=None, ctx=None, vocab=None, base=None, **extras):

        cls._build_context(context=ctx, vocab=vocab, base=base)

        try:
            super().__init_subclass__(**extras)
        except TypeError:
            pass

    @classmethod
    def _build_context(cls, context=None, vocab=None, base=None, language=None):
        """build the context of the based on specific keys defined in the specification."""
        VOCAB, BASE, LANGUAGE = "@vocab", "@base", "@language"
        if context is None:
            context = {}
        if vocab:
            context[VOCAB] = str(vocab)
        else:
            for x in cls.__mro__:
                if hasattr(x, "vocab"):
                    v = x.vocab()
                    if v:
                        context[VOCAB] = v
                    break

        if base:
            context[BASE] = str(base)

        if language:
            context[LANGUAGE] = language
        if context:
            cls.__annotations__.update(context)

    @classmethod
    def alias(cls):
        x = cls.__name__
        return x[0].lower() + x[1:] if x else x

    @classmethod
    def cast(*args):
        from .literal import Py

        return Py[args]

    @classmethod
    def enter(cls):
        pass

    @classmethod
    def exit(cls, *e):
        pass

    @classmethod
    def default(cls, *args):

        CONST, DEFAULT, ENUM = "const", "default", "enum"
        s = cls.schema(0)

        # find constants first, always return the constant if there is one
        if CONST in s:
            return (s[CONST],)

        if args:
            return args

        # then look for default
        if DEFAULT in s:
            return (s[DEFAULT],)

        # then look for enums
        if ENUM in s:
            return tuple(s[ENUM][:1])

        return args

    @classmethod
    def mediatype(cls):
        from .composite import Composite

        this = cls.schema(0)
        if "contentMediaType" in this:
            return this["contentMediaType"]
        return

    def _repr_mimebundle_(self, include=None, exclude=None):
        t = self.mediatype()
        if t is None:
            if hasattr(self, "parent"):
                t = self.parent.mediatype()

        if t is None:
            t = "text/plain"

        if t == "text/plain":
            self = repr(self)

        return {t: self}, {}

    @classmethod
    def annotate(cls, t=None, in_place=False, **kwargs):
        if t is not None:
            kwargs["@type"] = t
        if in_place:
            cls.__annotations__.update(kwargs)
            return cls
        return Generic.new_type(cls, **kwargs)

    @classmethod
    def instance(cls, *args, **kwargs):
        """create a new Any that can be described rdf information"""
        # the base class can't be instantiated with any arguments or keywords.
        # a Any has an arity of 0 or 1 than can accept rdf desciptors as
        # keyword arguments.
        try:
            # instantiate with arguments
            self = super().__new__(cls, *args)
        except TypeError:
            # mebbe it can't take arguments
            try:
                self = super().__new__(cls)
            except TypeError:
                # mebbe it isnt safe
                self = cls.__new__(cls, *args)
        self.__init__(*args)
        for k, v in kwargs.items():
            setattr(self, k, v)
        if args:
            self.value = args[0]
        return self

    @classmethod
    def strategy(cls):
        import hypothesis

        if cls not in cls.strategies:
            cls.strategies[cls] = __import__("hypothesis_jsonschema").from_schema(
                cls.schema()
            )
        return cls.strategies[cls]

        return hypothesis.strategies.none()

    @classmethod
    def schema(cls: Generic, ravel=True):
        x = Generic.flatten_schema(cls)
        if ravel:
            x = Generic.ravel_schema(x, parent=cls)
        return x


del typing
