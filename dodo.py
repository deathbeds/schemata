uml_ignore = "compat testing templates.py ui.py mediatypes.py apis.py patches.py utils.py exceptions.py _schema.py callables.py".split()


def task_uml():
    return dict(
        actions=[
            f"pyreverse -o png -p schemata --ignore={','.join(uml_ignore)} src/schemata "
        ]
    )


def task_format():
    return dict(actions=["isort .", "black ."], task_dep=["confpy"])


def task_docs():
    return dict(actions=["sphinx-build . _build/html"], task_dep=["confpy"])
    return dict(actions=["jb build --toc docs/toc.yml --config docs/config.yml ."])


def task_confpy():
    def append():
        import inspect

    return dict(
        actions=[
            "jb config sphinx --toc docs/toc.yml --config docs/config.yml  . > conf.py",
            """echo "\nbibtex_bibfiles = []" >> conf.py """,
        ]
    )


def get_type_hints(obj, globalns=None, localns=None):
    from sphinx.util.inspect import safe_getattr  # lazy loading

    try:
        return __import__("typing").get_type_hints(obj, globalns, localns)
    except (NameError, SyntaxError):
        # Failed to evaluate ForwardRef (maybe TYPE_CHECKING)
        return safe_getattr(obj, "__annotations__", {})
    except TypeError:
        return {}
    except KeyError:
        # a broken class found (refs: https://github.com/sphinx-doc/sphinx/issues/8084)
        return {}
    except AttributeError:
        # AttributeError is raised on 3.5.2 (fixed by 3.5.3)
        return {}
