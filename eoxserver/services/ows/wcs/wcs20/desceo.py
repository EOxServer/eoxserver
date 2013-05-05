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
This method provides a handler for EO-WCS DescribeEOCoverageSet operations.
"""

import sys

from eoxserver.core.system import System
from eoxserver.core.util.xmltools import DOMElementToXML
from eoxserver.resources.coverages.helpers import CoverageSet
from eoxserver.services.base import BaseRequestHandler
from eoxserver.services.requests import Response
from eoxserver.services.exceptions import (
    InvalidRequestException, InvalidSubsettingException,
    InvalidAxisLabelException
)
from eoxserver.services.ows.wcs.encoders import WCS20EOAPEncoder
from eoxserver.services.ows.wcs.wcs20.common import WCS20ConfigReader
from eoxserver.services.ows.wcs.wcs20.subset import WCS20SubsetDecoder


class WCS20DescribeEOCoverageSetHandler(BaseRequestHandler):
    """
    This handler generates responses to EO-WCS DescribeEOCoverageSet requests.
    It derives directly from :class:`~.BaseRequestHandler` and does not
    reuse MapServer (as MapServer does not support EO-WCS).
    
    The implented workflow begins with a call to :meth:`createWCSEOObjects`
    and then goes on to encode the EO coverage and Dataset Series metadata.
    
    The handler is aware of the count and sections parameters of
    DescribeEOCoverageSet which allow to limit the number of coverage
    and Dataset Series descriptions returned and the sections
    (CoverageDescriptions, DatasetSeriesDescriptions, All) included in the
    requests.
    
    An :exc:`~.InvalidRequestException` will be raised if incorrect parameters
    are encountered or the mandatory eoid parameter is missing.
    """

    REGISTRY_CONF = {
        "name": "WCS 2.0 EO-AP DescribeEOCoverageSet Handler",
        "impl_id": "services.ows.wcs20.WCS20DescribeEOCoverageSetHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "2.0.0",
            "services.interfaces.operation": "describeeocoverageset"
        }
    }

    PARAM_SCHEMA = {
        "service": {"xml_location": "/service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"},
        "eoid": {"xml_location": "/{http://www.opengis.net/wcseo/1.0}eoId", "xml_type": "string[]", "kvp_key": "eoid", "kvp_type": "stringlist"}, # TODO: what about multiple ids 
        "containment": {"xml_location": "/{http://www.opengis.net/wcseo/1.0}containment", "xml_type": "string", "kvp_key": "containment", "kvp_type": "string"},
        "trims": {"xml_location": "/{http://www.opengis.net/wcs/2.0}DimensionTrim", "xml_type": "element[]"},
        "slices": {"xml_location": "/{http://www.opengis.net/wcs/2.0}DimensionSlice", "xml_type": "element[]"},
        "count": {"xml_location": "/@count", "xml_type": "string", "kvp_key": "count", "kvp_type": "string"}, #TODO: kvp location
        "sections": {"xml_location": "/ows:section", "xml_type": "string[]", "kvp_key": "sections", "kvp_type": "stringlist"}
    }

    def _processRequest(self, req):
        
        req.setSchema(self.PARAM_SCHEMA)
        
        dataset_series_set, coverages = self.createWCSEOObjects(req)
        
        if req.getParamValue("count") is not None:
            try:
                count_req = int(req.getParamValue("count"))
            except:
                raise InvalidRequestException(
                    "Non-integer 'count' parameter.",
                    "InvalidParameterValue",
                    "count"
                )
            
            if count_req < 0:
                raise InvalidRequestException(
                    "Negative 'count' parameter.",
                    "InvalidParameterValue",
                    "count"
                )
                
        else:
            count_req = sys.maxint
        
        
        count_default = WCS20ConfigReader().getPagingCountDefault()
        count_used = count_req
        if count_default is not None:
            count_used = min(count_req, count_default)
        
        count_all_coverages = len(coverages)
        if count_used < count_all_coverages:
            coverages = coverages[:count_used]
        else:
            count_used = count_all_coverages
 
        encoder = WCS20EOAPEncoder()
        
        # "sections" parameter can be on of: CoverageDescriptions, DatasetSeriesDescriptions, or All.
        sections = req.getParamValue("sections")
        if sections is None or len(sections) == 0 or\
            "CoverageDescriptions" in sections or\
            "DatasetSeriesDescriptions" in sections or\
            "All" in sections:
            if sections is not None and len(sections) != 0 and\
                "DatasetSeriesDescriptions" not in sections and "All" not in sections:
                dataset_series_set = None
            if sections is not None and len(sections) != 0 and\
                "CoverageDescriptions" not in sections and "All" not in sections:
                coverages = None

            return Response(
                content=DOMElementToXML(
                    encoder.encodeEOCoverageSetDescription(
                        dataset_series_set,
                        coverages,
                        count_all_coverages,
                        count_used
                    )
                ),
                content_type="text/xml",
                status=200
            )
        else:
            raise InvalidRequestException("'sections' parameter must be either 'CoverageDescriptions', 'DatasetSeriesDescriptions', or 'All'.", "InvalidParameterValue", "sections")

    def createWCSEOObjects(self, req):
        """
        This method returns a tuple ``(dataset_series_set, coverages)`` of
        two lists containing Dataset Series or EO Coverage objects respectively.
        It parses the request parameters in ``req`` in order to determine the
        subset of EO-WCS objects to be included.
        
        The method makes use of
        :meth:`~.WCS20SubsetDecoder.getFilterExpressions` in order to parse
        subset expressions sent with the request and to obtain filter
        expressions that restrict the subset of EO-WCS objects to be included.
        
        The method will raise :exc:`~.InvalidRequestException` if parameters
        are missing, subset expressions are invalid or if the eoid parameter
        contains unknown names.
        """
        
        eo_ids = req.getParamValue("eoid")
            
        try:
            filter_exprs = \
                WCS20SubsetDecoder(req, 4326).getFilterExpressions()
        except InvalidSubsettingException, e:
            raise InvalidRequestException(e.msg, "InvalidSubsetting", "subset")
        except InvalidAxisLabelException, e:
            raise InvalidRequestException(e.msg, "InvalidAxisLabel", "subset")
        
        if eo_ids is None:
            raise InvalidRequestException(
                "Missing 'eoid' parameter",
                "MissingParameterValue",
                "eoid"
            )
        else:
            dataset_series_set = []
            coverages = CoverageSet()
            
            for eo_id in eo_ids:
                dataset_series = System.getRegistry().getFromFactory(
                    "resources.coverages.wrappers.DatasetSeriesFactory",
                    {"obj_id": eo_id}
                )
                if dataset_series is not None:
                    dataset_series_set.append(dataset_series)
                    coverages.union(dataset_series.getEOCoverages(filter_exprs))
                    
                else:
                    coverage = System.getRegistry().getFromFactory(
                        "resources.coverages.wrappers.EOCoverageFactory",
                        {"obj_id": eo_id}
                    )
                    if coverage is not None:
                        if coverage.matches(filter_exprs):
                            coverages.add(coverage)
                        for dataset in coverage.getDatasets(filter_exprs):
                            coverages.add(dataset)
                    else:
                        raise InvalidRequestException(
                            "No coverage or dataset series with EO ID '%s' found" % eo_id,
                            "NoSuchCoverage",
                            "eoid"
                        )
            
            return (dataset_series_set, coverages.to_sorted_list())


class WCS20CorrigendumDescribeEOCoverageSetHandler(WCS20DescribeEOCoverageSetHandler):
    REGISTRY_CONF = {
        "name": "WCS 2.0 EO-AP DescribeEOCoverageSet Handler",
        "impl_id": "services.ows.wcs20.WCS20CorrigendumDescribeEOCoverageSetHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "2.0.1",
            "services.interfaces.operation": "describeeocoverageset"
        }
    }
