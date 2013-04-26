#-------------------------------------------------------------------------------
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
#-------------------------------------------------------------------------------

from eoxserver.core.system import System
from eoxserver.testing.core import (
    EOxServerTestCase, BASE_FIXTURES, CommandTestCase, CommandFaultTestCase
)
from eoxserver.resources.coverages.managers import CoverageIdManager

EXTENDED_FIXTURES = BASE_FIXTURES + ["testing_coverages.json"]

class CoverageIdManagementTestCase(EOxServerTestCase):
    """ Base class for Coverage ID management test cases. """
    
    def setUp(self):
        super(CoverageIdManagementTestCase, self).setUp()
        self.mgr = CoverageIdManager()
        self.manage()
    
    def manage(self):
        """ Override this function to extend management before testing. """
        pass

class ManagementTestCase(EOxServerTestCase):
    """ Base class for test cases targeting the 
        synchronization functionalities.
    """
    
    def setUp(self):
        super(ManagementTestCase, self).setUp()
        self.manage()
    
    def getManager(self, mgrtype=None, intf_id=None):
        if mgrtype is None:
            mgrtype = self.getType()
        if intf_id is None:
            intf_id = self.getInterfaceID()
        
        return System.getRegistry().findAndBind(
            intf_id=intf_id,
            params={
                "resources.coverages.interfaces.res_type": mgrtype
            }
        )
    
    def getInterfaceID(self):
        return "resources.coverages.interfaces.Manager"
    
    def getType(self):
        raise NotImplementedError()
    
    def manage(self):
        """ Override this function to test management functions.
        """
        pass
    
    def testContents(self):
        """ Stub testing method. Override this to make more
            sophisticated checks for errors. 
        """
        pass

class CreateTestCase(ManagementTestCase):
    def create(self, mgrtype=None, intf_id=None, **kwargs):
        mgr = self.getManager(mgrtype, intf_id)
        return mgr.create(**kwargs)
    
class UpdateTestCase(ManagementTestCase):
    def update(self, mgrtype=None, intf_id=None, **kwargs):
        mgr = self.getManager(mgrtype, intf_id)
        return mgr.update(**kwargs)

class DeleteTestCase(ManagementTestCase):
    def delete(self, obj_id, mgrtype=None, intf_id=None):
        mgr = self.getManager()
        mgr.delete(obj_id)
        
class SynchronizeTestCase(ManagementTestCase):
    def synchronize(self, obj_id, mgrtype=None, intf_id=None, **kwargs):
        mgr = self.getManager()
        mgr.synchronize(obj_id, **kwargs)

# rectified dataset test cases

class RectifiedDatasetCreateTestCase(CreateTestCase):
    def getType(self):
        return "eo.rect_dataset"

class RectifiedDatasetUpdateTestCase(UpdateTestCase):
    def getType(self):
        return "eo.rect_dataset"
    
class RectifiedDatasetDeleteTestCase(DeleteTestCase):
    def getType(self):
        return "eo.rect_dataset"

# rectified stitched mosaic manager test cases

class RectifiedStitchedMosaicCreateTestCase(CreateTestCase):
    def getType(self):
        return "eo.rect_stitched_mosaic"

class RectifiedStitchedMosaicUpdateTestCase(UpdateTestCase):
    def getType(self):
        return "eo.rect_stitched_mosaic"

class RectifiedStitchedMosaicDeleteTestCase(DeleteTestCase):
    def getType(self):
        return "eo.rect_stitched_mosaic"

class RectifiedStitchedMosaicSynchronizeTestCase(SynchronizeTestCase):
    def getType(self):
        return "eo.rect_stitched_mosaic"

# dataset series manager test cases

class DatasetSeriesCreateTestCase(CreateTestCase):
    def getType(self):
        return "eo.dataset_series"

class DatasetSeriesUpdateTestCase(UpdateTestCase):
    def getType(self):
        return "eo.dataset_series"

class DatasetSeriesDeleteTestCase(DeleteTestCase):
    def getType(self):
        return "eo.dataset_series"

