import inspect
import operator
import typing
from functools import partialmethod

from . import exceptions, utils
from .utils import EMPTY


class TypeConversion:
    @classmethod
    def py(cls):
        return cls

    @classmethod
    def dtype(cls):
        import numpy

        return numpy.dtype(cls.py())

    @classmethod
    def return_annotation(cls):
        return cls


class Validate:
    @classmethod
    def get_validators(cls, *checked):
        for t in inspect.getmro(cls):
            if utils.is_validator(t):
                if t not in checked:
                    yield t
                    checked += (t.validator,)

    @classmethod
    def validate(cls, object):
        exception = exceptions.ValidationError()
        for t in cls.get_validators():
            with exception:
                t.validator.__func__(cls, object)
        exception.raises()

    @classmethod
    def validator(cls, object):
        pass


class TypeOps:
    def __add__(cls, *object, **kwargs):
        return type(cls.__name__, (cls,) + object, {})

    add = __add__

    def __radd__(cls, *object):
        return type(cls.__name__, object + (cls,), {})

    def __pos__(cls):
        return cls

    def __neg__(cls):
        from . import Not

        return Not[cls]

    not_ = __neg__

    def __and__(cls, *object):
        from . import AllOf

        return AllOf[(cls,) + object]

    and_ = __and__

    def __or__(cls, *object):
        from . import AnyOf

        return AnyOf[(cls,) + object]

    or_ = __or__

    def __xor__(cls, *object):
        from . import OneOf

        return OneOf[(cls,) + object]

    xor = __xor__

    def __rshift__(cls, object):
        return cls.cast(object)

    def __rrshift__(cls, object):
        from .callables import Cast

        return Cast[object, cls]

    def __lshift__(cls, object):
        from .callables import Do

        return cls >> Do[object]

    do = __lshift__

    def __rlshift__(cls, object):
        from .callables import Do

        return Do[object] >> cls

    def __eq__(cls, object):
        from .types import MetaType

        if isinstance(object, MetaType):
            return cls.schema() == object.schema()
        return super().__eq__(object)

    eq = __eq__

    def __hash__(cls):
        return hash(utils.get_hashable(cls))

    hash = __hash__

    def __getattr__(cls, str):
        try:
            return object.__getattribute__(cls, str)
        except AttributeError as e:
            error = e
        if str[0].islower():
            name = utils.uppercase(str)
            if hasattr(cls, name):

                def caller(*args, **kw):
                    if (not args) and kw:
                        args = (kw,)
                    nonlocal cls
                    object = getattr(cls, name)
                    if not args:
                        cls += object
                    elif len(args) is 1:
                        cls += object[args[0]]
                    else:
                        cls += object[args]

                    return cls

                return caller
        raise error

    getattr = __getattr__

    def __dir__(cls):
        object = super().__dir__()
        return object + [
            k[0].lower() + k[1:]
            for k in object
            if k[0].isupper() and isinstance(getattr(cls, k), type)
        ]

    dir = __dir__


class FluentNumber:
    def math_(self, attr, *args, **kwargs):
        import math

        return type(self)(getattr(math, attr)(self, *args, **kwargs))

    import math

    for k, v in vars(math).items():
        if k[0].islower():

            if callable(v):
                locals().update({k: partialmethod(math_, k)})
            else:
                locals().update({k: getattr(math, k)})

    del k


class FluentType:
    def pipe(self, callable, *args, **kwargs):
        return callable(self, *args, **kwargs)

    @classmethod
    def strategy(cls):
        import hypothesis_jsonschema

        return hypothesis_jsonschema.from_schema(cls.schema(True))

    def print(self):
        try:
            import rich

            return rich.print(self)
        except ModuleNotFoundError:
            import pprint

            if isinstance(self, str):
                print(self)
            else:
                pprint.pprint(self)


class FluentString:
    def _stringcase(self, case):
        import stringcase

        from .strings import String

        return String(getattr(stringcase, case)(self))

    for (
        k
    ) in "alphanumcase backslashcase camelcase camelcase constcase dotcase lowercase pascalcase pathcase sentencecase snakecase spinalcase titlecase trimcase uppercase".split():
        locals().update({k: partialmethod(_stringcase, k)})
    del k

    def splitlines(self, nl=False):
        from .arrays import List

        return List(str.splitlines(self, nl))

    def split(self, by=None, n=-1):
        from .arrays import List

        return List(str.split(self, by, n))

    def __add__(self, object):
        return type(self)(str.__add__(self, object))


class FluentTime:
    def __enter__(self):
        import freezegun

        self._freeze = freezegun.freeze_time(self)
        self._freeze.__enter__()

    def __exit__(self, *e):
        self._freeze.__exit__(*e)

    @classmethod
    def when(cls, object=EMPTY):
        return cls.cast()(object)

    def _maya(self, attr):
        import maya

        return operator.methodcaller(attr)(maya.MayaDT(self.timestamp()))

    for k in "slang_date slang_time iso8601 rfc2822 rfc3339".split():
        locals().update({k: partialmethod(_maya, k)})
    del k


