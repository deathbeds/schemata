import schemata, importlib, gettext, pathlib

_module = importlib.util.module_from_spec(
    importlib.machinery.ModuleSpec(
        "schemata.es",
        importlib.machinery.SourceFileLoader(
            "schemata.es", schemata.types.__loader__.path
        ),
        origin=schemata.types.__spec__.origin,
    )
)

_module.__file__ = schemata.types.__file__
_module.language = "es"
_module.__loader__.exec_module(_module)

locals().update(vars(_module))

del _module, importlib
