#-----------------------------------------------------------------------
#
# This software is named EOxServer, a server for Earth Observation data.
#
# Copyright (C) 2011 EOX IT Services GmbH
# Authors: Stephan Krause, Stephan Meissl
#
# This file is part of EOxServer <http://www.eoxserver.org>.
#
#    EOxServer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License,
#    or (at your option) any later version.
#
#    EOxServer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with EOxServer. If not, see <http://www.gnu.org/licenses/>.
#
#-----------------------------------------------------------------------

import re
import os.path
import sys
from xml.dom import minidom

from django.conf import settings
from django.contrib.gis.geos import Polygon

import logging

from eoxserver.lib.config import EOxSCoverageConfig, EOxSConfig
from eoxserver.lib.handlers import EOxSOperationHandler
from eoxserver.lib.domainset import EOxSTrim, EOxSSlice, EOxSRectifiedGrid
from eoxserver.lib.requests import EOxSResponse
from eoxserver.lib.interfaces import EOxSCoverageInterfaceFactory, EOxSDatasetSeriesFactory
from eoxserver.lib.ows import EOxSOWSCommonVersionHandler, EOxSOWSCommonExceptionHandler
from eoxserver.lib.util import DOMtoXML, DOMElementToXML, getDateTime, getSRIDFromCRSURI
from eoxserver.lib.exceptions import (EOxSInternalError,
    EOxSInvalidRequestException, EOxSNoSuchCoverageException,
    EOxSNoSuchDatasetSeriesException, EOxSUnknownParameterFormatException,
    EOxSInvalidAxisLabelException, EOxSInvalidSubsettingException,
    EOxSUnknownCRSException
)
from eoxserver.modules.wcs.common import EOxSWCSCommonHandler
from eoxserver.modules.wcs.encoders import EOxSWCS20Encoder, EOxSWCS20EOAPEncoder

from eoxserver.contrib import mapscript

class EOxSWCS20VersionHandler(EOxSOWSCommonVersionHandler):
    SERVICE = "WCS"
    VERSIONS = ("2.0.0",)
    ABSTRACT = False

    def _handleException(self, req, exception):
        handler = EOxSOWSCommonExceptionHandler()
        
        handler.setHTTPStatusCodes({
                "NoSuchCoverage": 404,
                "InvalidAxisLabel": 404,
                "InvalidSubsetting": 404
        })
        
        return handler.handleException(req, exception)

class EOxSWCS20GetCapabilitiesHandler(EOxSWCSCommonHandler):
    SERVICE = "WCS"
    VERSIONS = ("2.0.0",)
    OPERATIONS = ("getcapabilities",)
    ABSTRACT = False
    
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
        ms_req.coverages = EOxSCoverageInterfaceFactory.getVisibleCoverageInterfaces()
    
    def getMapServerLayer(self, coverage, **kwargs):
        layer = super(EOxSWCS20GetCapabilitiesHandler, self).getMapServerLayer(coverage, **kwargs)
        
        datasets = coverage.getDatasets(**kwargs)
        
        if len(datasets) == 0:
            raise EOxSInternalError("Misconfigured coverage '%s' has no file data." % coverage.getCoverageId())
        else:
            layer.data = os.path.abspath(datasets[0].getFilename()) # we just need an arbitrary file here
        
        return layer

    def postprocess(self, ms_req, resp):
        logging.debug("sys.path: %s" % str(sys.path))
        logging.debug("mapscript version: %s" % mapscript.msGetVersion())
        
        dom = minidom.parseString(resp.content)
        
        # change xsi:schemaLocation
        schema_location_attr = dom.documentElement.getAttributeNode("xsi:schemaLocation")
        schema_location_attr.nodeValue = "http://www.opengis.net/wcseo/1.0 http://schemas.opengis.net/wcseo/1.0/wcsEOAll.xsd"
        
        # we are finished if the response is an ows:ExceptionReport
        # proceed otherwise
        if dom.documentElement.localName != "ExceptionReport":
        
            encoder = EOxSWCS20EOAPEncoder()

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
                desc_eo_cov_set_op = encoder.encodeDescribeEOCoverageSetOperation(self.config.http_service_url)

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
                    
                    for coverage in EOxSCoverageInterfaceFactory.getVisibleCoverageInterfaces():
                        cov_summary = encoder.encodeCoverageSummary(coverage)
                        contents_new.appendChild(cov_summary)

                # append dataset series summaries
                if sections is None or len(sections) == 0 or "Contents" in sections or\
                   "DatasetSeriesSummary" in sections:
                    
                    for dataset_series in EOxSDatasetSeriesFactory.getAllDatasetSeriesInterfaces():
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

