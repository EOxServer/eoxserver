#-----------------------------------------------------------------------
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
from django.contrib.gis.geos import GEOSGeometry, Polygon, MultiPolygon
from django.conf import settings

from eoxserver.core.system import System
from eoxserver.core.util.timetools import UTCOffsetTimeZoneInfo, isotime
from eoxserver.testing.core import BASE_FIXTURES
import eoxserver.resources.coverages.testbase as eoxstest
from eoxserver.resources.coverages.geo import GeospatialMetadata
from eoxserver.resources.coverages.metadata import EOMetadata
import eoxserver.resources.coverages.exceptions as exceptions


logger = logging.getLogger(__name__)

# create new rectified dataset from a local path

class RectifiedDatasetCreateWithLocalPathTestCase(eoxstest.RectifiedDatasetCreateTestCase):
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

class RectifiedDatasetCreateWithLocalPathAndMetadataTestCase(eoxstest.RectifiedDatasetCreateTestCase):
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

class RectifiedDatasetCreateWithContainerTestCase(eoxstest.RectifiedDatasetCreateTestCase):
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
                srid=4326, size_x=1023, size_y=451,
                extent=(-3.75, 32.158895, 28.326165, 46.3)
            ),
            "range_type_name": "RGB",
            "eo_metadata": EOMetadata(
                "STITCHED_MOSAIC",
                datetime.now(),
                datetime.now(),
                GEOSGeometry("POLYGON((-3 33, 27 33, 27 45, -3 45, -3 33))")
            ),
            "storage_dir": "/tmp/some/storage/dir"
        })
        
    def manage(self):
        self._create_containers()
        args = {
            "local_path": os.path.join(settings.PROJECT_DIR,
                          "data/meris/mosaic_MER_FRS_1P_RGB_reduced", 
                          "mosaic_ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced.tif"),
            "range_type_name": "RGB",
            "container": self.stitched_mosaic
        }
        self.wrapper = self.create(**args)

    def testContents(self):
        self.assertTrue(self.stitched_mosaic.contains(self.wrapper), 
                        "Stitched Mosaic has to contain the dataset.")
    
class RectifiedDatasetCreateWithContainerIDsTestCase(eoxstest.RectifiedDatasetCreateTestCase):
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
                GEOSGeometry("POLYGON((-3 33, 27 33, 27 45, -3 45, -3 33))")
            )
        })
        
        self.stitched_mosaic = mosaic_mgr.create(**{
            "data_dirs": [],
            "geo_metadata": GeospatialMetadata(
                srid=4326, size_x=1023, size_y=451,
                extent=(-3.75, 32.158895, 28.326165, 46.3)
            ),
            "range_type_name": "RGB",
            "eo_metadata": EOMetadata(
                "STITCHED_MOSAIC",
                datetime.now(),
                datetime.now(),
                GEOSGeometry("POLYGON((-3 33, 27 33, 27 45, -3 45, -3 33))")
            ),
            "storage_dir": "/tmp/some/storage/dir"
        })
    
    def manage(self):
        self._create_containers()
        args = {
            "local_path": os.path.join(settings.PROJECT_DIR,
                          "data/meris/mosaic_MER_FRS_1P_RGB_reduced", 
                          "mosaic_ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced.tif"),
            "range_type_name": "RGB",
            "container_ids": [self.stitched_mosaic.getCoverageId(), self.dataset_series.getEOID()]
        }
        self.wrapper = self.create(**args)

    def testContents(self):
        self.assertTrue(self.stitched_mosaic.contains(self.wrapper), 
                        "Stitched Mosaic has to contain the dataset.")
        
        self.assertTrue(self.dataset_series.contains(self.wrapper), 
                        "Dataset Series has to contain the dataset.")

# create new rectified dataset from a ftp path

class RectifiedDatasetCreateWithRemothePathTestCase(eoxstest.RectifiedDatasetCreateTestCase):
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

