#-------------------------------------------------------------------------------
# $Id$
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
from itertools import chain 

from django.utils.dateparse import parse_datetime
from django.contrib.gis.geos import Polygon, MultiPolygon

from eoxserver.core.util.xmltools import parse, NameSpace, NameSpaceMap
from eoxserver.core.util.iteratortools import pairwise
from eoxserver.core import Component, implements
from eoxserver.core.decoders import xml
from eoxserver.resources.coverages.metadata.interfaces import (
    MetadataReaderInterface
)

from eoxserver.resources.coverages import crss  


NS_EOP = NameSpace("http://www.opengis.net/eop/2.0", "eop")
NS_OPT = NameSpace("http://www.opengis.net/opt/2.0", "opt")
NS_SAR = NameSpace("http://www.opengis.net/sar/2.0", "sar")
NS_ATM = NameSpace("http://www.opengis.net/atm/2.0", "atm")
NS_ALT = NameSpace("http://www.opengis.net/alt/2.0", "alt")
NS_LMB = NameSpace("http://www.opengis.net/lmb/2.0", "lmb")
NS_SSP = NameSpace("http://www.opengis.net/ssp/2.0", "atm")
NS_OM = NameSpace("http://www.opengis.net/om/2.0", "om")
NS_GML = NameSpace("http://www.opengis.net/gml/3.2", "gml")
nsmap = NameSpaceMap(NS_EOP, NS_OM, NS_GML)


class EOOMFormatReader(Component):
    implements(MetadataReaderInterface)

    def test(self, obj):
        tree = parse(obj)
        if tree is None : return False 
        if isinstance(tree,etree._ElementTree):
            tree = tree.getroot() ; 
        return tree.tag == NS_EOP("EarthObservation")

    def read(self, obj):
        tree = parse(obj)
        if tree is not None:
            decoder = EOOMFormatDecoder(tree)
            return {
                "identifier": decoder.identifier,
                "begin_time": decoder.begin_time,
                "end_time": decoder.end_time,
                "footprint": decoder.footprint,
                "vmasks": filter( lambda v: v is not None, decoder.vmasks ), 
                "format": "eogml",
            }
        raise Exception("Could not parse from obj '%s'." % repr(obj))


def parse_vector_mask( elem ): 

    type = elem.xpath("eop:type/text()",namespaces=nsmap)[0]
    subtype = (elem.xpath("eop:subType/text()",namespaces=nsmap) or (None,))[0]
    format = elem.xpath("eop:format/text()",namespaces=nsmap)[0]
    tmp = (elem.xpath("eop:multiExtentOf/gml:MultiSurface",namespaces=nsmap) or (None,))[0]

    if ( format == "VECTOR" ) and (tmp is not None) : 
        mask = parse_multisurf_gml(tmp)

        return { "type": type, "subtype":subtype, "mask":mask } 


def parse_srs_name( srs_name ): 
    if not srs_name : return None 
    return crss.parseEPSGCode( srs_name , 
        ( crss.fromShortCode, crss.fromURN, crss.fromURL ) )

def parse_multisurf_gml(elem,srid=None):
    if not srid : srid = parse_srs_name( elem.get("srsName") ) 
    return MultiPolygon(
        *(( parse_polygon_gml(e,srid) for e in 
                elem.xpath("gml:surfaceMember/gml:Polygon",namespaces=nsmap) 
         )), srid=srid
    )

def parse_polygon_gml(elem,srid=None):
    if not srid : srid = parse_srs_name( elem.get("srsName") ) 
    return Polygon(
        *(( parse_list_gml(e.text,srid) for e in chain( 
                elem.xpath("gml:exterior/gml:LinearRing/gml:posList",namespaces=nsmap)[:1],
                elem.xpath("gml:interior/gml:LinearRing/gml:posList",namespaces=nsmap) )
         )), srid=srid 
    )

def parse_list_gml(string,srid):
    pairs = pairwise( float(v) for v in string.split(" ") )
    if crss.hasSwappedAxes_slow(srid) : 
        return list( (y,x) for x,y in pairs ) 
    else :
        return list( pairs )

class EOOMFormatDecoder(xml.Decoder):
    identifier = xml.Parameter("eop:metaDataProperty/eop:EarthObservationMetaData/eop:identifier/text()", type=str, num=1)
    begin_time = xml.Parameter("om:phenomenonTime/gml:TimePeriod/gml:beginPosition/text()", type=parse_datetime, num=1)
    end_time = xml.Parameter("om:phenomenonTime/gml:TimePeriod/gml:endPosition/text()", type=parse_datetime, num=1)
    footprint = xml.Parameter("om:featureOfInterest/eop:Footprint/eop:multiExtentOf/gml:MultiSurface",type=parse_multisurf_gml, num=1)
    vmasks = xml.Parameter("om:result//eop:mask/eop:MaskInformation",type=parse_vector_mask, num="*")
    
    namespaces = nsmap
