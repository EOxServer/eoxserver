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
