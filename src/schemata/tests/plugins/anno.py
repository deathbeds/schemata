# Derived from
# https://github.com/utgwkk/pytest-github-actions-annotate-failures
# MIT License
# Copyright (c) 2020 utagawa kiki

import os
import sys
import sysconfig
from pathlib import Path
from collections import OrderedDict

import pytest

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if not ("GITHUB_ACTIONS" in os.environ and report.when == "call" and report.failed):
        return

    in_site_packages = str(Path("site-packages/schemata"))
    in_workspace = str(Path("src/schemata"))

    filesystempath, lineno, _ = report.location
    full_path = str(Path(filesystempath).resolve())

    if in_site_packages not in full_path:
        return

    src_fragment = full_path.split(in_site_packages)[1]
    workspace_path = str(Path(in_workspace, src_fragment[1:]).as_posix())

    lineno += 1
    longrepr = report.head_line or item.name
    try:
        longrepr += "\n\n" + report.longrepr.reprcrash.message
        lineno = report.longrepr.reprcrash.lineno
    except AttributeError:
        pass

    print(_error_workflow_command(workspace_path, lineno, longrepr))


def _error_workflow_command(workspace_path, lineno, longrepr):
    details_dict = OrderedDict()
    details_dict["file"] = workspace_path
    if lineno is not None:
        details_dict["line"] = lineno
    details = ",".join("{}={}".format(k, v) for k, v in details_dict.items())

    if longrepr is None:
        return "\n::error {}".format(details.strip())

    longrepr = _escape(longrepr)
    return "\n::error {}::{}".format(details.strip(), longrepr.strip())


def _escape(s):
    return s.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
