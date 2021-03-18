from . import base as B
from . import types as T
from .types import String, Uri


class DateTime(T.String, T.String.Format["date-time"]):
    pass


class Date(T.String, T.String.Format["date"]):
    pass


class Time(T.String, T.String.Format["time"]):
    pass


class Email(T.String, T.String.Format["email"]):
    pass


class HostName(T.String, T.String.Format["hostname"]):
    pass


class IPv4(T.String, T.String.Format["ipyv4"]):
    pass


class IPv6(T.String, T.String.Format["ipyv6"]):
    pass


class UriTemplate(T.String, T.String.Format["uri-template"]):
    # conventions for uri templates
    # a UriTemplate is template for ids, we make it callable to resolve to Uri
    # with get, post, patch, head, options, ... methods

    def __call__(self, **kwargs):
        import uritemplate

        return T.Uri(uritemplate.URITemplate(self).expand(**kwargs))


class RegEx(T.String, T.String.Format["regex"]):
    pass


class Pattern(B.Any, B.Generic.Alias):
    type: "string"

    @classmethod
    def pattern(cls):
        s = cls.schema(False)
        return s[cls.alias()]


class Formatter:
    @classmethod
    def instance(cls, *args, **kwargs):
        pattern = cls.pattern()
        return cls.format(pattern, *args, **kwargs)


class Format(Formatter, Pattern):
    def format(self, *args, **kwargs):
        return self.format(*args, **kwargs)


class Jinja(Formatter, Pattern):
    def format(self, *args, **kwargs):
        import sys

        import jinja2

        return jinja2.Template(self).render({**sys.modules, **dict(*args, **kwargs)})


class Dollar(Formatter, Pattern):
    def format(self, *args, **kwargs):
        import string

        return string.Template(self).safe_substitute(dict(*args, **kwargs))


class JsonE(Formatter, Pattern):
    type: "dict"
    EVAL = "$eval"
    JSON = "$json"
    IF = "$if"
    FLATTEN = "$flatten"
    FLATTENDEEP = "$flattenDeep"
    FROMNOW = "$fromNow"
    LET = "$let"
    MAP = "$map"
    MATCH = "$match"
    SWITCH = "$switch"
    MERGE = "$merge"
    MERGEDEEP = "$mergeDeep"
    SORT = "$sort"
    REVERSE = "$reverse"
    THEN = "then"
    ELSE = "else"

    def format(self, *args, **kwargs):
        import jsone

        return jsone.render(self, dict(*args, **kwargs))
