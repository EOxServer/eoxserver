#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Martin Paces <martin.paces@eox.at>
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

"""
This module implements variaous managers providing API for operation over 
the stored datasets. For details of the provided functionality see the
documentation of the individual manager classes. 
"""

from eoxserver.core.system import System
from eoxserver.resources.coverages.interfaces import ManagerInterface

#-------------------------------------------------------------------------------
# manifest of the exported objects  

__all__ = [ 
    "CoverageIdManager",
    "BaseManager",
    "BaseManagerContainerMixIn",
    "CoverageManager",
    "CoverageManagerDatasetMixIn",
    "CoverageManagerEOMixIn",
    "EODatasetManager",
    "RectifiedDatasetManager",
    "ReferenceableDatasetManager",
    "RectifiedStitchedMosaicManager",
    "DatasetSeriesManager",
    "RectifiedDatasetManagerImplementation",
    "ReferenceableDatasetManagerImplementation",
    "RectifiedStitchedMosaicManagerImplementation",
    "DatasetSeriesManagerImplementation",
]

#-------------------------------------------------------------------------------
# load managers' classes

from id_manager import CoverageIdManager
from base import BaseManager
from base import BaseManagerContainerMixIn
from coverage import CoverageManager
from coverage import CoverageManagerDatasetMixIn
from coverage import CoverageManagerEOMixIn
from eo_ds import EODatasetManager
from eo_ds_rect import RectifiedDatasetManager
from eo_ds_ref import ReferenceableDatasetManager
from eo_sm_rect import RectifiedStitchedMosaicManager
from eo_ds_series import DatasetSeriesManager

#-------------------------------------------------------------------------------
# create managers' implementations 
        
RectifiedDatasetManagerImplementation = \
    ManagerInterface.implement(RectifiedDatasetManager)
    
ReferenceableDatasetManagerImplementation = \
    ManagerInterface.implement(ReferenceableDatasetManager)
    
RectifiedStitchedMosaicManagerImplementation = \
    ManagerInterface.implement(RectifiedStitchedMosaicManager)

DatasetSeriesManagerImplementation = \
    ManagerInterface.implement(DatasetSeriesManager)

#-------------------------------------------------------------------------------
# helper functions returning the managers' instances 

def __get_manager( class_obj ) : 

    return System.getRegistry().findAndBind(
            intf_id="resources.coverages.interfaces.Manager",
            params={ "resources.coverages.interfaces.res_type":class_obj._type}) 


def getRectifiedDatasetManager(): 
    """ get instance/implementation of ``RectifiedDatasetManager`` """ 
    return __get_manager( RectifiedDatasetManager ) 

def getReferenceableDatasetManager(): 
    """ get instance/implementation of ``ReferenceableDatasetManager`` """ 
    return __get_manager( ReferenceableDatasetManager ) 

def getRectifiedStitchedMosaicManager(): 
    """ get instance/implementation of ``RectifiedStitchedMosaicManager`` """ 
    return __get_manager( RectifiedStitchedMosaicManager ) 

def getDatasetSeriesManager(): 
    """ get instance/implementation of ``DatasetSeriesManager`` """ 
    return __get_manager( DatasetSeriesManager ) 

#-------------------------------------------------------------------------------
