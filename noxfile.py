import functools
import io
import os
import pathlib
import subprocess

with __import__("contextlib").suppress(ModuleNotFoundError):

    import nox  # isort:skip

    CI = "GITHUB_ACTION" in os.environ or "READTHEDOCS" in os.environ

    @nox.session(python=False, reuse_venv=not CI)
    def build(session):
        if CI:
            session.install(*"--upgrade pip wheel setuptools flit".split())
        "SOURCE_DATE_EPOCH=$(git log -1 --format=%ct)",
        env = dict(
            SOURCE_DATE_EPOCH=subprocess.check_output("git log -1 --format=%ct".split())
            .decode("utf-8")
            .strip()
        )
        session.run(*"flit build".split(), env=env)

    @nox.session(python=False, reuse_venv=not CI)
    def test(session):
        if CI:
            session.install(*"--ignore-installed --upgrade .[test,ci]".split())
        session.run("pytest")
        session.run(*"coverage html".split())

    @nox.session(python=False)
    def docs(session):
        try:
            import jupyter_book
        except:
            if CI:
                session.install(*"--ignore-installed --upgrade .[docs]".split())
            else:
                develop(session)
        confpy(session)
        # use sphinx for the build to ensure we can work on readthedocs
        session.run(*"sphinx-build . _build/html".split())
        pathlib.Path("_build/html/.nojekyll").touch()

    @nox.session(python=False)
    def develop(session):
        try:
            import flit
        except:
            session.install("flit")
        session.run(*"flit install -s".split())

    @nox.session(python=False)
    def confpy(session):
        with open("conf.py", "w") as file:
            session.run(
                *"jb config sphinx --toc docs/_toc.yml --config docs/_config.yml .".split(),
                stdout=file
            )

        with open("conf.py", "a") as file:
            file.write("\nbibtex_bibfiles=[]\n")

        session.run(*"black conf.py".split())


def task_download_schema():
    return dict(actions=[x for x in """""".splitlines()])


def task_uml():
    return dict(actions=[])
