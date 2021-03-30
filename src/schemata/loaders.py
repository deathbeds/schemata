from schemata import Translate


class Toml(
    Translate,
    Translate.ContentMediaType["application/toml"],
    Translate.FileExtension[".toml"],
):
    @classmethod
    def load(cls, object):
        import toml

        return Json(toml.loads(object))

    @classmethod
    def dump(cls, object):
        import toml

        return cls(toml.dumps(object))


class Json(
    Translate,
    Translate.ContentMediaType["application/json"],
    Translate.FileExtension[".json"],
):
    def load(object):
        import json

        return json.loads(object)

    @classmethod
    def dump(cls, object):
        import json

        return cls(json.dumps(object))


class Yaml(
    Translate,
    Translate.ContentMediaType["text/x-yaml"],
    Translate.FileExtension[".yaml", ".yml"],
):
    def load(self):
        import yaml

        return yaml.safe_load(object)

    @classmethod
    def dump(cls, object):
        import yaml

        return cls(yaml.safe_dump(object))