class DatasetSeriesSynchronizeTestCase(SynchronizeTestCase):
    def getType(self):
        return "eo.dataset_series"


class EODatasetMixIn(object):
    def findDatasetsByFilters(self, *filters):
        """ Convenience method to get a list of coverages by given filter
        expressions.
        """
        filter_exprs = [
            System.getRegistry().getFromFactory(
                factory_id = "resources.coverages.filters.CoverageExpressionFactory",
                params = filter_expr
            )
            for filter_expr in filters
        ]
        
        return System.getRegistry().bind(
            "resources.coverages.wrappers.EOCoverageFactory"
        ).find(
            impl_ids = [
                "resources.coverages.wrappers.RectifiedDatasetWrapper",
                "resources.coverages.wrappers.ReferenceableDatasetWrapper"
            ],
            filter_exprs = filter_exprs
        )
     
    def getDatasetById(self, cid):
        """ Convenience method to get a coverage by its ID.
        """
        return System.getRegistry().getFromFactory(
            "resources.coverages.wrappers.EOCoverageFactory",
            {"obj_id": cid}
        )


class RectifiedStitchedMosaicMixIn(object):
    def getStitchedMosaicById(self, cid):
        return System.getRegistry().getFromFactory(
            "resources.coverages.wrappers.EOCoverageFactory",
            {"obj_id": cid}
        )


class DatasetSeriesMixIn(object):
    def getDatasetSeriesById(self, eoid):
        return System.getRegistry().getFromFactory(
            "resources.coverages.wrappers.DatasetSeriesFactory",
            {"obj_id": eoid}
        )


class CoverageCommandTestCase(CommandTestCase):
    fixtures = EXTENDED_FIXTURES


class CoverageCommandFaultTestCase(CommandFaultTestCase):
    pass

class CommandRegisterDatasetTestCase(CoverageCommandTestCase, EODatasetMixIn):
    fixtures = BASE_FIXTURES # normally we want an empty database
    
    name = "eoxs_register_dataset"
    coverages_to_be_registered = [] # list of dicts with two keys allowed:
                                    # 'eo_id', 'coverage_id'
    
    def getCoveragesToBeRegistered(self):
        result = {}
        for ctbr in self.coverages_to_be_registered:
            eo_id = ctbr.get("eo_id")
            coverage_id = ctbr.get("coverage_id")
            coverage = None
            
            if eo_id:
                try:
                    coverage = self.findDatasetsByFilters({
                        "op_name": "attr",
                        "operands": ("eo_id", "=", eo_id)
                    })[0]
                except IndexError:
                    pass
            
            if coverage_id:
                coverage = self.getDatasetById(coverage_id)
            result[eo_id or coverage_id] = coverage
            
        return result
    
    def testCoverageRegistered(self):
        for cid, coverage in self.getCoveragesToBeRegistered().items():
            if not coverage:
                self.fail("Coverage with ID '%s' was not inserted." % cid)


class CommandInsertTestCase(CoverageCommandTestCase, DatasetSeriesMixIn, EODatasetMixIn):
    name = "eoxs_insert_into_series"
    
    datasets_to_be_inserted = []
    dataset_series_id = "MER_FRS_1P_RGB_reduced"
    
    def testContents(self):
        dss = self.getDatasetSeriesById(self.dataset_series_id)
        for dataset_id in self.datasets_to_be_inserted:
            self.assertIn(dataset_id, [coverage.getCoverageId() 
                                       for coverage in dss.getEOCoverages()])

 
class CommandExcludeTestCase(CoverageCommandTestCase, DatasetSeriesMixIn, EODatasetMixIn):
    name = "eoxs_remove_from_series"
    
    datasets_to_be_excluded = []
    dataset_series_id = "MER_FRS_1P_RGB_reduced"
    
    def testContents(self):
        dss = self.getDatasetSeriesById(self.dataset_series_id)
        for dataset_id in self.datasets_to_be_excluded:
            self.assertNotIn(dataset_id, [coverage.getCoverageId() 
                                          for coverage in dss.getEOCoverages()])
