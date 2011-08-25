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

from eoxserver.testing.core import (
    DatasetSeriesSynchronizationTestCase, 
    RectifiedStitchedMosaicSynchronizationTestCase,
    BASE_FIXTURES
)
from eoxserver.resources.coverages.models import (
    DatasetSeriesRecord, EOMetadataRecord, DataDirRecord,
    RectifiedDatasetRecord, RangeTypeRecord,
    LineageRecord, FileRecord, ExtentRecord
, RectifiedStitchedMosaicRecord)
from django.utils.datetime_safe import datetime
from django.contrib.gis.geos import GEOSGeometry
from django.conf import settings

import logging
import os.path

logging.basicConfig(
    filename=os.path.join('logs', 'test.log'),
    level=logging.DEBUG,
    format="[%(asctime)s][%(levelname)s] %(message)s"
)

class DatasetSeriesRemoveDataDirTestCase(DatasetSeriesSynchronizationTestCase):
    """ Remove the DataDir from a DatasetSeries. After
        the synchronization, all Datasets in that 
        directory should be removed from the
        DatasetSeries.
    """
    
    fixtures = BASE_FIXTURES + ["testing_coverages.json"]
    
    def setUp(self):
        dss = DatasetSeriesRecord.objects.get(pk=1)
        dss.data_dirs.all()[0].delete()
        
        self.synchronize(dss)
    
    def testNumberOfDatasets(self):
        dss = DatasetSeriesRecord.objects.get(pk=1)
        self.assertEqual(len(dss.rect_datasets.all()), 0)
        
    def testNumberOfMosaics(self):
        dss = DatasetSeriesRecord.objects.get(pk=1)
        self.assertEqual(len(dss.rect_stitched_mosaics.all()), 1)

class DatasetSeriesRemoveDatasetFromDataDirTestCase(DatasetSeriesSynchronizationTestCase):
    """ Remove a Dataset which is included in a DataDir.
        Upon removal and synchronization, this Dataset 
        should be re-inserted in the DatasetSeries. 
    """
    
    fixtures = BASE_FIXTURES + ["testing_coverages.json"]
    
    def setUp(self):
        coverage_id = "MER_FRS_1PNPDE20060830_100949_000001972050_"\
                      "00423_23523_0079_uint16_reduced_compressed"
        dss = DatasetSeriesRecord.objects.get(pk=1)
        ds = RectifiedDatasetRecord.objects.get(coverage_id=coverage_id)
        dss.rect_datasets.remove(ds)
        
        self.synchronize(dss)
        
    def testNumberOfDatasets(self):
        dss = DatasetSeriesRecord.objects.get(pk=1)
        self.assertEqual(len(dss.rect_datasets.all()), 3)
        
class DatasetSeriesAddAutomaticDatasetTestCase(DatasetSeriesSynchronizationTestCase):
    """ Add an automatic Dataset to the DatasetSeries. 
        After the synchronization, the Dataset should
        be removed again.
    """
    
    fixtures = BASE_FIXTURES + ["testing_coverages.json"]
    
    def setUp(self):
        self.coverage_id = "mosaic_MER_FRS_1PNPDE20060822_092058_"\
                           "000001972050_00308_23408_0077_RGB_reduced"
        dss = DatasetSeriesRecord.objects.get(pk=1)
        ds = RectifiedDatasetRecord.objects.get(coverage_id=self.coverage_id)
        dss.rect_datasets.through.objects.create(datasetseriesrecord=dss,
                                                 rectifieddatasetrecord=ds)
        
        self.synchronize(dss)
    
    def testNumberOfDatasets(self):
        dss = DatasetSeriesRecord.objects.get(pk=1)
        self.assertEqual(len(dss.rect_datasets.all()), 3)
        
class DatasetSeriesAddManualDatasetTestCase(DatasetSeriesSynchronizationTestCase):
    """ Add a manual Dataset to the DatasetSeries. 
        It should still be linked to the DatasetSeries
        after the synchronization.
    """
    
    fixtures = BASE_FIXTURES + ["testing_coverages.json"]
    
    def setUp(self):
        self.coverage_id = "mosaic_MER_FRS_1PNPDE20060822_092058_"\
                           "000001972050_00308_23408_0077_RGB_reduced"
        dss = DatasetSeriesRecord.objects.get(pk=1)
        
        # set to manually created Dataset
        ds = RectifiedDatasetRecord.objects.get(coverage_id=self.coverage_id)
        ds.automatic = False
        ds.save()
        
        dss.rect_datasets.through.objects.create(datasetseriesrecord=dss,
                                                 rectifieddatasetrecord=ds)
        
        self.synchronize(dss)
    
    def testNumberOfDatasets(self):
        dss = DatasetSeriesRecord.objects.get(pk=1)
        self.assertEqual(len(dss.rect_datasets.all()), 4)

