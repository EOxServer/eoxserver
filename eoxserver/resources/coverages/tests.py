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

import os.path
import shutil
import logging
from datetime import timedelta

from django.utils.datetime_safe import datetime
from django.contrib.gis.geos import GEOSGeometry
from django.conf import settings

from eoxserver.core.system import System
from eoxserver.testing.core import BASE_FIXTURES
from eoxserver.resources.coverages.testbase import (
    RectifiedDatasetCreateTestCase, RectifiedDatasetUpdateTestCase,
    RectifiedDatasetDeleteTestCase, RectifiedStitchedMosaicCreateTestCase,
    RectifiedStitchedMosaicUpdateTestCase, RectifiedStitchedMosaicDeleteTestCase,
    RectifiedStitchedMosaicSynchronizeTestCase, 
    DatasetSeriesCreateTestCase, DatasetSeriesUpdateTestCase,
    DatasetSeriesDeleteTestCase, DatasetSeriesSynchronizeTestCase,
    CoverageIdManagementTestCase, EXTENDED_FIXTURES
)
from eoxserver.resources.coverages.geo import GeospatialMetadata
from eoxserver.resources.coverages.metadata import EOMetadata
import eoxserver.resources.coverages.exceptions as exceptions

# create new rectified dataset from a local path

class DatasetCreateWithLocalPathTestCase(RectifiedDatasetCreateTestCase):
    def manage(self):
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
    def manage(self):
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

class DatasetCreateWithContainerTestCase(RectifiedDatasetCreateTestCase):
    fixtures = BASE_FIXTURES
    
    def _create_containers(self):
        mosaic_mgr = System.getRegistry().findAndBind(
            intf_id="resources.coverages.interfaces.Manager",
            params={
                "resources.coverages.interfaces.res_type": "eo.rect_stitched_mosaic"
            }
        )
        
        self.stitched_mosaic = mosaic_mgr.create(**{
            "data_dirs": [],
            "geo_metadata": GeospatialMetadata(
                srid=4326, size_x=100, size_y=100,
                extent=(1, 2, 3, 4)
            ),
            "range_type_name": "RGB",
            "eo_metadata": EOMetadata(
                "STITCHED_MOSAIC",
                datetime.now(),
                datetime.now(),
                GEOSGeometry("POLYGON((1 2, 3 2, 3 4, 1 4, 1 2))")
            ),
            "storage_dir": "/some/storage/dir"
        })
        
    def manage(self):
        self._create_containers()
        args = {
            "local_path": os.path.join(settings.PROJECT_DIR,
                          "data/meris/MER_FRS_1P_reduced", 
                          "ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed.tif"),
            "range_type_name": "RGB",
            "container": self.stitched_mosaic
        }
        self.wrapper = self.create(**args)

    def testContents(self):
        self.assertTrue(self.stitched_mosaic.contains(self.wrapper.getModel().pk), 
                        "Stitched Mosaic has to contain the dataset.")
    
class DatasetCreateWithContainerIDsTestCase(RectifiedDatasetCreateTestCase):
    fixtures = BASE_FIXTURES
    
    def _create_containers(self):
        dss_mgr = System.getRegistry().findAndBind(
            intf_id="resources.coverages.interfaces.Manager",
            params={
                "resources.coverages.interfaces.res_type": "eo.dataset_series"
            }
        )
        
        mosaic_mgr = System.getRegistry().findAndBind(
            intf_id="resources.coverages.interfaces.Manager",
            params={
                "resources.coverages.interfaces.res_type": "eo.rect_stitched_mosaic"
            }
        )
        
        self.dataset_series = dss_mgr.create(**{
            "data_dirs": [],
            "eo_metadata": EOMetadata(
                "DATASET_SERIES",
                datetime.now(),
                datetime.now(),
                GEOSGeometry("POLYGON((1 2, 3 2, 3 4, 1 4, 1 2))")
            )
        })
        
        self.stitched_mosaic = mosaic_mgr.create(**{
            "data_dirs": [],
            "geo_metadata": GeospatialMetadata(
                srid=4326, size_x=100, size_y=100,
                extent=(1, 2, 3, 4)
            ),
            "range_type_name": "RGB",
            "eo_metadata": EOMetadata(
                "STITCHED_MOSAIC",
                datetime.now(),
                datetime.now(),
                GEOSGeometry("POLYGON((1 2, 3 2, 3 4, 1 4, 1 2))")
            ),
            "storage_dir": "/some/storage/dir"
        })
    
    def manage(self):
        self._create_containers()
        args = {
            "local_path": os.path.join(settings.PROJECT_DIR,
                          "data/meris/MER_FRS_1P_reduced", 
                          "ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed.tif"),
            "range_type_name": "RGB",
            "container_ids": [self.stitched_mosaic.getCoverageId(), self.dataset_series.getEOID()]
        }
        self.wrapper = self.create(**args)

    def testContents(self):
        self.assertTrue(self.stitched_mosaic.contains(self.wrapper.getModel().pk), 
                        "Stitched Mosaic has to contain the dataset.")
        
        self.assertTrue(self.dataset_series.contains(self.wrapper.getModel().pk), 
                        "Dataset Series has to contain the dataset.")