class EOxSWCS20DescribeCoverageHandler(EOxSOperationHandler):
    SERVICE = "WCS"
    VERSIONS = ("2.0.0",)
    OPERATIONS = ("describecoverage",)
    ABSTRACT = False
    
    PARAM_SCHEMA = {
        "service": {"xml_location": "/@ows:service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/@ows:version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"},
        "coverageids": {"xml_location": "/wcs:CoverageId", "xml_type": "string[]", "kvp_key": "coverageid", "kvp_type": "stringlist"}
    }
    
    def handle(self, req):
        req.setSchema(self.PARAM_SCHEMA)

        self.createCoverages(req)
        
        encoder = EOxSWCS20EOAPEncoder()
        
        return EOxSResponse(
            content=DOMElementToXML(encoder.encodeCoverageDescriptions(req.coverages, True)), # TODO: Distinguish between encodeEOCoverageDescriptions and encodeCoverageDescription?
            content_type="text/xml",
            status=200
        )

    def createCoverages(self, req):
        coverage_ids = req.getParamValue("coverageids")
        
        if coverage_ids is None:
            raise EOxSInvalidRequestException("Missing 'coverageid' parameter.", "MissingParameterValue", "coverageid")
        else:
            for coverage_id in coverage_ids:
                try:
                    req.coverages.append(EOxSCoverageInterfaceFactory.getCoverageInterface(coverage_id))
                except EOxSNoSuchCoverageException, e:
                    raise EOxSInvalidRequestException(e.msg, "NoSuchCoverage", coverage_id)

