from schemata.utils import get_default

from .strings import String
from .types import EMPTY, Any, Type

__all__ = "E", "F", "Jinja"


class Template(Type):
    pass


class Templates(Template):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, cls.render(*args, **kwargs))

    def __class_getitem__(cls, object):
        return cls + Template[object]


class F(Templates, String):
    @classmethod
    def render(cls, *args, **kwargs):
        return cls.value(Template).format(*args, **kwargs)


class Jinja(Templates, String):
    @classmethod
    def render(cls, *args, **kwargs):
        import jinja2

        return jinja2.Template(cls.value(Template)).render(*args, **kwargs)

    @classmethod
    def input(cls):
        import jinja2.meta

        from . import Any, Dict

        return Dict.properties(
            {
                x: Any
                for x in jinja2.meta.find_undeclared_variables(
                    jinja2.Environment().parse(cls.value(Template))
                )
            }
        )


class UriTemplate(Templates):
    @classmethod
    def render(cls, **kwargs):
        import uritemplate

        return uritemplate.expand(cls.value(Template), **kwargs)


class E(Templates):
    @classmethod
    def render(cls, object=EMPTY):
        import jsone

        return jsone.render(cls.value(Template).schema(), get_default(cls, object, {}))

    class Eval_(Type):
        pass

    class Json_(Type):
        pass

    class If_(Type):
        pass

    class Then(Type):
        pass

    class Else(Type):
        pass

    class Flatten_(Type):
        pass

    class FlattenDeep_(Type):
        pass

    class FromNow_(Type):
        pass

    class Let_(Type):
        pass

    class Map_(Type):
        pass

    class Match_(Type):
        pass

    class Switch_(Type):
        pass

    class Merge_(Type):
        pass

    class MergeDeep_(Type):
        pass

    class Sort_(Type):
        pass

    class Reverse_(Type):
        pass
