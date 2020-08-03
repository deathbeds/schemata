import rdflib, munch

site_packages = rdflib.Namespace('python://site-packages/')
stdlib = rdflib.Namespace('python://')

types = {
    rdflib.XSD.integer: int,
    rdflib.XSD.float: float,
    rdflib.XSD.string: str,
    rdflib.XSD.boolean: bool,
    rdflib.RDF.nil: type(None),
    rdflib.RDF.type: dict,
    rdflib.RDF.List: list, 
}