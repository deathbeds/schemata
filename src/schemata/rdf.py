from .strings import Uri
from .types import Any


class Base__(Any):
    pass


class Container__(Any):
    pass


class Direction__(Any):
    pass


class Graph__(Any):
    pass


class __(Any):
    pass


class Id__(Any):
    pass


class Import__(Any):
    pass


class Included__(Any):
    pass


class Index__(Any):
    pass


class Json__(Any):
    pass


class Language__(Any):
    pass


class List__(Any):
    pass


class Nest__(Any):
    pass


class List__(Any):
    pass


class Prefix__(Any):
    pass


class Protected__(Any):
    pass


class Set__(Any):
    pass


class Type__(Any):
    pass


class Set__(Any):
    pass


class Vocab__(Any):
    pass


class Version__(Any):
    pass


class Context__(Any):
    @classmethod
    def expand(cls, object):
        from pyld import jsonld

        from . import rdf

        return jsonld.expand(
            object,
            options=dict(expandContext=cls.schema()),
        )

    @classmethod
    def compact(cls, object):
        from pyld import jsonld

        from . import rdf

        return jsonld.compact(object, cls.schema())


DC11 = Uri.cache()("http://purl.org/dc/elements/1.1/")
DCTERMS = Uri.cache()("http://purl.org/dc/terms/")
CRED = Uri.cache()("https://w3id.org/credentials#")
FOAF = Uri.cache()("http://xmlns.com/foaf/0.1/")
GEOJSON = Uri.cache()("https://purl.org/geojson/vocab#")
PROV = Uri.cache()("http://www.w3.org/ns/prov#")
I18N = Uri.cache()("https://www.w3.org/ns/i18n#")
RDF = Uri.cache()("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
SCHEMA = Uri.cache()("http://schema.org/")
SKOS = Uri.cache()("http://www.w3.org/2004/02/skos/core#")
XSD = Uri.cache()("http://www.w3.org/2001/XMLSchema#")

RDFS = Uri.cache()("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
DBPEDIA = Uri.cache()("http://dbpedia.org/resource/")