class FluentArrays:
    def map(self, callable, *args, **kwargs):
        from .types import MetaType

        cls = type(self)
        if isinstance(callable, MetaType):
            cls = cls[callable]
        return cls.cast()((callable(x, *args, **kwargs) for x in self))

    def filter(self, callable, *args, **kwargs):
        cls = type(self)
        return cls.cast()((x for x in self if callable(x, *args, **kwargs)))

    def dataframe(self, *args, **kwargs):
        import pandas

        return pandas.DataFrame(self, *args, **kwargs)

    def series(self, *args, **kwargs):
        import pandas

        return pandas.Series(self, *args, **kwargs)

    def append(self, *args):
        list.append(self, *args)
        return self

    def extend(self, *args):
        list.extend(self, *args)
        return self

    def insert(self, *args):
        list.insert(self, *args)
        return self

    def remove(self, *args):
        list.remove(self, *args)
        return self

    def clear(self, *args):
        list.clear(self, *args)
        return self

    def sum(self, start=0):
        from .arrays import List

        if isinstance(start, str):
            from .strings import String

            # usually strings fail to sum on strings.
            return String(start.join(self))
        return List(sum(self, start))

    def sort(self, inplace=True, key=EMPTY, reverse=EMPTY):
        if inplace:
            self.sort(key=key or None, reverse=key or False)
        return type(self).verified(
            [sorted(self, key=EMPTY or None, reverse=EMPTY or False)]
        )


class FluentDict:
    def items(self, cls=True):
        from .objects import Dict

        if not cls:
            return dict.items(self)
        from .arrays import List, Tuple

        if cls is True:
            cls = List

        return cls.cast()[
            Tuple[
                type(self).value(Dict.PropertyNames, default=object),
                type(self).value(Dict.AdditionalProperties, default=object),
            ]
        ](dict.items(self))

    def values(self, cls=True):
        from .objects import Dict

        if not cls:
            return dict.values(self)
        if cls is True:
            from .arrays import List as cls

        return cls.cast()[type(self).value(Dict.Properties)](dict.values(self))

    def keys(self, cls=EMPTY):
        from .objects import Dict

        if not cls:
            return dict.keys(self)
        if cls is True:
            from .arrays import List as cls

        return cls.cast()[type(self).value(Dict.PropertyNames)](dict.keys(self))

    def map(self, *input, args=EMPTY, kwargs=EMPTY):
        if len(input) is 0:
            return self
        if len(input) is 1:
            return self.valmap(*input, *(args or ()), **(kwargs or {}))
        if len(input) is 2:
            return self.itemmap(*input, *(args or ()), **(kwargs or {}))
        raise BaseException("at most 2 position arguments allowed")

    def filter(self, *input, args=EMPTY, kwargs=EMPTY):
        if len(input) is 0:
            return self
        if len(input) is 1:
            return self.valfilter(*input, *(args or ()), **(kwargs or {}))
        if len(input) is 2:
            return self.itemfilter(*input, *(args or ()), **(kwargs or {}))
        raise BaseException("at most 2 position arguments allowed")

    def valmap(self, callable=EMPTY, *args, **kwargs):
        if callable:
            from .types import MetaType

            cls = type(self)
            if isinstance(cls, MetaType) and isinstance(callable, MetaType):
                cls += callable
            self = cls({k: callable(v, *args, **kwargs) for k, v in self.items()})
        return self

    def itemmap(self, key=EMPTY, value=EMPTY, *args, **kwargs):
        if key or value:
            from .types import MetaType

            cls = type(self)
            if isinstance(cls, MetaType) and isinstance(callable, MetaType):
                cls += callable
            self = cls(
                {
                    key(k, *args, **kwargs)
                    if key
                    else k: value(v, *args, **kwargs)
                    if value
                    else v
                    for k, v in self.items()
                }
            )
        return self

    def keymap(self, callable=EMPTY, *args, **kwargs):
        if callable:
            from .types import MetaType

            cls = type(self)
            if isinstance(cls, MetaType) and isinstance(callable, MetaType):
                cls += callable
            self = cls({k: callable(v, *args, **kwargs) for k, v in self.items()})
        return self

    def valfilter(self, callable=EMPTY, *args, **kwargs):
        if callable:
            cls = type(self)
            self = cls({k: v for k, v in self.items() if callable(v, *args, **kwargs)})
        return self

    def keyfilter(self, callable=EMPTY, *args, **kwargs):
        if callable:
            cls = type(self)
            self = cls({k: v for k, v in self.items() if callable(k, *args, **kwargs)})
        return self

    def itemfilter(self, key=EMPTY, value=EMPTY, *args, **kwargs):

        if key or value:
            cls = type(self)
            self = cls(
                {
                    k: v
                    for k, v in self.items()
                    if (key(k) if k else True)
                    and (value(v, *args, **kwargs) if v else True)
                }
            )
        return self


class Statistics:
    pass


class Gather:
    async def _gather(self):
        import asyncio

        import httpx

        from .arrays import List

        async with httpx.AsyncClient() as client:
            return List(await asyncio.gather(*self.map(client.get)))

    def gather(self):
        try:
            import asyncio

            return asyncio.run(self._gather())
        except RuntimeError:
            import nest_asyncio

            nest_asyncio.apply()
            return asyncio.run(self._gather())


class Meaning:
    pass
