from django.contrib.gis.geos import GEOSGeometry, Point
from django.contrib.gis.measure import D

from eoxserver.core import Component, implements
from eoxserver.core.decoders import kvp, enum
from eoxserver.core.util.xmltools import NameSpace
from eoxserver.services.opensearch.interfaces import SearchExtensionInterface


class GeoExtension(Component):
    implements(SearchExtensionInterface)

    namespace = NameSpace(
        "http://a9.com/-/opensearch/extensions/geo/1.0/", "geo"
    )

    schema = {
        "bbox": ("bbox", True),
        "r": ("radius", True),
        "geom": ("geometry", True),
        "lon": ("lon", True),
        "lat": ("lat", True),
        "georel": ("relation", True)
    }

    def filter(self, qs, parameters):
        decoder = GeoExtensionDecoder(parameters)

        geom = decoder.bbox or decoder.geometry
        lon, lat = decoder.lon, decoder.lat
        distance = decoder.radius
        relation = decoder.relation

        if geom:
            if relation == "intersects":
                qs = qs.filter(footprint__intersects=geom)
            elif relation == "contains":
                qs = qs.filter(footprint__coveredby=geom)
            elif relation == "disjoint":
                qs = qs.filter(footprint__disjoint=geom)

        elif lon is not None and lat is not None and distance is not None:
            geom = Point(lon, lat)
            if relation == "intersects":
                qs = qs.filter(footprint__distance_lte=(geom, distance))
            elif relation == "contains":
                # TODO: right?, also only available on postgis
                qs = qs.filter(footprint__dwithin=(geom, distance))
            elif relation == "disjoint":
                qs = qs.filter(footprint__distance_gt=(geom, distance))

        return qs


def parse_bbox(raw):
    values = map(float, raw.split(","))
    if len(values) != 4:
        raise ValueError("Invalid number of coordinates in 'bbox'.")
    return GEOSGeometry.from_bbox(values)


def parse_radius(raw):
    # TODO: allow the specification of additional units
    value = float(raw)
    if value < 0:
        raise ValueError("Invalid radius specified")
    return D(m=value)


class GeoExtensionDecoder(kvp.Decoder):
    bbox = kvp.Parameter(num="?", type=parse_bbox)
    radius = kvp.Parameter(num="?", type=float)
    geometry = kvp.Parameter(num="?", type=GEOSGeometry)
    lon = kvp.Parameter(num="?", type=float)
    lat = kvp.Parameter(num="?", type=float)
    relation = kvp.Parameter(num="?",
        type=enum(("intersects", "contains", "disjoint"), False),
        default="intersects"
    )
