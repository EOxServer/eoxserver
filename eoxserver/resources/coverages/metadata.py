#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
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

from xml.dom import minidom

from eoxserver.core.util.xmltools import XMLDecoder
from eoxserver.core.util.timetools import getDateTime
from eoxserver.core.util.geotools import posListToWkt
from eoxserver.resources.coverages.exceptions import MetadataException

class MetadataInterface(object):
    
    def getEOID(self):
        return None

    def getBeginTime(self):
        return None
    
    def getEndTime(self):
        return None
    
    def getFootprint(self):
        return None
    
    def getMetadataFormat(self):
        return None

class XMLMetadataInterface(MetadataInterface):
    PARAM_SCHEMA = {}
    
    def __init__(self, xml):
        self.decoder = XMLDecoder(xml, self.PARAM_SCHEMA)
        self.xml_text = xml
    
    def getEOID(self):
        return self.decoder.getValue("eoid")
        
    def getBeginTime(self):
        return getDateTime(self.decoder.getValue("begintime"))
    
    def getEndTime(self):
        return getDateTime(self.decoder.getValue("endtime"))
    
    def getFootprint(self):
        polygon_dicts = self.decoder.getValue("footprint")
        
        polygon_wkts = []
        for polygon_dict in polygon_dicts:
            exterior_wkt = "(%s)" % posListToWkt(polygon_dict["exterior_ring"])
            interior_wkts = ["(%s)" % posListToWkt(interior_ring) for interior_ring in polygon_dict["interior_rings"]]
            
            if len(interior_wkts) == 0:
                polygon_wkts.append("(%s)" % exterior_wkt)
            else:
                polygon_wkts.append("(%s,%s)" % (exterior_wkt, ",".join(interior_wkts)))
        
        if len(polygon_wkts) == 1:
            wkt = "POLYGON%s" % polygon_wkts[0]
        elif len(polygon_wkts) == 0:
            wkt = ""
        else:
            wkt = "MULTIPOLYGON(%s)" % ",".join(polygon_wkts)
        
        return wkt
    
    def getXMLText(self):
        return self.xml_text
    

class NativeMetadataInterface(XMLMetadataInterface):
    PARAM_SCHEMA = {
        "eoid": {"xml_location": "/EOID", "xml_type": "string"},
        "begintime": {"xml_location": "/BeginTime", "xml_type": "string"},
        "endtime": {"xml_location": "/EndTime", "xml_type": "string"},
        "footprint": {"xml_location": "/Footprint/Polygon", "xml_type": "dict[1:]", "xml_dict_elements": {
            "exterior_ring": {"xml_location": "Exterior", "xml_type": "floatlist"},
            "interior_rings": {"xml_location": "Interior", "xml_type": "floatlist[]"}
        }}
    }

    def getMetadataFormat(self):
        return "native" 

class DIMAPMetadataInterface(XMLMetadataInterface):
    def getMetadataFormat(self):
        return "dimap" 
    
class EOGMLMetadataInterface(XMLMetadataInterface):
    PARAM_SCHEMA = {
        "eoid": {"xml_location": "/eop:metaDataProperty/eop:EarthObservationMetaData/eop:identifier", "xml_type": "string"},
        "begintime": {"xml_location": "/om:phenomenonTime/gml:TimePeriod/gml:beginPosition", "xml_type": "string"},
        "endtime": {"xml_location": "/om:phenomenonTime/gml:TimePeriod/gml:endPosition", "xml_type": "string"},
        "footprint": {"xml_location": "/om:featureOfInterest/eop:Footprint/eop:multiExtentOf/gml:MultiSurface/gml:surfaceMember/gml:Polygon", "xml_type": "dict[1:]", "xml_dict_elements": {
            "exterior_ring": {"xml_location": "gml:exterior/gml:LinearRing/gml:posList", "xml_type": "floatlist"},
            "interior_rings": {"xml_location": "gml:interior/gml:LinearRing/gml:posList", "xml_type": "floatlist[]"}
        }}
    }
    
    def getMetadataFormat(self):
        return "eogml" 

class MetadataInterfaceFactory(object):
    @classmethod
    def getMetadataInterface(cls, xml, format):
        if format.lower() == "native":
            return NativeMetadataInterface(xml)
        elif format.lower() == "dimap":
            return DIMAPMetadataInterface(xml)
        elif format.lower() == "eogml":
            return EOGMLMetadataInterface(xml)
        else:
            raise MetadataException("Unknown metadata format '%s'" % format)

    @classmethod
    def getMetadataInterfaceForFile(cls, filename, format=None):
        try:
            f = open(filename)
        except:
            raise MetadataException("Could not open file '%s'" % filename)
        
        xml = f.read()
        f.close()
        
        if format is None:
            used_format = cls._detectFormat(xml)
        else:
            used_format = format
        
        return cls.getMetadataInterface(xml, used_format)
        
    @classmethod
    def _detectFormat(cls, xml):
        DETECTION_SCHEMA = {
            "root_name": {"xml_location": "/", "xml_type": "localName"}
        }
    
        decoder = XMLDecoder(xml, DETECTION_SCHEMA)
        
        root_name = decoder.getValue("root_name")
        
        if root_name == "Metadata":
            return "native"
        elif root_name == "EarthObservation":
            return "eogml"
        elif root_name == "...":
            return "dimap"
        else:
            raise MetadataException("Unknown metadata format.")
