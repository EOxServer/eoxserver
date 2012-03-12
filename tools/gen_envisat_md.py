#!/usr/bin/python

from osgeo import gdal
import re
import os.path
from sys import argv
from datetime import datetime
from django.contrib.gis.geos import GEOSGeometry
from eoxserver.core.system import System
from eoxserver.core.util.xmltools import XMLDecoder, DOMElementToXML
from eoxserver.core.util.timetools import getDateTime, isotime
from eoxserver.processing.gdal.reftools import get_footprint_wkt
from eoxserver.services.ows.wcs.encoders import GMLEncoder

class EOPEncoder(GMLEncoder):
    def _initializeNamespaces(self):
        ns_dict = super(EOPEncoder, self)._initializeNamespaces()
        ns_dict.update({
            "om": "http://www.opengis.net/om/2.0",
            "eop": "http://www.opengis.net/eop/2.0"
        })
        return ns_dict

    def encodeFootprint(self, footprint, eo_id):
        return self._makeElement(
            "eop", "Footprint", [
                ("@gml", "id", "footprint_%s" % eo_id),
                ("eop", "multiExtentOf", [
                    (self.encodeMultiPolygon(footprint, eo_id),)
                ])
            ]
        )
    
    def encodeMetadataProperty(self, eo_id):
        sub_elements =  [
            ("eop", "identifier", eo_id),
            ("eop", "acquisitionType", "NOMINAL"), # TODO
            ("eop", "status", "ARCHIVED") # TODO
        ]
        
        return self._makeElement(
            "eop", "metaDataProperty", [
                ("eop", "EarthObservationMetaData", sub_elements)
            ]
        )

    def encodeEarthObservation(self, eo_id, begin_time, end_time, footprint):
        begin_time_iso = isotime(begin_time)
        end_time_iso = isotime(end_time)
        result_time_iso = isotime(end_time)

        return self._makeElement(
            "eop", "EarthObservation", [
                ("@gml", "id", "eop_%s" % eo_id),
                ("om", "phenomenonTime", [
                    ("gml", "TimePeriod", [
                        ("@gml", "id", "phen_time_%s" % eo_id),
                        ("gml", "beginPosition", begin_time_iso),
                        ("gml", "endPosition", end_time_iso)
                    ])
                ]),
                ("om", "resultTime", [
                    ("gml", "TimeInstant", [
                        ("@gml", "id", "res_time_%s" % eo_id),
                        ("gml", "timePosition", result_time_iso)
                    ])
                ]),
                ("om", "procedure", []),
                ("om", "observedProperty", []),
                ("om", "featureOfInterest", [
                    (self.encodeFootprint(footprint, eo_id),)
                ]),
                ("om", "result", []),
                (self.encodeMetadataProperty(eo_id),)
            ]
        )
        
def parse_timestamp(timestamp):
    MONTHS = {
        "JAN": 1,
        "FEB": 2,
        "MAR": 3,
        "APR": 4,
        "MAY": 5,
        "JUN": 6,
        "JUL": 7,
        "AUG": 8,
        "SEP": 9,
        "OCT": 10,
        "NOV": 11,
        "DEC": 12
    }
    
    m = re.match(r"(\d{2})-([A-Z]{3})-(\d{4}) (\d{2}):(\d{2}):(\d{2}).*", timestamp)
    day = int(m.group(1))
    month = MONTHS[m.group(2)]
    year = int(m.group(3))
    hour = int(m.group(4))
    minute = int(m.group(5))
    second = int(m.group(6))
    
    return datetime(year, month, day, hour, minute, second)

if __name__=="__main__":
    path = argv[1]

    ds = gdal.Open(path)
    
    eo_id = os.path.splitext(os.path.basename(path))[0]
    begin_time = parse_timestamp(ds.GetMetadataItem("MPH_SENSING_START"))
    end_time = parse_timestamp(ds.GetMetadataItem("MPH_SENSING_STOP"))
    
    del ds

    footprint = GEOSGeometry(get_footprint_wkt(path))
    footprint.srid = 4326

    encoder = EOPEncoder()  
    
    xml = DOMElementToXML(
        encoder.encodeEarthObservation(
            eo_id,
            begin_time,
            end_time,
            footprint
        )
    )
  
    xml_file = open(os.path.join(os.path.dirname(path), "%s.xml" % eo_id), "w")
    xml_file.write(xml)
    xml_file.close()
