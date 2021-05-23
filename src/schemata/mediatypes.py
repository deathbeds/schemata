from . import ContentMediaType
from .strings import String, Type


class Plain(ContentMediaType["application"]):
    @classmethod
    def loads(cls, self):
        return self

    @classmethod
    def dumps(cls, self):
        return self


class Json(ContentMediaType["application/json"]):
    @classmethod
    def loads(cls, self):
        import json

        return json.loads(self)

    @classmethod
    def dumps(cls, self):
        import json

        return (String + Json)(json.dumps(self))


class Yaml(ContentMediaType["application/yaml"]):
    @classmethod
    def loads(cls, self):
        import yaml

        return yaml.safe_load(self)

    @classmethod
    def dumps(cls, self, **kwargs):
        import yaml

        return (String + Yaml)(yaml.safe_dump(self, **kwargs))


class Toml(ContentMediaType["text/toml"]):
    @classmethod
    def loads(cls, self):
        import toml

        return toml.loads(self)

    @classmethod
    def dumps(cls, self):
        import toml

        return (String + Toml)(toml.dumps(self))


class Markdown(ContentMediaType["text/markdown"]):
    pass


class Html(ContentMediaType["text/html"]):
    pass


Type.Plain = Plain
Type.Json = Json
Type.Yaml = Yaml
Type.Toml = Toml
Type.Markdown = Markdown
Type.Html = Html
