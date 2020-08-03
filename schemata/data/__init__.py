"""Load schema from vendors."""
import json, pathlib

here = pathlib.Path(__file__).parent

# Load jsonschema


for file in """
core applicator content format hyper-schema meta-data validation
""".strip().split():
    with (here / "jsonschema" / f"{file}.json").open("r") as file:
        schema = json.load(file)
    locals()[schema["$id"]] = schema

# Load geojson schema

for file in """
Point MultiPoint MultiPolygon MultiLineString LineString Feature FeatureCollection
""".strip().split():
    with (here / "geojson" / f"{file}.json").open("r") as file:
        schema = json.load(file)
    locals()[schema["$id"]] = schema

locals()[
    "https://specs.frictionlessdata.io/table-schema/table-schema.json"
] = json.loads(pathlib.Path(here / "table-schema.json").read_text())

# notebook format
del file, schema, here
