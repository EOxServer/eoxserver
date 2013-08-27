from lxml import etree

from django.utils.dateparse import parse_datetime
from django.contrib.gis.geos import Polygon

from eoxserver.core.util.xmltools import parse, NameSpace, NameSpaceMap
from eoxserver.core.util.iteratortools import pairwise
from eoxserver.core import Component, implements
from eoxserver.core.decoders import xml
from eoxserver.resources.coverages.metadata.interfaces import (
    MetadataReaderInterface
)


NS_EOP = NameSpace("http://www.opengis.net/eop/2.0", "eop")
NS_OM = NameSpace("http://www.opengis.net/om/2.0", "om")
NS_GML = NameSpace("http://www.opengis.net/gml/3.2", "gml")
nsmap = NameSpaceMap(NS_EOP, NS_OM, NS_GML)


class EOOMFormatReader(Component):
    implements(MetadataReaderInterface)

    def test(self, obj):
        tree = parse(obj)
        return tree is not None and tree.tag == NS_EOP("EarthObservation")

    def read(self, obj):
        tree = parse(obj)
        if tree is not None:
            decoder = EOOMFormatDecoder(tree)
            return {
                "identifier": decoder.identifier,
                "begin_time": decoder.begin_time,
                "end_time": decoder.end_time,
                "footprint": decoder.footprint
            }
        raise Exception("Could not parse from obj '%s'." % repr(obj))


def parse_footprint_xml(elem):
    return Polygon(
        parse_ring(elem.findtext("gml:exterior/gml:LinearRing/gml:posList", namespaces=nsmap)),
        *map(lambda e: parse_ring(e.text), elem.findall("gml:interior/gml:LinearRing/gml:posList", namespaces=nsmap))
    )

def parse_ring(string):
    points = []
    raw_coords = map(float, string.split(" "))
    return [(lon, lat) for lat, lon in pairwise(raw_coords)]


class EOOMFormatDecoder(xml.Decoder):
    identifier = xml.Parameter("eop:metaDataProperty/eop:EarthObservationMetaData/eop:identifier/text()")
    begin_time = xml.Parameter("om:phenomenonTime/gml:TimePeriod/gml:beginPosition/text()", type=parse_datetime)
    end_time = xml.Parameter("om:phenomenonTime/gml:TimePeriod/gml:endPosition/text()", type=parse_datetime)
    footprint = xml.Parameter("om:featureOfInterest/eop:Footprint/eop:multiExtentOf/gml:MultiSurface/gml:surfaceMember/gml:Polygon", type=parse_footprint_xml)

    namespaces = nsmap
