import datetime

from . import base, types


# set default datetimes to now
class DateTime(types.String, types.String.Format["date-time"]):
    @classmethod
    def object(cls, *args):

        import strict_rfc3339

        return datetime.datetime.utcfromtimestamp(
            strict_rfc3339.rfc3339_to_timestamp(*args)
        )

    def py(cls):
        return datetime.datetime


class Date(DateTime, types.String.Format["date"]):
    @classmethod
    def object(cls, *args):
        return super().object(str.__add__(*args, "T00:00:00+00:00"))


class Time(DateTime, types.String.Format["time"]):
    @classmethod
    def object(cls, *args):
        return super().object("1970-01-01T".__add__(*args))


class Email(types.String, types.String.Format["email"]):
    pass


class HostName(types.String, types.String.Format["hostname"]):
    pass


class IPv4(types.String, types.String.Format["ipyv4"]):
    pass


class IPv6(types.String, types.String.Format["ipyv6"]):
    pass


class Pointer(types.String, types.String.Format["json-pointer"]):
    def object(cls, *args):
        if len(args) > 1 or args and not args[0].startswith("/"):
            args = (__import__("jsonpointer").JsonPointer.from_parts(args).path,)
        return super().object(*args)

    def resolve(self, object):
        return __import__("jsonpointer").resolve_pointer(object, self)

    def __truediv__(self, object):
        return Pointer(self + "/" + object)


class UriTemplate(types.String, types.String.Format["uri-template"]):
    def uri(self, **kwargs):
        return types.Uri(__import__("uritemplate").URITemplate(self).expand(**kwargs))


class Regex(types.String, types.String.Format["regex"]):
    @classmethod
    def object(cls, *args):
        import re

        return re.compile(super().object(*args))


class Fstring(types.String):
    def type(cls, object):
        import parse

        _parse = parse.compile(object)
        return cls + cls.Pattern[_parse._match_re]


class Parse(base.Pattern, types.String):
    @classmethod
    def object(cls, *args, **kwargs):
        return super().object(cls.Pattern.forms(cls)._format.format(*args, **kwargs))

    @classmethod
    def type(cls, *args):
        import parse

        return cls + cls.Pattern[parse.compile(*args)]


class Jinja(types.Instance["jinja2.Template"]):
    @classmethod
    def object(cls, *args, **kwargs):
        import jinja2

        return super().object().render(*args, **kwargs)

    @classmethod
    def type(cls, *args):
        return cls + cls.Args[args]


class Toml(
    types.String,
    types.String.ContentMediaType["application/toml"],
    types.String.FileExtension[".toml"],
):
    def loads(object):
        return types.Json(__import__("toml").loads(object))

    @classmethod
    def dumps(cls, object):
        return cls(__import__("toml").dumps(object))


class Yaml(
    types.String,
    types.String.ContentMediaType["text/x-yaml"],
    types.String.FileExtension[".yaml", ".yml"],
):
    def loads(object):
        return types.Json(__import__("yaml").safe_load(object))

    @classmethod
    def dumps(cls, object):
        return types.Json(__import__("yaml").safe_dump(object))


class JsonString(
    types.String,
    types.String.ContentMediaType["application/json"],
    types.String.FileExtension[".json", ".ipynb"],
):
    def loads(object):

        return types.Json(__import__("json").loads(object))

    @classmethod
    def dumps(cls, object):
        return cls(__import__("json").dumps(object))


class Markdown(
    types.String,
    types.String.ContentMediaType["text/markdown"],
    types.String.FileExtension[".md"],
):
    _repr_markdown_ = str


class Html(
    types.String,
    types.String.ContentMediaType["text/html"],
    types.String.FileExtension[".html"],
):
    _repr_html_ = str
