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

"""
This module provides factories for the Data Access Layer.
"""

from eoxserver.core.system import System
from eoxserver.core.records import (
    RecordWrapperFactoryInterface, RecordWrapperFactory
)
from eoxserver.core.exceptions import InternalError
from eoxserver.backends.models import Location

class LocationFactory(RecordWrapperFactory):
    """
    This is a factory for location wrappers. It inherits from
    :class:`~.RecordWrapperFactory`.
    """
    REGISTRY_CONF = {
        "name": "LocationFactory",
        "impl_id": "backends.factories.LocationFactory",
        "binding_method": "direct"
    }
    
    def _get_record_by_pk(self, pk):
        return Location.objects.get(pk=pk)
        
    def _get_record_wrapper(self, record):
        wrapper = self.impls[record.location_type]()
        wrapper.setRecord(record)
        
        return wrapper
        
LocationFactoryImplementation = \
RecordWrapperFactoryInterface.implement(LocationFactory)
