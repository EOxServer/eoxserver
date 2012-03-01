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

from eoxserver.services.interfaces import (
    ServiceHandlerInterface, VersionHandlerInterface,
    OperationHandlerInterface
)
from eoxserver.services.owscommon import OWSCommonServiceHandler

from eoxserver.services.ows.wms.common import WMS1XGetCapabilitiesHandler
from eoxserver.services.ows.wms.wms1011 import (
    WMS10VersionHandler,
    WMS110VersionHandler,
    WMS111VersionHandler,
    WMS10_11GetMapHandler
)
from eoxserver.services.ows.wms.wms13 import (
    WMS13VersionHandler,
    WMS13GetCapabilitiesHandler,
    WMS13GetMapHandler,
    WMS13GetFeatureInfoHandler,
    WMS13GetLegendGraphicHandler
)

class WMSServiceHandler(OWSCommonServiceHandler):
    REGISTRY_CONF = {
        "name": "WMS Service Handler",
        "impl_id": "services.ows.wms1x.WMSServiceHandler",
        "registry_values": {
            "services.interfaces.service": "wms"
        }
    }
    
    SERVICE = "wms"

WMSServiceHandlerImplementation = ServiceHandlerInterface.implement(WMSServiceHandler)

WMS10VersionHandlerImplementation = VersionHandlerInterface.implement(WMS10VersionHandler)

WMS110VersionHandlerImplementation = VersionHandlerInterface.implement(WMS110VersionHandler)

WMS111VersionHandlerImplementation = VersionHandlerInterface.implement(WMS111VersionHandler)

WMS13VersionHandlerImplementation = VersionHandlerInterface.implement(WMS13VersionHandler)

class WMS10GetCapabilitiesHandler(WMS1XGetCapabilitiesHandler):
    REGISTRY_CONF = {
        "name": "WMS 1.0 GetCapabilities Handler",
        "impl_id": "services.ows.wms1x.WMS10GetCapabilitiesHandler",
        "registry_values": {
            "services.interfaces.service": "wms",
            "services.interfaces.version": "1.0.0",
            "services.interfaces.operation": "getcapabilities"
        }
    }

WMS10GetCapabilitiesHandlerImplementation = OperationHandlerInterface.implement(WMS10GetCapabilitiesHandler)

class WMS110GetCapabilitiesHandler(WMS1XGetCapabilitiesHandler):
    REGISTRY_CONF = {
        "name": "WMS 1.1.0 GetCapabilities Handler",
        "impl_id": "services.ows.wms1x.WMS110GetCapabilitiesHandler",
        "registry_values": {
            "services.interfaces.service": "wms",
            "services.interfaces.version": "1.1.0",
            "services.interfaces.operation": "getcapabilities"
        }
    }

WMS110GetCapabilitiesHandlerImplementation = OperationHandlerInterface.implement(WMS110GetCapabilitiesHandler)

class WMS111GetCapabilitiesHandler(WMS1XGetCapabilitiesHandler):
    REGISTRY_CONF = {
        "name": "WMS 1.1.1 GetCapabilities Handler",
        "impl_id": "services.ows.wms1x.WMS111GetCapabilitiesHandler",
        "registry_values": {
            "services.interfaces.service": "wms",
            "services.interfaces.version": "1.1.1",
            "services.interfaces.operation": "getcapabilities"
        }
    }

WMS111GetCapabilitiesHandlerImplementation = OperationHandlerInterface.implement(WMS111GetCapabilitiesHandler)

WMS13GetCapabilitiesHandlerImplementation = OperationHandlerInterface.implement(WMS13GetCapabilitiesHandler)

class WMS10GetMapHandler(WMS10_11GetMapHandler):
    REGISTRY_CONF = {
        "name": "WMS 1.0 GetMap Handler",
        "impl_id": "services.ows.wms1x.WMS10GetMapHandler",
        "registry_values": {
            "services.interfaces.service": "wms",
            "services.interfaces.version": "1.0.0",
            "services.interfaces.operation": "getmap"
        }
    }

WMS10GetMapHandlerImplementation = OperationHandlerInterface.implement(WMS10GetMapHandler)

class WMS110GetMapHandler(WMS10_11GetMapHandler):
    REGISTRY_CONF = {
        "name": "WMS 1.1.0 GetMap Handler",
        "impl_id": "services.ows.wms1x.WMS110GetMapHandler",
        "registry_values": {
            "services.interfaces.service": "wms",
            "services.interfaces.version": "1.1.0",
            "services.interfaces.operation": "getmap"
        }
    }

WMS110GetMapHandlerImplementation = OperationHandlerInterface.implement(WMS110GetMapHandler)

class WMS111GetMapHandler(WMS10_11GetMapHandler):
    REGISTRY_CONF = {
        "name": "WMS 1.1.1 GetMap Handler",
        "impl_id": "services.ows.wms1x.WMS111GetMapHandler",
        "registry_values": {
            "services.interfaces.service": "wms",
            "services.interfaces.version": "1.1.1",
            "services.interfaces.operation": "getmap"
        }
    }

WMS111GetMapHandlerImplementation = OperationHandlerInterface.implement(WMS111GetMapHandler)

WMS13GetMapHandlerImplementation = OperationHandlerInterface.implement(WMS13GetMapHandler)

WMS13GetFeatureInfoHandlerImplementation = OperationHandlerInterface.implement(WMS13GetFeatureInfoHandler)

WMS13GetLegendGraphicHandlerImplementation = OperationHandlerInterface.implement(WMS13GetLegendGraphicHandler)
