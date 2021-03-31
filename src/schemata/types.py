import functools
import mimetypes
import os
import sys
import typing

from . import base, exceptions, util


# the Literal is the bridge between actual python types and base.Generic types, they emit concrete
# implementations of python types like int, float, list, dict with they advantage that they may be described
# in rdf notation.
class Literal(base.Literals, base.Type):
    def type(cls, *x):
        if x:
            return cls.default(*x)
        return cls

    @classmethod
    def pytype(cls, *args):
        if args:
            m = {str: String, float: Number, int: Integer, list: List, dict: Dict}
            t = type(*args)
            if t in m:
                return m[t]
            return t
        return super().pytype()


class Null(Literal, base.Type["null"]):
    pass


Null.register(type(None))


class Bool(Literal, base.Type["boolean"]):
    pass


Bool.register(bool)


class String(base.Strings, Literal, base.Type["string"]):
    def loads(self):
        return self


class Number(base.Numbers, Literal, base.Type["number"]):
    pass


Float = Number


class Integer(base.Numbers, Literal, base.Type["integer"]):
    pass


class List(base.Lists, Literal, base.Type["array"]):
    def object(cls, *args):
        if args:
            if isinstance(*args, (set, tuple)):
                args = (list(*args),)
        return cls.validate(super().object(*args))

    def type(cls, x):
        return cls + cls.Items[x]

    # fluent list api
    def append(self, object):
        return self.extend((object,))

    def extend(self, args=None):
        self + (args or [])
        list.extend(self, args or [])
        return self

    def insert(self, id, value):
        if id < 0:
            id += len(self)

        self.validate(self[:id] + [value] + self[id:])
        list.insert(self, id, value)

        return self

    def pop(self, id=-1):
        if id == -1:
            id = len(self) - 1
        self.validate(self[:id] + self[id + 1 :])
        return list.pop(self, id)

    def remove(self, value):
        self.pop(self.index(value))
        return self

    def __setitem__(self, key, value):
        if isinstance(key, int):
            if key < 0:
                key += len(self)
        if isinstance(key, slice):
            x = list(self)
            x[key] = value
            self.validate(x)
        else:
            self.validate(self[: key - 1] + [value] + self[key + 1 :])
        return list.__setitem__(self, key, value)

    __iadd__ = extend

    def __add__(self, object):
        if isinstance(object, tuple):
            object = list(object)
        return type(self)(list.__add__(self, object))

    def __delitem__(self, x):
        return self.pop(x)


class Tuple(List, base.Title["Tuple"]):
    pass


Tuple.register(tuple)


class Environ(base.Plural):
    def type(cls, *args):
        if not args:
            return cls
        x, *_ = args
        if isinstance(x, tuple):
            if len(x) == 2:
                if not x[0] in os.environ:
                    os.environ[x[0]] = x[1]
        return super().type(*args)

    def object(cls):
        return os.getenv(*cls.Environ.form(cls)[:1])


class Py(base.Sys):
    def validate(cls, *args):
        if isinstance(*args, cls.pytype()):
            return args
        raise exceptions.ValidationError(f"{args} is not an object of {cls}")


class Instance(Py):
    @classmethod
    def object(cls, *args, **kwargs):
        """kind of like a functor."""
        # call callables, basically making this a functor
        return util.call(
            super().object(),
            *(cls.Args.form(cls) or ()),
            *args,
            **{**(cls.Kwargs.form(cls) or {}), **kwargs},
        )


class Pipe(Instance):
    def object(cls, *args, **kwargs):
        for f in cls.AtType.form(cls):
            args, kwargs = (util.call(f, *args, **kwargs),), {}
        return args[0]


class Star(Pipe):
    def object(cls, *args, **kwargs):
        return super().object(**dict(*args, **kwargs))


class Do(Pipe):
    # so many schema have a thing, this is ours
    def object(cls, *args, **kwargs):
        super().object(*args, **kwargs)
        return (args + (None,))[0]


