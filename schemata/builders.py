import collections
import enum
import inspect, types
from schemata.types import Schemata

from numpy.lib.arraysetops import isin
from typing import Dict

from . import exceptions, utils


class Builder:
    priority = ["type", "required", "title", "description"]

    def __init__(self, schema=None, **kwargs):
        schema = schema or {}
        self.object = schema
        if isinstance(self.object, type):
            schema = self.object.schema()

        elif not isinstance(schema, dict):
            schema = {}
        self.schema = dict(utils.merge(kwargs, schema))
        super(Builder, type(self)).__init__(self)

    def post(self):
        return self

    def build(self):
        self.visit()
        return self.post()


class DictVisitor:
    def visit(self):
        # visit know things first and generic later
        defer, self.nah = [], []
        priority = self.priority or ()
        has_generic = hasattr(self, "generic")
        for k in sorted(self.schema, key=(priority + list(self.schema)).index):
            munge = k.replace(":", "_")
            if munge.startswith("$"):
                munge = munge[1:] + "_"
            munge = utils.uppercase(munge)
            if hasattr(self, munge) and callable(getattr(self, munge)):
                getattr(self, munge)(k, self.schema[k])
            elif has_generic and k in priority:
                self.generic(k, self.schema[k])
            elif has_generic:
                defer.append(k)
            else:
                self.nah.append(k)

        for k in defer:
            self.generic(k, self.schema[k])
        return self


class SignatureVisitor:
    def visit(self):
        sig = inspect.signature(self.object)
        for key, value in inspect._ParameterKind.__members__.items():
            if hasattr(self, key):
                for id, parameter in enumerate(sig.parameters.values()):
                    if parameter.kind == value:
                        getattr(self, key)(parameter, id)
        return self


class NsVisitor:
    def visit(self):
        for k, v in self.object.items():
            self.generic(k, v)

        return self


class DictBuilder(Builder, collections.UserDict):
    def __init__(self, *args, **kwargs):
        Builder.__init__(self, *args, **kwargs)
        self.update({k: v() for k, v in getattr(self, "__annotations__", {}).items()})

    def one_for_one(self, key, value):
        self[key] = value


class ListBuilder(Builder, collections.UserList):
    pass


class SignatureBuilder(DictBuilder, SignatureVisitor):
    required: tuple
    properties: dict
    additionalProperties: type(None)

    def POSITIONAL_ONLY(self, param, id):
        pass

    def POSITIONAL_OR_KEYWORD(self, param, id):
        self["required"] += (param.name,)
        self.KEYWORD_ONLY(param, id)

    def VAR_POSITIONAL(self, param, id):
        pass

    def KEYWORD_ONLY(self, param, id):
        if param.annotation is not inspect._empty:
            self["properties"][param.name] = param.annotation

    def VAR_KEYWORD(self, param, id):
        self["additionalProperties"] = (
            True if param.annotation is inspect._empty else param.annotation
        )

    def post(self):
        return InstanceBuilder(self.data).build()

    @classmethod
    def from_signature(cls, object):
        return SignatureBuilder(object).build()


class TypeSignatureBuilder(SignatureBuilder):
    required: tuple
    properties: dict
    additionalProperties: type(None)

    def RETURN(self, value):
        if value is not inspect._empty:
            self["properties"][self.object.__name__] = value

    def POSITIONAL_OR_KEYWORD(self, param, id):
        if not id:
            if param.annotation is inspect._empty:
                assert False, f"cannot type {self.object}"
            if isinstance(param.annotation, str):
                self["required"] += tuple(param.annotation.split())
            elif isinstance(param.annotation, (list, set, tuple)):
                self["required"] += tuple(param.annotation)
        else:
            super().POSITIONAL_OR_KEYWORD(param, id)

    def post(self):
        name = self.object.__name__
        for k in "properties required".split():
            self[k] or self.pop(k)

        if self["additionalProperties"] is None:
            self.pop("additionalProperties")

        if self.data:
            self.data = dict(dependencies={name: self.data})

        anno = inspect.signature(self.object).return_annotation
        if anno is not inspect._empty:
            self.data["properties"] = {name: anno}

        doc = inspect.getdoc(self.object)
        if doc and isinstance(doc, str):
            from . import Schemata

            self.data["properties"][name] += Schemata.cls("description", doc)

        return self.data


