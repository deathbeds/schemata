from . import base as B
from . import literal as L
from .literal import String, Uri


class DateTime(L.String, L.String.Format["date-time"]):
    pass


class Date(L.String, L.String.Format["date"]):
    pass


class Time(L.String, L.String.Format["time"]):
    pass


class Email(L.String, L.String.Format["email"]):
    pass


class HostName(L.String, L.String.Format["hostname"]):
    pass


class IPv4(L.String, L.String.Format["ipyv4"]):
    pass


class IPv6(L.String, L.String.Format["ipyv6"]):
    pass


class UriTemplate(L.String, L.String.Format["uri-template"]):
    # conventions for uri templates
    # a UriTemplate is template for ids, we make it callable to resolve to Uri
    # with get, post, patch, head, options, ... methods

    def apply(self, *args, **kwargs):
        import uritemplate

        return L.Uri(uritemplate.URITemplate(self).expand(**kwargs))


class RegEx(L.String, L.String.Format["regex"]):
    pass


class Pointer(L.String, L.String.Format["json-pointer"]):
    @classmethod
    def instance(cls, *args):
        if len(args) > 1:
            args = (__import__("jsonpointer").JsonPointer.from_parts(args).path,)
        return super().instance(*args)

    def apply(self, object):
        # a pointer can be called against an object to resolve
        return __import__("jsonpointer").resolve_pointer(object, self)

    def __truediv__(self, object):
        return Pointer(self + "/" + object)


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
        return self.format(**dict(*args, **kwargs))


class Jinja(Formatter, Pattern):
    def format(self, *args, **kwargs):
        import jinja2, sys

        return jinja2.Template(self).render(*args, **sys.modules, **kwargs)


class Dollar(Formatter, Pattern):
    def format(self, *args, **kwargs):
        import string

        return string.Template(self).safe_substitute(*args, **kwargs)


class E(Formatter, Pattern):
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
