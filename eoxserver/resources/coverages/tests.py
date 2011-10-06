#-----------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Fabian Schindler <fabian.schindler@eox.at>
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
#-----------------------------------------------------------------------

from eoxserver.core.system import System
from eoxserver.testing.core import BASE_FIXTURES
from eoxserver.resources.coverages.testbase import (
    RectifiedDatasetCreateTestCase, RectifiedDatasetUpdateTestCase,
    RectifiedDatasetDeleteTestCase, RectifiedStitchedMosaicCreateTestCase,
    RectifiedStitchedMosaicUpdateTestCase, RectifiedStitchedMosaicDeleteTestCase,
    DatasetSeriesCreateTestCase, DatasetSeriesUpdateTestCase,
    DatasetSeriesDeleteTestCase
)
from eoxserver.resources.coverages.geo import GeospatialMetadata
from eoxserver.resources.coverages.metadata import EOMetadata

from django.utils.datetime_safe import datetime
from django.contrib.gis.geos import GEOSGeometry
from django.conf import settings

import logging
import os.path

# create new rectified dataset from a local path

class DatasetCreateWithLocalPathTestCase(RectifiedDatasetCreateTestCase):
    def setUp(self):
        super(DatasetCreateWithLocalPathTestCase,self).setUp()
        args = {
            "local_path": os.path.join(settings.PROJECT_DIR,
                          "data/meris/MER_FRS_1P_reduced", 
                          "ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed.tif"),
            "range_type_name": "RGB",
        }
        self.wrapper = self.create(**args)

    def testContents(self):
        pass
    
# create new rectified dataset from a local path with metadata

class DatasetCreateWithLocalPathAndMetadataTestCase(RectifiedDatasetCreateTestCase):
    def setUp(self):
        super(DatasetCreateWithLocalPathAndMetadataTestCase, self).setUp()
        args = {
            "local_path": os.path.join(
                settings.PROJECT_DIR,
                "data/meris/MER_FRS_1P_reduced", 
                "ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed.tif"
            ),
            "range_type_name": "RGB",
            "md_local_path": os.path.join(
                settings.PROJECT_DIR,
                "data/meris/MER_FRS_1P_reduced", 
                "ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed.xml"
            )
        }
        self.wrapper = self.create(**args)

    def testContents(self):
        pass

# create new rectified dataset from a ftp path

class DatasetCreateWithRemothePathTestCase(RectifiedDatasetCreateTestCase):
    def setUp(self):
        super(DatasetCreateWithLocalPathAndMetadataTestCase, self).setUp()
        args = {
            "local_path": os.path.join(
                settings.PROJECT_DIR,
                "data/meris/MER_FRS_1P_reduced", 
                "ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed.tif"
            ),
            "range_type_name": "RGB",
            "md_local_path": os.path.join(
                settings.PROJECT_DIR,
                "data/meris/MER_FRS_1P_reduced", 
                "ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed.xml"
            )
        }
        self.wrapper = self.create(**args)


# create new rectified dataset from a rasdaman location 

class DatasetCreateWithRasdamanLocationTestCase(RectifiedDatasetCreateTestCase):
    def setUp(self):
        super(DatasetCreateWithRasdamanLocationTestCase, self).setUp()
        args = {
            "collection": "MERIS",
            "oid": 9217,
            "ras_host": "localhost",
            "range_type_name": "RGB",
            "geo_metadata": GeospatialMetadata(
                srid=4326,
                size_x=541,
                size_y=449,
                extent=(11.331755,32.19025,28.29481,46.268645)
            ),
            "md_local_path": os.path.join(
                settings.PROJECT_DIR,
                "data/meris/MER_FRS_1P_reduced", 
                "ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed.xml"
            )
        }
        self.wrapper = self.create(**args)

    def testType(self):
        self.assertEqual(self.wrapper.getType(), "eo.rect_dataset")
    
    

# create new mosaic and add a local path to locations

