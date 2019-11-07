#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
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


from lxml import etree
from lxml.builder import E

from django.contrib.gis.geos import Polygon, MultiPolygon

from eoxserver.core.util.xmltools import parse
from eoxserver.core.util.timetools import isoformat
from eoxserver.core.util.iteratortools import pairwise
from eoxserver.core.util.timetools import parse_iso8601
from eoxserver.core.decoders import xml
from eoxserver.core import Component

class NativeFormat(Component):
    formats = ("native", )

    def test(self, obj):
        xml = parse(obj)
        return xml is not None and xml.getroot().tag == "Metadata"

    def get_format_name(self, obj):
        return "native"

    def read(self, obj):
        tree = parse(obj)
        if tree is not None:
            decoder = NativeFormatDecoder(tree)
            return {
                "identifier": decoder.identifier,
                "begin_time": decoder.begin_time,
                "end_time": decoder.end_time,
                "footprint": MultiPolygon(*decoder.polygons),
                "format": "native"
            }
        raise Exception("Could not parse from obj '%s'." % repr(obj))

    def write(self, values, file_obj, format=None, encoding=None, pretty=False):
        def flip(point):
            return point[1], point[0]

        # ignore format
        tree = E.Metadata(
            E.EOID(values["identifier"]),
            E.BeginTime(isoformat(values["begin_time"])),
            E.EndTime(isoformat(values["end_time"])),
            E.Footprint(
                *map(lambda polygon:
                    E.Polygon(
                        E.Exterior(
                            " ".join([
                                "%f %f" % flip(point)
                                for point in polygon.exterior_ring
                            ])
                        ),
                        *[E.Interior(
                            " ".join([
                                "%f %f" % flip(point)
                                for point in interior
                            ])
                        ) for interior in polygon[1:]]
                    ),
                    values["footprint"]
                )
            )
        )

        file_obj.write(
            etree.tostring(tree, pretty_print=pretty, encoding=encoding)
        )


def parse_polygon_xml(elem):
    return Polygon(
        parse_ring(elem.findtext("Exterior")),
        *map(lambda e: parse_ring(e.text), elem.findall("Interior"))
    )


def parse_ring(string):
    raw_coords = map(float, string.split(" "))
    return [(lon, lat) for lat, lon in pairwise(raw_coords)]


class NativeFormatDecoder(xml.Decoder):
    identifier = xml.Parameter("EOID/text()")
    begin_time = xml.Parameter("BeginTime/text()", type=parse_iso8601)
    end_time = xml.Parameter("EndTime/text()", type=parse_iso8601)
    polygons = xml.Parameter("Footprint/Polygon", type=parse_polygon_xml, num="+")
