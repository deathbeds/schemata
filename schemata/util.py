"""Utility functions for schemata."""

import frozendict
import inspect
import typing


def get_annotations(object: typing.Union[type, object]) -> typing.Dict:
    """Get the annotations from an object."""
    return getattr(object, "__annotations__", {})


def freeze(object: typing.Union[type, object]) -> typing.Hashable:
    """Freeze a nested mutable object into something hashable."""
    if isinstance(object, list):
        return tuple(map(freeze, object))
    if isinstance(object, dict):
        return frozendict.frozendict({k: freeze(v) for k, v in object.items()})
    return object


def unfreeze(object: typing.Union[type, object]) -> typing.Hashable:
    """Unfreeze an immutable object into something not hashable."""
    if isinstance(object, tuple):
        return list(map(unfreeze, object))
    if isinstance(object, frozendict.frozendict):
        return dict({k: unfreeze(v) for k, v in object.items()})
    return object


def merge_annotations(cls: type) -> type(None):
    """Merge annotations from an mro."""
    cls.__annotations__ = get_annotations(cls)
    for subclass in reversed(inspect.getmro(cls)):
        for k, v in unfreeze(get_annotations(subclass)).items():
            if isinstance(v, dict):
                cls.__annotations__[k] = cls.__annotations__.get(k, {})
                cls.__annotations__[k].update(v)
            elif isinstance(v, (list, tuple)):
                if k in cls.__annotations__ and cls.__annotations__[k] != v:
                    cls.__annotations__[k] = cls.__annotations__.get(k, type(v)())
                    cls.__annotations__[k] += v
            elif (
                isinstance(v, type)
                or type(v) is typing._GenericAlias
                and v.__origin__ is typing.Union
            ):
                if k in cls.__annotations__:
                    cls.__annotations__[k] = typing.Union[cls.__annotations__[k], v]
                else:
                    cls.__annotations__[k] = v
            elif not isinstance(cls.__annotations__, frozendict.frozendict):
                cls.__annotations__[k] = v

    cls.__annotations__ = freeze(cls.__annotations__)


def schema_from_annotations(annotation) -> typing.Dict[typing.AnyStr, typing.Any]:
    """Construct a schema from python annotations."""

    if isinstance(annotation, typing._GenericAlias):
        if annotation.__origin__ is typing.Union:
            annotation = annotation.__args__
    if isinstance(annotation, (dict, frozendict.frozendict)):
        return {k: schema_from_annotations(v) for k, v in annotation.items()}
    if isinstance(annotation, (tuple, list)):
        return list(map(schema_from_annotations, annotation))
    if isinstance(annotation, type):
        return getattr(annotation, "__schema__", {})
    return annotation

