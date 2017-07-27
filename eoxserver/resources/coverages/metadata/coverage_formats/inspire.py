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

from django.contrib.gis.geos import Polygon, MultiPolygon

from eoxserver.core.util.xmltools import parse, NameSpace, NameSpaceMap
from eoxserver.core.util.timetools import parse_iso8601
from eoxserver.core.util.iteratortools import pairwise
from eoxserver.core.decoders import xml

NS_GMD = NameSpace("http://www.isotc211.org/2005/gmd", "gmd")
NS_GML = NameSpace("http://www.opengis.net/gml", "gml")
NS_GCO = NameSpace("http://www.isotc211.org/2005/gco", "gco")

nsmap = NameSpaceMap(NS_GMD, NS_GCO, NS_GML)


class InspireFormatReader(object):
    def test(self, obj):
        tree = parse(obj)
        return tree is not None and tree.getroot().tag == NS_GMD("MD_Metadata")

    def read(self, obj):
        tree = parse(obj)
        if tree is not None:
            decoder = InspireFormatDecoder(tree)
            return {
                "identifier": decoder.identifier,
                "begin_time": decoder.begin_time,
                "end_time": decoder.end_time,
                "footprint": decoder.footprint,
                "format": "inspire"
            }
        raise Exception("Could not parse from obj '%s'." % repr(obj))


def parse_line_string(string):
    raw_coords = map(float, string.strip().split())
    return MultiPolygon(
        Polygon([(lon, lat) for lat, lon in pairwise(raw_coords)])
    )


class InspireFormatDecoder(xml.Decoder):
    identifier = xml.Parameter("gmd:fileIdentifier/gco:CharacterString/text()", type=str, num=1)
    begin_time = xml.Parameter("gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:source/gmd:LI_Source/gmd:sourceExtent/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod/gml:beginPosition/text()", type=parse_iso8601, num=1)
    end_time = xml.Parameter("gmd:dataQualityInfo/gmd:DQ_DataQuality/gmd:lineage/gmd:LI_Lineage/gmd:source/gmd:LI_Source/gmd:sourceExtent/gmd:EX_Extent/gmd:temporalElement/gmd:EX_TemporalExtent/gmd:extent/gml:TimePeriod/gml:endPosition/text()", type=parse_iso8601, num=1)
    footprint = xml.Parameter("gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_BoundingPolygon/gmd:polygon/gml:LineString/gml:posList/text()", type=parse_line_string, num=1)

    namespaces = nsmap
