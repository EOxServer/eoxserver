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

import logging
import os
import os.path

from eoxserver.lib.handlers import EOxSMapServerOperationHandler, EOxSExceptionHandler, EOxSExceptionEncoder
from eoxserver.lib.ows import EOxSOWSCommonServiceHandler, EOxSOWSCommonVersionHandler
from eoxserver.lib.ogc import EOxSOGCExceptionHandler
from eoxserver.lib.domainset import EOxSTrim, EOxSSlice
from eoxserver.lib.requests import EOxSResponse
from eoxserver.lib.interfaces import EOxSCoverageInterfaceFactory, EOxSDatasetSeriesFactory
from eoxserver.lib.util import EOxSXMLEncoder, DOMtoXML, DOMElementToXML, isotime
from eoxserver.lib.exceptions import (EOxSInternalError,
    EOxSInvalidRequestException, EOxSNoSuchCoverageException
)

from eoxserver.contrib import mapscript

class EOxSWMSServiceHandler(EOxSOWSCommonServiceHandler):
    SERVICE = "WMS"
    ABSTRACT = False

class EOxSWMS10VersionHandler(EOxSOWSCommonVersionHandler):
    SERVICE = "WMS"
    VERSIONS = ("1.0", "1.0.0")
    ABSTRACT = False

    def _handleException(self, req, exception):
        return EOxSWMS10ExceptionHandler().handleException(req, exception)

class EOxSWMS11VersionHandler(EOxSOWSCommonVersionHandler):
    SERVICE = "WMS"
    VERSIONS = ("1.1", "1.1.0", "1.1.1")
    ABSTRACT = False

    def _handleException(self, req, exception):
        return EOxSWMS11ExceptionHandler().handleException(req, exception)

class EOxSWMS13VersionHandler(EOxSOWSCommonVersionHandler):
    SERVICE = "WMS"
    VERSIONS = ("1.3", "1.3.0")
    ABSTRACT = False
    
    def _handleException(self, req, exception):
        return EOxSOGCExceptionHandler().handleException(req, exception)

class EOxSWMSCommonHandler(EOxSMapServerOperationHandler):
    ABSTRACT = True
    
    def addLayers(self, ms_req):
        time_param = ms_req.getParamValue("time")
        slices = []
        if time_param:
            slices.append(EOxSSlice("time", None, "\"%s\"" % time_param))
        
        for coverage in ms_req.coverages:
            ms_req.map.insertLayer(self.getMapServerLayer(coverage, slices=slices))

    def getMapServerLayer(self, coverage, **kwargs):
        logging.debug("EOxSWMSCommonHandler.getMapServerLayer")
        
        if coverage.getType() == "eo.rect_dataset_series":
            layer = mapscript.layerObj()
            
            layer.name = coverage.getEOID()
            layer.status = mapscript.MS_ON
            layer.setMetaData("wms_label", coverage.getEOID())
            
            time_extent = ",".join([isotime(dataset.getBeginTime()) for dataset in coverage.getDatasets()])
            
            layer.setMetaData("wms_timeextent", time_extent)
            #layer.setMetaData("wms_timeitem", "valid_time_begin")
            #layer.setMetaData("wms_timedefault", time_layer["default"])

        else:
            layer = super(EOxSWMSCommonHandler, self).getMapServerLayer(coverage, **kwargs)
            layer.setMetaData("ows_srs", "EPSG:%d" % int(coverage.getGrid().srid))
            layer.setMetaData("wms_label", coverage.getCoverageId())
            layer.setMetaData("wms_extent", "%f %f %f %f" % coverage.getGrid().getExtent2D())
            layer.setExtent(*coverage.getGrid().getExtent2D())
        
        layer.type = mapscript.MS_LAYER_RASTER
        #layer.dump = mapscript.MS_TRUE
        layer.setConnectionType(mapscript.MS_RASTER, '')
        try:
            if coverage.getType() in ("file", "eo.rect_dataset"):
                datasets = coverage.getDatasets(**kwargs)
                if len(datasets) == 0:
                    # TODO: produce a no-data value only coverage
                    raise EOxSInternalError("Cannot handle empty coverages")
                elif len(datasets) == 1:
                    layer.data = os.path.abspath(datasets[0].getFilename())
                else:
                    raise EOxSInternalError("A single file or EO dataset should never return more than one dataset.")
                
            elif coverage.getType() == "eo.rect_mosaic":
                layer.tileindex = os.path.abspath(coverage.getShapeFilePath())
                layer.tileitem = "location"
                
            elif coverage.getType() == "eo.rect_dataset_series":
                datasets = coverage.getDatasets(**kwargs)
                if len(datasets) == 0:
                    raise EOxSInternalError("Cannot handle empty coverages")
                
                layer.setExtent(*datasets[0].getGrid().getExtent2D())
                layer.setProjection("EPSG:%d"%datasets[0].getGrid().srid)
                layer.setMetaData("wms_srs", "EPSG:%d"%int(datasets[0].getGrid().srid))
                #layer.setMetaData("wms_crs", "EPSG:%d"%datasets[0].getGrid().srid)

                layer.data = datasets[0].getFilename() # TODO: Show all requested files. (Default without time parameter to all.)

        except EOxSInternalError:
            # create an empty layer
            logging.debug(layer.data)
            layer.setProjection("EPSG:4326")
            layer.setMetaData("wms_srs", "EPSG:3035 EPSG:4326 EPSG:900913") # TODO find out possible projections

        return layer