class RectifiedDatasetCreateWithRasdamanLocationTestCase(eoxstest.RectifiedDatasetCreateTestCase):
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
    

class RectifiedDatasetUpdateGeoMetadataTestCase(eoxstest.RectifiedDatasetUpdateTestCase):
    fixtures = eoxstest.EXTENDED_FIXTURES
    
    def manage(self):
        args = {
            "obj_id": "MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_uint16_reduced_compressed",
            "set": {
                "geo_metadata": GeospatialMetadata(
                    srid=3035,
                    size_x=100,
                    size_y=100,
                    extent=(0, 0, 10000000, 10000000)
                )
            }
        }
        self.update(**args)
    
    def testContents(self):
        coverage = System.getRegistry().getFromFactory(
            "resources.coverages.wrappers.EOCoverageFactory",
            {"obj_id": "MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_uint16_reduced_compressed"}
        )
        
        self.assertEqual(3035, coverage.getAttrValue("srid"))
        self.assertEqual((100, 100), (coverage.getAttrValue("size_x"), coverage.getAttrValue("size_y")))
        self.assertEqual((0, 0, 10000000, 10000000),( 
            coverage.getAttrValue("minx"),
            coverage.getAttrValue("miny"),
            coverage.getAttrValue("maxx"),
            coverage.getAttrValue("maxy")
        ))
    
class RectifiedDatasetUpdateGeoMetadataViaSetAttrMetadataTestCase(eoxstest.RectifiedDatasetUpdateTestCase):
    fixtures = eoxstest.EXTENDED_FIXTURES
    
    def manage(self):
        args = {
            "obj_id": "MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_uint16_reduced_compressed",
            "set": {
                "srid": 3035,
                "size_x": 100,
                "size_y": 100,
                "minx": 0,
                "miny": 0,
                "maxx": 10000000,
                "maxy": 10000000
            }
        }
        self.update(**args)
    
    def testContents(self):
        coverage = System.getRegistry().getFromFactory(
            "resources.coverages.wrappers.EOCoverageFactory",
            {"obj_id": "MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_uint16_reduced_compressed"}
        )
        
        self.assertEqual(3035, coverage.getAttrValue("srid"))
        self.assertEqual((100, 100), (coverage.getAttrValue("size_x"), coverage.getAttrValue("size_y")))
        self.assertEqual((0, 0, 10000000, 10000000),( 
            coverage.getAttrValue("minx"),
            coverage.getAttrValue("miny"),
            coverage.getAttrValue("maxx"),
            coverage.getAttrValue("maxy")
        ))

class RectifiedDatasetUpdateEOMetadataTestCase(eoxstest.RectifiedDatasetUpdateTestCase):
    fixtures = eoxstest.EXTENDED_FIXTURES
    
    def manage(self):
        import pytz
        utc = pytz.timezone("UTC")
        self.begin_time = datetime.now(utc)
        self.end_time = datetime.now(utc)
        self.footprint = MultiPolygon(Polygon.from_bbox((-3, 33, 12, 46)))
        #GEOSGeometry("POLYGON((1 2, 3 2, 3 4, 1 4, 1 2))")
        args = {
            "obj_id": "mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced",
            "set": {
                "eo_metadata": EOMetadata(
                    "SomeEOID",
                    self.begin_time,
                    self.end_time,
                    self.footprint
                )
            }
        }
        self.update(**args)
        
    def testContents(self):
        coverage = System.getRegistry().getFromFactory(
            "resources.coverages.wrappers.EOCoverageFactory",
            {"obj_id": "mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced"}
        )
        
        self.assertEqual("SomeEOID", coverage.getEOID())
        self.assertEqual(self.begin_time, coverage.getBeginTime())
        self.assertEqual(self.end_time, coverage.getEndTime())
        self.assertTrue(self.footprint.equals_exact(coverage.getFootprint(), 0.001),
                        "Footprints mismatch.")

