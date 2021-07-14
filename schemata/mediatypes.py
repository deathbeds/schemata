import mimetypes
from os import stat

from schemata.files import File

from . import strings, utils
from .types import Any, Schemata, Type

mimetypes = mimetypes.MimeTypes()

__all__ = ("ContentEncoding", "ContentMediaType", "Plain", "Json", "Toml", "Yaml")


class ContentMediaType(Any.from_key("contentMediaType")):
    def __init_subclass__(cls):
        setattr(Schemata, cls.__name__, cls)
        super().__init_subclass__()

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

    def __rich_protocol__(self, console):
        media = Schemata.value(self, ContentMediaType)

        if media == "text/markdown":
            import rich.markdown

            yield rich.markdown.Markdown(self)
        else:
            yield self


class ContentEncoding(Any.from_key("contentEncoding")):
    pass


class FileExtension(Any.from_key("fileExtension")):
    def __init_subclass__(cls):
        setattr(Schemata, cls.__name__, cls)
        super().__init_subclass__()

    @classmethod
    def get_loader(cls, object):
        for x in reversed(list(utils.get_subclasses(cls))):
            if object in utils.enforce_tuple(Schemata.value(x, FileExtension)):
                if hasattr(x, "loads"):
                    return x
        assert False, f"no loader discovered for {object}"

    @classmethod
    def get_dumper(cls, object):
        for x in reversed(list(utils.get_subclasses(cls))):
            if object in utils.enforce_tuple(Schemata.value(x, FileExtension)):
                if hasattr(x, "dumps"):
                    return x
        assert False, f"no loader discovered for {object}"


class MediaExtension(Any):
    def __class_getitem__(cls, object):
        cls = type(
            cls.__name__,
            (FileExtension[tuple(object[1].split())], ContentMediaType[object[0]], cls),
            {},
        )

        for y in object[1].split():
            mimetypes.add_type(object[0], y)
        return cls


class MediaString:
    def loads(self):
        return self

    @classmethod
    def dumps(cls, self):
        return self


class Plain(ContentMediaType["text/plain"], MediaString):
    pass


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


class Markdown(MediaExtension["text/markdown", ".md .markdown"], MediaString):
    pass


class Html(MediaExtension["text/html", ".html"], MediaString):
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
