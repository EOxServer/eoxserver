#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2014 EOX IT Services GmbH
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

from lxml.builder import ElementMaker

from eoxserver.core.util.xmltools import NameSpace, NameSpaceMap
from eoxserver.core.util.timetools import isoformat
from eoxserver.resources.coverages import crss

# namespace declarations
ns_gml = NameSpace("http://www.opengis.net/gml/3.2", "gml")
ns_gmlcov = NameSpace("http://www.opengis.net/gmlcov/1.0", "gmlcov")
ns_om = NameSpace("http://www.opengis.net/om/2.0", "om")
ns_eop = NameSpace("http://www.opengis.net/eop/2.0", "eop")

nsmap = NameSpaceMap(ns_gml, ns_gmlcov, ns_om, ns_eop)

# Element factories
GML = ElementMaker(namespace=ns_gml.uri, nsmap=nsmap)
GMLCOV = ElementMaker(namespace=ns_gmlcov.uri, nsmap=nsmap)
OM = ElementMaker(namespace=ns_om.uri, nsmap=nsmap)
EOP = ElementMaker(namespace=ns_eop.uri, nsmap=nsmap)


class GML32Encoder(object):
    def encode_linear_ring(self, ring, sr):
        frmt = "%.3f %.3f" if sr.projected else "%.8f %.8f"

        swap = crss.getAxesSwapper(sr.srid)
        pos_list = " ".join(frmt % swap(*point) for point in ring)

        return GML("LinearRing",
            GML("posList",
                pos_list
            )
        )

    def encode_polygon(self, polygon, base_id):
        return GML("Polygon",
            GML("exterior",
                self.encode_linear_ring(polygon[0], polygon.srs)
            ),
            *(GML("interior",
                self.encode_linear_ring(interior, polygon.srs)
            ) for interior in polygon[1:]),
            **{ns_gml("id"): "polygon_%s" % base_id}
        )

    def encode_multi_surface(self, geom, base_id):
        if geom.geom_typeid in (6, 7):  # MultiPolygon and GeometryCollection
            polygons = [
                self.encode_polygon(polygon, "%s_%d" % (base_id, i+1))
                for i, polygon in enumerate(geom)
            ]
        elif geom.geom_typeid == 3:     # Polygon
            polygons = [self.encode_polygon(geom, base_id)]
        else:
            polygons = []

        return GML("MultiSurface",
            *[GML("surfaceMember", polygon) for polygon in polygons],
            **{ns_gml("id"): "multisurface_%s" % base_id,
               "srsName": "EPSG:%d" % geom.srid
            }
        )

    def encode_time_period(self, begin_time, end_time, identifier):
        return GML("TimePeriod",
            GML("beginPosition", isoformat(begin_time)),
            GML("endPosition", isoformat(end_time)),
            **{ns_gml("id"): identifier}
        )

    def encode_time_instant(self, time, identifier):
        return GML("TimeInstant",
            GML("timePosition", isoformat(time)),
            **{ns_gml("id"): identifier}
        )


class EOP20Encoder(GML32Encoder):
    def encode_footprint(self, footprint, eo_id):
        return EOP("Footprint",
            EOP("multiExtentOf", self.encode_multi_surface(footprint, eo_id)),
            **{ns_gml("id"): "footprint_%s" % eo_id}
        )

    def encode_metadata_property(self, eo_id, contributing_datasets=None):
        return EOP("metaDataProperty",
            EOP("EarthObservationMetaData",
                EOP("identifier", eo_id),
                EOP("acquisitionType", "NOMINAL"),
                EOP("status", "ARCHIVED"),
                *([EOP("composedOf", contributing_datasets)]
                    if contributing_datasets else []
                )
            )
        )

    def encode_earth_observation(self, identifier, begin_time, end_time,
                                 footprint, contributing_datasets=None,
                                 subset_polygon=None):

        if subset_polygon is not None:
            footprint = footprint.intersection(subset_polygon)

        elements = []
        if begin_time and end_time:
            elements.append(
                OM("phenomenonTime",
                    self.encode_time_period(
                        begin_time, end_time, "phen_time_%s" % identifier
                    )
                )
            )
        if end_time:
            elements.append(
                OM("resultTime",
                    self.encode_time_instant(
                        end_time, "res_time_%s" % identifier
                    )
                )
            )

        elements.extend([
            OM("procedure"),
            OM("observedProperty"),
        ])

        if footprint:
            elements.append(
                OM("featureOfInterest",
                    self.encode_footprint(footprint, identifier)
                )
            )
        elements.extend([
            OM("result"),
            self.encode_metadata_property(identifier, contributing_datasets)
        ])

        return EOP("EarthObservation",
            *elements,
            **{ns_gml("id"): "eop_%s" % identifier}
        )