class RectifiedDatasetUpdateEOMetadataViaSetAttrTestCase(eoxstest.RectifiedDatasetUpdateTestCase):
    fixtures = eoxstest.EXTENDED_FIXTURES
    
    def manage(self):
        import pytz
        utc = pytz.timezone("UTC")
        self.begin_time = datetime.now(utc)
        self.end_time = datetime.now(utc)
        self.footprint = GEOSGeometry("MULTIPOLYGON(((-3 33, 12 33, 12 45, -3 45, -3 33)))")
        args = {
            "obj_id": "mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced",
            "set": {
                "eo_id": "SomeEOID",
                "footprint": self.footprint,
                "begin_time": self.begin_time,
                "end_time": self.end_time
            }
        }
        self.update(**args)
        
    def testContents(self):
        coverage = System.getRegistry().getFromFactory(
            "resources.coverages.wrappers.EOCoverageFactory",
            {"obj_id": "mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced"}
        )
        
        self.assertEqual("SomeEOID", coverage.getEOID())
        self.assertEqual(self.begin_time, coverage.getBeginTime())
        self.assertEqual(self.end_time, coverage.getEndTime())
        self.assertEqual(self.footprint, coverage.getFootprint())

class RectifiedDatasetUpdateLinkContainersTestCase(eoxstest.RectifiedDatasetUpdateTestCase):
    fixtures = eoxstest.EXTENDED_FIXTURES
    
    def manage(self):
        args = {
            "obj_id": "mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced",
            "link": {
                "container_ids": ["MER_FRS_1P_reduced"]
            }
        }
        self.update(**args)
        
    def testContents(self):
        coverage = System.getRegistry().getFromFactory(
            "resources.coverages.wrappers.EOCoverageFactory",
            {"obj_id": "mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced"}
        )
        
        self.assertIn("MER_FRS_1P_reduced", [container.getEOID() for container in coverage.getContainers()])

class RectifiedDatasetUpdateUnlinkContainersTestCase(eoxstest.RectifiedDatasetUpdateTestCase):
    fixtures = eoxstest.EXTENDED_FIXTURES
    
    def manage(self):
        args = {
            "obj_id": "mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced",
            "unlink": {
                "container_ids": ["mosaic_MER_FRS_1P_RGB_reduced"]
            }
        }
        self.update(**args)
        
    def testContents(self):
        coverage = System.getRegistry().getFromFactory(
            "resources.coverages.wrappers.EOCoverageFactory",
            {"obj_id": "mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced"}
        )
        
        self.assertNotIn("mosaic_MER_FRS_1P_RGB_reduced", [container.getEOID() for container in coverage.getContainers()])

class RectifiedDatasetUpdateCoverageAndEOIDTestCase(eoxstest.RectifiedDatasetUpdateTestCase):
    fixtures = eoxstest.EXTENDED_FIXTURES
    
    def manage(self):
        args = {
            "obj_id": "mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced",
            "set": {
                "coverage_id": "SomeCoverageID",
                "eo_id": "SomeEOID"
            }
        }
        self.update(**args)
    
    def testContents(self):
        coverage = System.getRegistry().getFromFactory(
            "resources.coverages.wrappers.EOCoverageFactory",
            {"obj_id": "SomeCoverageID"}
        )
        
        self.assertEqual("SomeCoverageID", coverage.getCoverageId())
        self.assertEqual("SomeEOID", coverage.getEOID())


