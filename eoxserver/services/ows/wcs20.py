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

import re
import os.path
import sys
from xml.dom import minidom

from django.conf import settings
from django.contrib.gis.geos import Polygon

import logging

from eoxserver.core.system import System
from eoxserver.core.exceptions import( 
    InternalError, UnknownCRSException, UnknownParameterFormatException,
    InvalidExpressionError
)
from eoxserver.core.util.xmltools import DOMtoXML, DOMElementToXML
from eoxserver.core.util.timetools import getDateTime
from eoxserver.core.util.geotools import getSRIDFromCRSURI
from eoxserver.resources.coverages.filters import (
    BoundedArea, Slice, TimeInterval
)
from eoxserver.resources.coverages.exceptions import (
    NoSuchCoverageException, NoSuchDatasetSeriesException
)
from eoxserver.services.interfaces import (
    VersionHandlerInterface, OperationHandlerInterface
)
from eoxserver.services.base import BaseRequestHandler
from eoxserver.services.requests import Response
from eoxserver.services.owscommon import (
    OWSCommonVersionHandler, OWSCommonExceptionHandler,
    OWSCommonConfigReader
)
from eoxserver.services.mapserver import (
    gdalconst_to_imagemode, gdalconst_to_imagemode_string
)
from eoxserver.services.exceptions import (
    InvalidRequestException, InvalidAxisLabelException,
    InvalidSubsettingException
)
from eoxserver.services.ows.wcs.common import WCSCommonHandler
from eoxserver.services.ows.wcs.encoders import WCS20Encoder, WCS20EOAPEncoder

from eoxserver.contrib import mapscript

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
        handler = OWSCommonExceptionHandler()
        
        handler.setHTTPStatusCodes({
                "NoSuchCoverage": 404,
                "InvalidAxisLabel": 404,
                "InvalidSubsetting": 404
        })
        
        return handler.handleException(req, exception)

WCS20VersionHandlerImplementation = VersionHandlerInterface.implement(WCS20VersionHandler)

