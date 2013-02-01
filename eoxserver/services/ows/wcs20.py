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
    VersionHandlerInterface, OperationHandlerInterface
)
from eoxserver.services.owscommon import (
    OWSCommonVersionHandler, OWSCommonExceptionHandler,
    OWSCommonConfigReader
)
from eoxserver.services.ows.wcs.wcs20.getcap import (
    WCS20GetCapabilitiesHandler, WCS20CorrigendumGetCapabilitiesHandler
)
from eoxserver.services.ows.wcs.wcs20.desccov import (
    WCS20DescribeCoverageHandler, WCS20CorrigendumDescribeCoverageHandler
)
from eoxserver.services.ows.wcs.wcs20.desceo import (
    WCS20DescribeEOCoverageSetHandler, WCS20CorrigendumDescribeEOCoverageSetHandler
)
from eoxserver.services.ows.wcs.wcs20.getcov import (
    WCS20GetCoverageHandler, WCS20CorrigendumGetCoverageHandler
)


class WCS20VersionHandler(OWSCommonVersionHandler):
    SERVICE = "wcs"
    
    REGISTRY_CONF = {
        "name": "WCS 2.0 Version Handler",
        "impl_id": "services.ows.wcs20.WCS20VersionHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "2.0.0"
        }
    }
    
    def _handleException(self, req, exception):
        schemas = {
            "http://www.opengis.net/ows/2.0": "http://schemas.opengis.net/ows/2.0/owsAll.xsd"
        }
        handler = OWSCommonExceptionHandler(schemas)
        
        handler.setHTTPStatusCodes({
                "NoSuchCoverage": 404,
                "InvalidAxisLabel": 404,
                "InvalidSubsetting": 404
        })
        
        return handler.handleException(req, exception)


class WCS20CorrigendumVersionHandler(WCS20VersionHandler):
    REGISTRY_CONF = {
        "name": "WCS 2.0 Version Handler",
        "impl_id": "services.ows.wcs20.WCS20CorrigendumVersionHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "2.0.1"
        }
    }


WCS20VersionHandlerImplementation = VersionHandlerInterface.implement(WCS20VersionHandler)
WCS20CorrigendumVersionHandlerImplementation = VersionHandlerInterface.implement(WCS20CorrigendumVersionHandler)

WCS20GetCapabilitiesHandlerImplementation = OperationHandlerInterface.implement(WCS20GetCapabilitiesHandler)
WCS20CorrigendumGetCapabilitiesHandlerImplementation = OperationHandlerInterface.implement(WCS20CorrigendumGetCapabilitiesHandler)

WCS20DescribeCoverageHandlerImplementation = OperationHandlerInterface.implement(WCS20DescribeCoverageHandler)
WCS20CorrigendumDescribeCoverageHandlerImplementation = OperationHandlerInterface.implement(WCS20CorrigendumDescribeCoverageHandler)
    
WCS20DescribeEOCoverageSetHandlerImplementation = OperationHandlerInterface.implement(WCS20DescribeEOCoverageSetHandler)
WCS20CorrigendumDescribeEOCoverageSetHandlerImplementation = OperationHandlerInterface.implement(WCS20CorrigendumDescribeEOCoverageSetHandler)

WCS20GetCoverageHandlerImplementation = OperationHandlerInterface.implement(WCS20GetCoverageHandler)
WCS20CorrigendumGetCoverageHandlerImplementation = OperationHandlerInterface.implement(WCS20CorrigendumGetCoverageHandler)



