import typing

from .strings import String
from .types import (
    EMPTY,
    JSONSCHEMA_SCHEMATA_MAPPING,
    Any,
    Cast,
    Const,
    Default,
    Type,
    Value,
)
from .utils import enforce_tuple, get_default, get_verified_object, testing, validates

__all__ = "List", "Tuple", "Set"


class Sequence:
    def __class_getitem__(cls, object):
        if isinstance(object, dict):
            from .mappings import Dict

            object = Dict + Dict.Properties[object]
        if isinstance(object, tuple):
            return Tuple + Sequence.Items[object]
        return cls + Sequence.Items[object]

    class Items(Any, id="applicator:/properties/items"):
        @validates(list, tuple, set)
        def is_valid(cls, object):
            value = cls.value(Sequence.Items)
            if value:
                if isinstance(value, (tuple, list)):
                    for i, (x, y) in enumerate(zip(value, object)):
                        x.validate(y)
                    other = cls.value(Sequence.AdditionalItems)
                    if other:
                        for x in other[i:]:
                            other.validate(x)
                else:
                    for i, x in enumerate(object):
                        value.validate(x)

        def map(self, callable, *args, **kwargs):
            for cls in type(self).mro():
                if cls in (Tuple, List, Set):
                    cls += Cast
            else:
                cls = List
            if isinstance(callable, type):
                cls += callable
            return cls

    class AdditionalItems(Any, id="applicator:/properties/additionalItems"):
        pass

    class MinItems(Any, id="validation:/properties/minItems"):
        @validates(list, tuple, set)
        def is_valid(cls, object):
            testing.assertGreaterEqual(len(object), cls.value(Sequence.MinItems))

    class MaxItems(Any, id="validation:/properties/maxItems"):
        @validates(list, tuple, set)
        def is_valid(cls, object):
            testing.assertLessEqual(len(object), cls.value(Sequence.MaxItems))

    class UniqueItems(Any, id="validation:/properties/uniqueItems"):
        @validates(list, tuple, set)
        def is_valid(cls, object):
            assert len(set(object)) == len(
                object
            ), f"the items of the object are not unique"

    class Contains(Any):
        pass

    class Sorted(Any):
        pass

    class Reversed(Any):
        pass

    @classmethod
    def sorted(cls, key=EMPTY, reverse=EMPTY):
        cls = cls + Sequence.Sorted[key or True]
        if reverse is not EMPTY:
            cls = cls + Sequence.Reversed[reverse]
        return cls


class List(Sequence, Type["array"], list):
    def __init__(self, object=EMPTY):
        cls = type(self)
        object = get_default(cls, object)
        if object is EMPTY:
            super().__init__()
        else:
            super().__init__(object)

        sorted = cls.value(Sequence.Sorted)
        if sorted is not EMPTY:
            reversed = cls.value(Sequence.Reversed)
            kw = {}
            if reversed is not EMPTY:
                kw.update(reverse=reversed)

            if not isinstance(sorted, bool):
                kw.update(key=sorted)
            self.sort(**kw)

    @classmethod
    def is_valid(cls, object):
        testing.assertIsInstance(object, (tuple, list, set))

    @classmethod
    def py(cls, ravel=True):

        value = cls.value(List.Items)
        if value:
            return typing.List[value]
        return list

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
        if isinstance(start, str):
            # usually strings fail to sum on strings.
            return String(start.join(self))
        return sum(self, start)

    def sort(self, inplace=True, key=EMPTY, reverse=EMPTY):
        if inplace:
            self.sort(key=key or None, reverse=key or False)
        return type(cls).verified(
            [sorted(self, key=EMPTY or None, reverse=EMPTY or False)]
        )


class Tuple(Sequence, Type["array"], tuple):
    @classmethod
    def is_valid(cls, object):
        testing.assertIsInstance(object, tuple)

    @classmethod
    def py(cls, ravel=True):

        value = cls.value(List.Items)
        if value:
            return typing.Tuple[value]
        return tuple


class Set(Sequence, Type["array"], set):
    @classmethod
    def is_valid(cls, object):
        testing.assertIsInstance(object, set)

    @classmethod
    def py(cls, ravel=True):

        value = cls.value(List.Items)
        if value:
            return typing.Set[value]
        return set


JSONSCHEMA_SCHEMATA_MAPPING["array"] = List
