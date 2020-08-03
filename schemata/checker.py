"""The checker module defines locale aware jsonschema type and format checkers"""

import jsonschema, json, munch, frozendict


def is_array(validator, object):
    return isinstance(object, (list, tuple))


def is_object(validator, object):
    return isinstance(object, (frozendict.frozendict, munch.Munch, dict))


Validator = jsonschema.validators.extend(
    jsonschema.Draft7Validator,
    type_checker=jsonschema.Draft7Validator.TYPE_CHECKER.redefine(
        "array", is_array
    ).redefine("object", is_object),
)

checker = jsonschema.draft7_format_checker


def is_json(object):
    json.loads(object)
    return True

checker.checkers["json"] = is_json, (json.JSONDecodeError,)

