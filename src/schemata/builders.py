from . import arrays, objects, utils
from .types import Any


@utils.register
def build_dict(x: type):
    return objects.Dict.AdditionalProperties[x]


@build_dict.register
def build_list_str(x: str):
    return objects.Dict.Required[tuple(x.split())]


@build_dict.register(int)
@build_dict.register(float)
def build_list_numeric(x):
    return objects.Dict.MinProperties[x] + objects.Dict.MaxProperties[x]


@build_dict.register
def build_dict_tuple(x: tuple):
    for y in x:
        if not isinstance(y, str):
            break
    else:
        return objects.Dict.Required[x]

    if 0 < len(x) < 3:
        for y in x:
            if not isinstance(y, type):
                break
        else:
            cls = objects.Dict.PropertyNames[x[0]]
            if len(x) == 2:
                cls += build_dict(x[1])
            return cls
    raise TypeError(f"dictionaries take at most two properties")


@build_dict.register
def build_dict_dict(x: dict):
    return objects.Dict.Properties[x]


@build_dict.register
def build_dict_slice(x: slice):
    cls = None
    if x.start is not None:
        if not isinstance(x.start, (int, float)):
            raise TypeError("slice expects start and stop to be in numeric")
        t = objects.Dict.MinProperties[x.start]
        cls = cls and cls.add(t) or t
    if x.stop is not None:
        if not isinstance(x.stop, (int, float)):
            raise TypeError("slice expects start and stop to be in numeric")
        t = objects.Dict.MaxProperties[x.stop]
        cls = cls and cls.add(t) or t

    if x.step is not None:
        t = build_dict(x.step)
        cls = cls and cls.add(t) or t
    return cls


from . import objects, utils


@utils.register
def build_list(x: type):
    return arrays.List.Items[x]


@build_list.register(int)
@build_list.register(float)
def build_list_numeric(x):
    return arrays.List.MinItems[x] + arrays.List.MaxItems[x]


@build_list.register
def build_list_tuple(x: tuple):
    cls = None
    for y in reversed(x):
        t = build_list(y)

        if cls:
            cls = cls.add(arrays.List.Items[t])
        else:
            cls = t

    return cls


@build_list.register
def build_list_dict(x: dict):
    return arrays.Arrays.Items[objects.Dict.properties(x)]


@build_list.register
def build_list_slice(x: slice):
    cls = None
    if x.start is not None:
        if not isinstance(x.start, (int, float)):
            raise TypeError("slice expects start and stop to be in numeric")
        t = arrays.List.MinItems[x.start]
        cls = cls and cls.add(t) or t
    if x.stop is not None:
        if isinstance(x.stop, type):
            if x.start is not None:
                if x.step is not None:
                    TypeError("cant create the type")
                return cls + arrays.List.MaxItems[x.start] + x.stop
        t = arrays.List.MaxItems[x.stop]
        cls = cls and cls.add(t) or t

    if x.step is not None:
        t = x.step
        cls = cls and cls.add(t) or t
    return cls
