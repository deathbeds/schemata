
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