try:
    import functools
    import io
    import os
    import pathlib
    import subprocess

    import nox

    CI = "GITHUB_ACTION" in os.environ

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
        session.run(
            *"pytest -vv --pyargs . --nbval -pno:importnb --durations=5 --cov=schemata --cov-report=term-missing:skip-covered --no-cov-on-fail".split()
        )
        session.run(*"coverage html".split())

    @nox.session(python=False)
    def docs(session):
        try:
            import jupyter_book
        except:
            session.install(*"--ignore-installed --upgrade .[docs]".split())
        with open("conf.py", "w") as file:
            session.run(
                *"jb config sphinx --toc docs/_toc.yml --config docs/_config.yml .".split(),
                stdout=file
            )

        session.run(*"jb build --toc docs/_toc.yml --config docs/_config.yml .".split())
        pathlib.Path("_build/html/.nojekyll").touch()


except ModuleNotFoundError:
    pass


def task_download_schema():
    return dict(actions=[x for x in """""".splitlines()])


def task_uml():
    return dict(actions=[])
