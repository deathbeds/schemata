"""The checker module defines locale aware jsonschema type and format checkers.

It provides a localizing Validator for different locales."""

import jsonschema, json, frozendict, pathlib
from . import util, translate


def is_array(validator, object):
    return isinstance(object, (list, tuple))


def is_object(validator, object):
    return isinstance(object, (frozendict.frozendict, dict))


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


def localize_validator(lang):
    if lang in LOCALIZED_VALIDATOR:
        return LOCALIZED_VALIDATOR.get(lang)

    LocalizedValidator = jsonschema.validators.extend(
        jsonschema.Draft7Validator,
        type_checker=jsonschema.Draft7Validator.TYPE_CHECKER.redefine(
            "array", is_array
        ).redefine("object", is_object),
    )
    LocalizedValidator.VALIDATORS = translate.translate(LocalizedValidator.VALIDATORS, lang)
    LocalizedValidator.TYPE_CHECKER = jsonschema.TypeChecker(
        {
            **LocalizedValidator.TYPE_CHECKER._type_checkers,
            **translate.translate(LocalizedValidator.TYPE_CHECKER._type_checkers, lang),
        }
    )
    LOCALIZED_VALIDATOR[lang] = LocalizedValidator
    return LOCALIZED_VALIDATOR[lang]


LOCALIZED_VALIDATOR = {}