# create new mosaic and add a local path to locations
class RectifiedStitchedMosaicCreateWithLocalPathTestCase(eoxstest.RectifiedStitchedMosaicCreateTestCase):
    def manage(self):
        args = {
            "data_dirs": [{
                "path": os.path.join(settings.PROJECT_DIR,
                                     "data/meris/mosaic_MER_FRS_1P_RGB_reduced"),
                "search_pattern": "*.tif",
                "type": "local"
            }],
            "geo_metadata": GeospatialMetadata(
                srid=4326, size_x=1023, size_y=451,
                extent=(-3.75, 32.158895, 28.326165, 46.3)
            ),
            "range_type_name": "RGB",
            "eo_metadata": EOMetadata(
                "STITCHED_MOSAIC",
                datetime.now(),
                datetime.now(),
                GEOSGeometry("POLYGON((-3 33, 27 33, 27 45, -3 45, -3 33))")
            ),
            "storage_dir": "/tmp/some/storage/dir"
        }
        self.wrapper = self.create(**args)
        
    def testContents(self):
        # test the number of datasets
        self.assertEqual(len(self.wrapper.getDatasets()), 3)
        
        # test validity of datasets


# create new mosaic and add a remote path to locations
class RectifiedStitchedMosaicCreateWithRemotePathTestCase(eoxstest.RectifiedStitchedMosaicCreateTestCase):
    def manage(self):
        args = {
            "data_dirs": [{
                "path": "test/mosaic_MER_FRS_1P_RGB_reduced",
                "search_pattern": "*.tif",
                "type": "ftp",
                
                "host": "hma.eox.at",
                "user": "anonymous",
                "password": ""
            }],
            "geo_metadata": GeospatialMetadata(
                srid=4326, size_x=1023, size_y=451,
                extent=(-3.75, 32.158895, 28.326165, 46.3)
            ),
            "range_type_name": "RGB",
            "eo_metadata": EOMetadata(
                "SOMEEOID",
                datetime.now(),
                datetime.now(),
                GEOSGeometry("POLYGON((-3 33, 27 33, 27 45, -3 45, -3 33))")
            ),
            "storage_dir": "/tmp/some/storage/dir"
        }
        self.wrapper = self.create(**args)
        
    def testContents(self):
        self.assertEqual(len(self.wrapper.getDatasets()), 3)


#TODO enable when implemented
# create new mosaic and add a rasdaman location to locations
#class RectifiedStitchedMosaicCreateWithRasdamanLocationTestCase(eoxstest.RectifiedStitchedMosaicCreateTestCase):
#    def manage(self):
#        args = {
#            "data_dirs": [{
#                "type": "rasdaman",
#                "host": "localhost",
#                "collection": "MERIS"
#            }],
#            "geo_metadata": GeospatialMetadata(
#                srid=4326, size_x=100, size_y=100,
#                extent=(1, 2, 3, 4)
#            ),
#            "range_type_name": "RGB",
#            "eo_metadata": EOMetadata(
#                "SOMEEOID",
#                datetime.now(),
#                datetime.now(),
#                GEOSGeometry("POLYGON((1 2, 3 2, 3 4, 1 4, 1 2))")
#            ),
#            "storage_dir": "/tmp/some/storage/dir"
#        }
#        self.wrapper = self.create(**args)


class RectifiedStitchedMosaicUpdateLinkDataSourcesTestCase(eoxstest.RectifiedStitchedMosaicUpdateTestCase):
    fixtures = eoxstest.EXTENDED_FIXTURES
    
    def manage(self):
        args = {
            "obj_id": "mosaic_MER_FRS_1P_RGB_reduced",
            "link": {
                "data_dirs": [{
                    "type": "local",
                    "path": os.path.join(
                        settings.PROJECT_DIR,
                        "data/meris/MER_FRS_1P_reduced", 
                        "ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed.tif"
                    ),
                    "md_path": os.path.join(
                        settings.PROJECT_DIR,
                        "data/meris/MER_FRS_1P_reduced", 
                        "ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed.xml"
                    )
                }]
            }
        }
        
        self.update(**args)
    
    def testContents(self):
        pass


