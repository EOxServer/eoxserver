#!/usr/bin/python
#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2012 EOX IT Services GmbH
#
# Simple CLI tool to compare files with GDAL.
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

from osgeo import gdal
import re
import os.path
from sys import argv, exit
from datetime import datetime
from lxml import etree
from collections import namedtuple

from django.contrib.gis.geos import GEOSGeometry

from eoxserver.core import env
from eoxserver.processing.gdal.reftools import get_footprint_wkt
from eoxserver.resources.coverages.metadata.formats.gdal_dataset_envisat import (
    GDALDatasetEnvisatMetadataFormatReader
)
from eoxserver.services.gml.v32.encoders import EOP20Encoder


EOMetadata = namedtuple("EOMetadata", 
    ("identifier", "begin_time", "end_time", "footprint")
)

if __name__ == "__main__":
    try:
        path = argv[1]
    except IndexError:
        print "Requires filename"
        exit(1)

    reader = GDALDatasetEnvisatMetadataFormatReader(env)
    ds = gdal.Open(path)

    if not ds:
        print "Cannot open '%s' as GDAL Dataset." % path
        exit(1)
    elif not reader.test_ds(ds):
        print "Dataset '%s' does not contain required ENVISAT metadata." % path
        exit(1)
    
    md = reader.read_ds(ds)
    del ds

    footprint = GEOSGeometry(get_footprint_wkt(ds))
    footprint.srid = 4326

    encoder = EOP20Encoder()
    
    xml = encoder.serialize(
        encoder.encode_earth_observation(EOMetadata(footprint=footprint, **md))
    )
  
    with open(os.path.join(os.path.dirname(path))) as f:
        f.write(xml)