# create new rectified dataset from a ftp path

class DatasetCreateWithRemothePathTestCase(RectifiedDatasetCreateTestCase):
    def manage(self):
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
    def manage(self):
        args = {
            "collection": "MERIS",
            "ras_host": "localhost",
            "range_type_name": "RGB",
            "geo_metadata": GeospatialMetadata(
                srid=4326,
                size_x=541,
                size_y=449,
                extent=(11.331755, 32.19025, 28.29481, 46.268645)
            ),
            "md_local_path": os.path.join(
                settings.PROJECT_DIR,
                "data/meris/mosaic_MER_FRS_1P_RGB_reduced", 
                "mosaic_ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced.xml"
            )
        }
        self.wrapper = self.create(**args)

    def testType(self):
        self.assertEqual(self.wrapper.getType(), "eo.rect_dataset")
    
    

# create new mosaic and add a local path to locations

class MosaicCreateWithLocalPathTestCase(RectifiedStitchedMosaicCreateTestCase):
    def manage(self):
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
    def manage(self):
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
    def manage(self):
        args = {
            "data_dirs": [{
                "type": "rasdaman",
                "host": "localhost",
                "collection": "MERIS"
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

# create dataset series with a local path

class DatasetSeriesCreateWithLocalPathTestCase(DatasetSeriesCreateTestCase):
    fixtures = BASE_FIXTURES
    
    def manage(self):
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
            )
        }
        self.wrapper = self.create(**args)
        
    def testContents(self):
        self.assertEqual(len(self.wrapper.getEOCoverages()), 3)
        

# create dataset series with a remote path

# alter dataset series to remove a location

class DatasetSeriesRemoveLocationTestCase(DatasetSeriesUpdateTestCase):
    fixtures = EXTENDED_FIXTURES
    
    def manage(self):
        pass
    
    def testContents(self):
        pass

class DatasetSeriesSynchronizeNewDirectoryTestCase(DatasetSeriesSynchronizeTestCase):
    fixtures = BASE_FIXTURES
    
    def manage(self):
        # create an empty series, with an unsynchronized data source
        datasource_factory = System.getRegistry().bind(
            "resources.coverages.data.DataSourceFactory"
        )
        location_factory = System.getRegistry().bind(
            "backends.factories.LocationFactory"
        )
        
        dataset_series_factory = System.getRegistry().bind(
            "resources.coverages.wrappers.DatasetSeriesFactory"
        )
        
        # this code should not be duplicated; intentionally misused ;)
        self.wrapper = dataset_series_factory.create(
            impl_id="resources.coverages.wrappers.DatasetSeriesWrapper",
            params={
                "data_sources": [datasource_factory.create(
                    type="data_source",
                    **{
                        "location": location_factory.create(
                            **{
                                "path": os.path.join(settings.PROJECT_DIR,
                                                     "data/meris/MER_FRS_1P_reduced"),
                                "type": "local"
                            }
                        ),
                       "search_pattern": "*.tif"
                    }
                )],
                "eo_metadata": EOMetadata(
                    "SOMEEOID",
                    datetime.now(),
                    datetime.now(),
                    GEOSGeometry("POLYGON((1 2, 3 2, 3 4, 1 4, 1 2))")
                )
            }
        )
        
        self.synchronize(self.wrapper.getEOID())
    
    def testContents(self):
        # after sync, the datasets shall be registered.
        self.assertEqual(len(self.wrapper.getEOCoverages()), 3)

class DatasetSeriesSynchronizeFileRemovedTestCase(DatasetSeriesSynchronizeTestCase):
    fixtures = BASE_FIXTURES
    
    def _create_files(self):
        src = os.path.join(settings.PROJECT_DIR, 
                           "data/meris/mosaic_MER_FRS_1P_RGB_reduced")
        
        self.dst = os.path.join(settings.PROJECT_DIR,
                                "data/meris/TEMPORARY_mosaic_MER_FRS_1P_RGB_reduced")
        shutil.copytree(src, self.dst)
        
    def manage(self):
        self._create_files()
        
        args = {
            "data_dirs": [{
                "path": os.path.join(settings.PROJECT_DIR,
                                     "data/meris/TEMPORARY_mosaic_MER_FRS_1P_RGB_reduced"),
                "search_pattern": "*.tif",
                "type": "local"
            }],
            "eo_metadata": EOMetadata(
                "SOMEEOID",
                datetime.now(),
                datetime.now(),
                GEOSGeometry("POLYGON((1 2, 3 2, 3 4, 1 4, 1 2))")
            )
        }
        
        mgr = self.getManager()
        self.wrapper = mgr.create(**args)
        
        # delete one file
        path = os.path.join(
            settings.PROJECT_DIR,
            "data/meris/TEMPORARY_mosaic_MER_FRS_1P_RGB_reduced",
            "mosaic_ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced.tif"
        )
        logging.info("Deleting file at path: %s"%path)
        os.remove(path)
        
        self.synchronize(self.wrapper.getEOID())
    
    def testContents(self):
        # after sync, the datasets shall be registered.
        self.assertEqual(len(self.wrapper.getEOCoverages()), 2)

    def tearDown(self):
        super(DatasetSeriesSynchronizeTestCase, self).tearDown()
        shutil.rmtree(self.dst)

#===============================================================================
# Coverage ID management
#===============================================================================

class CoverageIdReserveTestCase(CoverageIdManagementTestCase):
    def manage(self):    
        self.mgr.reserve("SomeCoverageID", until=datetime.now() + timedelta(days=1))
    
    def testNotAvailable(self):
        self.assertFalse(self.mgr.available("SomeCoverageID"))

class CoverageIdReserveDefaultUntilTestCase(CoverageIdManagementTestCase):
    def manage(self):    
        self.mgr.reserve("SomeCoverageID")
    
    def testNotAvailable(self):
        self.assertFalse(self.mgr.available("SomeCoverageID"))


class CoverageIdReleaseTestCase(CoverageIdManagementTestCase):
    def manage(self):
        self.mgr.reserve("SomeCoverageID", until=datetime.now() + timedelta(days=1))
        self.mgr.release("SomeCoverageID")
    
    def testAvailable(self):
        self.assertTrue(self.mgr.available("SomeCoverageID"))
    
class CoverageIdAlreadyReservedTestCase(CoverageIdManagementTestCase):
    def manage(self):    
        self.mgr.reserve("SomeCoverageID", until=datetime.now() + timedelta(days=1))
    
    def testReserved(self):
        try:
            self.mgr.reserve("SomeCoverageID")
        except exceptions.CoverageIdReservedError:
            pass
        else:
            self.fail("Reservation of reserved ID did not raise the according "
                      "exception")

class CoverageIdInUseTestCase(CoverageIdManagementTestCase):
    fixtures = EXTENDED_FIXTURES
    
    def testIdInUseRectifiedDataset(self):
        try:
            self.mgr.reserve("mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced")
        except exceptions.CoverageIdInUseError:
            pass
        else:
            self.fail("Reservation of ID in use did not raise the according "
                      "exception")
    
    def testIdInUseRectifiedStitchedMosaic(self):
        try:
            self.mgr.reserve("mosaic_MER_FRS_1P_RGB_reduced")
        except exceptions.CoverageIdInUseError:
            pass
        else:
            self.fail("Reservation of ID in use did not raise the according "
                      "exception")

class CoverageIdReleaseFailTestCase(CoverageIdManagementTestCase):
    def testRelease(self):
        try:
            self.mgr.release("SomeID", True)
        except exceptions.CoverageIdReleaseError:
            pass
        else:
            self.fail("No exception thrown when unreserved ID was released.")

class CoverageIdAvailableTestCase(CoverageIdManagementTestCase):
    fixtures = EXTENDED_FIXTURES
    
    def testNotAvailable(self):
        self.assertFalse(self.mgr.available("mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced"))

    def testAvailable(self):
        self.assertTrue(self.mgr.available("SomeID"))
        
class CoverageIdRequestIdTestCase(CoverageIdManagementTestCase):
    def manage(self):    
        self.mgr.reserve("SomeCoverageID", "SomeRequestID", until=datetime.now() + timedelta(days=1))
        self.mgr.reserve("SomeCoverageID2", "SomeRequestID", until=datetime.now() + timedelta(days=1))
        
    def testCoverageIds(self):
        self.assertItemsEqual(
            ["SomeCoverageID", "SomeCoverageID2"],
            self.mgr.getCoverageIds("SomeRequestID") 
        )
    
    def testRequestId(self):
        self.assertEqual("SomeRequestID", self.mgr.getRequestId("SomeCoverageID"))
        self.assertEqual("SomeRequestID", self.mgr.getRequestId("SomeCoverageID2"))