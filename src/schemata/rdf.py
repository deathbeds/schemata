from .strings import Uri
from .types import Any


class Vocab__(Any):
    pass


class Id__(Any):
    pass


RDF = Uri.cache()("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = Uri.cache()("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
DBPEDIA = Uri.cache()("http://dbpedia.org/resource/")
SCHEMA = Uri.cache()("http://schema.org/")
