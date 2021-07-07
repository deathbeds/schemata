import datetime
import operator

from . import exceptions, formats, mediatypes, times, utils
from .types import EMPTY, Any, Schemata, Type

__all__ = (
    "String",
    "Bytes",
    "Uri",
    "Uuid",
    "Email",
    "JsonPointer",
)


class String(Type["string"], str):
    def __class_getitem__(cls, object):
        if isinstance(object, str):
            return cls + Pattern[object]
        return cls + object

    def splitlines(self, nl=False):
        from .arrays import List

        return List(str.splitlines(self, nl))

    def split(self, by=None, n=-1):
        from .arrays import List

        return List(str.split(self, by, n))

    def __add__(self, object):
        return type(self)(str.__add__(self, object))


class Pattern(Any):
    @utils.validates(str)
    def validator(cls, object):
        if not Schemata.value(cls, formats.Format):
            exceptions.assertRegex(object, Schemata.value(cls, Pattern))


class MinLength(Any):
    @utils.validates(str)
    def validator(cls, object):

        exceptions.assertGreaterEqual(len(object), Schemata.value(cls, MinLength))


class MaxLength(Any):
    @utils.validates(str)
    def validator(cls, object):
        exceptions.assertLessEqual(len(object), Schemata.value(cls, MaxLength))


class Bytes(mediatypes.ContentEncoding["base64"], bytes):
    @classmethod
    def validator(cls, object):
        exceptions.assertIsInstance(object, bytes)


# set default datetimes to now
class Email(formats.Email, String):
    pass


class Uuid(String, formats.Uuid):
    def __new__(cls, object=EMPTY, *args, **kwargs):
        import uuid

        if not object:
            version = Schemata.value(cls, Uuid.Version)
            if version:
                object = getattr(uuid, f"uuid{version}")(*args, **kwargs)
            else:
                object = "00000000-0000-0000-0000-000000000000"
        else:
            object = Schemata.validator(cls, object, *args, **kwargs)
        return super().__new__(cls, str(object))

    def __class_getitem__(cls, object):
        return cls + Uuid.Version[object]

    class Version(Any):
        pass

    @classmethod
    def to_pytype(cls):
        import uuid

        return uuid.Uuid


class Uri(String, formats.Uri):
    def __new__(cls, *args, **kwargs):
        template = Schemata.value(cls, Pattern)
        if template:
            args, kwargs = (
                formats.UriTemplate.render.__func__(cls, *args, **kwargs),
            ), {}
        return super().__new__(cls, *args, **kwargs)

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

    def __add__(self, object):
        return str.__new__(type(self), super().__add__(object))

    def __truediv__(self, object):
        return str.__new__(type(self), self + "/" + object)

    def __getattr__(self, object):
        if object.startswith("__"):
            return super().__getattr__(object)
        return str.__new__(type(self), super().__add__(object))

    def iframe(self, width="100%", height=600):
        import IPython

        return IPython.display.IFrame(self, width=width, height=height)


class UriReference(Uri, formats.UriReference):
    pass


class JsonPointer(String, formats.JsonPointer):
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


utils.JSONSCHEMA_SCHEMATA_MAPPING["string"] = String
