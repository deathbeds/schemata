import typing

from . import apis, exceptions, utils
from .strings import Uri
from .types import EMPTY, Any, Type

__all__ = "List", "Tuple", "Set", "Arrays"


class Arrays(apis.FluentArrays):
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


class List(Arrays, apis.Meaning, Type["array"], list):
    def __init__(self, *args):
        from . import callables

        cls = type(self)
        if not args:
            args = utils.enforce_tuple(utils.get_default(cls, cls.__mro__[-2]()))

        cast = cls.value(callables.Cast)
        if cast:
            args = (cls.preprocess(*args),)

        sort = cls.value(Arrays.Sorted)

        if sort:
            args = (
                sorted(
                    list(*args),
                    key=callable(sort) and sort or None,
                    reverse=cls.value(Arrays.Reversed, default=False),
                ),
            )

        if not cast:
            cls.validate(*args)

        list.__init__(self, *args)

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
        from . import callables

        cls = type(self)
        if not args:
            args = utils.enforce_tuple(utils.get_default(cls, cls.__mro__[-2]()))

        cast = cls.value(callables.Cast)
        if cast:
            args = (cls.preprocess(*args),)

        if not cast:
            cls.validate(*args)

        super().__init__(*args)

    @classmethod
    def validator(cls, object):
        exceptions.assertIsInstance(object, set)

    @classmethod
    def py(cls, ravel=True):

        value = cls.value(List.Items)
        if value:
            return typing.Set[value]
        return set


utils.JSONSCHEMA_SCHEMATA_MAPPING["array"] = List
