"""The core types of schemata"""
# We have to use symbollic dictionaries in this script
import rdflib
from . import mutable, util
from .core import jsonschema

_ = locals().get("_", __import__("gettext").gettext)


locals()[_("null")] = type(
    _("null"),
    (jsonschema,),
    {"__annotations__": {_("type"): _("null"), "@type": rdflib.RDF.nil}},
)

locals()[_("boolean")] = type(
    _("boolean"),
    (jsonschema,),
    {"__annotations__": {_("type"): _("boolean"), "@type": rdflib.XSD.boolean}},
)
locals()[_("integer")] = type(
    _("integer"),
    (jsonschema,),
    {"__annotations__": {_("type"): _("integer"), "@type": rdflib.XSD.integer}},
)

locals()[_("number")] = type(
    _("number"),
    (jsonschema,),
    {"__annotations__": {_("type"): _("number"), "@type": rdflib.XSD.float}},
)

locals()[_("array")] = type(
    _("array"),
    (jsonschema,),
    {"__annotations__": {_("type"): _("array"), "@type": rdflib.RDF.List}},
)


locals()[_("string")] = type(
    _("string"),
    (jsonschema,),
    {"__annotations__": {_("type"): _("string"), "@type": rdflib.XSD.string}},
)

locals()[_("object")] = type(
    _("object"),
    (mutable.display, jsonschema, mutable.mapping,),
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