class DatsetSeriesNewDataDirTestCase(DatasetSeriesSynchronizationTestCase):
    """ Create an empty DatasetSeries and add a DataDir.
        Upon synchronization, the DatasetSeries should 
        contain 3 Datasets.
    """
    
    def setUp(self):
        dss = DatasetSeriesRecord.objects.create(
            eo_id="testDatasetSeries",
            image_pattern="*.tif",
            
            eo_metadata=EOMetadataRecord.objects.create(
                timestamp_begin=datetime(year=2011, month=1, day=1),
                timestamp_end=datetime(year=2011, month=1, day=1),
                footprint=GEOSGeometry('POLYGON(( 10 10, 10 20, 20 20, 20 15, 10 10))')
            )
        )
        
        DataDirRecord.objects.create(dataset_series=dss,
                                     # TODO: get path from config!!!
                                     dir=os.path.abspath(os.path.join(settings.PROJECT_DIR,
                                                                      "data/meris/MER_FRS_1P_reduced")))
        
        self.synchronize(dss)
        
    def testNumberOfDatasets(self):
        dss = DatasetSeriesRecord.objects.get(eo_id="testDatasetSeries")
        self.assertEqual(len(dss.rect_datasets.all()), 3)

class DatasetSeriesNewDataDirReservedTestCase(DatasetSeriesSynchronizationTestCase):
    """ Add a DataDir to a newly created DatasetSeries.
        The same DataDir is already included with another
        DatasetSeries.
    """
    
    fixtures = BASE_FIXTURES + ["testing_coverages.json"]
    
    def setUp(self):
        dss = DatasetSeriesRecord.objects.create(
            eo_id="testDatasetSeries",
            image_pattern="*.tif",
            
            eo_metadata=EOMetadataRecord.objects.create(
                timestamp_begin=datetime(year=2011, month=1, day=1),
                timestamp_end=datetime(year=2011, month=1, day=1),
                footprint=GEOSGeometry('POLYGON(( 10 10, 10 20, 20 20, 20 15, 10 10))')
            )
        )
        
        dd = DataDirRecord.objects.create(dataset_series=dss,
                                          dir=os.path.abspath(os.path.join(settings.PROJECT_DIR,
                                                                           "data/meris/MER_FRS_1P_reduced")))
        
        self.synchronize(dss)
        
        dd.remove()
        
        self.synchronize(dss)

    def testNumberOfDatasets(self):
        dss = DatasetSeriesRecord.objects.get(eo_id="testDatasetSeries")
        self.assertEqual(len(dss.rect_datasets.all()), 3)
            
            
class RectifiedStitchedMosaicNewDatasetTestCase(RectifiedStitchedMosaicSynchronizationTestCase):
    """ Add a newly created Dataset to the 
        RectifiedStitchedMosaic.
    """
    
    fixtures = BASE_FIXTURES + ["testing_coverages.json"]
    
    def setUp(self):
        rsm = RectifiedStitchedMosaicRecord.objects.get(pk=1)
        ds = RectifiedDatasetRecord.objects.create(
            range_type=RangeTypeRecord.objects.get(name="RGB"),
            eo_metadata=EOMetadataRecord.objects.create(
                timestamp_begin=datetime(year=2011, month=1, day=1),
                timestamp_end=datetime(year=2011, month=1, day=1),
                footprint=GEOSGeometry('POLYGON(( 10 10, 10 20, 20 20, 20 15, 10 10))')
            ),
            lineage=LineageRecord.objects.create(),
            file=FileRecord.objects.create(
                                           # Get path from config
                path="data/meris/mosaic_MER_FRS_1P_RGB_reduced/mosaic_ENVISAT-MER_FRS_"\
                     "1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced.tif"
            ),
            extent=ExtentRecord.objects.create(
                srid=4326,
                minx=10,
                miny=10,
                maxx=20,
                maxy=20,
                size_x=10,
                size_y=10
            )
        )
        
        rsm.rect_datasets.through.objects.create(rectifiedstitchedmosaicrecord=rsm,
                                                 rectifieddatasetrecord=ds)
        
        # Enable the RectifiedStitchedMosaicWrapper interface, as it is normally disabled
        # TODO: remove this, if the interface is enabled by default
        from eoxserver.core.system import System
        id = "resources.coverages.wrappers.RectifiedStitchedMosaicWrapper"
        System.getRegistry().enableImplementation(id)
        
        self.synchronize(rsm)
        
    def testNumberOfDatasets(self):
        rsm = RectifiedStitchedMosaicRecord.objects.get(pk=1)
        self.assertEqual(len(rsm.rect_datasets.all()), 4)
        
        