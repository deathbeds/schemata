import enum
import typing

from numpy.lib.arraysetops import isin

import schemata
from schemata.numbers import MultipleOf

from . import exceptions, mixins, utils
from .strings import Uri
from .types import EMPTY, Any, Schemata, Type

__all__ = "List", "Tuple", "Set", "Arrays"


validates = utils.validates(list, tuple, set)


class Arrays(mixins.Array):
    def __class_getitem__(cls, object):
        """
        >>> List[1:10:schemata.String].schema(1)
        {'type': 'array', 'minItems': 1, 'maxItems': 10, 'items': {'type': 'string'}}

        >>> List[schemata.String].schema(1)
        {'type': 'array', 'items': {'type': 'string'}}

        >>> List[dict(a=Integer)].schema(1)
        {'type': 'array', 'items': {'type': 'object', 'properties': {'a': {'type': 'integer'}}}}

        >>> List[Integer, String].schema(1)
        {'type': 'array', 'items': ({'type': 'integer'}, {'type': 'string', 'examples': ('abc', '123'), 'description': 'string types'})}

        >>> List[10].schema()
        {'type': 'array', 'minItems': 10, 'maxItems': 10}
        """
        from . import builders

        return cls + builders.InstanceBuilder(**build_list(object)).build()


class Items(Any):
    @validates
    def validator(cls, object):
        value = Schemata.value(cls, Items)
        if isinstance(value, (tuple, list)):
            for i, (x, y) in enumerate(zip(value, object)):
                exceptions.ValidationException(type=x, schema=i, path=i).validate(y)
        else:
            for i, x in enumerate(object):
                exceptions.ValidationException(type=value, path=i).validate(x)


class AdditionalItems(Any):
    pass


class MinItems(Any):
    @validates
    def validator(cls, object):
        exceptions.assertGreaterEqual(len(object), Schemata.value(cls, MinItems))


class MaxItems(Any):
    @validates
    def validator(cls, object):
        exceptions.assertLessEqual(len(object), Schemata.value(cls, MaxItems))


class UniqueItems(Any):
    @validates
    def validator(cls, object):
        assert len(set(object)) == len(
            object
        ), f"the items of the object are not unique"


class Contains(Any):
    pass


class List(Arrays, Type["array"], list):
    pass


class Tuple(Arrays, Type["array"], tuple):
    pass


class Set(Arrays, Type["array"], set):
    pass


utils.JSONSCHEMA_SCHEMATA_MAPPING["array"] = List


@utils.register
def build_list(x: type):
    return dict(items=x)


@build_list.register(int)
@build_list.register(float)
def build_list_numeric(x):
    return dict(minItems=x, maxItems=x)


@build_list.register
def build_list_tuple(x: tuple, **schema):
    last = schema
    for i, y in enumerate(x):
        if isinstance(y, type):
            last.setdefault("items", [])
            last["items"].append(y)
            continue
        items = build_list(y)
        last.update(items)
        last.setdefault("items", {})
        last = last["items"]
    return schema


@build_list.register
def build_list_dict(x: dict):
    return dict(items=dict(properties=x))


@build_list.register
def build_list_slice(x: slice, **schema):
    if x.start is not None:
        schema["minItems"] = x.start
    if x.stop is not None:
        schema["maxItems"] = x.stop
    if x.step is not None:
        schema["items"] = isinstance(x.step, Schemata) and x.step or Type[x.step]
    return schema


class ListofUri(List[Uri]):
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
