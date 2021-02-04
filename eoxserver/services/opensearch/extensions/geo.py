#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------


from django.contrib.gis.geos import GEOSGeometry, Point, Polygon, MultiPolygon
from django.contrib.gis.measure import D

from eoxserver.core.decoders import kvp, enum
from eoxserver.core.util.xmltools import NameSpace


class GeoExtension(object):
    """ Implementation of the OpenSearch `'Geo' extension draft
    <http://www.opensearch.org/Specifications/OpenSearch/Extensions/Geo/1.0/Draft_2>`_.
    Currently all parameters apart from the ``name`` are supported. The point
    plus radius with the relation type ``contains`` requires a PostGIS database
    backend.
    """

    namespace = NameSpace(
        "http://a9.com/-/opensearch/extensions/geo/1.0/", "geo"
    )

    def filter(self, qs, parameters):
        decoder = GeoExtensionDecoder(parameters)

        geom = decoder.box or decoder.geometry
        lon, lat = decoder.lon, decoder.lat
        distance = decoder.radius
        relation = decoder.relation
        uid = decoder.uid

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
        elif lon is not None and lat is not None:
            geom = Point(lon, lat)
            if relation == "intersects":
                qs = qs.filter(footprint__intersects=geom)
            elif relation == "contains":
                qs = qs.filter(footprint__coveredby=geom)
            elif relation == "disjoint":
                qs = qs.filter(footprint__disjoint=geom)

        if uid:
            qs = qs.filter(identifier=uid)

        return qs

    def get_schema(self, collection=None, model_class=None):
        return (
            dict(name="bbox", type="box"),
            dict(name="geom", type="geometry", profiles=[
                dict(
                    href="http://www.opengis.net/wkt/LINESTRING",
                    title="This service accepts WKT LineStrings"
                ),
                dict(
                    href="http://www.opengis.net/wkt/POINT",
                    title="This service accepts WKT Point"
                ),
                dict(
                    href="http://www.opengis.net/wkt/POLYGON",
                    title="This service accepts WKT Polygons"
                ),
                dict(
                    href="http://www.opengis.net/wkt/MULTILINESTRING",
                    title="This service accepts WKT Multi-LineStrings"
                ),
                dict(
                    href="http://www.opengis.net/wkt/MULTIPOINT",
                    title="This service accepts WKT Multi-Point"
                ),
                dict(
                    href="http://www.opengis.net/wkt/MULTIPOLYGON",
                    title="This service accepts WKT Multi-Polygons"
                ),
            ]),
            dict(name="lon", type="lon"),
            dict(name="lat", type="lat"),
            dict(name="r", type="radius"),
            dict(name="georel", type="relation",
                options=["intersects", "contains", "disjoint"]
            ),
            dict(name="uid", type="uid")
        )


def parse_bbox(raw):
    values = list(map(float, raw.split(",")))
    if len(values) != 4:
        raise ValueError("Invalid number of coordinates in 'bbox'.")

    minx, miny, maxx, maxy = values
    if minx <= maxx:
        return Polygon.from_bbox(values)

    return MultiPolygon(
        Polygon.from_bbox((minx, miny, 180.0, maxy)),
        Polygon.from_bbox((-180.0, miny, maxx, maxy)),
    )


def parse_radius(raw):
    # TODO: allow the specification of additional units
    value = float(raw)
    if value < 0:
        raise ValueError("Invalid radius specified")
    return D(m=value)


class GeoExtensionDecoder(kvp.Decoder):
    box = kvp.Parameter(num="?", type=parse_bbox)
    radius = kvp.Parameter(num="?", type=float)
    geometry = kvp.Parameter(num="?", type=GEOSGeometry)
    lon = kvp.Parameter(num="?", type=float)
    lat = kvp.Parameter(num="?", type=float)
    relation = kvp.Parameter(num="?",
        type=enum(("intersects", "contains", "disjoint"), False),
        default="intersects"
    )
    uid = kvp.Parameter(num="?")
