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
This module contains the handler for WCS 2.0 / EO-WCS DescribeCoverage requests.
"""

from eoxserver.core.system import System
from eoxserver.core.util.xmltools import DOMElementToXML
from eoxserver.services.base import BaseRequestHandler
from eoxserver.services.requests import Response
from eoxserver.services.exceptions import InvalidRequestException
from eoxserver.services.ows.wcs.encoders import WCS20EOAPEncoder

class WCS20DescribeCoverageHandler(BaseRequestHandler):
    """
    This handler generates responses to WCS 2.0 / EO-WCS DescribeCoverage
    requests. It inherits directly from :class:`~.BaseRequestHandler` and
    does NOT reuse MapServer.
    
    The workflow implemented by the handler starts with the
    :meth:`createCoverages` method and generates the coverage descriptions
    using the :class:`~.WCS20EOAPEncoder` method
    :meth:`~.WCS20EOAPEncoder.encodeCoverageDescriptions`.
    """
    
    REGISTRY_CONF = {
        "name": "WCS 2.0 DescribeCoverage Handler",
        "impl_id": "services.ows.wcs20.WCS20DescribeCoverageHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "2.0.0",
            "services.interfaces.operation": "describecoverage"
        }
    }
    
    PARAM_SCHEMA = {
        "service": {"xml_location": "/@service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/@version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"},
        "coverageids": {"xml_location": "/{http://www.opengis.net/wcs/2.0}CoverageId", "xml_type": "string[]", "kvp_key": "coverageid", "kvp_type": "stringlist"}
    }
    
    def _processRequest(self, req):
        req.setSchema(self.PARAM_SCHEMA)

        self.createCoverages(req)
        
        encoder = WCS20EOAPEncoder()
        
        return Response(
            content=DOMElementToXML(encoder.encodeCoverageDescriptions(req.coverages, True)), # TODO: Distinguish between encodeEOCoverageDescriptions and encodeCoverageDescription?
            content_type="text/xml",
            status=200
        )

    def createCoverages(self, req):
        """
        This method retrieves the coverage metadata for the coverages denoted
        by the coverageid parameter of the request. It raises an
        :exc:`~.InvalidRequestException` if the coverageid parameter is
        missing or if it contains an unknown coverage ID.
        """
        coverage_ids = req.getParamValue("coverageids")
        
        if coverage_ids is None:
            raise InvalidRequestException("Missing 'coverageid' parameter.", "MissingParameterValue", "coverageid")
        else:
            for coverage_id in coverage_ids:
                coverage = System.getRegistry().getFromFactory(
                    "resources.coverages.wrappers.EOCoverageFactory",
                    {"obj_id": coverage_id}
                )
                if coverage is None:
                    raise InvalidRequestException(
                        "No coverage with coverage id '%s' found" % coverage_id,
                        "NoSuchCoverage",
                        coverage_id
                    )
                
                req.coverages.append(coverage)

class WCS20CorrigendumDescribeCoverageHandler(WCS20DescribeCoverageHandler):
    REGISTRY_CONF = {
        "name": "WCS 2.0 DescribeCoverage Handler",
        "impl_id": "services.ows.wcs20.WCS20CorrigendumDescribeCoverageHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "2.0.1",
            "services.interfaces.operation": "describecoverage"
        }
    }
