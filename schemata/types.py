"""The core types of schemata"""
# We have to use symbollic dictionaries in this script
import pathlib
import rdflib
from . import mutable, util, types, translate
from .core import jsonschema

language = locals().get("language", "en")

_ = translate.get_translation(language).gettext
# Make a bases class that can translate locales.

basis = locals()[language] = type(language, (jsonschema,), {}, language=language)

locals()[_("null")] = type(
    _("null"),
    (basis,),
    {"__annotations__": {_("type"): _("null"), "@type": rdflib.RDF.nil}},
)

locals()[_("boolean")] = type(
    _("boolean"),
    (basis,),
    {"__annotations__": {_("type"): _("boolean"), "@type": rdflib.XSD.boolean}},
)
locals()[_("integer")] = type(
    _("integer"),
    (basis,),
    {"__annotations__": {_("type"): _("integer"), "@type": rdflib.XSD.integer}},
)

locals()[_("number")] = type(
    _("number"),
    (basis,),
    {"__annotations__": {_("type"): _("number"), "@type": rdflib.XSD.float}},
)

locals()[_("array")] = type(
    _("array"),
    (basis,),
    {"__annotations__": {_("type"): _("array"), "@type": rdflib.RDF.List}},
)


locals()[_("string")] = type(
    _("string"),
    (basis,),
    {"__annotations__": {_("type"): _("string"), "@type": rdflib.XSD.string}},
)

locals()[_("object")] = type(
    _("object"),
    (mutable.display, basis, mutable.mapping,),
    {"__annotations__": {_("type"): _("object"), "@type": rdflib.RDF.type}},
)

locals()[_("dict")] = type(
    _("dict"),
    (locals()[_("object")],),
    {"__annotations__": {_("contentMediaType"): "application/json"}},
)


locals()[_("template")] = type(
    _("template"), (locals()[_("object")],), {"__call__": util.render_jsone_template}
)

del basis
