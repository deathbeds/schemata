from . import utils
from .types import Any


class Format(Any):
    pass


class Email(Format["email"]):
    @utils.validates(str)
    def validator(cls, object):
        import email_validator

        email_validator.validate_email(object)
        return object


class DataUrl(Format["data-url"]):
    pass


class DateTime(Format["date-time"]):
    class TZ(Any):
        pass


class Date(Format["date"]):
    @utils.validates(str)
    def validator(cls, object):
        from . import times

        times.make_datetime_rfc(object + "T00:00:00+00:00")


class Time(Format["time"]):
    @utils.validates(str)
    def validator(cls, object):
        from . import times

        times.make_datetime_rfc("1970-01-01T" + object + "+00:00")


class UriTemplate(Format["uri-template"]):
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


class Uri(Format["uri"]):
    @utils.validates(str)
    def validator(cls, object):
        import rfc3986

        assert rfc3986.uri_reference(object).is_valid(require_scheme=True)
