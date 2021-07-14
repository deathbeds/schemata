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
    return dict(
        actions=["sphinx-build . _build/html"],
        task_dep=["confpy", "schema"],
        verbosity=2,
    )


def task_confpy():
    def append():
        import inspect

    return dict(
        actions=[
            "jb config sphinx --toc docs/toc.yml --config docs/config.yml  . > conf.py",
            """echo "\nbibtex_bibfiles = []" >> conf.py """,
        ]
    )


def task_schema():
    def export():
        import json

        import schemata

        with open("src/schemata.jsonschema", "w") as f:
            data = schemata.utils.get_schema(
                {x.key(): x for x in schemata.utils.get_subclasses(schemata.Any)},
                ravel=True,
            )

            order = sorted(k for k, v in data.items() if v)
            data = dict(zip(order, map(data.get, order)))
            f.write(
                json.dumps(
                    schemata.Definitions[data].schema(True),
                    indent=2,
                )
            )

    return dict(actions=[export], targets=["src/schemata.jsonschema"])