class WCS20GetCapabilitiesHandler(WCSCommonHandler):
    SERVICE = "wcs"
    
    REGISTRY_CONF = {
        "name": "WCS 2.0 GetCapabilities Handler",
        "impl_id": "services.ows.wcs20.WCS20GetCapabilitiesHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "2.0.0",
            "services.interfaces.operation": "getcapabilities"
        }
    }
    
    PARAM_SCHEMA = {
        "service": {"xml_location": "/@ows:service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/@ows:version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"},
        "updatesequence": {"xml_location": "/@ows:updateSequence", "xml_type": "string", "kvp_key": "updatesequence", "kvp_type": "string"},
        #"coveragesubtype": {"xml_location": "/@wcseo:coverageSubtype", "xml_type": "string", "kvp_key": "coveragesubtype", "kvp_type": "string"},
        "sections": {"xml_location": "/ows:section", "xml_type": "string[]", "kvp_key": "sections", "kvp_type": "stringlist"}
    }
    
    # TODO: override createCoverages, configureRequest, configureMapObj
    def createCoverages(self, ms_req):
        #cov_subtype = ms_req.getParamValue("coveragesubtype")
        #if cov_subtype is not None:
            #if cov_subtype.lower() == "scene":
                #ms_req.coverages = EOxSCoverageInterfaceFactory.getCoverageInterfacesByType("file")
            #elif cov_subtype.lower() == "datasetseries":
                #ms_req.coverages = EOxSCoverageInterfaceFactory.getCoverageInterfacesByType("eo.collection")
            #else:
                #raise EOxSInvalidRequestException("Unknown coverage subtype '%s'" % cov_subtype, "InvalidParameterValue", "coverageSubtype")
        #else:
        visible_expr = System.getRegistry().getFromFactory(
            "resources.coverages.filters.CoverageExpressionFactory",
            {"op_name": "attr", "operands": ("visible", "=", True)}
        )
        
        factory = System.getRegistry().bind("resources.coverages.wrappers.EOCoverageFactory")
        ms_req.coverages = factory.find(filter_exprs=[visible_expr])
    
    def getMapServerLayer(self, coverage, **kwargs):
        layer = super(WCS20GetCapabilitiesHandler, self).getMapServerLayer(coverage, **kwargs)
        
        datasets = coverage.getDatasets()
        
        if len(datasets) == 0:
            raise InternalError("Misconfigured coverage '%s' has no file data." % coverage.getCoverageId())
        else:
            layer.data = os.path.abspath(datasets[0].getFilename()) # we just need an arbitrary file here
        
        return layer

    def postprocess(self, ms_req, resp):
        dom = minidom.parseString(resp.content)
        
        # change xsi:schemaLocation
        schema_location_attr = dom.documentElement.getAttributeNode("xsi:schemaLocation")
        schema_location_attr.nodeValue = "http://www.opengis.net/wcseo/1.0 http://schemas.opengis.net/wcseo/1.0/wcsEOAll.xsd"
        
        # we are finished if the response is an ows:ExceptionReport
        # proceed otherwise
        if dom.documentElement.localName != "ExceptionReport":
        
            encoder = WCS20EOAPEncoder()

            svc_identification = dom.getElementsByTagName("ows:ServiceIdentification").item(0)
            
            # append EO Profiles to ServiceIdentification
            if svc_identification is not None:
                eo_profiles = encoder.encodeEOProfiles()
                
                profiles = svc_identification.getElementsByTagName("ows:Profile")
                if len(profiles) == 0:
                    for eo_profile in eo_profiles:
                        svc_identification.appendChild(eo_profile)
                else:
                    for eo_profile in eo_profiles:
                        svc_identification.insertBefore(eo_profile, profiles.item(0))
                    
            # append DescribeEOCoverageSet
            op_metadata = dom.getElementsByTagName("ows:OperationsMetadata").item(0)
            
            if op_metadata is not None:
                desc_eo_cov_set_op = encoder.encodeDescribeEOCoverageSetOperation(
                    OWSCommonConfigReader().getHTTPServiceURL()
                )

                op_metadata.appendChild(desc_eo_cov_set_op)
                
                op_metadata.appendChild(encoder.encodeCountDefaultConstraint(100)) # TODO remove hardcoded number and make it configurable


            # rewrite wcs:Contents
            # adjust wcs:CoverageSubtype and add wcseo:DatasetSeriesSummary
            sections = ms_req.getParamValue("sections")
            
            if sections is None or len(sections) == 0 or "Contents" in sections or\
               "CoverageSummary" in sections or\
               "DatasetSeriesSummary" in sections:
                
                contents_new = encoder.encodeContents()

                # adjust wcs:CoverageSubtype
                if sections is None or len(sections) == 0 or "Contents" in sections or\
                   "CoverageSummary" in sections:
                    
                    for coverage in ms_req.coverages:
                        cov_summary = encoder.encodeCoverageSummary(coverage)
                        contents_new.appendChild(cov_summary)

                # append dataset series summaries
                if sections is None or len(sections) == 0 or "Contents" in sections or\
                   "DatasetSeriesSummary" in sections:
                    
                    dss_factory = System.getRegistry().bind(
                        "resources.coverages.wrappers.DatasetSeriesFactory"
                    )
                    
                    for dataset_series in dss_factory.find():
                        dss_summary = encoder.encodeDatasetSeriesSummary(dataset_series)
                        contents_new.appendChild(dss_summary)

                contents_old = dom.getElementsByTagName("wcs:Contents").item(0) 

                if contents_old is None:
                    dom.documentElement.appendChild(contents_new)
                else:
                    contents_old.parentNode.replaceChild(contents_new, contents_old)
        
        # rewrite XML and replace it in the response
        resp.content = DOMtoXML(dom)
        dom.unlink()
        
        return resp

WCS20GetCapabilitiesHandlerImplementation = OperationHandlerInterface.implement(WCS20GetCapabilitiesHandler)

