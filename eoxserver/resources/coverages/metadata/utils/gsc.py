# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# ------------------------------------------------------------------------------

from django.contrib.gis.geos import Polygon, MultiPolygon

from eoxserver.core.util.timetools import parse_iso8601
from eoxserver.core.util.xmltools import NameSpace, NameSpaceMap
from eoxserver.core.util.iteratortools import pairwise
from eoxserver.core.decoders import xml


NS_GSC = NameSpace("http://earth.esa.int/gsc", "gsc")
NS_EOP = NameSpace("http://earth.esa.int/eop", "eop")
NS_OPT = NameSpace("http://earth.esa.int/opt", "opt")
NS_SAR = NameSpace("http://earth.esa.int/sar", "sar")
NS_ATM = NameSpace("http://earth.esa.int/atm", "atm")
NS_GML = NameSpace("http://www.opengis.net/gml", "gml")

nsmap = NameSpaceMap(NS_GML, NS_GSC, NS_EOP, NS_OPT, NS_SAR, NS_ATM)
nsmap_gml = NameSpaceMap(NS_GML)


def parse_ring(string):
    raw_coords = [float(v) for v in string.split()]
    return [(lon, lat) for lat, lon in pairwise(raw_coords)]


def parse_polygon_xml(elem):
    return Polygon(
        parse_ring(
            elem.xpath(
                "gml:exterior/gml:LinearRing/gml:posList", namespaces=nsmap_gml
            )[0].text.strip()
        ), *[
            parse_ring(poslist_elem.text.strip())
            for poslist_elem in elem.xpath(
                "gml:interior/gml:LinearRing/gml:posList", namespaces=nsmap_gml
            )
        ]
    )


class GSCFormatDecoder(xml.Decoder):
    namespaces = nsmap

    identifier = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:metaDataProperty/gsc:EarthObservationMetaData/eop:identifier/text()", type=str, num=1)
    begin_time = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:validTime/gml:TimePeriod/gml:beginPosition/text()", type=parse_iso8601, num=1)
    end_time = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:validTime/gml:TimePeriod/gml:endPosition/text()", type=parse_iso8601, num=1)
    polygons = xml.Parameter("(gsc:sar_metadata|gsc:opt_metadata)/gml:target/eop:Footprint/gml:multiExtentOf/gml:MultiSurface/gml:surfaceMembers/gml:Polygon", type=parse_polygon_xml, num="+")

    @property
    def footprint(self):
        return MultiPolygon(*self.polygons)
