"""Core abstract types for schemata."""
from . import object, data


class table(object):
    __annotations__ = getattr(
        data, "https://specs.frictionlessdata.io/table-schema/table-schema.json"
    )


class field(object):
    __annotations__ = schemata.table.table.__schema__["properties"]["fields"]["items"]

    # There are bunch of different field tyzpes in the anyof key.