class EOxSWCS20DescribeEOCoverageSetHandler(EOxSOperationHandler):
    SERVICE = "WCS"
    VERSIONS = ("2.0.0",)
    OPERATIONS = ("describeeocoverageset",)
    ABSTRACT = False

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

    def handle(self, req):
        req.setSchema(self.PARAM_SCHEMA)
        
        wcseo_objects = self.createWCSEOObject(req)
        
        try:
            slices, trims = EOxSWCS20Utils.getSubsetting(req)
        except EOxSUnknownParameterFormatException, e:
            raise EOxSInvalidRequestException(e.msg, "InvalidSubsetting", "subset")
        except EOxSInvalidSubsettingException, e:
            raise EOxSInvalidRequestException(e.msg, "InvalidSubsetting", "subset")
        
        coverages = []
        dataset_series = []
        
        containment = req.getParamValue("containment")
        if containment is None:
            containment = "overlaps"
        elif containment.lower() not in ("overlaps", "contains"):
            raise EOxSInvalidRequestException("'containment' parameter must be either 'overlaps' or 'contains'", "InvalidParameterValue", "containment")
        
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
                except EOxSUnknownCRSException, e:
                    raise EOxSInvalidRequestException(e.msg, "NoApplicableCode", None)
                except EOxSInvalidAxisLabelException, e:
                    raise EOxSInvalidRequestException(e.msg, "InvalidAxisLabel", None)

        # TODO: find out config value 'count'
        # subset returned dataset series/coverages to min(count from config, count from req)
        
        count_req = sys.maxint
        if req.getParamValue("count") is not None:
            count_req = int(req.getParamValue("count"))
        
        count_default = EOxSConfig.getConfig().paging_count_default
        count_used = min(count_req, count_default)
        
        count_all_coverages = len(coverages)
        if count_used < count_all_coverages:
            coverages = coverages[:count_used]
        else:
            count_used = count_all_coverages
 
        encoder = EOxSWCS20EOAPEncoder()
        
        return EOxSResponse(
            content=DOMElementToXML(encoder.encodeEOCoverageSetDescription(dataset_series, coverages, count_all_coverages, count_used)), #TODO: Invoke with all datasetseries and EOCoverage elements.
            content_type="text/xml",
            status=200
        )

    def createWCSEOObject(self, req):
        eo_ids = req.getParamValue("eoid")
            
        if eo_ids is None:
            raise EOxSInvalidRequestException("Missing 'eoid' parameter", "MissingParameterValue", "eoid")
        else:
            wcseo_objects = []
            for eo_id in eo_ids:
                try:
                    wcseo_objects.append(EOxSDatasetSeriesFactory.getDatasetSeriesInterface(eo_id))
                except EOxSNoSuchDatasetSeriesException:
                    pass
                
                try:
                    wcseo_objects.append(EOxSCoverageInterfaceFactory.getCoverageInterfaceByEOID(eo_id))
                except EOxSNoSuchCoverageException:
                    pass
                
                if len(wcseo_objects) == 0:
                    raise EOxSInvalidRequestException("No coverage or dataset series with EO ID '%s' found" % eo_id, "NoSuchCoverage", "eoid")
            return wcseo_objects
    
    def validateSlice(self, slice, wcseo_object):
        try:
            if hasattr(wcseo_object, "getGrid"):
                slice.validate(wcseo_object.getGrid())
            else:
                slice.validate()
        except EOxSInvalidAxisLabelException, e:
            raise EOxSInvalidRequestException(e.msg, "InvalidAxisLabel", "subset")
        except EOxSInvalidSubsettingException, e:
            raise EOxSInvalidRequestException(e.msg, "InvalidSubsetting", "subset")

    def validateTrim(self, trim, wcseo_object):
        try:
            if hasattr(wcseo_object, "getGrid"):
                trim.validate(wcseo_object.getGrid())
            else:
                trim.validate()
        except EOxSInvalidAxisLabelException, e:
            raise EOxSInvalidRequestException(e.msg, "InvalidAxisLabel", "subset")
        except EOxSInvalidSubsettingException, e:
            raise EOxSInvalidRequestException(e.msg, "InvalidSubsetting", "subset")