class MosaicCreateWithLocalPathTestCase(RectifiedStitchedMosaicCreateTestCase):
    def setUp(self):
        super(MosaicCreateWithLocalPathTestCase,self).setUp()
        args = {
            "data_dirs": [{
                "path": os.path.join(settings.PROJECT_DIR,
                                     "data/meris/MER_FRS_1P_reduced"),
                "search_pattern": "*.tif",
                "type": "local"
            }],
            "geo_metadata": GeospatialMetadata(
                srid=4326, size_x=100, size_y=100,
                extent=(1, 2, 3, 4)
            ),
            "range_type_name": "RGB",
            "eo_metadata": EOMetadata(
                "SOMEEOID",
                datetime.now(),
                datetime.now(),
                GEOSGeometry("POLYGON((1 2, 3 2, 3 4, 1 4, 1 2))")
            ),
            "storage_dir": "/some/storage/dir"
        }
        self.wrapper = self.create(**args)
        
    def testContents(self):
        # test the number of datasets
        self.assertEqual(len(self.wrapper.getDatasets()), 3)
        
        # test validity of datasets


# create new mosaic and add a remote path to locations
class MosaicCreateWithRemotePathTestCase(RectifiedStitchedMosaicCreateTestCase):
    def setUp(self):
        super(MosaicCreateWithRemotePathTestCase,self).setUp()
        args = {
            "data_dirs": [{
                "path": "test/MER_FRS_1P_reduced",
                "search_pattern": "*.tif",
                "type": "ftp",
                
                "host": "hma.eox.at",
                "user": "anonymous",
                "password": ""
            }],
            "geo_metadata": GeospatialMetadata(
                srid=4326, size_x=100, size_y=100,
                extent=(1, 2, 3, 4)
            ),
            "range_type_name": "RGB",
            "eo_metadata": EOMetadata(
                "SOMEEOID",
                datetime.now(),
                datetime.now(),
                GEOSGeometry("POLYGON((1 2, 3 2, 3 4, 1 4, 1 2))")
            ),
            "storage_dir": "/some/storage/dir"
        }
        self.wrapper = self.create(**args)
        
    def testContents(self):
        self.assertEqual(len(self.wrapper.getDatasets()), 3)

# create new mosaic and add a rasdaman location to locations

class MosaicCreateWithRasdamanLocationTestCase(RectifiedStitchedMosaicCreateTestCase):
    def setUp(self):
        super(MosaicCreateWithRasdamanLocationTestCase, self).setUp()
        args = {
            "data_dirs": [{
                "type": "rasdaman",
                "host": "localhost",
                "collection": "MERIS",
                "oid": 9217,
            }],
            "geo_metadata": GeospatialMetadata(
                srid=4326, size_x=100, size_y=100,
                extent=(1, 2, 3, 4)
            ),
            "range_type_name": "RGB",
            "eo_metadata": EOMetadata(
                "SOMEEOID",
                datetime.now(),
                datetime.now(),
                GEOSGeometry("POLYGON((1 2, 3 2, 3 4, 1 4, 1 2))")
            ),
            "storage_dir": "/some/storage/dir"
        }
        self.wrapper = self.create(**args)
        
        
    def testContents(self):
        pass

# create dataset series with a local path

class DatasetSeriesCreateWithLocalPathTestCase(DatasetSeriesCreateTestCase):
    fixtures = BASE_FIXTURES
    
    def setUp(self):
        super(DatasetSeriesCreateWithLocalPathTestCase,self).setUp()
        args = {
            "data_dirs": [{
                "path": os.path.join(settings.PROJECT_DIR,
                                     "data/meris/MER_FRS_1P_reduced"),
                "search_pattern": "*.tif",
                "type": "local"
            }],
            "eo_metadata": EOMetadata(
                "SOMEEOID",
                datetime.now(),
                datetime.now(),
                GEOSGeometry("POLYGON((1 2, 3 2, 3 4, 1 4, 1 2))")
            ),
        }
        self.wrapper = self.create(**args)
        
    def testContents(self):
        self.assertEqual(len(self.wrapper.getEOCoverages()), 3)
        

# create dataset series with a remote path

# alter dataset series to remove a location

class DatasetSeriesRemoveLocationTestCase(DatasetSeriesUpdateTestCase):
    fixtures = BASE_FIXTURES + ["testing_coverages.json"]
    
    def setUp(self):
        super(DatasetSeriesRemoveLocationTestCase,self).setUp()
    
    def testContents(self):
        pass

