from abc import ABC, ABCMeta
from collections import UserList, UserDict, UserString
from weakref import WeakValueDictionary


class meta_types(ABCMeta):
    __types__ = WeakValueDictionary()

    def __new__(cls, name, bases, dict):
        meta_types.__types__[name] = super().__new__(cls, name, bases, dict)
        return meta_types.__types__[name]

    def register(cls, *args):
        for arg in args:
            super().register(arg)
            meta_types.__types__[arg] = cls


class types:
    class null(metaclass=meta_types):
        pass

    null.register(type(None))

    class boolean(metaclass=meta_types):
        pass

    boolean.register(bool)

    class integer(metaclass=meta_types):
        pass

    integer.register(int)

    class number(metaclass=meta_types):
        pass

    number.register(float)

    class string(metaclass=meta_types):
        pass

    string.register(str, UserString)

    class array(metaclass=meta_types):
        pass

    array.register(list, tuple, set, UserList)

    class object(metaclass=meta_types):
        pass

    object.register(dict, UserDict)
