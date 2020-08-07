import gettext, pathlib, rdflib, typing

TRANSLATIONS = {}

def get_translation(language="en"):
    if language in TRANSLATIONS:
        return TRANSLATIONS[language]
    TRANSLATIONS[language]=  gettext.translation(
        "schemata",
        pathlib.Path(__file__).parent / "locale",
        languages=[language],
    )
    return TRANSLATIONS[language]

def translate(object, _="en"):
    if isinstance(_, str):
        _ = get_translation(_).gettext
    if isinstance(object, rdflib.URIRef):
        return object
    elif isinstance(object, str):
        return _(object)
    elif isinstance(object, typing.Mapping):
        return {_(k): translate(v, _=_) for k, v in object.items()}
    elif isinstance(object, (list, tuple)):
        return type(object)(translate(x, _=_) for x in object)
    return object
