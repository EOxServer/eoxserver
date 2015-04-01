from json import dumps

from eoxserver.core import Component, implements
from eoxserver.core.util.timetools import isoformat
from eoxserver.services.opensearch.interfaces import ResultFormatInterface


class GeoJSONResultFormat(Component):
    """ GeoJSON result format.
    """

    implements(ResultFormatInterface)

    mimetype = "application/vnd.geo+json"
    name = "json"

    def encode(self, queryset):
        return dumps({
            "type": "FeatureCollection",
            "features": [
                self.encode_feature(eo_object)
                for eo_object in queryset
            ]
        })

    def encode_feature(self, eo_object):
        return {
            "type": "Feature",
            "id": eo_object.identifier,
            "bbox": eo_object.footprint.extent,
            "geometry": self.encode_geometry(eo_object.footprint),
            "properties": {
                "start_time": isoformat(eo_object.begin_time),
                "end_time": isoformat(eo_object.end_time)
            }
        }

    def encode_geometry(self, geometry):
        return dict(
            type=geometry.geom_type,
            coordinates=[
                [
                    [
                        [point[0], point[1]]
                        for point in linestring
                    ] for linestring in polygon
                ] for polygon in geometry
            ]
        )
