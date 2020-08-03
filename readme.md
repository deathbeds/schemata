# schemata

A primary goal of schemata isa to provide a locale-aware trait system for python uses
the jsonschema specification.

    import schemata

* types in your locale
* type validation
* type discovery
* type composition
* rich displays
* observable objects

# from language agnostic to locale aware

`schemata` implements a locale type system beginning with 
URIs and IRIs. It uses symbols as gestures to supplement language
before building a concrete Python vocabulary.

`schemata` tries to build from a language agnostic interface using symbols and urls.
The symbols and urls can locale specific type systems.

## supported schema

- [x] jsonschema-core
- [x] json hyper schema
- [x] geojson
- [ ] vega-lite
- [ ] tableschema
- [ ] schema.org
- [ ] notebook format

Schema must be implemented in two different conformations:

1. A schema is a meta schema that establishes an abstract type. In this case, the schema defines jsonschema types
that are not compatible with the base json schema.
2. A schema derives for the a jsonschema object because it's schema conforms the standard json schema.

## architecture
