try:
    import nox, os
    CI = "GITHUB_ACTION" in os.environ
    @nox.session(python=False, reuse_venv=not CI)
    def build(session):
        if CI:
            session.install(*"--upgrade pip wheel setuptools flit".split())
        "SOURCE_DATE_EPOCH=$(git log -1 --format=%ct)", 
        session.run(*"flit build".split())

    @nox.session(python=False)
    def test(sesion):
        session.install("pytest")

except ModuleNotFoundError:
    pass


def task_download_schema():
    return dict(actions=[x for x in """""".splitlines()])


def task_uml():
    return dict(actions=[])