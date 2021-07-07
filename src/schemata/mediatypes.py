import mimetypes

from schemata.files import File

from . import strings, utils
from .types import Any, Schemata, Type

mimetypes = mimetypes.MimeTypes()

__all__ = ("ContentEncoding", "ContentMediaType", "Plain", "Json", "Toml", "Yaml")


class ContentMediaType(Any):
    @classmethod
    def get_loader(cls, object):
        for x in reversed(list(utils.get_subclasses(cls))):
            if object in utils.enforce_tuple(Schemata.value(x, ContentMediaType)):
                if hasattr(x, "loads"):
                    return x
        assert False, f"no loader discovered for {object}"

    @classmethod
    def get_dumper(cls, object):
        for x in reversed(list(utils.get_subclasses(cls))):
            if object in utils.enforce_tuple(Schemata.value(x, ContentMediaType)):
                if hasattr(x, "dumps"):
                    return x
        assert False, f"no loader discovered for {object}"

    def _repr_mimebundle_(self, include=None, exclude=None):
        return {Schemata.value(self, ContentMediaType, default="text/plain"): self}, {}


class ContentEncoding(Any):
    pass


class FileExtension(Any):
    pass


class MediaExtension(Any):
    def __class_getitem__(cls, object):
        cls += ContentMediaType[object[0]] + FileExtension[tuple(object[1].split())]
        for y in object[1].split():
            mimetypes.add_type(object[0], y)
        return cls


class Plain(ContentMediaType["text/plain"]):
    def loads(self):
        return self

    @classmethod
    def dumps(cls, self):
        return self


class Json(MediaExtension["application/json", ".json .ipynb"]):
    def loads(self):
        import json

        return json.loads(self)

    @classmethod
    def dumps(cls, self):
        import json

        return (strings.String + Json)(json.dumps(self))


class Yaml(MediaExtension["application/yaml", ".yml .yaml"]):
    def loads(self):
        import yaml

        return yaml.safe_load(self)

    @classmethod
    def dumps(cls, self, **kwargs):
        import yaml

        return (strings.String + Yaml)(yaml.safe_dump(self, **kwargs))


class Toml(MediaExtension["text/toml", ".toml"]):
    def loads(self):
        import toml

        return toml.loads(self)

    @classmethod
    def dumps(cls, self):
        import toml

        return (strings.String + Toml)(toml.dumps(self))


class Markdown(MediaExtension["text/markdown", ".md .markdown"]):
    pass


class Html(MediaExtension["text/html", ".html"]):
    pass


class LD(Json, ContentMediaType["application/ld+json"]):
    pass


class Turtle(ContentMediaType["text/turtle"]):
    pass


class Rdf(ContentMediaType["application/rdf+xml"]):
    pass


class Image:
    pass


class Png(ContentMediaType["image/png"]):
    pass


class Bmp(ContentMediaType["image/bmp"]):
    pass


class Jpeg(ContentMediaType["image/jpeg"]):
    pass


Type.Plain = Plain
Type.Json = Json
Type.Yaml = Yaml
Type.Toml = Toml
Type.Markdown = Markdown
Type.Html = Html