class EOxSWCS20GetCoverageHandler(EOxSWCSCommonHandler):
    # TODO: override createCoverages, configureRequest, configureMapObj
    SERVICE = "WCS"
    VERSIONS = ("2.0.0",)
    OPERATIONS = ("getcoverage",)
    ABSTRACT = False

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
            raise EOxSInvalidRequestException("Missing 'coverageid' parameter", "MissingParameterValue", "coverageid")
        else:
            try:
                ms_req.coverages.append(EOxSCoverageInterfaceFactory.getCoverageInterface(coverage_id))
            except EOxSNoSuchCoverageException, e:
                raise EOxSInvalidRequestException(e.msg, "NoSuchCoverage", coverage_id)

    def _setParameter(self, ms_req, key, value):
        if key.lower() == "format" and len(ms_req.coverages[0].getRangeType()) > 3: # TODO
            if value.lower() == "image/tiff":
                super(EOxSWCS20GetCoverageHandler, self)._setParameter(ms_req, "format", "GTiff16")
            else:
                raise EOxSInvalidRequestException("Invalid or unsupported value '%s' for 'format' parameter." % value, "InvalidParameterValue", key)
        else:
            super(EOxSWCS20GetCoverageHandler, self)._setParameter(ms_req, key, value)

    def configureMapObj(self, ms_req):
        super(EOxSWCS20GetCoverageHandler, self).configureMapObj(ms_req)
        
        if len(ms_req.coverages[0].getRangeType()) > 3: # TODO see eoxserver.org ticket #3
            output_format = mapscript.outputFormatObj("GDAL/GTiff", "GTiff16")
            output_format.mimetype = "image/tiff"
            output_format.extension = "tif"
            output_format.imagemode = mapscript.MS_IMAGEMODE_INT16
        
            ms_req.map.appendOutputFormat(output_format)
            ms_req.map.setOutputFormat(output_format)
            
            logging.debug("EOxSWCS20GetCoverageHandler.configureMapObj: %s" % ms_req.map.imagetype)

    def addLayers(self, ms_req):
        slices, trims = EOxSWCS20Utils.getSubsetting(ms_req)

        for coverage in ms_req.coverages:
            ms_req.map.insertLayer(self.getMapServerLayer(coverage, slices=slices, trims=trims))

    def getMapServerLayer(self, coverage, **kwargs):
        layer = super(EOxSWCS20GetCoverageHandler, self).getMapServerLayer(coverage, **kwargs)
        
        if coverage.getType() in ("file", "eo.rect_dataset"):

            datasets = coverage.getDatasets()
            
            if len(datasets) == 0:
                raise EOxSInvalidRequestException("Image extent does not intersect with desired region.", "ExtentError", "extent") # TODO: check if this is the right exception report
            elif len(datasets) == 1:
                layer.data = os.path.abspath(datasets[0].getFilename())
                #TODO: set layer metadata
                
            else:
                raise EOxSInternalError("A single file or EO dataset should never return more than one dataset.")
                
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
                encoder = EOxSWCS20EOAPEncoder()
                
                if ms_req.coverages[0].getType() == "eo.rect_dataset":
                    resp_xml = encoder.encodeRectifiedDataset(
                        ms_req.coverages[0],
                        req = ms_req,
                        nodes = rectified_grid_coverage.childNodes
                    )
                elif ms_req.coverages[0].getType() == "eo.rect_mosaic":
                    slices, trims = EOxSWCS20Utils.getSubsetting(ms_req)

                    if len(trims) > 0:
                        poly = EOxSWCS20Utils.getPolygon(trims,
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

class EOxSWCS20Utils(object):
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
                        raise EOxSInvalidRequestException("Invalid subsetting operation '%s=%s'" % (key, value), "InvalidSubsetting", key)
                    else:
                        dimension = match.group(1)
                        crs = match.group(3)
                        if match.group(6) is not None:
                            trim = EOxSTrim(dimension, crs, match.group(4), match.group(6))
                            trims.append(trim)
                            logging.debug("EOxSWCS20Utils.getSubsetting: trim: dimension: %s; crs: %s; low: %s; high: %s" % (dimension, str(crs), match.group(4), match.group(6)))
                        else:
                            slice = EOxSSlice(dimension, crs, match.group(4))
                            slices.append(slice)
                            logging.debug("EOxSWCS20Utils.getSubsetting: slice: dimension: %s; crs: %s; slicePoint: %s" % (dimension, str(crs), match.group(4)))

        return (slices, trims)
    
    @classmethod
    def _getSubsettingXML(cls, req):
        slice_elements = req.getParamValue("slices")
        trim_elements = req.getParamValue("trims")
        
        slices = []
        trims = []
        
        for slice_element in slice_elements:
            slice = EOxSSlice(
                dimension=slice_element.getElementsByTagName("wcs:Dimension")[0].firstChild.data,
                crs=None,
                slice_point=slice_element.getElementsByTagName("wcs:SlicePoint")[0].firstChild.data
            )
            slices.append(slice)
            
        for trim_element in trim_elements:
            trim = EOxSTrim(
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
                raise EOxSInvalidRequestException("All subsets must be expressed in the same CRS.")
        
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
            
            imageCRSgrid = EOxSRectifiedGrid(dim=grid.dim, spatial_dim=grid.spatial_dim,low=grid.low,high=grid.high,axis_labels=grid.axis_labels,srid=grid.srid,origin=grid.origin,offsets=grid.offsets)
            
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

