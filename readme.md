# schemata

[![cov-badge]][cov]

[cov-badge]: https://img.shields.io/codecov/c/github/deathbeds/schemata?token=hob01Xmh6Z
[cov]: https://app.codecov.io/gh/deathbeds/schemata

A primary goal of schemata isa to provide a locale-aware trait system for python.

    import schemata

The trait system provides the following features:

- [x] Validation
- [x] Defaults
- [x] Examples
- [x] Locales
- [ ] Notification
- [ ] GUI Generation
  - [x] IPython
  - [ ] Widgets
- [ ] Predefined types
  - [x] `jsonschema` types
  - [ ] `jsonschema` formats
  - [x] Container Types
- [ ] API Compatability
  - [ ] dataclasses (maybe attrs)
  - [ ] traitlets
  - [ ] pydantic
  - [ ] param

## from language agnostic to locale aware

`schemata` implements a locale type system beginning with
URIs and IRIs. It uses symbols as gestures to supplement language
before building a concrete Python vocabulary.

`schemata` tries to build from a language agnostic interface using symbols and urls.
The symbols and urls can locale specific type systems.

## supported schema

### `jsonschema`

- [x] jsonschema-core
- [x] json hyper schema
- [x] geojson
- [ ] vega-lite
- [ ] tableschema
- [ ] schema.org
- [ ] notebook format

### python types

- [ ] Instances
- [ ] Types

Schema must be implemented in two different conformations:

1. A schema is a meta schema that establishes an abstract type. In this case, the schema defines jsonschema types
that are not compatible with the base json schema.
2. A schema derives for the a jsonschema object because it's schema conforms the standard json schema.

## architecture

Existing trait libraries use special objects, with custom logic, to acheive the features 
of traitlet patterns. On the other hand, `schemata` provides concrete python types with traitlet features.

`schemata` uses open source projects to extend the abilities of the library.

## comparison with other trait libraries

`schemata` is preceded by a few different trait libraries `enthought.traits`, `traitlets`, and `pydantic`.
`traitlets` is a reimplementation of the `enthought.traits` by the `IPython` community; `traitlets` have been the
configuration for `jupyter` and `IPython` since.
`traitlets` preceeded a lot of critical web technology critical to the `jupyter` interactive computing ecosystem;
`traitlets` are only concerned with Python objects and lack features of the modern.
`pydantic` provides value as trait system by building off of the `jsonschema` specification to validate types.
`schemata` unifies `traitlets` and `pydantic` by providing a description type interface based off of open web standards.

The desire is a trait system for interactive computing that enables more expressive design and testing of interactive
computing technology.


