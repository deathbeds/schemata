from . import strings, utils
from .types import EMPTY, Any, Type

__all__ = ("E",)


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
