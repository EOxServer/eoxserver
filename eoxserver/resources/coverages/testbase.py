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
from eoxserver.testing.core import EOxServerTestCase

class ManagementTestCase(EOxServerTestCase):
    """ Base class for test cases targeting the 
        synchronization functionalities.
    """
    
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
    
    # Additional fixtures can be loaded with this statement:
    # fixtures = BASE_FIXTURES + ['additional_fixtures.json']
    
    def synchronize(self, model, synchronizerCls):
        synchronizer = synchronizerCls(model)
        synchronizer.update()


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