class WCS20DescribeCoverageHandler(BaseRequestHandler):
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
        "service": {"xml_location": "/@ows:service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/@ows:version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"},
        "coverageids": {"xml_location": "/wcs:CoverageId", "xml_type": "string[]", "kvp_key": "coverageid", "kvp_type": "stringlist"}
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

WCS20DescribeCoverageHandlerImplementation = OperationHandlerInterface.implement(WCS20DescribeCoverageHandler)

class WCS20DescribeEOCoverageSetHandler(BaseRequestHandler):
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
        "service": {"xml_location": "/@ows:service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/@ows:version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"},
        "eoid": {"xml_location": "/wcseo:eoId", "xml_type": "string[]", "kvp_key": "eoid", "kvp_type": "stringlist"}, # TODO: what about multiple ids 
        "containment": {"xml_location": "/wcseo:containment", "xml_type": "string", "kvp_key": "containment", "kvp_type": "string"},
        "trims": {"xml_location": "/wcs:DimensionTrim", "xml_type": "element[]"},
        "slices": {"xml_location": "/wcs:DimensionSlice", "xml_type": "element[]"},
        "count": {"xml_location": "/@count", "xml_type": "string", "kvp_key": "count", "kvp_type": "string"} #TODO: kvp location
    }

    def _processRequest(self, req):
        req.setSchema(self.PARAM_SCHEMA)
        
        dataset_series_set, req_coverages = self.createWCSEOObjects(req)
        
        try:
            filter_exprs = \
                WCS20SubsetDecoder(req, 4326).getFilterExpressions()
        except InvalidSubsettingException, e:
            raise InvalidRequestException(e.msg, "InvalidSubsetting", "subset")
        except InvalidAxisLabelException, e:
            raise InvalidRequestException(e.msg, "InvalidAxisLabel", "subset")
        
        output_coverages = []
        output_coverages.extend(req_coverages)
        
        for coverage in req_coverages:
            if coverage.getType() == "eo.rect_stitched_mosaic":
                output_coverages.extend(
                    coverage.getDatasets(filter_exprs=filter_exprs)
                )
        
        for dataset_series in dataset_series_set:
            output_coverages.extend(
                dataset_series.getEOCoverages(filter_exprs=filter_exprs)
            )

        # TODO: find out config value 'count'
        # subset returned dataset series/coverages to min(count from config, count from req)
        
        count_req = sys.maxint
        if req.getParamValue("count") is not None:
            count_req = int(req.getParamValue("count"))
        
        count_default = WCS20ConfigReader().getPagingCountDefault()
        count_used = min(count_req, count_default)
        
        count_all_coverages = len(output_coverages)
        if count_used < count_all_coverages:
            output_coverages = output_coverages[:count_used]
        else:
            count_used = count_all_coverages
 
        encoder = WCS20EOAPEncoder()
        
        return Response(
            content=DOMElementToXML(
                encoder.encodeEOCoverageSetDescription(
                    dataset_series_set,
                    output_coverages,
                    count_all_coverages,
                    count_used
                )
            ), #TODO: Invoke with all datasetseries and EOCoverage elements.
            content_type="text/xml",
            status=200
        )

    def createWCSEOObjects(self, req):
        eo_ids = req.getParamValue("eoid")
            
        if eo_ids is None:
            raise InvalidRequestException(
                "Missing 'eoid' parameter",
                "MissingParameterValue",
                "eoid"
            )
        else:
            dataset_series_set = []
            coverages = []
            
            for eo_id in eo_ids:
                dataset_series = System.getRegistry().getFromFactory(
                    "resources.coverages.wrappers.DatasetSeriesFactory",
                    {"obj_id": eo_id}
                )
                
                if dataset_series is not None:
                    dataset_series_set.append(dataset_series)
                else:
                    coverage = System.getRegistry().getFromFactory(
                        "resources.coverages.wrappers.EOCoverageFactory",
                        {"obj_id": eo_id}
                    )
                    
                    if coverage is not None:
                        coverages.append(coverage)
                    else:
                        raise InvalidRequestException(
                            "No coverage or dataset series with EO ID '%s' found" % eo_id,
                            "NoSuchCoverage",
                            "eoid"
                        )
                        
            return (dataset_series_set, coverages)
    
