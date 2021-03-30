import functools

from .base import Form, Forward, Generic, Plural, call, lowercased, suppress


class Numeric(Form):
    pass


class Plural(Form):
    def type(cls, object=None, **kwargs):
        if isinstance(object, list):
            object = tuple(object)

        if not isinstance(object, tuple):
            object = (object,)
        if not object:
            if not kwargs:
                return cls

        return super().type(object, **kwargs)

    @classmethod
    def form(cls, *args):  # pragma: no cover
        return super().form(*args) or ()


class Nested(Plural):
    @classmethod
    def type(cls, object):
        x = super().type(object)
        v = ()
        for y in cls.form(x):
            if issubclass(y, cls):
                v += cls.form(y)
            else:
                v += (y,)
        x.__annotations__[cls.form()] = v
        return x


class Mapping(Form):
    def type(cls, object):
        if isinstance(object, type):
            pass
        elif not isinstance(object, dict):
            object = dict(object)
        return super().type(object)

    @classmethod
    def form(cls, *args):  # pragma: no cover
        return super().form(*args) or {}


# json schema formes


class MinLength(Numeric):
    pass


class MaxLength(Numeric):
    pass


class Pattern(Form):
    @classmethod
    def type(cls, *x):
        import re

        return super().type(re.compile(*x))


class Format(Form):
    pass


class MultipleOf(Numeric):
    pass


class Minimum(Numeric):
    pass


class Maximum(Numeric):
    pass


class ExclusiveMaximum(Numeric):
    pass


class ExclusiveMinimum(Numeric):
    pass


class Items(Form):
    pass


class Contains(Form):
    pass


class AdditionalItems(Form):
    pass


class MinItems(Numeric):
    pass


class MaxItems(Numeric):
    pass


class UniqueItems(Form):
    pass


class Properties(Mapping):
    @classmethod
    def ui_schema(cls):
        import collections

        s, u = cls.schema().ravel(), collections.defaultdict(dict)
        for k, v in s["properties"].items():
            for m, n in v.items():
                if m.startswith("ui:"):
                    u[k].update({m: n})

        return u


class AdditionalProperties(Form):
    def __missing__(self, key):
        cls = type(self)
        p = AdditionalProperties.form(cls)
        if p:
            self.update({key: call(p)})
        return self[key]


class Dependencies(Mapping):
    pass


class Required(Plural):
    pass


class PropertyNames(Mapping):
    pass


class MinProperties(Numeric):
    pass


class MaxProperties(Numeric):
    pass


class PatternProperties(Mapping):
    pass


class Keys(Form):
    pass


class ContentMediaType(Form):
    def _repr_mimebundle_(self, *a, **k):
        return {ContentMediaType.form(type(self)): self}, {}

    def __rich__(self):
        t = ContentMediaType.form(type(self))
        if t in {"text/markdown", "text/x-markdown"}:
            import rich.markdown

            return rich.markdown.Markdown(self)
        return self


class Examples(Plural):
    pass


class Title(Form):
    pass


class Description(Form):
    pass


# schemata specific formes


class Optional(Form):
    pass


class FileExtension(Plural):
    pass


class MimeType(Form):
    def __rich__(self):
        import rich.syntax

        return rich.syntax.Syntax(self)

    def __init_subclass__(cls):
        import mimetypes

        t = MimeType.form(cls)
        for e in FileExtension.form(cls) if t else ():
            mimetypes.add_type(t, e)


class Args(Plural):
    pass


class Kwargs(Mapping):
    pass


class AtContext(Mapping):
    pass


class AtVocab(Form):
    pass


class AtBase(Form):
    pass


class AtLanguage(Form):
    pass


class AtId(Form):
    pass


class AtGraph(Plural):
    pass


class Literals(metaclass=Generic):
    def pipe(self, f, *args, **kwargs):
        return call(f, self, *args, **kwargs)


class Strings(Literals):
    def _stringcase(self, key):
        import stringcase

        from .types import String

        return o(getattr(stringcase, key)(self))

    for (
        x
    ) in "alphanumcase backslashcase camelcase capitalcase constcase dotcase lowercase pascalcase pathcase sentencecase snakecase spinalcase titlecase trimcase uppercase".split():
        locals()[x] = functools.partialmethod(_stringcase, x)

    lowercased = lowercased

    del x


class Numbers(Literals):
    pass


class Lists(Literals):
    def map(x, f):
        from .types import List

        cls = type(x)
        if isinstance(f, type):
            return cls[type](list(map(f, x)))
        return cls(list(map(f, x)))

    def filter(x, f):
        from .types import List

        if isinstance(f, type):
            t = List[type]
            next = list.__new__(t)
            list.__init__(next, filter(f, x))
            return next
        return List(list(filter(f, x)))

    def groupby(x, f):
        import itertools

        from .types import Dict

        v = {k: list(v) for k, v in itertools.groupby(x, f)}
        t = Dict[(f, type(x)) if isinstance(f, type) else type(x)]
        return t(v)


class Dicts(Literals):
    def type(cls, x):
        title = Generic.Title[cls.__name__]

        if isinstance(x, dict):
            cls = cls + Generic.Properties[x] + title
        elif isinstance(x, tuple):
            if len(x) == 1 and x[0]:
                cls = cls + Generic.Keys[x[0]]

            elif len(x) == 2:
                cls = cls + Generic.Keys[x[0]] + Generic.AdditionalItems[x[1]]

            else:
                raise TypeError("key value")
        elif isinstance(x, type):
            cls = cls + Generic.AdditionalProperties[x]
        return cls

    def _prepare_type(x, *args):
        from .types import Dict

        if len(args) == 1:
            K, V = None, *args
        elif len(args) == 2:
            K, V = args
        t = Dict
        if K is None:
            if isinstance(V, type):
                t = t[V]
            return t, K, V
        else:
            if isinstance(K, type):
                t = t[(K,) if isinstance(V, type) else (K, V)]
            elif isinstance(V, type):
                t = t[V]

        return t, K, V

    def filter(x, *args):
        t, K, V = x._prepare_type(*args)
        if K is None:
            return t({k: v for k, v in x.items() if V(v)})
        return t({k: v for k, v in x.items() if K(v) and V(v)})

    def map(x, *args):
        t, K, V = x._prepare_type(*args)
        if K is None:
            return t({k: V(v) for k, v in x.items()})
        return t({K(k): V(v) for k, v in x.items() if K(v) and V(v)})
