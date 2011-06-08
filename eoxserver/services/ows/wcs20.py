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
    InternalError, UnknownCRSException, UnknownParameterFormatException
)
from eoxserver.core.util.xmltools import DOMtoXML, DOMElementToXML
from eoxserver.core.util.timetools import getDateTime
from eoxserver.core.util.geotools import getSRIDFromCRSURI
from eoxserver.resources.coverages.domainset import Trim, Slice, RectifiedGrid
from eoxserver.resources.coverages.exceptions import (
    NoSuchCoverageException, NoSuchDatasetSeriesException
)
from eoxserver.resources.coverages.interfaces import CoverageInterfaceFactory, DatasetSeriesFactory # TODO: correct imports
from eoxserver.services.interfaces import (
    VersionHandlerInterface, OperationHandlerInterface
)
from eoxserver.services.base import BaseRequestHandler
from eoxserver.services.requests import Response
from eoxserver.services.owscommon import (
    OWSCommonVersionHandler, OWSCommonExceptionHandler,
    OWSCommonConfigReader
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
        ms_req.coverages = CoverageInterfaceFactory.getVisibleCoverageInterfaces()
    
    def getMapServerLayer(self, coverage, **kwargs):
        layer = super(WCS20GetCapabilitiesHandler, self).getMapServerLayer(coverage, **kwargs)
        
        datasets = coverage.getDatasets(**kwargs)
        
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
            
            
            # append EO Profile to ServiceIdentification
            
            if svc_identification is not None:
                eo_profile = encoder.encodeEOProfile()
                
                profiles = svc_identification.getElementsByTagName("ows:Profile")
                if len(profiles) == 0:
                    svc_identification.appendChild(eo_profile)
                else:
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
            # append wcseo:EOCoverageSubtype to wcs:CoverageSummary
            
            sections = ms_req.getParamValue("sections")
            
            if sections is None or len(sections) == 0 or "Contents" in sections or\
               "CoverageSummary" in sections or\
               "DatasetSeriesSummary" in sections:
                
                contents_new = encoder.encodeContents()
                
                if sections is None or len(sections) == 0 or "Contents" in sections or\
                   "CoverageSummary" in sections:
                    
                    for coverage in CoverageInterfaceFactory.getVisibleCoverageInterfaces():
                        cov_summary = encoder.encodeCoverageSummary(coverage)
                        contents_new.appendChild(cov_summary)

                # append dataset series summaries
                if sections is None or len(sections) == 0 or "Contents" in sections or\
                   "DatasetSeriesSummary" in sections:
                    
                    for dataset_series in DatasetSeriesFactory.getAllDatasetSeriesInterfaces():
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
                try:
                    req.coverages.append(CoverageInterfaceFactory.getCoverageInterface(coverage_id))
                except NoSuchCoverageException, e:
                    raise InvalidRequestException(e.msg, "NoSuchCoverage", coverage_id)

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
        
        wcseo_objects = self.createWCSEOObject(req)
        
        try:
            slices, trims = WCS20Utils.getSubsetting(req)
        except UnknownParameterFormatException, e:
            raise InvalidRequestException(e.msg, "InvalidSubsetting", "subset")
        except InvalidSubsettingException, e:
            raise InvalidRequestException(e.msg, "InvalidSubsetting", "subset")
        
        coverages = []
        dataset_series = []
        
        containment = req.getParamValue("containment")
        if containment is None:
            containment = "overlaps"
        elif containment.lower() not in ("overlaps", "contains"):
            raise InvalidRequestException("'containment' parameter must be either 'overlaps' or 'contains'", "InvalidParameterValue", "containment")
        
        for wcseo_object in wcseo_objects:
            for slice in slices:
                self.validateSlice(slice, wcseo_object)
            for trim in trims:
                self.validateTrim(trim, wcseo_object)
                
            if wcseo_object.getType() in ("eo.rect_dataset", "eo.rect_mosaic"):
                coverages.append(wcseo_object)
            else:
                dataset_series.append(wcseo_object)
            
            if wcseo_object.getType() in ("eo.rect_dataset_series", "eo.rect_mosaic"):
                try:
                    coverages.extend(wcseo_object.getDatasets(containment=containment.lower(), slices=slices, trims=trims))
                except UnknownCRSException, e:
                    raise InvalidRequestException(e.msg, "NoApplicableCode", None)
                except InvalidAxisLabelException, e:
                    raise InvalidRequestException(e.msg, "InvalidAxisLabel", None)

        # TODO: find out config value 'count'
        # subset returned dataset series/coverages to min(count from config, count from req)
        
        count_req = sys.maxint
        if req.getParamValue("count") is not None:
            count_req = int(req.getParamValue("count"))
        
        count_default = WCS20ConfigReader().getPagingCountDefault()
        count_used = min(count_req, count_default)
        
        count_all_coverages = len(coverages)
        if count_used < count_all_coverages:
            coverages = coverages[:count_used]
        else:
            count_used = count_all_coverages
 
        encoder = WCS20EOAPEncoder()
        
        return Response(
            content=DOMElementToXML(encoder.encodeEOCoverageSetDescription(dataset_series, coverages, count_all_coverages, count_used)), #TODO: Invoke with all datasetseries and EOCoverage elements.
            content_type="text/xml",
            status=200
        )

    def createWCSEOObject(self, req):
        eo_ids = req.getParamValue("eoid")
            
        if eo_ids is None:
            raise InvalidRequestException("Missing 'eoid' parameter", "MissingParameterValue", "eoid")
        else:
            wcseo_objects = []
            for eo_id in eo_ids:
                try:
                    wcseo_objects.append(DatasetSeriesFactory.getDatasetSeriesInterface(eo_id))
                except NoSuchDatasetSeriesException:
                    pass
                
                try:
                    wcseo_objects.append(CoverageInterfaceFactory.getCoverageInterfaceByEOID(eo_id))
                except NoSuchCoverageException:
                    pass
                
                if len(wcseo_objects) == 0:
                    raise InvalidRequestException("No coverage or dataset series with EO ID '%s' found" % eo_id, "NoSuchCoverage", "eoid")
            return wcseo_objects
    
    def validateSlice(self, slice, wcseo_object):
        try:
            if hasattr(wcseo_object, "getGrid"):
                slice.validate(wcseo_object.getGrid())
            else:
                slice.validate()
        except InvalidAxisLabelException, e:
            raise InvalidRequestException(e.msg, "InvalidAxisLabel", "subset")
        except InvalidSubsettingException, e:
            raise InvalidRequestException(e.msg, "InvalidSubsetting", "subset")

    def validateTrim(self, trim, wcseo_object):
        try:
            if hasattr(wcseo_object, "getGrid"):
                trim.validate(wcseo_object.getGrid())
            else:
                trim.validate()
        except InvalidAxisLabelException, e:
            raise InvalidRequestException(e.msg, "InvalidAxisLabel", "subset")
        except InvalidSubsettingException, e:
            raise InvalidRequestException(e.msg, "InvalidSubsetting", "subset")

WCS20DescribeEOCoverageSetHandlerImplementation = OperationHandlerInterface.implement(WCS20DescribeEOCoverageSetHandler)

class WCS20GetCoverageHandler(WCSCommonHandler):
    # TODO: override createCoverages, configureRequest, configureMapObj
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
            try:
                ms_req.coverages.append(CoverageInterfaceFactory.getCoverageInterface(coverage_id))
            except NoSuchCoverageException, e:
                raise InvalidRequestException(e.msg, "NoSuchCoverage", coverage_id)

    def _setParameter(self, ms_req, key, value):
        if key.lower() == "format" and len(ms_req.coverages[0].getRangeType()) > 3: # TODO
            super(WCS20GetCoverageHandler, self)._setParameter(ms_req, "format", "GTiff16")
        else:
            super(WCS20GetCoverageHandler, self)._setParameter(ms_req, key, value)
    
    def configureMapObj(self, ms_req):
        super(WCS20GetCoverageHandler, self).configureMapObj(ms_req)
        
        if len(ms_req.coverages[0].getRangeType()) > 3: # TODO see eoxserver.org ticket #3
            output_format = mapscript.outputFormatObj("GDAL/GTiff", "GTiff16")
            output_format.mimetype = "image/tiff"
            output_format.extension = "tif"
            output_format.imagemode = mapscript.MS_IMAGEMODE_INT16
        
            ms_req.map.appendOutputFormat(output_format)
            ms_req.map.setOutputFormat(output_format)
            
            logging.debug("WCS20GetCoverageHandler.configureMapObj: %s" % ms_req.map.imagetype)

    def addLayers(self, ms_req):
        slices, trims = WCS20Utils.getSubsetting(ms_req)

        for coverage in ms_req.coverages:
            ms_req.map.insertLayer(self.getMapServerLayer(coverage, slices=slices, trims=trims))

    def getMapServerLayer(self, coverage, **kwargs):
        layer = super(WCS20GetCoverageHandler, self).getMapServerLayer(coverage, **kwargs)
        
        if coverage.getType() in ("file", "eo.rect_dataset"):

            datasets = coverage.getDatasets()
            
            if len(datasets) == 0:
                raise InvalidRequestException("Image extent does not intersect with desired region.", "ExtentError", "extent") # TODO: check if this is the right exception report
            elif len(datasets) == 1:
                layer.data = os.path.abspath(datasets[0].getFilename())
                #TODO: set layer metadata
                
            else:
                raise InternalError("A single file or EO dataset should never return more than one dataset.")
                
            #layer.setMetaData("wcs_bandcount", str(len(coverage.getRangeType())))
            
        elif coverage.getType() == "eo.rect_mosaic":
           
            layer.tileindex = os.path.abspath(coverage.getShapeFilePath())
            layer.tileitem = "location"
        
        # this was under the "eo.rect_mosaic"-path. minor accurracy issues
        # have evolved since making it accissible to all paths
             
        grid = coverage.getGrid()
        
        layer.setMetaData("wcs_extent", "%.10f %.10f %.10f %.10f" % grid.getExtent2D())
        layer.setMetaData("wcs_resolution", "%f %f" % (grid.offsets[0][0], grid.offsets[1][1]))
        layer.setMetaData("wcs_size", "%d %d" % (grid.high[0] - grid.low[0] + 1, grid.high[1] - grid.low[1] + 1))
        layer.setMetaData("wcs_nativeformat", "GTiff")
        layer.setMetaData("wcs_bandcount", "%d"%len(coverage.getRangeType()))

        channels = " ".join(channel.name for channel in coverage.getRangeType())
        layer.setMetaData("wcs_band_names", channels)
        
        # set layer depending metadata
        for channel in coverage.getRangeType():
            axis_metadata = {
                "%s_band_description"%channel.name: channel.description,
                "%s_band_definition"%channel.name: channel.definition,
                "%s_band_uom"%channel.name: channel.uom
            }
            for key, value in axis_metadata.items():
                if value != '':
                    layer.setMetaData(key, value)
            
            layer.setMetaData("%s_interval"%channel.name,
                              "%g %g"%(channel.allowed_values_start,
                                       channel.allowed_values_end))
            
            layer.setMetaData("%s_significant_figures"%channel.name,
                              "%d"%channel.allowed_values_significant_figures)
            
        if len(coverage.getRangeType()) > 3: # TODO make this dependent on actual data type
            layer.setMetaData("wcs_formats", "GTiff16")
            layer.setMetaData("wcs_imagemode", "INT16")
        else:
            layer.setMetaData("wcs_imagemode", "BYTE")
        
        return layer

    def postprocess(self, ms_req, resp):
        coverage_id = ms_req.getParamValue("coverageid")
        
        if ms_req.coverages[0].getType() == "eo.rect_mosaic":
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
                elif ms_req.coverages[0].getType() == "eo.rect_mosaic":
                    slices, trims = WCS20Utils.getSubsetting(ms_req)

                    if len(trims) > 0:
                        poly = WCS20Utils.getPolygon(trims,
                                                         ms_req.coverages[0].getFootprint(),
                                                         ms_req.coverages[0].getGrid())
                    else:
                        poly = None

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

class WCS20Utils(object):
    @classmethod
    def _getSubsettingKVP(cls, req):
        #extract slicing and trimming parameters
        slices = []
        trims = []
        
        for key, values in req.getParams().items():
            if key.startswith("subset"):
                for value in values:
                    match = re.match(r'(\w+)(,([^(]+))?\(([^,]*)(,([^)]*))?\)', value)
                    if match is None:
                        raise InvalidRequestException("Invalid subsetting operation '%s=%s'" % (key, value), "InvalidSubsetting", key)
                    else:
                        dimension = match.group(1)
                        crs = match.group(3)
                        if match.group(6) is not None:
                            trim = Trim(dimension, crs, match.group(4), match.group(6))
                            trims.append(trim)
                            logging.debug("WCS20Utils.getSubsetting: trim: dimension: %s; crs: %s; low: %s; high: %s" % (dimension, str(crs), match.group(4), match.group(6)))
                        else:
                            slice = Slice(dimension, crs, match.group(4))
                            slices.append(slice)
                            logging.debug("WCS20Utils.getSubsetting: slice: dimension: %s; crs: %s; slicePoint: %s" % (dimension, str(crs), match.group(4)))

        return (slices, trims)
    
    @classmethod
    def _getSubsettingXML(cls, req):
        slice_elements = req.getParamValue("slices")
        trim_elements = req.getParamValue("trims")
        
        slices = []
        trims = []
        
        for slice_element in slice_elements:
            slice = Slice(
                dimension=slice_element.getElementsByTagName("wcs:Dimension")[0].firstChild.data,
                crs=None,
                slice_point=slice_element.getElementsByTagName("wcs:SlicePoint")[0].firstChild.data
            )
            slices.append(slice)
            
        for trim_element in trim_elements:
            trim = Trim(
                dimension=trim_element.getElementsByTagName("wcs:Dimension")[0].firstChild.data,
                crs=None,
                trim_low=trim_element.getElementsByTagName("wcs:TrimLow")[0].firstChild.data,
                trim_high=trim_element.getElementsByTagName("wcs:TrimHigh")[0].firstChild.data
            )
            trims.append(trim)
            
        return (slices, trims)
    
    @classmethod
    def getSubsetting(cls, req):
        if req.getParamType() == "kvp":
            return cls._getSubsettingKVP(req)
        else:
            return cls._getSubsettingXML(req)
    
    @classmethod
    def getPolygon(cls, trims, footprint, grid):
        crs = trims[0].crs
        
        for trim in trims[1:]:
            if trim.crs != crs:
                raise InvalidRequestException("All subsets must be expressed in the same CRS.")
        
        if crs is not None:
            srid = getSRIDFromCRSURI(crs)
            fp_minx, fp_miny, fp_maxx, fp_maxy = footprint.transform(srid, True).extent
            minx = None
            miny = None
            maxx = None
            maxy = None
            
            for trim in trims:
                if trim.dimension in ("x", "long"):
                    if trim.trim_low is None:
                        minx = fp_minx 
                    else:
                        minx = max(fp_minx, trim.trim_low)
                    
                    if trim.trim_high is None:
                        maxx = fp_maxx
                    else:
                        maxx = min(fp_maxx, trim.trim_high)
                elif trim.dimension in ("y", "lat"):
                    if trim.trim_low is None:
                        miny = fp_miny
                    else:
                        miny = max(fp_miny, trim.trim_low)
                    
                    if trim.trim_high is None:
                        maxy = fp_maxy
                    else:
                        maxy = min(fp_maxy, trim.trim_high)
            
            if minx is None:
                minx = fp_minx
            if miny is None:
                miny = fp_miny
            if maxx is None:
                maxx = fp_maxx
            if maxy is None:
                maxy = fp_maxy
            
            poly = Polygon.from_bbox((minx, miny, maxx, maxy))
            poly.srid = srid
            
        else: # if no CRS is given, imageCRS is assumed
            srid = footprint.srid
            
            imageCRSgrid = RectifiedGrid(dim=grid.dim, spatial_dim=grid.spatial_dim,low=grid.low,high=grid.high,axis_labels=grid.axis_labels,srid=grid.srid,origin=grid.origin,offsets=grid.offsets)
            
            for trim in trims:
                if trim.dimension in ("x", "long"):
                    if trim.trim_low is not None:
                        imageCRSgrid.low = (trim.trim_low, imageCRSgrid.low[1])
                    if trim.trim_high is not None:
                        imageCRSgrid.high = (trim.trim_high, imageCRSgrid.high[1])
                
                elif trim.dimension in ("y", "lat"):        
                    if trim.trim_low is not None:
                        imageCRSgrid.low = (imageCRSgrid.low[0], trim.trim_low)
                    if trim.trim_high is not None:
                        imageCRSgrid.high = (imageCRSgrid.high[0], trim.trim_high)
            
            poly = imageCRSgrid.getBBOX()
            
        return poly

class WCS20ConfigReader(object):
    REGISTRY_CONF = {
        "name": "WCS 2.0 Configuration Reader",
        "impl_id": "services.ows.wcs20.WCS20ConfigReader",
        "registry_values": {}
    }

    def validate(self, config):
        pass

    def getPagingCountDefault(self):
        return System.getConfig().getConfigValue("services.ows.wcs20", "paging_count_default")