class Juxt(Instance):
    def type(cls, object):
        if isinstance(object, slice):
            object = slice(
                object.start and Juxt[object.start],
                object.stop and Juxt[object.stop],
                object.step and Juxt[object.step],
            )

        if callable(object):
            return object
        elif isinstance(object, str):
            pass
        elif not isinstance(object, str) and isinstance(
            object, (typing.Sequence, typing.Set)
        ):
            return super().type((type(object), *map(Juxt.type, object)))

        elif isinstance(object, typing.Container):
            # convert dictionary containers to key, value pairs
            return super().type(
                (
                    type(object),
                    *tuple(
                        Juxt.type((isinstance(k, str) and k.format or k, v))
                        for k, v in object.items()
                    ),
                )
            )
        return Instance[object]

    def object(cls, *args, **kwargs):
        t, *v = cls.AtType.form(cls)
        return t(util.call(x, *args, **kwargs) for x in v)


class Dict(base.Dicts, Literal, base.Type["object"]):
    def __setitem__(self, k, v):
        self.update({k: v})

    def update(self, *args, **kwargs):
        kwargs = dict(*args, **kwargs)
        r = type(self).Required.form(self) or ()
        x = self.force_update(type(self).object(**{**self, **kwargs}))
        with util.suppress(AttributeError):
            x._update_display()

        return x

    def force_update(self, *args, **kwargs):
        dict.update(self, dict(*args, **kwargs))
        return self

    def pop(self, key, default=None):
        try:
            v = self[key]
        except KeyError:
            return default
        self.validate({k: v for k, v in self.items() if k != key})
        try:
            return dict.pop(self, key, default)
        finally:
            with util.suppress(AttributeError):
                self._update_display()

    @classmethod
    def object(cls, *args, **kwargs):
        if not args or kwargs:
            if issubclass(cls, cls.Default):
                return super().object()
        if not all(isinstance(x, dict) for x in args):
            raise exceptions.ValidationError
        kwargs = super().object(dict(*args, **kwargs))
        p, d, r = (
            cls.Properties.form(cls),
            dict(cls.Dependencies.form(cls)),
            cls.Required.form(cls),
        )
        for k, v in p.items():
            if k in d:
                continue

            if k not in kwargs and issubclass(v, cls.Default):
                kwargs.force_update({k: cls.Default.form(v)})

        while d:
            for x in list(d):
                if all(x in kwargs for x in d[x]):
                    v = cls.Default.form(cls.Properties.form(cls)[x])

                    kwargs.force_update({x: v(kwargs)})
                    d.pop(x)
                    break
            else:
                break

        return cls.validate(kwargs)

    @classmethod
    def validate(cls, *args):
        if args:
            args = (base.Type.validate.__func__(cls, *args),)
        k = cls.Keys.form(cls)
        if args and k:
            for x in list(*args):
                if not isinstance(x, k):
                    raise exceptions.ValidationError(f"not all keys are objects of {k}")
        return args[0] if args else dict()

    @classmethod
    def type(cls, *args):
        if not args:
            return cls
        x, *_ = args
        if isinstance(x, dict):
            return cls.properties(x)
        if isinstance(x, tuple):
            if len(x) <= 2:
                cls = cls + cls.Keys[x[0]]

            if len(x) == 2:
                cls = cls.additionalProperties(x)

            return cls
        return cls.additionalProperties(x)


class Uri(String, String.Format["uri"]):
    def get(self, *args, **kwargs):
        return __import__("requests").get(self, *args, **kwargs)


class Dir(Literal, util.Path):
    def object(cls, *args):
        return util.Path.__new__(util.Path(*args).is_file() and File or Dir, *args)


class Glob:
    pass


class File(Dir):
    def object(cls, *args):
        return util.Path.__new__(File, *args)

    def mimetype(self):
        t, _ = mimetypes.guess_type("*" + self.suffix)
        return t

    def read(self):
        if isinstance(self, str):
            self = File(self)
        t = self.mimetype()
        if t:
            for cls in base.Generic.String.__subclasses__():
                if base.Generic.ContentMediaType.form(cls) == t:
                    return cls(self.read_text())

        return self.read_text()


