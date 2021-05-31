import typing

from . import apis, exceptions, utils
from .strings import Uri
from .types import EMPTY, JSONSCHEMA_SCHEMATA_MAPPING, Any, Type

__all__ = "List", "Tuple", "Set", "Arrays"


class Arrays(apis.FluentArrays):

    def __new__(cls, *args):
        from . import callables
        type = cls.mro()[-2]
        if not args:
            args = utils.enforce_tuple(utils.get_default(cls, list()))

        cast = cls.value(callables.Cast)
        if cast:
            args, kwargs = utils.enforce_tuple((list if cast is True else cast)(*args)), {}

        else:
            cls.validate(*args)
        self = type.__new__(cls, *args)
        self.__init__(*args)
        if cast:
            cls.validate(self)
        return self
            
    def __class_getitem__(cls, object):
        from .builders import build_list

        if isinstance(object, tuple):
            return Tuple.items(object)
        return cls.add(*utils.enforce_tuple(build_list(object)))


    class Items(Any, id="applicator:/properties/items"):
        @utils.validates(list, tuple, set)
        def validator(cls, object):
            value = cls.value(Arrays.Items)
            if value:
                if isinstance(value, (tuple, list)):
                    for i, (x, y) in enumerate(zip(value, object)):
                        x.validate(y)
                    other = cls.value(Arrays.AdditionalItems)
                    if other:
                        for x in other[i:]:
                            other.validate(x)
                else:
                    for i, x in enumerate(object):
                        value.validate(x)

    class AdditionalItems(Any, id="applicator:/properties/additionalItems"):
        pass

    class MinItems(Any, id="validation:/properties/minItems"):
        @utils.validates(list, tuple, set)
        def validator(cls, object):
            exceptions.assertGreaterEqual(len(object), cls.value(Arrays.MinItems))

    class MaxItems(Any, id="validation:/properties/maxItems"):
        @utils.validates(list, tuple, set)
        def validator(cls, object):
            exceptions.assertLessEqual(len(object), cls.value(Arrays.MaxItems))

    class UniqueItems(Any, id="validation:/properties/uniqueItems"):
        @utils.validates(list, tuple, set)
        def validator(cls, object):
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
        cls = cls + Arrays.Sorted[key or True]
        if reverse is not EMPTY:
            cls = cls + Arrays.Reversed[reverse]
        return cls


class List(Arrays, Type["array"], list):
    

    def __init__(self, *args):
        args and list.__init__(self, *args)
    #     cls = type(self)

    #     sorted = cls.value(Arrays.Sorted)
    #     if sorted is not EMPTY:
    #         reversed = cls.value(Arrays.Reversed)
    #         kw = {}
    #         if reversed is not EMPTY:
    #             kw.update(reverse=reversed)

    #         if not isinstance(sorted, bool):
    #             kw.update(key=sorted)
    #         list.sort(self, **kw)

    @classmethod
    def validator(cls, object):
        exceptions.assertIsInstance(object, (tuple, list, set))

    @classmethod
    def py(cls, ravel=True):
        value = cls.value(List.Items)
        if value:
            return typing.List[value]
        return list


class ListofUri(List[Uri], apis.Gather):
    pass


class Tuple(Arrays, Type["array"], tuple):
    @classmethod
    def validator(cls, object):
        exceptions.assertIsInstance(object, tuple)

    @classmethod
    def py(cls, ravel=True):
        from . import builders, utils

        value = cls.value(Arrays.Items)
        if value:
            return typing.Tuple[tuple(map(utils.get_py, value))]
        return tuple


class Set(Arrays, Type["array"], set):
    def __init__(self, *args):
        args and set.__init__(self, *args)

    @classmethod
    def validator(cls, object):
        exceptions.assertIsInstance(object, set)

    @classmethod
    def py(cls, ravel=True):

        value = cls.value(List.Items)
        if value:
            return typing.Set[value]
        return set


JSONSCHEMA_SCHEMATA_MAPPING["array"] = List