WCS20DescribeEOCoverageSetHandlerImplementation = OperationHandlerInterface.implement(WCS20DescribeEOCoverageSetHandler)

class WCS20GetCoverageHandler(WCSCommonHandler):
    REGISTRY_CONF = {
        "name": "WCS 2.0 GetCoverage Handler",
        "impl_id": "services.ows.wcs20.WCS20GetCoverageHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "2.0.0",
            "services.interfaces.operation": "getcoverage"
        }
    }

    PARAM_SCHEMA = {
        "service": {"xml_location": "/@ows:service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/@ows:version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"},
        "coverageid": {"xml_location": "/wcs:CoverageId", "xml_type": "string", "kvp_key": "coverageid", "kvp_type": "string"},
        "trims": {"xml_location": "/wcs:DimensionTrim", "xml_type": "element[]"},
        "slices": {"xml_location": "/wcs:DimensionSlice", "xml_type": "element[]"},
        "format": {"xml_location": "/wcs:Format", "xml_type": "string", "kvp_key": "format", "kvp_type": "string"},
        "mediatype": {"xml_location": "/wcs:Mediatype", "xml_type": "string", "kvp_key": "mediatype", "kvp_type": "string"}
    }
    
    def createCoverages(self, ms_req):
        coverage_id = ms_req.getParamValue("coverageid")
            
        if coverage_id is None:
            raise InvalidRequestException("Missing 'coverageid' parameter", "MissingParameterValue", "coverageid")
        else:
            coverage = System.getRegistry().getFromFactory(
                "resources.coverages.wrappers.EOCoverageFactory",
                {"obj_id": coverage_id}
            )
            
            if coverage is not None:
                ms_req.coverages.append(coverage)
            else:
                raise InvalidRequestException(
                    e.msg, "NoSuchCoverage", coverage_id
                )

    def _setParameter(self, ms_req, key, value):
        if key.lower() == "format" and len(ms_req.coverages[0].getRangeType().bands) > 3:
            if value.lower() == "image/tiff":
                super(WCS20GetCoverageHandler, self)._setParameter(ms_req, "format", "GTiff_")
            else:
                raise InvalidRequestException("Format '%s' is not allowed in coverages with more than three bands." % value, "InvalidParameterValue", key)
        else:
            super(WCS20GetCoverageHandler, self)._setParameter(ms_req, key, value)
    
    def configureMapObj(self, ms_req):
        super(WCS20GetCoverageHandler, self).configureMapObj(ms_req)
        
        output_format = mapscript.outputFormatObj("GDAL/GTiff", "GTiff_")
        output_format.mimetype = "image/tiff"
        output_format.extension = "tif"
        
        coverage = ms_req.coverages[0]
        rangetype = coverage.getRangeType()
        
        output_format.imagemode = gdalconst_to_imagemode(
            ms_req.coverages[0].getRangeType().data_type
        )
        
        ms_req.map.appendOutputFormat(output_format)
        ms_req.map.setOutputFormat(output_format)
        
        logging.debug("WCS20GetCoverageHandler.configureMapObj: %s" % ms_req.map.imagetype)

    def addLayers(self, ms_req):
        decoder = WCS20SubsetDecoder(ms_req, "imageCRS")
        filter_exprs = decoder.getFilterExpressions()

        for coverage in ms_req.coverages:
            ms_req.map.insertLayer(self.getMapServerLayer(coverage, filter_exprs=filter_exprs))

    def getMapServerLayer(self, coverage, **kwargs):
        layer = super(WCS20GetCoverageHandler, self).getMapServerLayer(coverage, **kwargs)
        
        if coverage.getType() in ("file", "eo.rect_dataset"):

            datasets = coverage.getDatasets(
                filter_exprs = kwargs.get("filter_exprs", [])
            )
            
            if len(datasets) == 0:
                raise InvalidRequestException("Image extent does not intersect with desired region.", "ExtentError", "extent") # TODO: check if this is the right exception report
            elif len(datasets) == 1:
                layer.data = os.path.abspath(datasets[0].getFilename())
                
            else:
                raise InternalError("A single file or EO dataset should never return more than one dataset.")
            
        elif coverage.getType() == "eo.rect_stitched_mosaic":
           
            layer.tileindex = os.path.abspath(coverage.getShapeFilePath())
            layer.tileitem = "location"
        
        # this was under the "eo.rect_mosaic"-path. minor accurracy issues
        # have evolved since making it accissible to all paths
             
        extent = coverage.getExtent()
        srid = coverage.getSRID()
        size = coverage.getSize()
        rangetype = coverage.getRangeType()
        resolution = ((extent[2]-extent[0]) / float(size[0]),
                      (extent[1]-extent[3]) / float(size[1]))
        
        layer.setMetaData("wcs_extent", "%.10f %.10f %.10f %.10f" % extent)
        layer.setMetaData("wcs_resolution", "%f %f" % resolution)
        layer.setMetaData("wcs_size", "%d %d" % size)
        layer.setMetaData("wcs_nativeformat", "GTiff")
        layer.setMetaData("wcs_bandcount", "%d" % len(rangetype.bands))

        bands = " ".join([band.name for band in rangetype.bands])
        layer.setMetaData("wcs_band_names", bands)
        
        layer.setMetaData("wcs_interval",
                          "%f %f" % rangetype.getAllowedValues())
            
        layer.setMetaData("wcs_significant_figures",
                          "%d" % rangetype.getSignificantFigures())
        
        # set layer depending metadata
        for band in rangetype.bands:
            axis_metadata = {
                "%s_band_description" % band.name: band.description,
                "%s_band_definition" % band.name: band.definition,
                "%s_band_uom" % band.name: band.uom
            }
            for key, value in axis_metadata.items():
                if value != '':
                    layer.setMetaData(key, value)
        
        
        layer.setMetaData("wcs_formats", "GTiff_")
        layer.setMetaData(
            "wcs_imagemode", 
            gdalconst_to_imagemode_string(rangetype.data_type)
        )
        
        return layer

    def postprocess(self, ms_req, resp):
        coverage_id = ms_req.getParamValue("coverageid")
        
        if ms_req.coverages[0].getType() == "eo.rect_stitched_mosaic":
            include_composed_of = False #True

        else:
            include_composed_of = False
            poly = None
        
        resp.splitResponse()
        
        if resp.ms_response_xml:
            dom = minidom.parseString(resp.ms_response_xml)
            rectified_grid_coverage = dom.getElementsByTagName("gmlcov:RectifiedGridCoverage").item(0)
            
            if rectified_grid_coverage is not None:
                encoder = WCS20EOAPEncoder()
                
                if ms_req.coverages[0].getType() == "eo.rect_dataset":
                    resp_xml = encoder.encodeRectifiedDataset(
                        ms_req.coverages[0],
                        req = ms_req,
                        nodes = rectified_grid_coverage.childNodes
                    )
                elif ms_req.coverages[0].getType() == "eo.rect_stitched_mosaic":
                    decoder = WCS20SubsetDecoder(ms_req, "imageCRS")
                    
                    poly = decoder.getBoundingPolygon(
                         ms_req.coverages[0].getFootprint(),
                         ms_req.coverages[0].getSRID(),
                         ms_req.coverages[0].getSize()[0],
                         ms_req.coverages[0].getSize()[1],
                         ms_req.coverages[0].getExtent()
                    )

                    resp_xml = encoder.encodeRectifiedStitchedMosaic(
                        ms_req.coverages[0],
                        req = ms_req,
                        nodes = rectified_grid_coverage.childNodes,
                        poly = poly
                    )
                    

                resp = resp.getProcessedResponse(DOMElementToXML(resp_xml))
                dom.unlink()

        return resp

