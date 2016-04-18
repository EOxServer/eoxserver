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
