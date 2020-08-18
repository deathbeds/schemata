import schemata.core, abc

import typing


class Forward(abc.ABCMeta):
    def __new__(cls, name, bases, kwargs):
        return super().__new__(
            cls, name, bases, dict(__forward_reference__=typing.ForwardRef(name))
        )

    def eval(cls):
        if not cls.__forward_reference__.__forward_evaluated__:
            try:
                cls.__forward_reference__._evaluate(
                    __import__("sys").modules, __import__("sys").modules
                )
            except:
                ...
        return cls.__forward_reference__.__forward_value__

    def __getitem__(cls, object):
        return type(
            object, (py,), dict(__forward_reference__=typing.ForwardRef(object))
        )

    def __getstate__(self):
        return (self.__forward_reference__,)

    def __setstate__(self, forward_reference):
        self.__forward_reference__ = forward_reference

    def __hash__(self):
        return hash(self.__getstate__())

    def __eq__(cls, object):
        return cls.eval() == object

    def __instancecheck__(cls, object):
        cls = cls.eval()
        if isinstance(cls, (type, tuple)):
            return isinstance(object, cls)
        return False

    def __subclasscheck__(cls, object):
        cls = cls.eval()
        if isinstance(cls, (type, tuple)):
            return issubclass(object, cls)
        return False


class py(metaclass=Forward):
    def __new__(cls, *args, **kwargs):
        return cls.eval()(*args, **kwargs)
