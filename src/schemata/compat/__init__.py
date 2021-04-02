import functools
import inspect
import re

from .. import base


@functools.singledispatch
def get_signature(x):
    return inspect.signature(x)


@get_signature.register
def _get_signature_from_schema(x: base.Generic):
    return get_signature(x.schema())


@get_signature.register
def _get_signature_from_schema(x: re.Pattern):
    return inspect.Signature(
        [
            # inspect.Parameter("string", inspect.Parameter.POSITIONAL_ONLY),
            *(
                inspect.Parameter(x, inspect.Parameter.KEYWORD_ONLY)
                for x in sorted(x.groupindex)
            ),
            inspect.Parameter("kwargs", inspect.Parameter.VAR_KEYWORD),
        ]
    )


@get_signature.register
def _get_signature_from_schema(s: dict):
    p = s.get("properties", {})

    a = []
    required = s.get("required", [])
    for k in required:
        try:
            a += (
                inspect.Parameter(
                    k,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=p.get(k, inspect._empty),
                ),
            )
        except (ValueError, TypeError):
            return inspect.signature(cls)

    for k in p:
        if k in required:
            continue

        v = p[k]
        if isinstance(v, type) and issubclass(v, base.Default):
            d = base.Default.forms(v)
            if not callable(d):
                a += (
                    inspect.Parameter(
                        k,
                        inspect.Parameter.KEYWORD_ONLY,
                        annotation=p[k],
                        default=d,
                    ),
                )
            continue

        try:
            a += (
                inspect.Parameter(
                    k,
                    inspect.Parameter.KEYWORD_ONLY,
                    annotation=p[k],
                ),
            )
        except ValueError:
            pass

    additional = s.get("additionalProperties", True)
    if not additional:
        a += (
            (
                inspect.Parameter(
                    "kwargs",
                    inspect.Parameter.VAR_KEYWORD,
                    annotation=inspect._empty
                    if isinstance(additional, bool)
                    else additional,
                ),
            ),
        )
    return inspect.Signature(a)
