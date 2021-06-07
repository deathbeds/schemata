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


def task_schema():
    def export():
        import json

        import schemata

        with open("src/schemata.jsonschema", "w") as f:
            f.write(
                json.dumps(
                    schemata.utils.get_schema(
                        schemata.Definitions[
                            {
                                x.key(): x
                                for x in schemata.utils.get_subclasses(schemata.Any)
                            }
                        ],
                        ravel=True,
                    ),
                    indent=2,
                )
            )

    return dict(actions=[export], targets=["src/schemata.jsonschema"])
