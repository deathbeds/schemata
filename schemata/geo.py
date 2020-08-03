"""Core abstract types for schemata."""
from . import object, data

class geometry(object):
    __annotations__ =dict(contentMediaType='application/geo+json')
    
    def _repr_meta_(self):
        return {self.__annotations__['contentMediaType']: {'level': 10}}

class point(geometry):
    __annotations__=getattr(data, "https://geojson.org/schema/Point.json")


class multi_polygon(geometry):
    __annotations__=getattr(data, "https://geojson.org/schema/MultiPolygon.json")


class feature(geometry):
    __annotations__=getattr(data, "https://geojson.org/schema/Feature.json")


class feature_collection(geometry):
    __annotations__=getattr(data, "https://geojson.org/schema/FeatureCollection.json")


class multi_point(geometry):
    __annotations__=getattr(data, "https://geojson.org/schema/MultiPoint.json")


class line_string(geometry):
    __annotations__=getattr(data, "https://geojson.org/schema/LineString.json")


class multi_line_string(geometry):
    __annotations__=getattr(data, "https://geojson.org/schema/MultiLineString.json")