WCS20GetCoverageHandlerImplementation = OperationHandlerInterface.implement(WCS20GetCoverageHandler)

class WCS20SubsetDecoder(object):
    def __init__(self, req, default_crs_id=None):
        self.req = req
        self.default_crs_id = default_crs_id
        
        self.slices = None
        self.trims = None
        
        self.containment = "overlaps"
    
    def _decodeKVPExpression(self, key, value):
        match = re.match(
            r'(\w+)(,([^(]+))?\(([^,]*)(,([^)]*))?\)', value
        )
        if match is None:
            raise InvalidRequestException(
                "Invalid subsetting operation '%s=%s'" % (key, value),
                "InvalidSubsetting",
                key
            )
        else:
            axis_label = match.group(1)
            crs = match.group(3)
            
            if match.group(6) is not None:
                subset = (axis_label, crs, match.group(4), match.group(6))
                subset_type = "trim"
            else:
                subset = (axis_label, crs, match.group(4))
                subset_type = "slice"

        return (subset, subset_type)
    
    def _decodeKVP(self):
        trims = []
        slices = []
        
        for key, values in self.req.getParams().items():
            if key.startswith("subset"):
                for value in values:
                    subset, subset_type = \
                        self._decodeKVPExpression(key, value)
                    
                    if subset_type == "trim":
                        trims.append(subset)
                    else:
                        slices.append(subset)
        
        self.trims = trims
        self.slices = slices
    
    def _decodeXML(self):
        trims = []
        slices = []
        
        slice_elements = self.req.getParamValue("slices")
        trim_elements = self.req.getParamValue("trims")
        
        for slice_element in slice_elements:
            axis_label = slice_element.getElementsByTagName("wcs:Dimension")[0].firstChild.data
            crs = None
            slice_point = slice_element.getElementsByTagName("wcs:SlicePoint")[0].firstChild.data
            
            slices.append((axis_label, crs, slice_point))
            
        for trim_element in trim_elements:
            axis_label = trim_element.getElementsByTagName("wcs:Dimension")[0].firstChild.data
            crs = None
            trim_low = trim_element.getElementsByTagName("wcs:TrimLow")[0].firstChild.data
            trim_high = trim_element.getElementsByTagName("wcs:TrimHigh")[0].firstChild.data
        
            trims.append((axis_label, crs, trim_low, trim_high))
            
        self.slices = slices
        self.trims = trims
    
    def _decode(self):
        if self.req.getParamType() == "kvp":
            self._decodeKVP()
        else:
            self._decodeXML()
        
        try:
            self.containment = \
                self.req.getParamValue("containment", "overlaps")
        except:
            pass
    
    def _getSliceExpression(self, slice):
        axis_label = slice[0]
        
        if axis_label in ("t", "time", "phenomenonTime"):
            return self._getTimeSliceExpression(slice)
        else:
            return self._getSpatialSliceExpression(slice)
        
    def _getTimeSliceExpression(self, slice):
        axis_label = slice[0]
        
        if slice[1] is not None and \
           slice[1] != "http://www.opengis.net/def/trs/ISO-8601/0/Gregorian+UTC":
            raise InvalidSubsettingException(
                "Time reference system '%s' not recognized. Please use UTC." %\
                slice[1]
            )
        
        if not slice[2].startswith('"') and slice[2].endswith('"'):
            raise InvalidSubsettingException(
                "Date/Time tokens have to be enclosed in quotation marks (\")"
            )
        else:
            dt_str = slice[2].strip('"')
        
        try:
            slice_point = getDateTime(dt_str)
        except:
            raise InvalidSubsettingException(
                "Could not convert slice point token '%s' to date/time." %\
                dt_str
            )
        
        return System.getRegistry().getFromFactory(
            "resources.coverages.filters.CoverageExpressionFactory",
            {"op_name": "time_slice", "operands": (slice_point,)}
        )
        
    def _getSpatialSliceExpression(self, slice):
        axis_label = slice[0]
        
        if slice[1] is None:
            crs_id = self.default_crs_id
        else:
            try:
                crs_id = getSRIDFromCRSURI(slice[1])
            except:
                raise InvalidSubsettingException(
                    "Unrecognized CRS URI '%s'" % slice[1]
                )
        
        try:
            slice_point = float(slice[2])
        except:
            raise InvalidSubsettingException(
                "Could not convert slice point token '%s' to number." %\
                slice[2]
            )
        
        return System.getRegistry().getFromFactory(
            "resources.coverages.filters.CoverageExpressionFactory",
            {
                "op_name": "spatial_slice",
                "operands": (Slice(
                    axis_label = axis_label,
                    crs_id = crs_id,
                    slice_point = slice_point
                ),)
            }
        )
    
    def _getTrimExpressions(self, trims):
        time_intv, crs_id, x_bounds, y_bounds = self._decodeTrims(trims)
        
        if self.containment == "overlaps":
            op_part = "intersects"
        elif self.containment == "contains":
            op_part = "within"
        else:
            raise InvalidParameterException(
                "Unknown containment mode '%s'."
            )
        
        filter_exprs = []
            
        if time_intv is not None:
            filter_exprs.append(System.getRegistry().getFromFactory(
                "resources.coverages.filters.CoverageExpressionFactory",
                {
                    "op_name": "time_%s" % op_part,
                    "operands": (time_intv,)
                }
            ))
        
        if x_bounds is None and y_bounds is None:
            pass
        else:
            # NOTE: cannot filter w.r.t. imageCRS
            if crs_id != "imageCRS":
                if x_bounds is None:
                    x_bounds = ("unbounded", "unbounded")
                
                if y_bounds is None:
                    y_bounds = ("unbounded", "unbounded")
                
                try:
                    area = BoundedArea(
                        crs_id,
                        x_bounds[0],
                        y_bounds[0],
                        x_bounds[1],
                        y_bounds[1]
                    )
                except InvalidExpressionError, e:
                    raise InvalidSubsettingException(str(e))
                    
                filter_exprs.append(System.getRegistry().getFromFactory(
                    "resources.coverages.filters.CoverageExpressionFactory",
                    {
                        "op_name": "footprint_%s_area" % op_part,
                        "operands": (area,)
                    }
                ))
        
        return filter_exprs

    def _decodeTrims(self, trims):
        time_intv = None
        crs_id = None
        x_bounds = None
        y_bounds = None
        
        for trim in trims:
            if trim[0] in ("t", "time", "phenomenonTime"):
                if time_intv is None:
                    begin = self._getDateTimeBound(trim[2])
                    end = self._getDateTimeBound(trim[3])
                    
                    try:
                        time_intv = TimeInterval(begin, end)
                    except Exception, e:
                        raise InvalidSubsettingException(str(e))
                else:
                    raise InvalidSubsettingException(
                        "Multiple definitions for time subsetting."
                    )
            elif trim[0] in ("x", "lon", "long", "Long"):
                if x_bounds is None:
                    new_crs_id = self._getCRSID(trim[1])
                    
                    if crs_id is None:
                        crs_id = new_crs_id
                    elif crs_id != new_crs_id:
                        raise InvalidSubsettingException(
                            "CRSs for multiple spatial trims must be the same."
                        )
                        
                    x_bounds = (
                        self._getCoordinateBound(trim[2]),
                        self._getCoordinateBound(trim[3])
                    )
                else:
                    raise InvalidSubsettingException(
                        "Multiple definitions for first spatial axis subsetting."
                    )
            elif trim[0] in ("y", "lat", "Lat"):
                if y_bounds is None:
                    new_crs_id = self._getCRSID(trim[1])
                    
                    if crs_id is None:
                        crs_id = new_crs_id
                    elif crs_id != new_crs_id:
                        raise InvalidSubsettingException(
                            "CRSs for multiple spatial trims must be the same."
                        )
                    
                    y_bounds = (
                        self._getCoordinateBound(trim[2]),
                        self._getCoordinateBound(trim[3])
                    )
                else:
                    raise InvalidSubsettingException(
                        "Multiple definitions for second spatial axis subsetting."
                    )
            else:
                raise InvalidAxisLabelException(
                    "Invalid axis label '%s'." % trim[0]
                )
        
        return (time_intv, crs_id, x_bounds, y_bounds)
        
    
    def _getDateTimeBound(self, token):
        if token is None:
            return "unbounded"
        else:
            if not token.startswith('"') or not token.endswith('"'):
                raise InvalidSubsettingException(
                    "Date/Time tokens have to be enclosed in quotation marks (\")"
                )
            else:
                dt_str = token.strip('"')
            
            try:
                return getDateTime(dt_str)
            except:
                raise InvalidSubsettingException(
                    "Cannot convert token '%s' to Date/Time." % token
                )
    
    def _getCoordinateBound(self, token):
        if token is None:
            return "unbounded"
        else:
            try:
                return float(token)
            except:
                raise InvalidSubsettingException(
                    "Cannot convert token '%s' to number." % token
                )
    
    def _getCRSID(self, crs_expr):
        if crs_expr is None:
            return self.default_crs_id
        else:
            try:
                return getSRIDFromCRSURI(crs_expr)
            except Exception, e:
                raise InvalidSubsettingException(e.msg)
    
    def getFilterExpressions(self):
        self._decode()
        
        filter_exprs = []
        
        for slice in self.slices:
            filter_exprs.append(self._getSliceExpression(slice))
            
        filter_exprs.extend(self._getTrimExpressions(self.trims))
        
        return filter_exprs
    
    def getBoundingPolygon(self, footprint, srid, size_x, size_y, extent):
        self._decode()
        
        time_intv, crs_id, x_bounds, y_bounds = \
            self._decodeTrims(self.trims)
        
        if x_bounds is None and y_bounds is None:
            return None
        
        if x_bounds is None:
            x_bounds = ("unbounded", "unbounded")
        if y_bounds is None:
            y_bounds = ("unbounded", "unbounded")
        
        if crs_id == "imageCRS":
            if x_bounds[0] == "unbounded":
                minx = extent[0]
            else:
                l = max(float(x_bounds[0]) / float(size_x), 0.0)
                minx = extent[0] + l * (extent[2] - extent[0])
            
            if y_bounds[0] == "unbounded":
                miny = extent[1]
            else:
                l = max(float(y_bounds[0]) / float(size_y), 0.0)
                miny = extent[3] - l * (extent[3] - extent[1])
            
            if x_bounds[1] == "unbounded":
                maxx = extent[2]
            else:
                l = min(float(x_bounds[1]) / float(size_x), 1.0)
                maxx = extent[0] + l * (extent[2] - extent[0])
            
            if y_bounds[1] == "unbounded":
                maxy = extent[3]
            else:
                l = min(float(y_bounds[1]) / float(size_y), 1.0)
                maxy = extent[3] - l * (extent[3] - extent[1])
            
            poly = Polygon.from_bbox((minx, miny, maxx, maxy))
            poly.srid = srid
        
        else:
            fp_minx, fp_miny, fp_maxx, fp_maxy = \
                footprint.transform(crs_id, True).extent
            
            if x_bounds[0] == "unbounded":
                minx = fp_minx
            else:
                minx = max(fp_minx, x_bounds[0])
            
            if y_bounds[0] == "unbounded":
                miny = fp_miny
            else:
                miny = max(fp_miny, y_bounds[0])
            
            if x_bounds[1] == "unbounded":
                maxx = fp_maxx
            else:
                maxx = min(fp_maxx, x_bounds[1])
            
            if y_bounds[1] == "unbounded":
                maxy = fp_maxy
            else:
                maxy = min(fp_maxy, y_bounds[1])
            
            poly = Polygon.from_bbox((minx, miny, maxx, maxy))
            poly.srid = crs_id
            
        return poly

class WCS20ConfigReader(object):
    REGISTRY_CONF = {
        "name": "WCS 2.0 Configuration Reader",
        "impl_id": "services.ows.wcs20.WCS20ConfigReader"
    }

    def validate(self, config):
        pass

    def getPagingCountDefault(self):
        return System.getConfig().getConfigValue("services.ows.wcs20", "paging_count_default")