class RectifiedStitchedMosaicUpdateUnlinkDatasetsTestCase(eoxstest.RectifiedStitchedMosaicUpdateTestCase):
    fixtures = eoxstest.EXTENDED_FIXTURES
    
    def manage(self):
        args = {
            "obj_id": "mosaic_MER_FRS_1P_RGB_reduced",
            "unlink": {
                "coverage_ids": [
                    "mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced"
                ]  
            }
        }
        
        self.update(**args)
    
    def testContents(self):
        mosaic = System.getRegistry().getFromFactory(
            "resources.coverages.wrappers.EOCoverageFactory",
            {"obj_id": "mosaic_MER_FRS_1P_RGB_reduced"}
        )
        
        self.assertNotIn("mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced",
                         [coverage.getCoverageId() for coverage in mosaic.getDatasets()])
        


# create dataset series with a local path
class DatasetSeriesCreateWithLocalPathTestCase(eoxstest.DatasetSeriesCreateTestCase):
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

class DatasetSeriesRemoveLocationTestCase(eoxstest.DatasetSeriesUpdateTestCase):
    fixtures = eoxstest.EXTENDED_FIXTURES
    
    def manage(self):
        pass
    
    def testContents(self):
        pass

class DatasetSeriesSynchronizeNewDirectoryTestCase(eoxstest.DatasetSeriesSynchronizeTestCase):
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
        wrapper = System.getRegistry().getFromFactory(
            "resources.coverages.wrappers.DatasetSeriesFactory",
            {"obj_id": "SOMEEOID"}
        )
        
        # after sync, the datasets shall be registered.
        self.assertEqual(len(wrapper.getEOCoverages()), 3)
        
        self.assertEqual(wrapper.getBeginTime(), 
                         min([dataset.getBeginTime() 
                              for dataset in wrapper.getEOCoverages()]))
        
        self.assertEqual(wrapper.getEndTime(), 
                         max([dataset.getEndTime() 
                              for dataset in wrapper.getEOCoverages()]))
        
        footprint = wrapper.getEOCoverages()[0].getFootprint().envelope
        for dataset in wrapper.getEOCoverages()[1:]:
            footprint = footprint.union(dataset.getFootprint()).envelope
        self.assertTrue(wrapper.getFootprint().envelope.equals_exact(footprint, 0.001),
                        "Footprints mismatch.")

class DatasetSeriesSynchronizeFileRemovedTestCase(eoxstest.DatasetSeriesSynchronizeTestCase):
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
        logger.info("Deleting file at path: %s"%path)
        os.remove(path)
        
        self.synchronize(self.wrapper.getEOID())
    
    def testContents(self):
        # after sync, the datasets shall be registered.
        
        wrapper = System.getRegistry().getFromFactory(
            "resources.coverages.wrappers.DatasetSeriesFactory",
            {"obj_id": "SOMEEOID"}
        )
        
        self.assertEqual(len(wrapper.getEOCoverages()), 2)
        
        self.assertEqual(wrapper.getBeginTime(), 
                         min([dataset.getBeginTime() 
                              for dataset in wrapper.getEOCoverages()]))
        
        self.assertEqual(wrapper.getEndTime(), 
                         max([dataset.getEndTime() 
                              for dataset in wrapper.getEOCoverages()]))
        
        footprint = wrapper.getEOCoverages()[0].getFootprint().envelope
        for dataset in wrapper.getEOCoverages()[1:]:
            footprint = footprint.union(dataset.getFootprint()).envelope
        self.assertTrue(wrapper.getFootprint().envelope.equals_exact(footprint, 0.001),
                        "Footprints mismatch.")
    
    def tearDown(self):
        super(DatasetSeriesSynchronizeFileRemovedTestCase, self).tearDown()
        shutil.rmtree(self.dst)

