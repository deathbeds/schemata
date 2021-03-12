"""a mapping our types to the builtins. our builtin types provide @type information relative to 
canonical schema like rdf, rdfs, xsd."""

from . import base as B

from . import literal as L
from . import strings as S


class Json(
    L.List ^ L.Dict ^ L.String ^ L.Number ^ L.Bool ^ L.Null,
    B.Generic.ContentMediaType["application/json"],
):
    import json

    loader = json.loads
    dumper = json.dumps
    del json


Json.__annotations__["loader"] = Json

Pointer = S.Pointer


class Ø(BaseException):
    def __bool__(self):
        return False


class Schema(L.Dict):
    def apply(self, object):
        from .literal import Dict

        return Dict[self].validate()
