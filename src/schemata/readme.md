# types and traits

static typing is the new hot 💩. in different communities, static typing is enabled enomorous teams to work even increasingly enormous code bases. this is great for teams, but for the scientists or analyst it may be superfluous. another powerful feature of types is they have rigorous mathematical definitions that allow static inference of the type system, type systems can be validated.

in interactive computing, the goal is to tell a story or have a conversation with code. as such, the code effects the quality of the entire narrative. each type annotation adds to the length, and if it does not effect the code then it is superfluous. 

the `typing` library provides markers for types that can provide inference, but most `typing` generics can not be used in a concrete way.

`schemata` is a trait and type system. it provides >100 python types to improve the description of your codes, and perform static analysis. as a trait system, each of these have concrete validation methods and they can be instantiated unlike a `typing.Generic`. since each schemata type contains a schema it provides other affordances like:

* automatic test generation
* contextual type displays
* rdf metadata descriptions

# python in jsonschema

some popular trait libraries are `traitlets`, `param`, or `pydantic`. each of these libraries has one base trait, it is not a type, it is an object. the rest of the abstractions are drawn off a single base __object__. `schemata` goes further to define types, rather than objects. the benefit of this is that `schemata` now has mathematical foundations.

there is a funny joke in python that says:

    sys.null, sys.true, sys.false = None, True, False

what we are saying here is that python is really damn close to `json`. that is powerful feature of python that drives web applications like `jupyter, IPython, panel and fastapi` off of their respective trait systems.

the `json` type system contains six types: `Null, Bool, Number, String, List and Dict`. the `jsonschema` specification extends `json` system. for example, `pydantic` works by building schema in python, it is delightful! good types can be hard to write, so we designed `schemata` to address this is issue. it builds `jsonschema` from python too, but the schema is held on types rather than objects. `schemata` expresses all of the features of draft 7 `jsonschema` including keys like `dependencies`. just for shits, `schemata` expresses a full symbollic expression system for building dense types descriptions.