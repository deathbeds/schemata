import datetime
import operator

from numpy.lib.arraysetops import isin

from . import formats, strings, mixins
from .callables import Any, Cast
from .utils import EMPTY, Ø, get_default, register

__all__ = "Date", "DateTime", "Time"

DT = operator.attrgetter(
    "year", "month", "day", "hour", "minute", "second", "microsecond", "tzinfo"
)


class DateTime(mixins.Time, formats.DateTime, datetime.datetime):
    pattern = "%Y-%m-%dT%H:%M:%S%z"

    class TZ(Any):
        pass

    def __new__(cls, *args, **kwargs):
        if not args:
            args = DT(datetime.datetime.now())
        else:
            if len(args) == 1:
                if isinstance(*args, datetime.datetime):
                    args = DT(*args)
                elif isinstance(*args, str):
                    args = DT(cls.strptime(*args, cls.pattern))

        return datetime.datetime.__new__(cls, *args, **kwargs)

    @classmethod
    def when(cls, *args, **kwargs):
        if len(args) == 1:
            if isinstance(*args, str):
                import maya

                args = (maya.when(*args).datetime(),)
        return cls(*args, **kwargs)

    cast = classmethod(when.__func__)

    def __str__(self):
        return self.strftime(self.pattern)

    def __float__(self):
        return self.timestamp()

    def __int__(self):
        return int(float(self))

    __repr__ = __str__


class Date(DateTime, formats.Date):
    pattern = "%Y-%m-%d"


class Time(DateTime, formats.Time):
    pattern = "%H:%M:%S%z"
