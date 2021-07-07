import collections
import inspect

import schemata

from . import exceptions, utils


class Builder:
    priority = ["type", "required", "title", "description"]

    def __init__(self, *schema, **kwargs):

        if len(schema) == 1:
            if isinstance(*schema, type):
                self._type = schema[0]
                schema = self._type.schema()

        self.schema = dict(utils.merge(schema), **kwargs)
        super(Builder, type(self)).__init__(self)

    def post(self):
        return self

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

    def build(self):
        self.visit()
        return self.post()


class DictBuilder(Builder, collections.UserDict):
    def __init__(self, *args, **kwargs):
        Builder.__init__(self, *args, **kwargs)
        self.data.update(
            {k: v() for k, v in getattr(self, "__annotations__", {}).items()}
        )

    def one_for_one(self, key, value):
        self.data[key] = value


class ListBuilder(Builder, collections.UserList):
    pass


class InstanceBuilder(ListBuilder):
    def __init__(self, *args, **kwargs):
        self.mapping = utils.get_prototype_mapping()
        super().__init__(*args, **kwargs)

    def generic(self, key, value):
        if key in self.mapping:
            self.data.append(self.mapping[key][value])

    def post(self):
        return type(self.schema.get("title", "DerivedType"), tuple(self.data), {})


DOCTEXT = """>>> {type}({object})
{out}
"""

SECTION = """{key}
{sep}
{body}"""

NOT = """>>> exceptions.assertRaises({type}, {object})
"""


class NumPyDoc(DictBuilder):
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
        self.data[""].append(value)

    def Examples(self, key, value):
        self.data["Examples"].extend(
            DOCTEXT.format(
                type=self._type.__name__,
                object=repr(x),
                out="" if x is None else repr(x),
            )
            for x in value
        )

    def Comment_(self, key, value):
        self.data["Notes"].append(
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


class SignatureBuilder(DictBuilder):
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


def from_signature(callable, **schema):
    from . import Any

    if isinstance(callable, inspect.Signature):
        sig = callable
    else:
        doc = inspect.getdoc(callable)
        if doc:
            schema["description"] = doc
        sig = inspect.signature(callable)

    schema.update(properties={}, required=[], additionalProperties=None)

    for i, p in enumerate(sig.parameters.values()):
        if not i:
            if isinstance(p.annotation, (tuple, list, set)):
                schema["required"].extend(p.annotation)
                continue

        if p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
            schema["required"].append(p.name)
        if p.kind in {
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        }:
            if p.annotation is not inspect._empty:
                schema["properties"][p.name] = p.annotation
            if p.default is not inspect._empty:
                if p.name in schema["properties"]:
                    schema["properties"][p.name] += Any.Default[p.default]
                else:
                    schema["properties"][p.name] = dict(default=p.default)

        elif p.kind == inspect.Parameter.VAR_KEYWORD:
            schema["additionalProperties"] = (
                p.annotation is inspect._empty and True or p.annotation
            )
    if schema["additionalProperties"] is None:
        schema.pop("additionalProperties")

    for k in ("properties", "required"):
        schema[k] or schema.pop(k)
    return InstanceBuilder(schema).build()