class EOxSWMS1XGetCapabilitiesHandler(EOxSWMSCommonHandler):
    SERVICE = "WMS"
    VERSIONS = ("1.0", "1.0.0", "1.1", "1.1.0", "1.3", "1.3.0")
    OPERATIONS = ("getcapabilities")
    ABSTRACT = False
    
    def createCoverages(self, ms_req):
        #ms_req.coverages = EOxSCoverageInterfaceFactory.getAllCoverageInterfaces()
        ms_req.coverages = EOxSCoverageInterfaceFactory.getVisibleCoverageInterfaces()
        ms_req.coverages.extend(EOxSDatasetSeriesFactory.getAllDatasetSeriesInterfaces())
        
    def getMapServerLayer(self, coverage, **kwargs):
        layer = super(EOxSWMS1XGetCapabilitiesHandler, self).getMapServerLayer(coverage, **kwargs)
        
        datasets = coverage.getDatasets(**kwargs)
        
        if coverage.getType() == "eo.rect_dataset_series":
            layer.setMetaData("wms_extent", "%f %f %f %f" % coverage.getWGS84Extent())
            layer.setExtent(*coverage.getWGS84Extent())
        
        if len(datasets) == 0:
            raise EOxSInternalError("Misconfigured coverage '%s' has no file data." % coverage.getCoverageId())
        else:
            layer.data = os.path.abspath(datasets[0].getFilename())
            
        logging.debug("EOxSWMSCommonHandler.getMapServerLayer: filename: %s" % layer.data)
        
        return layer

    def postprocess(self, ms_req, resp):
        return resp

class EOxSWMS1XGetMapHandler(EOxSWMSCommonHandler):
    SERVICE = "WMS"
    VERSIONS = ("1.0", "1.0.0", "1.1", "1.1.0", "1.3", "1.3.0")
    OPERATIONS = ("getmap")
    ABSTRACT = True
    
    def createCoverages(self, ms_req):
        layers = ms_req.getParamValue("layers")
        
        if layers is None:
            raise EOxSInvalidRequestException("Missing 'LAYERS' parameter", "MissingParameterValue", "layers")
        else:
            for layer in layers:
                try:
                    ms_req.coverages.append(EOxSCoverageInterfaceFactory.getCoverageInterface(layer))
                except EOxSNoSuchCoverageException:
                    try:
                        ms_req.coverages.append(EOxSDatasetSeriesFactory.getDatasetSeriesInterface(layer))
                    except EOxSNoSuchCoverageException, e:
                        raise EOxSInvalidRequestException(e.msg, "LayerNotDefined", "layers")

