"""Semantically enrich python types."""
__version__ = "0.0.1"

# from .abc import Schema

from .base import *  # isort:skip
from . import apps, forms, strings, numbers

from .types import *  # isort:skip

# from .strings import *


def load_ipython_extension(shell):  # pragma: no cover
    from .ipython import load_ipython_extension

    load_ipython_extension(shell)


def unload_ipython_extension(shell):  # pragma: no cover
    from .ipython import unload_ipython_extension

    unload_ipython_extension(shell)
