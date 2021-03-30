from .types import Form, Instance, String


class Uri(String, String.Format["uri"]):
    def get(*args, **kwargs):
        return __import__("requests").get(self, *args, **kwargs)


# set default datetimes to now
class DateTime(String, String.Format["date-time"]):
    @classmethod
    def object(cls, *args):
        import datetime

        import strict_rfc3339

        return datetime.datetime.utcfromtimestamp(
            strict_rfc3339.rfc3339_to_timestamp(*args)
        )


class Date(DateTime, String.Format["date"]):
    @classmethod
    def object(cls, *args):
        return super().object(str.__add__(*args, "T00:00:00+00:00"))


class Time(DateTime, String.Format["time"]):
    @classmethod
    def object(cls, *args):
        return super().object("1970-01-01T".__add__(*args))


class Email(String, String.Format["email"]):
    pass


class HostName(String, String.Format["hostname"]):
    pass


class IPv4(String, String.Format["ipyv4"]):
    pass


class IPv6(String, String.Format["ipyv6"]):
    pass


class Pointer(String, String.Format["json-pointer"]):
    def object(cls, *args):
        if len(args) > 1:
            args = (__import__("jsonpointer").JsonPointer.from_parts(args).path,)
        return super().object(*args)

    def resolve(self, object):
        # a pointer can be called against an object to resolve
        return __import__("jsonpointer").resolve_pointer(object, self)

    def __truediv__(self, object):
        return Pointer(self + "/" + object)


class UriTemplate(String, String.Format["uri-template"]):
    # conventions for uri templates
    # a UriTemplate is template for ids, we make it callable to resolve to Uri
    # with get, post, patch, head, options, ... methods

    def __call__(self, **kwargs):
        import uritemplate

        return Uri(uritemplate.URITemplate(self).expand(**kwargs))


class Regex(String, String.Format["regex"]):
    @classmethod
    def object(cls, *args):
        import re

        return re.compile(super().object(*args))


class Fstring(String, Form):
    @classmethod
    def type(cls, object):
        import parse

        cls = super().type(_parse._match_re)
        return cls


class Parse(Instance["parse.compile"]):
    @classmethod
    def type(cls, *args):
        return cls + cls.Args[args] + cls.Pattern[parse.compile(*args)._match_re]


class Jinja(Instance["jinja2.Template"]):
    @classmethod
    def object(cls, *args, **kwargs):
        import jinja2

        return super().object().render(*args, **kwargs)

    @classmethod
    def type(cls, *args):
        return cls + cls.Args[args]


class Code(String):
    @classmethod
    def load(cls, object):
        return cls(object)

    def type(cls, object):
        if object.startswith("."):
            return cls + Generic.FileExtension[object]
        return cls + Generic.MimeType[object]

    def _repr_html_(self):
        import pygments

        s = type(self).schema()
        lexer = None
        for e in s.get("fileExtension", ()):
            try:
                lexer = pygments.lexers.get_lexer_for_filename("*" + e)
                break
            except:
                pass
        if lexer is None:
            lexer = pygments.lexers.get_lexer_for_mimetype(
                s.get("mimeType", "text/plain")
            )
        return pygments.highlight(
            self,
            lexer,
            pygments.formatters.HtmlFormatter(
                linenos="table", wrapcode=True, noclasses=True
            ),
        )


class Toml(Code, String.MimeType["application/toml"], String.FileExtension[".toml"]):
    def loads(object):
        import toml

        from .types import Json

        return Json(toml.loads(object))

    @classmethod
    def dumps(cls, object):
        import toml

        return cls(toml.dumps(object))


class Yaml(
    Code,
    String.MimeType["text/x-yaml"],
    String.FileExtension[".yaml", ".yml"],
):
    def loads(object):
        import yaml

        from .types import Json

        return Json(yaml.safe_load(object))

    @classmethod
    def dumps(cls, object):
        pass


class JsonString(
    Code,
    String.MimeType["application/json"],
    String.FileExtension[".json", ".ipynb"],
):
    def loads(object):
        import json

        from .types import Json

        return Json(json.loads(object))

    @classmethod
    def dumps(cls, object):
        import json

        return cls(json.dumps(object))


class Markdown(
    Code,
    String.MimeType["text/x-markdown"],
    String.FileExtension[".md"],
):
    def __rich__(self):
        import rich.markdown

        return rich.markdown.Markdown(self)

    def loads(self):
        return (String + String.ContentMediaType["text/markdown"])(str(self))


class Html(
    String,
    String.ContentMediaType["text/html"],
    String.MimeType["text/html"],
    String.FileExtension[".html"],
):
    pass


class Md(String, Form.ContentMediaType["text/markdown"]):
    def __rich__(x, indent=0):
        import textwrap

        import rich.markdown

        if isinstance(x, list):
            x = "\n".join(f"* {Md.__rich__(y, indent+2)}" for y in x)

        if indent:
            return textwrap.indent(x, " " * indent)

        if not isinstance(x, str):
            x = str(x)

        return rich.markdown.Markdown(x)

    def __getattr__(self, tag):
        def main(**kwargs):
            kwargs = (
                kwargs and " " + " ".join(f'{k}="{v}"' for k, v in kwargs.items()) or ""
            )
            return Html(f"""<{tag}{kwargs}>{self}</{tag}>""")

        return main