class EOxSWMS10_11GetMapHandler(EOxSWMS1XGetMapHandler):
    SERVICE = "WMS"
    VERSIONS = ("1.0", "1.0.0", "1.1", "1.1.0")
    OPERATIONS = ("getmap")
    ABSTRACT = False
    
    PARAM_SCHEMA = {
        "service": {"xml_location": "/@service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/@version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"},
        "srs": {"xml_location": "/srs", "xml_type": "string", "kvp_key": "srs", "kvp_type": "string"}, # TODO: check XML location
        "layers": {"xml_location": "/layer", "xml_type": "string[]", "kvp_key": "layers", "kvp_type": "string[]"}, # TODO: check XML location
        "time": {"xml_location": "/time", "xml_type": "string", "kvp_key": "time", "kvp_type": "string"}
    }
    
    def configureMapObj(self, ms_req):
        super(EOxSWMS10_11GetMapHandler, self).configureMapObj(ms_req)
        
        ms_req.map.setMetaData("wms_exceptions_format", "text/xml")#"application/vnd.ogc.se_xml")
        
        srs = ms_req.getParamValue("srs")
        if srs is not None:
            try:
                ms_req.map.setProjection(srs)
            except:
                ms_req.map.setProjection("EPSG:4326")
        else:
            raise EOxSInvalidRequestException("Mandatory 'SRS' parameter missing.", "MissingParameterValue", "srs")
    
    def getMapServerLayer(self, coverage, **kwargs):
        layer = super(EOxSWMS10_11GetMapHandler, self).getMapServerLayer(coverage, **kwargs)
        layer.setMetaData("wms_exceptions_format","application/vnd.ogc.se_xml")
        
        return layer 


class EOxSWMS13GetMapHandler(EOxSWMS1XGetMapHandler):
    SERVICE = "WMS"
    VERSIONS = ("1.3", "1.3.0")
    OPERATIONS = ("getmap")
    ABSTRACT = False
    
    PARAM_SCHEMA = {
        "service": {"xml_location": "/@service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/@version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"},
        "crs": {"xml_location": "/crs", "xml_type": "string", "kvp_key": "crs", "kvp_type": "string"}, # TODO: check XML location
        "layers": {"xml_location": "/layer", "xml_type": "string[]", "kvp_key": "layers", "kvp_type": "string[]"}, # TODO: check XML location
        "time": {"xml_location": "/time", "xml_type": "string", "kvp_key": "time", "kvp_type": "string"}
    }
    
    def configureMapObj(self, ms_req):
        super(EOxSWMS13GetMapHandler, self).configureMapObj(ms_req)

        ms_req.map.setMetaData("wms_exceptions_format", "xml")
        ms_req.map.setMetaData("ows_srs","EPSG:4326")
        
        crs = ms_req.getParamValue('crs')
        if crs is not None:
            try:        
                ms_req.map.setProjection(crs)
            except:
                ms_req.map.setProjection("EPSG:4326")
        else:
            raise EOxSInvalidRequestException("Mandatory 'CRS' parameter missing", "MissingParameterValue", "crs")
    
    def getMapServerLayer(self, coverage, **kwargs):
        layer = super(EOxSWMS13GetMapHandler, self).getMapServerLayer(coverage, **kwargs)
        layer.setMetaData("wms_exceptions_format","xml")
        

        return layer

class EOxSWMS10ExceptionHandler(EOxSExceptionHandler):
    def _filterExceptions(self, exception):
        if not isinstance(exception, EOxSInvalidRequestException):
            raise
    
    def _getEncoder(self):
        return EOxSWMS10ExceptionEncoder()
        
    def _getContentType(self, exception):
        return "text/xml"
        
class EOxSWMS10ExceptionEncoder(EOxSExceptionEncoder):
    def encodeExceptionReport(self, exception_text, exception_code):
        return self._makeElement("", "WMTException", [
            ("", "@version", "1.0.0"),
            ("", "@@", str(exception_text))
        ])
    
    def encodeInvalidRequestException(self, exception):
        return self.encodeExceptionReport(exception.msg, exception.error_code)

class EOxSWMS11ExceptionHandler(EOxSExceptionHandler):
    def _filterExceptions(self, exception):
        if not isinstance(exception, EOxSInvalidRequestException):
            raise
    
    def _getEncoder(self):
        return EOxSWMS11ExceptionEncoder()
        
    def _getContentType(self, exception):
        return "application/vnd.ogc.se_xml"

class EOxSWMS11ExceptionEncoder(EOxSExceptionEncoder):
    def encodeExceptionReport(self, exception_text, exception_code):
        return self._makeElement("", "ServiceExceptionReport", [
            ("", "@version", "1.1.1"),
            ("", "ServiceException", [
                ("", "@code", exception_code),
                ("", "@@", exception_text)
            ])
        ])
    
    def encodeInvalidRequestException(self, exception):
        return self.encodeExceptionReport(exception.msg, exception.error_code)
