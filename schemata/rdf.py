from . import data, Any, Schemata


class LD(Any.from_schema(data.load("ld"))):
    pass


for k, v in Schemata.value(LD, "definitions").items():
    for x, y in v.schema()["properties"].items():
        Schemata.cls(x)