class DatasetSeriesUpdateLinkCoveragesTestCase(eoxstest.DatasetSeriesUpdateTestCase):
    fixtures = eoxstest.EXTENDED_FIXTURES
    
    def manage(self):
        args = {
            "obj_id": "MER_FRS_1P_reduced",
            "link": {
                "coverage_ids": [
                    "mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced"
                ]
            }
        }
        
        self.update(**args)
        
    def testContents(self):
        dataset_series = System.getRegistry().getFromFactory(
            "resources.coverages.wrappers.DatasetSeriesFactory",
            {"obj_id": "MER_FRS_1P_reduced"}
        )
        
        self.assertIn("mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced",
                      [coverage.getCoverageId() for coverage in dataset_series.getEOCoverages()])

class DatasetSeriesUpdateLinkCoverages2TestCase(eoxstest.DatasetSeriesUpdateTestCase):
    fixtures = eoxstest.EXTENDED_FIXTURES
    
    def manage(self):
        args = {
            "obj_id": "MER_FRS_1P_RGB_reduced",
            "link": {
                "coverage_ids": [
                    "MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_uint16_reduced_compressed"
                ]
            }
        }
        
        self.update(**args)
        
    def testContents(self):
        dataset_series = System.getRegistry().getFromFactory(
            "resources.coverages.wrappers.DatasetSeriesFactory",
            {"obj_id": "MER_FRS_1P_RGB_reduced"}
        )
        
        self.assertIn("MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_uint16_reduced_compressed",
                      [coverage.getCoverageId() for coverage in dataset_series.getEOCoverages()])


class DatasetSeriesUpdateUnlinkCoveragesTestCase(eoxstest.DatasetSeriesUpdateTestCase):
    fixtures = eoxstest.EXTENDED_FIXTURES
    
    def manage(self):
        args = {
            "obj_id": "MER_FRS_1P_reduced",
            "unlink": {
                "coverage_ids": [
                    "MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_uint16_reduced_compressed"
                ]
            }
        }
        
        self.update(**args)
        
    def testContents(self):
        dataset_series = System.getRegistry().getFromFactory(
            "resources.coverages.wrappers.DatasetSeriesFactory",
            {"obj_id": "MER_FRS_1P_reduced"}
        )
        
        self.assertNotIn("MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_uint16_reduced_compressed",
                         [coverage.getCoverageId() for coverage in dataset_series.getEOCoverages()])

#===============================================================================
# Coverage ID management
#===============================================================================

class CoverageIdReserveTestCase(eoxstest.CoverageIdManagementTestCase):
    def manage(self):    
        self.mgr.reserve("SomeCoverageID", until=datetime.now() + timedelta(days=1))
    
    def testNotAvailable(self):
        self.assertFalse(self.mgr.available("SomeCoverageID"))

class CoverageIdReserveWithSameRequestIdTestCase(eoxstest.CoverageIdManagementTestCase):
    def manage(self):    
        self.mgr.reserve("SomeCoverageID", "RequestID", until=datetime.now() + timedelta(days=1))
    
    def testReserveAgain(self):
        try:
            self.mgr.reserve("SomeCoverageID", "RequestID", until=datetime.now() + timedelta(days=2))
        except exceptions.CoverageIdReservedError:
            self.fail("Reserving with same request ID should not raise.")
    
class CoverageIdReserveDefaultUntilTestCase(eoxstest.CoverageIdManagementTestCase):
    def manage(self):    
        self.mgr.reserve("SomeCoverageID")
    
    def testNotAvailable(self):
        self.assertFalse(self.mgr.available("SomeCoverageID"))

class CoverageIdReleaseTestCase(eoxstest.CoverageIdManagementTestCase):
    def manage(self):
        self.mgr.reserve("SomeCoverageID", until=datetime.now() + timedelta(days=1))
        self.mgr.release("SomeCoverageID")
    
    def testAvailable(self):
        self.assertTrue(self.mgr.available("SomeCoverageID"))
    
class CoverageIdAlreadyReservedTestCase(eoxstest.CoverageIdManagementTestCase):
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

