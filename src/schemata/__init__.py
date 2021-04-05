"""Semantically enrich python types."""
__version__ = "0.0.1"

# from .abc import Schema

from . import base  # isort:skip

from .types import *  # isort:skip
from .exceptions import ConsentException, ValidationError, ValidationErrors

from . import apps, numbers, strings, ui  # isort:skip


if "IPython" in __import__("sys").modules:
    from .compat.ipython import load_ipython_extension, unload_ipython_extension
