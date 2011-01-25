#-----------------------------------------------------------------------
#
# This software is named EOxServer, a server for Earth Observation data.
#
# Copyright (C) 2011 EOX IT Services GmbH
# Authors: Stephan Krause, Stephan Meissl
#
# This file is part of EOxServer <http://www.eoxserver.org>.
#
#    EOxServer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License,
#    or (at your option) any later version.
#
#    EOxServer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with EOxServer. If not, see <http://www.gnu.org/licenses/>.
#
#-----------------------------------------------------------------------

from xml.dom import minidom

from eoxserver.lib.exceptions import EOxSMetadataException, EOxSXMLException
from eoxserver.lib.util import EOxSXMLDecoder, getDateTime, posListToWkt

class EOxSMetadataInterface(object):
    def __init__(self, filename):
        super(EOxSMetadataInterface, self).__init__()
        
        self.filename = filename
    
    def getEOID(self):
        return None

    def getBeginTime(self):
        return None
    
    def getEndTime(self):
        return None
    
    def getFootprint(self):
        return None

class EOxSXMLMetadataInterface(EOxSMetadataInterface):
    PARAM_SCHEMA = {}
    
    def __init__(self, filename):
        super(EOxSXMLMetadataInterface, self).__init__(filename)
        
        try:
            f = open(filename)
        except:
            raise EOxSMetadataException("Could not open file '%s'" % filename)
        
        xml = f.read()
        f.close()
        
        self.decoder = EOxSXMLDecoder(xml, self.PARAM_SCHEMA)

class EOxSNativeMetadataInterface(EOxSXMLMetadataInterface):
    PARAM_SCHEMA = {
        "eoid": {"xml_location": "/EOID", "xml_type": "string"},
        "begintime": {"xml_location": "/BeginTime", "xml_type": "string"},
        "endtime": {"xml_location": "/EndTime", "xml_type": "string"},
        "footprint": {"xml_location": "/Footprint/Polygon", "xml_type": "dict[1:]", "xml_dict_elements": {
            "exterior_ring": {"xml_location": "Exterior", "xml_type": "floatlist"},
            "interior_rings": {"xml_location": "Interior", "xml_type": "floatlist[]"}
        }}
    }

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
        else:
            wkt = "MULTIPOLYGON(%s)" % ",".join(polygon_wkts)
        
        return wkt

class EOxSDIMAPMetadataInterface(EOxSXMLMetadataInterface):
    pass
    
class EOxSEOGMLMetadataInterface(EOxSXMLMetadataInterface):
    pass
    
class EOxSMetadataInterfaceFactory(object):
    @classmethod
    def getMetadataInterface(cls, filename, format):
        if format.lower() == "native":
            return EOxSNativeMetadataInterface(filename)
        elif format.lower() == "dimap":
            return EOxSDIMAPMetadataInterface(filename)
        elif format.lower() == "eogml":
            return EOxSEOGMLMetadataInterface(filename)
        else:
            raise EOxSMetadataException("Unknown metadata format '%s'" % format)

