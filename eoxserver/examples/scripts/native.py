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

import os.path

from eoxserver.server.models import (
    EOxSRectifiedDatasetSeriesRecord, EOxSRectifiedStitchedMosaicRecord
)
from eoxserver.lib.util import EOxSXMLEncoder, EOxSXMLDecoder, isotime, findFiles

class EOxSNativeEncoder(EOxSXMLEncoder):
    def encodePolygon(self, polygon):
        pos_list = " ".join(["%f %f" % (point[0], point[1]) for point in polygon[0]])
        
        return self._makeElement(
            "", "Polygon", [
                ("", "Exterior", pos_list)
            ]
        )
    
    def encodeEOMetadata(self, eo_id, eo_metadata):
        return self._makeElement(
            "", "Metadata", [
                ("", "EOID", eo_id),
                ("", "BeginTime", isotime(eo_metadata.timestamp_begin)),
                ("", "EndTime", isotime(eo_metadata.timestamp_end)),
                ("", "Footprint", [
                    (self.encodePolygon(eo_metadata.footprint),)
                ])
            ]
        )
    
    def encodeCRMetadata(self, eo_id, begin_time, end_time, pos_list):
        return self._makeElement(
            "", "Metadata", [
                ("", "EOID", eo_id),
                ("", "BeginTime", begin_time),
                ("", "EndTime", end_time),
                ("", "Footprint", [
                    ("", "Polygon", [
                        ("", "Exterior", pos_list)
                    ])
                ])
            ]
        )

def generateMetadataFilesFromRecords(eo_id, target_dir):
    try:
        wcseo_object = EOxSRectifiedDatasetSeriesRecord.objects.get(eo_id=eo_id)
    except:
        wcseo_object = EOxSRectifiedStitchedMosaicRecord.objects.get(eo_id=eo_id)
    
    encoder = EOxSNativeEncoder()
    
    for dataset in wcseo_object.rect_datasets.all():
        md_el = encoder.encodeEOMetadata(dataset.eo_id, dataset.eo_metadata)
        
        md_filename = "%s.%s" % (os.path.splitext(os.path.basename(dataset.file.path))[0], "xml")
        f = open(os.path.join(target_dir, md_filename), 'w')
        f.write(md_el.toxml())
        f.close()

GSC_SCHEMA = {
    "begintime": {"xml_location": "/gsc:opt_metadata/gml:validTime/gml:TimePeriod/gml:beginPosition", "xml_type": "string"},
    "endtime": {"xml_location": "/gsc:opt_metadata/gml:validTime/gml:TimePeriod/gml:endPosition", "xml_type": "string"},
    "poslist": {"xml_location": "/gsc:opt_metadata/gml:target/eop:Footprint/gml:multiExtentOf/gml:MultiSurface/gml:surfaceMembers/gml:Polygon/gml:exterior/gml:LinearRing/gml:posList", "xml_type": "floatlist"}
}

def generateMetadataFilesFromCR(src_dir, target_dir, eo_id_prefix, eo_id_suffix):
    cr_filenames = findFiles(src_dir, "*.xml")
    for cr_filename in cr_filenames:
        g = open(cr_filename)
        cr = g.read()
        g.close()
        
        decoder = EOxSXMLDecoder(cr, GSC_SCHEMA)
        
        eo_id = "%s%s%s" % (eo_id_prefix, os.path.splitext(os.path.basename(cr_filename))[0], eo_id_suffix)
        begin_time = decoder.getValue("begintime")
        end_time = decoder.getValue("endtime")
        
        positions = decoder.getValue("poslist")
        new_positions = [positions[i + 1 - 2 * (i % 2)] for i in range(0, len(positions))]
        pos_list = " ".join([str(f) for f in new_positions])
        
        encoder = EOxSNativeEncoder()
        
        md_el = encoder.encodeCRMetadata(eo_id, begin_time, end_time, pos_list)
        
        md_filename = "%s.%s" % (eo_id, "xml")
        f = open(os.path.join(target_dir, md_filename), 'w')
        f.write(md_el.toxml())
        f.close()
