import os

from .plugins.anno import pytest_runtest_makereport

collect_ignore_glob = ["_build"]
pytest_plugins = ["pytester"]
