"""Semantically enrich python types.

schemata defines an ephemeral/optional type system for python that relies on
rdf type representations to map to and from python types.

the primary application of schemata is to enrich the outputs with meaning. in this
framing, schemata is superfluous to the user, but their notebooks will
have improved reproducible qualities.

notebooks have primarily grown as a substrate for literature that is enhanced
by mimetypes that provide visual meaning. in this context, there are sufficient
literacy skills required to responsibly derive meaning from the document. 

schemata extends notebooks to be linked data documents that augment the
existing mimetypes with semantic rdf types.

we should raise errors as rdf too.
"""
__version__ = "0.0.1"

from .base import *

from .literal import *  # isort:skip
from .composite import *  # isort:skip

# from .literal import *  # isort:skip
from .json import *  # isort:skip
from .strings import *  # isort:skip
from .callables import *  # isort:skip
from . import app, numbers, strings, literal, composite, alias, json  # isort:skip

__import__("jsonschema").Draft7Validator.TYPE_CHECKER.redefine(
    "array", lambda c, x: isinstance(x, (list, tuple))
)


def load_ipython_extension(shell):
    from .ipython import load_ipython_extension

    load_ipython_extension(shell)


def unload_ipython_extension(shell):
    from .ipython import unload_ipython_extension

    unload_ipython_extension(shell)
