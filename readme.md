# schemata

[![cov-badge]][cov]

[cov-badge]: https://img.shields.io/codecov/c/github/deathbeds/schemata?token=hob01Xmh6Z
[cov]: https://app.codecov.io/gh/deathbeds/schemata

`schemata` is trait system for Python and IPytohn applications that provide:

* validation
* testing strategies
* interactive user interfaces
* observable pattern

`schemata`'s type system is composable and expresses the type annotations in the form of json schema. attaching the schema to the types allows different interfaces to construct defaults in aspects like testing, visualization, and verification.


Learn more from the documentation.

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