class CoverageIdInUseTestCase(eoxstest.CoverageIdManagementTestCase):
    fixtures = eoxstest.EXTENDED_FIXTURES
    
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

class CoverageIdReleaseFailTestCase(eoxstest.CoverageIdManagementTestCase):
    def testRelease(self):
        try:
            self.mgr.release("SomeID", True)
        except exceptions.CoverageIdReleaseError:
            pass
        else:
            self.fail("No exception thrown when unreserved ID was released.")

class CoverageIdAvailableTestCase(eoxstest.CoverageIdManagementTestCase):
    fixtures = eoxstest.EXTENDED_FIXTURES
    
    def testNotAvailable(self):
        self.assertFalse(self.mgr.available("mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced"))

    def testAvailable(self):
        self.assertTrue(self.mgr.available("SomeID"))
        
class CoverageIdRequestIdTestCase(eoxstest.CoverageIdManagementTestCase):
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


#===============================================================================
# CLI Command tests
#===============================================================================

# eoxs_register_dataset

class RegisterLocalDatasetSimpleTestCase(eoxstest.CommandRegisterDatasetTestCase):
    kwargs = {
        "d": "autotest/data/meris/MER_FRS_1P_reduced/ENVISAT-MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed.tif",
        "rangetype": "RGB"
    }
    coverages_to_be_registered = [
        {"eo_id": "MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed"}
    ]


class RegisterLocalDatasetWithCoverageIdTestCase(eoxstest.CommandRegisterDatasetTestCase):
    kwargs = {
        "d": "autotest/data/meris/MER_FRS_1P_reduced/ENVISAT-MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed.tif",
        "rangetype": "RGB",
        "i": "someCoverageID"
    }
    coverages_to_be_registered = [{"coverage_id": "someCoverageID"}]

class RegisterLocalDatasetMultipleTestCase(eoxstest.CommandRegisterDatasetTestCase):
    kwargs = {
        "d": ("autotest/data/meris/MER_FRS_1P_reduced/ENVISAT-MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed.tif",
              "autotest/data/meris/MER_FRS_1P_reduced/ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed.tif",
              "autotest/data/meris/MER_FRS_1P_reduced/ENVISAT-MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_uint16_reduced_compressed.tif"),
        "rangetype": "RGB"
    }
    coverages_to_be_registered = [
        {"eo_id": "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed"},
        {"eo_id": "MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed"},
        {"eo_id": "MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_uint16_reduced_compressed"}
    ]
    

class RegisterRemoteDatasetTestCase(eoxstest.CommandRegisterDatasetTestCase):
    kwargs = {
        "d": "test/mosaic_MER_FRS_1P_RGB_reduced/mosaic_ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced.tif",
        "m": "test/mosaic_MER_FRS_1P_RGB_reduced/mosaic_ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced.xml", 
        "mode": "ftp",
        "host": "hma.eox.at",
        "user": "anonymous",
        "rangetype": "RGB"
    }
    coverages_to_be_registered = [
        {"eo_id": "mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced_ftp"}
    ]


# TODO: TCs for rasdaman coverages

# no rasdaman publicly available

# TODO: TCs for default-... and visible options

class RegisterLocalDatasetVisibleTestCase(eoxstest.CommandRegisterDatasetTestCase):
    kwargs = {
        "d": "autotest/data/meris/MER_FRS_1P_reduced/ENVISAT-MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed.tif",
        "rangetype": "RGB",
        "visible": "True"
    }
    coverages_to_be_registered = [
        {"eo_id": "MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed"}
    ]

    def testCoverageVisible(self):
        coverage = self.getCoveragesToBeRegistered().values()[0]
        self.assertTrue(coverage.getAttrValue("visible"))