class Enum(base.Form.Plural, Literal):
    def object(cls, *args, **kwargs):
        # self.value = cls.validate(self)
        # cls._attach_parent(self)
        enum = Enum.form(cls)
        self = cls.validate(Literal(args[0] if args else enum[0]))
        if len(enum) is 1 and isinstance(*enum, dict):
            return enum[0].get(self)
        return self

    @classmethod
    def choices(cls):
        e = Enum.form(cls)
        if len(e) is 1 and isinstance(e[0], dict):
            # Enum is defined as a plural form
            return tuple(*e)
        return e


Enum.register(__import__("enum").Enum)


class Cycler(Enum):
    @classmethod
    def form(cls, *args):
        if args:
            return cls.Enum.form(*args)
        return cls.Enum.form()

    def object(cls):
        return __import__("itertools").cycle(cls.choices())


class Composite(base.Type):
    """a schemaless form type mixin, the name of the class is used to derive others"""

    def validate(cls, object):
        # composites use the object creation for typing checking
        return cls.object(object)

    @classmethod
    def object(cls, *args):
        if not args:
            with util.suppress(AttributeError):
                args = (super().object(),)
        return args


class AnyOf(base.Form.Nested, Composite):
    def object(cls, *args):
        args = super().object(*args)
        ts = AnyOf.form(cls)
        for t in ts:
            try:
                x = util.call(t, *args)
                return cls._attach_parent(x)
            except exceptions.ValidationErrors + (ValueError,):
                if t is ts[-1]:
                    raise exceptions.ValidationError()


class AllOf(base.Form.Nested, Composite):
    def object(cls, *args):
        args = super().object(*args)
        result = {}
        for t in AllOf.form(cls):
            result.setdefault("x", util.call(t, *args))

        x = result.get("x", args[0])

        return cls._attach_parent(x)


class OneOf(base.Form.Nested, Composite):
    def object(cls, *args, **kwargs):
        args = super().object(*args)
        i, x = 0, None
        for t in OneOf.form(cls):
            try:
                if i:
                    util.call(t, *args, **kwargs)
                else:
                    x = util.call(t, *args, **kwargs)

                i += 1
            except exceptions.ValidationErrors as e:
                continue
            if i > 1:
                break

        if i == 1:
            return cls._attach_parent(x)

        raise exceptions.ValidationError()


class Not(Composite):
    def object(cls, *args):
        try:
            cls.form(cls)(*args)
        except exceptions.ValidationErrors:
            x, *_ = args

            return cls._attach_parent(x)
        raise exceptions.ValidationError


class Else(base.Form):
    pass


class Then(base.Form):
    pass


class If(base.Form):
    def object(cls, *args):
        try:
            args = (If.form(cls)(*args),)
            t = Then.form(cls)
            if t:
                return t(*args)
            return args[0]
        except exceptions.ValidationErrors as exc:
            e = Else.form(cls)
            if e:
                return e(*args)

    def type(cls, object):
        if isinstance(object, slice):
            cls = super().type(object.start)
            if object.stop is not None:
                cls = cls + Then[object.stop]
            if object.step is not None:
                cls = cls + Else[object.step]
        return cls


class Json(
    List ^ Dict ^ String ^ Number ^ Bool ^ Null,
    base.Form.ContentMediaType["application/json"],
):
    pass


class Bunch(Dict):
    def __getattribute__(self, k):
        if not k.startswith("_"):
            if base.Form.Properties.form(type(self)):
                try:
                    return dict.__getitem__(self, k)
                except KeyError:
                    pass

        return object.__getattribute__(self, k)

    def __setattr__(self, k, v):
        if not k.startswith("_"):
            if base.Generic.Properties.form(type(self)):
                self[k] = v
                return

        return object.__setattr__(self, k, v)


class Set(List, base.Form.Title["Set"], base.Form.UniqueItems[True]):
    pass


Set.register(set)
