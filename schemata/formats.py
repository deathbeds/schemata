from . import utils
from .types import Any


class Format(Any.from_key("format")):
    pass


class Email(Any.from_key("format", "email")):
    @utils.validates(str)
    def validator(cls, object):
        import email_validator

        email_validator.validate_email(object)
        return object


class DataUrl(Any.from_key("format", "data-url")):
    pass


class DateTime(Any.from_key("format", "date-time")):
    class TZ(Any):
        pass


class Date(Any.from_key("format", "date")):
    @utils.validates(str)
    def validator(cls, object):
        from . import times

        times.make_datetime_rfc(object + "T00:00:00+00:00")


class Time(Any.from_key("format", "time")):
    @utils.validates(str)
    def validator(cls, object):
        from . import times

        times.make_datetime_rfc("1970-01-01T" + object + "+00:00")


class UriTemplate(Any.from_key("format", "uri-template")):
    @classmethod
    def render(cls, *args, **kw):
        import uritemplate

        from .strings import String
        from .types import Type

        template = uritemplate.URITemplate(cls.value(String.Pattern))
        return template.expand(dict(zip(template.variable_names, args)), **kw)

    @utils.validates(str)
    def validator(cls, object):
        pattern = cls.value(UriTemplate)
        if pattern:
            import uritemplate

            from .strings import String

            uritemplate.URITemplate(object)
        return object


class Uri(Any.from_key("format", "uri")):
    @utils.validates(str)
    def validator(cls, object):
        import rfc3986

        assert rfc3986.uri_reference(object).is_valid(require_scheme=True)


class Uuid(Any.from_key("format", "uuid")):
    @utils.validates(str)
    def validator(cls, object, *args, **kwargs):
        import uuid

        return uuid.UUID(object, *args, **kwargs)


class JsonPointer(Any.from_key("format", "json-pointer")):
    @utils.validates(str)
    def validator(cls, object):
        import jsonpointer

        return jsonpointer.JsonPointer(object)


class UriReference(Any.from_key("format", "uri-reference")):
    pass
