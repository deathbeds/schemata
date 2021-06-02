from . import strings
from .types import Any, Type

__all__ = ("ContentEncoding", "ContentMediaType", "Plain", "Json", "Toml", "Yaml")


class ContentMediaType(Any, id="content:/properties/contentMediaType"):
    def _repr_mimebundle_(self, include=None, exclude=None):
        return dict({type(self).value(ContentMediaType, "text/plain"): self})


class ContentEncoding(Any, id="content:/properties/contentEncoding"):
    pass


class Plain(ContentMediaType["application"]):
    def loads(self):
        return self

    @classmethod
    def dumps(cls, self):
        return self


class Json(ContentMediaType["application/json"]):
    def loads(self):
        import json

        return json.loads(self)

    @classmethod
    def dumps(cls, self):
        import json

        return (strings.String + Json)(json.dumps(self))


class Yaml(ContentMediaType["application/yaml"]):
    def loads(self):
        import yaml

        return yaml.safe_load(self)

    @classmethod
    def dumps(cls, self, **kwargs):
        import yaml

        return (strings.String + Yaml)(yaml.safe_dump(self, **kwargs))


class Toml(ContentMediaType["text/toml"]):
    def loads(self):
        import toml

        return toml.loads(self)

    @classmethod
    def dumps(cls, self):
        import toml

        return (strings.String + Toml)(toml.dumps(self))


class Markdown(ContentMediaType["text/markdown"]):
    pass


class Html(ContentMediaType["text/html"]):
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
