from . import formats, strings, utils, times
from .strings import String
from .types import EMPTY, Any, Type

__all__ = (
    "E",
    "F",
    "Jinja",
    "UriTemplate",
)


class Template:
    def __class_getitem__(cls, object):
        return Any.__class_getitem__.__func__(cls, object)

    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, cls.render(*args, **kwargs))


class StringTemplate(Template, String):
    pass


class F(StringTemplate):
    @classmethod
    def render(cls, *args, **kwargs):
        return cls.value(F).format(*args, **kwargs)


class Jinja(StringTemplate):
    @classmethod
    def render(cls, *args, **kwargs):
        import jinja2

        return jinja2.Template(cls.value(Jinja)).render(*args, **kwargs)

    @classmethod
    def input(cls):
        import jinja2.meta

        from . import Any, Dict

        return Dict.properties(
            {
                x: Any
                for x in jinja2.meta.find_undeclared_variables(
                    jinja2.Environment().parse(cls.value(Jinja))
                )
            }
        )


class UriTemplate(formats.UriTemplate, String):
    def render(self, *args, **kw):
        import uritemplate

        template = uritemplate.URITemplate(self)
        return Uri(template.expand(dict(zip(template.variable_names, args)), **kw))


class E:
    @classmethod
    def render(cls, object=EMPTY):
        import jsone

        return jsone.render(
            cls.value(Template).schema(), utils.get_default(cls, object, {})
        )

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
