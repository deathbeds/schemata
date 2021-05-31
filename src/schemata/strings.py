import datetime
import operator

from requests_cache.core import CachedSession

from . import exceptions, formats, mediatypes, templates, times, utils
from .apis import FluentString
from .types import EMPTY, JSONSCHEMA_SCHEMATA_MAPPING, Any, Type

__all__ = (
    "String",
    "Bytes",
    "Uri",
    "Uuid",
    "Email",
    "JsonPointer",
    "F",
    "Jinja",
    "UriTemplate",
)


class Bytes(mediatypes.ContentEncoding["base64"], bytes):
    @classmethod
    def validator(cls, object):
        exceptions.assertIsInstance(object, bytes)


# a string type
class String(Type["string"], FluentString, str):
    @classmethod
    def validator(cls, object):
        exceptions.assertIsInstance(object, str)

    def __class_getitem__(cls, object):
        if isinstance(object, str):
            return cls + cls.Pattern[object]
        if isinstance(object, slice):
            if object.step is not None:
                cls = cls[object.step]
            if object.start is not None:
                cls += String.MinLength[object.start]
            if object.stop is not None:
                cls += String.MaxLength[object.stop]
            return cls
        return super().__class_getitem__(object)

    class Pattern(Any, id="validation:/properties/pattern"):
        @utils.validates(str)
        def validator(cls, object):
            if not cls.value(formats.Format):
                exceptions.assertRegex(object, cls.value(String.Pattern))

    class MinLength(Any, id="validation:/properties/minLength"):
        @utils.validates(str)
        def validator(cls, object):

            exceptions.assertGreaterEqual(len(object), cls.value(String.MinLength))

    class MaxLength(Any, id="validation:/properties/maxLength"):
        @utils.validates(str)
        def validator(cls, object):
            exceptions.assertLessEqual(len(object), cls.value(String.MaxLength))


# set default datetimes to now
class Email(formats.Email, String):
    pass


class Uuid(String, formats.Format["uuid"]):
    def __new__(cls, object=EMPTY, *args, **kwargs):
        import uuid

        if not object:
            version = cls.value(Uuid.Version)
            if version:
                object = getattr(uuid, f"uuid{version}")(*args, **kwargs)
            else:
                object = "00000000-0000-0000-0000-000000000000"
        else:
            object = uuid.UUID(object, *args, **kwargs)
        return super().__new__(cls, str(object))

    @utils.validates(str)
    def validator(cls, object):
        import uuid

        uuid.UUID(object)

    def __class_getitem__(cls, object):
        return cls + Uuid.Version[object]

    class Version(Any):
        pass

    @classmethod
    def py(cls):
        import uuid

        return uuid.Uuid


class Uri(String, formats.Uri):
    def __class_getitem__(cls, object):
        cls = super().__class_getitem__(object)
        if isinstance(object, str):
            cls += formats.UriTemplate
        return cls

    @classmethod
    def object(cls, *args, **kwargs):
        template = cls.value(String.Pattern)
        if template:
            return Type.object.__func__(cls, cls.render(*args, **kwargs))

        return super().object(*args, **kwargs)

    def get(self, **kwargs):
        cache = type(self).value(Uri.Cache)
        if cache:
            if cache is True:
                cache = ".schemata-requests"
            import requests_cache

            with requests_cache.CachedSession() as session:
                response = session.get(self, **kwargs)
        else:
            import requests

            response = requests.get(self, **kwargs)
        return response

    @classmethod
    def cache(cls, object=True):
        return cls + Uri.Cache[object]

    class Cache(Any):
        pass

    def __truediv__(self, object):
        return self + "/" + object


class UriReference(Uri, formats.Format["uri-reference"]):
    pass


class JsonPointer(String, formats.Format["json-pointer"]):
    @utils.validates(str)
    def validator(cls, object):
        import jsonpointer

        return jsonpointer.JsonPointer(object)

    def resolve(self, object, **kw):
        import jsonpointer

        return jsonpointer.resolve_pointer(object, self, **kw)

    @classmethod
    def from_parts(cls, *args):
        import jsonpointer

        return cls(jsonpointer.JsonPointer.from_parts(args).path)

    def __truediv__(self, object):
        import jsonpointer

        return self.from_parts(*self.lstrip("/").split("/") + [object])


class DateTime(String, formats.DateTime):
    def __new__(cls, object=EMPTY):
        if not object:
            object = times.make_datetime(EMPTY).isoformat()

        return super().__new__(cls, object)

    def datetime(self):
        return DateTime(times.make_datetime_rfc(self))


class Date(DateTime, formats.Date):
    def __new__(cls, object=EMPTY):
        if not object:
            object = times.make_datetime(EMPTY).isoformat()[:10]
        return super().__new__(cls, object)

    def datetime(self):
        return times.DateTime(times.make_datetime_rfc(self + "T00:00:00+00:00"))


class Time(DateTime, formats.Time):
    def __new__(cls, object=EMPTY):
        if not object:
            object = times.make_datetime(EMPTY).isoformat().rpartition(".")[0][11:]
        return super().__new__(cls, object)

    def datetime(self):

        return times.DateTime(times.make_datetime_rfc("1970-01-01T" + self + "+00:00"))


JSONSCHEMA_SCHEMATA_MAPPING["string"] = String


class Template:
    def __class_getitem__(cls, object):
        return Any.__class_getitem__.__func__(cls, object)

    @classmethod
    def object(cls, *args, **kwargs):
        return super().object(cls.render(*args, **kwargs))


class StringTemplate(Template, String):
    pass


class F(StringTemplate):
    @classmethod
    def render(cls, *args, **kwargs):
        return cls.value(F).format(*args, **kwargs)


class Jinja(StringTemplate):
    @classmethod
    def render(cls, *args, **kwargs):
        import jinja2

        return jinja2.Template(cls.value(Jinja)).render(*args, **kwargs)

    @classmethod
    def input(cls):
        import jinja2.meta

        from . import Any, Dict

        return Dict.properties(
            {
                x: Any
                for x in jinja2.meta.find_undeclared_variables(
                    jinja2.Environment().parse(cls.value(Jinja))
                )
            }
        )


class UriTemplate(String, formats.UriTemplate):
    def render(self, *args, **kw):
        import uritemplate

        template = uritemplate.URITemplate(self)
        return template.expand(dict(zip(template.variable_names, args)), **kw)