class RegisterLocalDatasetInvisibleTestCase(eoxstest.CommandRegisterDatasetTestCase):
    kwargs = {
        "d": "autotest/data/meris/MER_FRS_1P_reduced/ENVISAT-MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed.tif",
        "rangetype": "RGB",
        "invisible": "True"
    }
    coverages_to_be_registered = [
        {"eo_id": "MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed"}
    ]

    def testCoverageInvisible(self):
        coverage = self.getCoveragesToBeRegistered().values()[0]
        self.assertFalse(coverage.getAttrValue("visible"))


class RegisterLocalDatasetDefaultsTestCase(eoxstest.CommandRegisterDatasetTestCase):
    srid = 3035
    size = (100, 100)
    extent = (3000000, -2400000, 4400000, -1200000)
    poly = MultiPolygon([Polygon.from_bbox((0, 0, 10, 10))])
    begin_time = datetime(2012, 06, 10, 12, 30, tzinfo=UTCOffsetTimeZoneInfo())
    end_time = datetime(2012, 06, 10, 12, 45, tzinfo=UTCOffsetTimeZoneInfo())
    
    kwargs = {
        "d": "autotest/data/meris/mosaic_cache/mosaic_MER_FRS_1P_RGB_reduced/tiles/000/000/tile_merged_000001_000000.tiff",
        "rangetype": "RGB",
        "default-srid": str(srid),
        "default-size": "%s,%s" % size,
        "default-extent": "%s,%s,%s,%s" % extent,
        "default-begin-time": isotime(begin_time),
        "default-end-time": isotime(end_time),
        "default-footprint": poly.wkt,
        "coverage-id": "A",
        "traceback": "True"
        
    }
    coverages_to_be_registered = [
        {"coverage_id": "A"}
    ]
    
    def testDefaults(self):
        coverage = self.getDatasetById("A")
        
        self.assertEqual(self.srid, coverage.getSRID())
        self.assertEqual(self.size, coverage.getSize())
        self.assertEqual(self.extent, coverage.getExtent())
        self.assertEqual(self.begin_time, coverage.getBeginTime())
        self.assertEqual(self.end_time, coverage.getEndTime())
        self.assertEqual(self.poly, coverage.getFootprint())

# TODO: TCs for datasetseries/stitchedmosaic insertions

# eoxs_add_dataset_series


# eoxs_synchronize


# eoxs_insert_into_series

class InsertByIdTestCase(eoxstest.CommandInsertTestCase):
    args = ("MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_uint16_reduced_compressed", 
            "MER_FRS_1P_RGB_reduced")
    
    datasets_to_be_inserted = ["MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_uint16_reduced_compressed"]

class InsertByIdExplicitTestCase(eoxstest.CommandInsertTestCase):
    args = (
        "--datasets", 
        "MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_uint16_reduced_compressed",
        "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed", 
        "MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed",
        "--dataset-series",
        "MER_FRS_1P_RGB_reduced"
    )
    datasets_to_be_inserted = [
        "MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_uint16_reduced_compressed",
        "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed",
        "MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed"
    ]


class InsertByUnknownIdFaultTestCase(eoxstest.CoverageCommandFaultTestCase):
    args = ("invalidID",  "MER_FRS_1P_RGB_reduced")


# eoxs_remove_from_series

class ExcludeByIdTestCase(eoxstest.CommandExcludeTestCase):
    args = ("mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced",
            "MER_FRS_1P_RGB_reduced")
    
    datasets_to_be_excluded = ["mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced"]


class ExcludeByIdExplicitTestCase(eoxstest.CommandExcludeTestCase):
    args = (
        "--datasets", 
        "mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced",
        "mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced", 
        "mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced",
        "--dataset-series",
        "MER_FRS_1P_RGB_reduced"
    )
    datasets_to_be_excluded = [
        "mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced",
        "mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced",
        "mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced"
    ]


class ExcludeByUnknownIdFaultTestCase(eoxstest.CoverageCommandFaultTestCase):
    args = ("invalidID",  "MER_FRS_1P_RGB_reduced")
