import datetime
import operator

from . import formats, strings
from .apis import FluentTime
from .callables import Any, Cast
from .utils import EMPTY, Ø, get_default, register

__all__ = "Date", "DateTime", "Time"


@register
def make_datetime(object):
    return object


def make_datetime_rfc(object: str):
    import strict_rfc3339

    return datetime.datetime.utcfromtimestamp(
        strict_rfc3339.rfc3339_to_timestamp(object)
    )


def make_datetime_maya(object: str):
    import maya

    return maya.when(object).datetime()


@make_datetime.register
def make_datetime_str(object: str):
    try:
        return make_datetime_rfc(object)
    except BaseException as e:
        return make_datetime_maya(object)


@make_datetime.register
def make_datetime_null(object: Ø):
    return datetime.datetime.now()


class DateTime(FluentTime, formats.DateTime, datetime.datetime):
    class TZ(Any):
        pass

    def __new__(cls, object=EMPTY):
        object = make_datetime(get_default(cls, object))
        return datetime.datetime.__new__(
            cls,
            *operator.attrgetter(
                *"year month day hour minute second microsecond tzinfo".split()
            )(object),
        )

    @classmethod
    def py(cls):
        return datetime.datetime

    def __str__(self):
        import strict_rfc3339

        return strings.String[type(self)](
            strict_rfc3339.timestamp_to_rfc3339_utcoffset(self.timestamp())
        )

    def __float__(self):
        return self.timestamp()

    def __int__(self):
        return int(float(self))


class Date(DateTime, formats.Date):
    def __new__(cls, object=EMPTY):
        object = get_default(cls, object)
        if isinstance(object, str):
            if not cls.value(Cast):
                object += "T00:00:00+00:00"
        return super().__new__(cls, object)


class Time(DateTime, formats.Time):
    @classmethod
    def object(cls, object=EMPTY):
        object = get_default(cls, object)
        if isinstance(object, str):
            if not cls.value(Cast):
                object = "1970-01-01T" + object
        return super().__new__(cls, object)
