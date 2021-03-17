"""the base types for schemata

in this module we introduce the schemata type api
"""

import functools
import typing

from .abc import Generic, ValidationError, ValidationErrors


def call(f, *args, **kwargs):
    """a universal call method we use"""
    # lists and dicts dont init properly, mebbe they do now,
    # this function exists because of each cases.
    if hasattr(f, "instance"):
        return f.instance(*args, **kwargs)
    return f(*args, **kwargs)


class Display:
    # custom display properties in ipython
    def _repr_mimebundle_(self, include=None, exclude=None):
        # customize the default view behavior for the object
        # currently we have an opinion about mediatype
        # the reality is that the formatter should be entirely its own thing.
        t = self.mediatype()
        if t is None:
            # parent is defined on Composite types allowing derived types to reference
            # their parent types.
            if hasattr(self, "parent"):
                t = self.parent.mediatype()

        if t is None:
            # default to text plain
            t = "text/plain"

        if t == "text/plain":
            self = repr(self)

        return {t: self}, {}

    # https://rich.readthedocs.io/en/latest/protocol.html
    # def __rich__(self):
    #     # rich display
    #     return

    # def __rich_console__(self):
    #     yield

    # def __rich_measure__(self), console, max_dict):
    #     pass

    # def __pt_container__(self):
    #     # prompt toolkit display
    #     return


class Any(Display, metaclass=Generic):
    # the primary concrete type of every schemata export

    # modify the construction behavior of the type
    # Any represents _any object_, it is equivalent to RDFS.Resource
    def __new__(cls, *args, **kwargs):
        # derived schemata types should use the instance method instead of
        # __new__ and __init__ for overriding functions
        return cls.instance(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        # short circuit initialization below this point and execute it ourselves
        # in the instance methods
        pass

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

    # modify features of the ABC
    @classmethod
    def default(cls, *args):
        # conventions to build defaults from const, default, enum

        CONST, DEFAULT, ENUM = "const", "default", "enum"
        s = cls.schema(0)
        if isinstance(s, typing.Iterable):
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
        return cls.schema(0).get(Generic.ContentMediaType.alias())

    @classmethod
    def strategy(cls):
        # derive a hypothesis strategy from type
        # our default strategy is to create strategies from the schema on
        # all of the objects.
        import hypothesis

        if cls not in cls.strategies:
            cls.strategies[cls] = __import__("hypothesis_jsonschema").from_schema(
                cls.schema()
            )
        return cls.strategies[cls]

    @classmethod
    def schema(cls: Generic, ravel=True):
        # generate the schema for the class

        # flatten schema squashes all annotations into a single dictionary
        x = Generic.flatten_schema(cls)
        if ravel:
            # raveling converts python types to jsonschema types
            # the unraveled schema is useful for python things, the ravelled types is
            # useful for jsonschema
            x = Generic.ravel_schema(x, parent=cls)
        return x

    @classmethod
    def alias(cls):
        # a common alias for the type, the default is the lowercase class name

        x = cls.__name__
        return x[0].lower() + x[1:] if x else x  #  lowercase x

    @classmethod
    def enter(cls):
        # an empty enter method for abc compliance
        pass  # pragma: no cover

    @classmethod
    def exit(cls, *e):
        # an empty exit method for abc compliance
        pass  # pragma: no cover