class NsBuilder(DictBuilder, NsVisitor):
    dependencies: dict
    properties: dict
    definitions: dict

    def generic(self, key, value):
        from . import Any

        if key == "__doc__":
            if value and isinstance(value, str):
                self["description"] = value

        elif key == "__annotations__":
            while value:
                self["properties"].update([value.popitem()])
        elif isinstance(value, type(Any)):

            self["definitions"][key] = value

        elif callable(value):
            try:
                self.data = utils.merge(self.data, TypeSignatureBuilder(value).build())
            except AssertionError:
                pass

    def post(self):
        return InstanceBuilder({k: v for k, v in self.items() if v}).build()

    @classmethod
    def from_cls(cls, object, **kwargs):
        return NsBuilder(object).build()


class InstanceBuilder(ListBuilder, DictVisitor):
    def generic(self, key, value):
        from . import Schemata

        if isinstance(value, dict):
            value = {k: InstanceBuilder(v).build() for k, v in value.items()}

        self.data.append(Schemata.cls(key, value))

    def post(self):
        if not self.data:
            return type
        if len(self) == 1:
            return self.data[0]

        cls = type(self.schema.get("title", "DerivedType"), tuple(self.data), {})
        defs = Schemata.value(cls, "definitions")
        if defs:
            for k, v in defs.items():
                setattr(cls, k, v)
        return cls

    @classmethod
    def from_schema(cls, object, **kwargs):
        return InstanceBuilder(object, **kwargs).build()


DOCTEXT = """>>> {type}({object})
{out}
"""

SECTION = """{key}
{sep}
{body}"""

NOT = """>>> exceptions.assertRaises({type}, {object})
"""


class NumPyDoc(DictBuilder, DictVisitor):
    __annotations__ = {"": list}
    Arguments: list
    Attention: list
    Attributes: list
    Caution: list
    Danger: list
    Error: list
    Example: list
    Examples: list
    Methods: list
    Notes: list
    Returns: list
    References: list
    Tip: list
    Todo: list
    __annotations__.update({"Keyword Arguments": list, "See Also": list})

    def Description(self, key, value):
        self[""].append(value)

    def Examples(self, key, value):
        self["Examples"].extend(
            DOCTEXT.format(
                type=self._type.__name__,
                object=repr(x),
                out="" if x is None else repr(x),
            )
            for x in value
        )

    def Comment_(self, key, value):
        self["Notes"].append(
            "".join(x.lstrip("#").lstrip() for x in value.splitlines(True))
        )

    def Not_(self, key, value):
        from . import Any, Schemata

        if isinstance(value, Schemata):
            value = value.schema()

        for example in value.get("examples", ()):
            self.data["Examples"].append(
                NOT.format(type=self._type.__name__, object=repr(example))
            )

    locals()["not"] = Not_

    def post(self):
        return "\n\n".join(
            SECTION.format(key=k, sep="-" * len(k), body="\n".join(v))
            for k, v in self.data.items()
            if v
        ).lstrip()


class SignatureExporter(DictBuilder, DictVisitor):
    args: dict
    kwargs: dict
    additionalProperties: bool

    def Required(self, key, value):
        properties = self.schema.get("properties", {})
        for x in value:
            if x in properties:
                self.data["args"][x] = properties[x]
            else:
                self.data["args"][x] = None

    def Properties(self, key, value):
        for k, v in value.items():
            if k not in self.data["args"]:
                self.data["kwargs"][k] = v

    def AdditionalProperties(self, key, value):
        self.data["additionalProperties"] = value

    def post(self):
        from . import Any, Schemata

        parameters = [
            inspect.Parameter(
                k,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=v
                and Schemata.value(v, Any.Default, default=None)
                or inspect._empty,
                annotation=v or inspect._empty,
            )
            for k, v in self.data["args"].items()
        ]
        parameters += [
            inspect.Parameter(
                k,
                inspect.Parameter.KEYWORD_ONLY,
                default=v
                and Schemata.value(v, Any.Default, default=None)
                or inspect._empty,
                annotation=v or inspect._empty,
            )
            for k, v in self.data["kwargs"].items()
        ]
        if self.data["additionalProperties"] != False:
            parameters.append(
                inspect.Parameter(
                    "kwargs",
                    inspect.Parameter.VAR_KEYWORD,
                    annotation=True
                    if self.data["additionalProperties"] in (None, True)
                    else self.data["additionalProperties"],
                )
            )
        if parameters:
            return inspect.Signature(parameters)
        return inspect.signature(utils.get_first_builtin_type(self._type))

    @classmethod
    def to_signature(cls, object):
        return SignatureExporter(object).build()


from_schema = InstanceBuilder.from_schema
from_cls = NsBuilder.from_cls
from_signature = SignatureBuilder.from_signature
to_signature = SignatureExporter.to_signature
