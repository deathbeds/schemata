from .apis import StringCase
from .types import (
    JSONSCHEMA_SCHEMATA_MAPPING,
    Any,
    ContentEncoding,
    ContentMediaType,
    Type,
    UiWidget,
)
from .utils import EMPTY, partialmethod, testing, validates

__all__ = "String", "Bytes", "Uri", "Uuid"


class Bytes(ContentEncoding["base64"], bytes):
    @classmethod
    def is_valid(cls, object):
        testing.assertIsInstance(object, bytes)


class String(Type["string"], StringCase, str):
    @classmethod
    def is_valid(cls, object):

        testing.assertIsInstance(object, str)

    class Pattern(Any, id="validation:/properties/pattern"):
        @validates(str)
        def is_valid(cls, object):
            testing.assertRegex(object, cls.value(String.Pattern))

    def __class_getitem__(cls, object):
        if isinstance(object, str):
            return cls + cls.Pattern[object]
        return super().__class_getitem__(object)

    class Format(Any):
        pass

    class MinLength(Any, id="validation:/properties/minLength"):
        @validates(list, tuple, set)
        def is_valid(cls, object):
            testing.assertGreaterEqual(len(object), cls.value(String.MinLength))

    class MaxLength(Any, id="validation:/properties/maxLength"):
        @validates(list, tuple, set)
        def is_valid(cls, object):
            testing.assertLessEqual(len(object), cls.value(String.MaxLength))

    class Text(UiWidget["text"]):
        pass

    class Textarea(UiWidget["textarea"]):
        pass


class Email(String.Format["email"]):
    pass


class DataUrl(String.Format["data-url"]):
    pass


class Date(String.Format["date"]):
    pass


class DateTime(String.Format["date-time"]):
    pass


class Time(String.Format["time"]):
    pass


class Uri(String, String.Format["uri"]):
    @validates(str)
    def is_valid(cls, object):

        import rfc3986

        from .utils import not_format

        assert rfc3986.uri_reference(object).is_valid(require_scheme=True), not_format(
            cls, object
        )

    def __class_getitem__(cls, object):
        from .templates import UriTemplate

        return cls + UriTemplate[object]


class Uuid(String, String.Format["uuid"]):
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

    @validates(str)
    def is_valid(cls, object):

        import uuid

        uuid.UUID(object)

    def __class_getitem__(cls, object):
        return cls + Uuid.Version[object]

    class Version(Any):
        pass


class UriReference(String.Format["uri-reference"], Uri):
    pass


JSONSCHEMA_SCHEMATA_MAPPING["string"] = String
