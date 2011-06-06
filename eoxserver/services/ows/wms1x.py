#-----------------------------------------------------------------------
# $Id$
#
# This software is named EOxServer, a server for Earth Observation data.
#
# Copyright (C) 2011 EOX IT Services GmbH
# Authors: Stephan Krause, Stephan Meissl
#
# This file is part of EOxServer <http://eoxserver.org>.
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

from osgeo import gdal, ogr, osr

from django.conf import settings

from eoxserver.core.util.xmltools import XMLEncoder, DOMtoXML, DOMElementToXML
from eoxserver.core.util.timetools import isotime
from eoxserver.core.exceptions import InternalError
from eoxserver.resources.coverages.exceptions import (
    NoSuchCoverageException, SynchronizationError
)
from eoxserver.resources.coverages.domainset import Trim, Slice
from eoxserver.services.interfaces import (
    ServiceHandlerInterface, VersionHandlerInterface,
    OperationHandlerInterface, ExceptionHandlerInterface,
    ExceptionEncoderInterface
)
from eoxserver.services.mapserver import MapServerOperationHandler
from eoxserver.services.base import (
    BaseRequestHandler, BaseExceptionHandler
)
from eoxserver.services.owscommon import (
    OWSCommonServiceHandler, OWSCommonVersionHandler
)
from eoxserver.services.ogc import OGCExceptionHandler
from eoxserver.services.requests import Response
from eoxserver.services.exceptions import InvalidRequestException
from eoxserver.resources.coverages.interfaces import CoverageInterfaceFactory, DatasetSeriesFactory # TODO: correct imports

from eoxserver.contrib import mapscript

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

class WMS10VersionHandler(OWSCommonVersionHandler):
    REGISTRY_CONF = {
        "name": "WMS 1.0 Version Handler",
        "impl_id": "services.ows.wms1x.WMS10VersionHandler",
        "registry_values": {
            "services.interfaces.service": "wms",
            "services.interfaces.version": "1.0.0",
        }
    }
    
    SERVICE = "wms"
    VERSION = "1.0.0"

    def _handleException(self, req, exception):
        return WMS10ExceptionHandler().handleException(req, exception)

WMS10VersionHandlerImplementation = VersionHandlerInterface.implement(WMS10VersionHandler)

class WMS110VersionHandler(OWSCommonVersionHandler):
    REGISTRY_CONF = {
        "name": "WMS 1.1.0 Version Handler",
        "impl_id": "services.ows.wms1x.WMS110VersionHandler",
        "registry_values": {
            "services.interfaces.service": "wms",
            "services.interfaces.version": "1.1.0"
        }
    }
    
    SERVICE = "wms"
    VERSIONS = "1.1.0"

    def _handleException(self, req, exception):
        return WMS11ExceptionHandler().handleException(req, exception)

WMS110VersionHandlerImplementation = VersionHandlerInterface.implement(WMS110VersionHandler)
        
class WMS111VersionHandler(OWSCommonVersionHandler):
    REGISTRY_CONF = {
        "name": "WMS 1.1.1 Version Handler",
        "impl_id": "services.ows.wms1x.WMS111VersionHandler",
        "registry_values": {
            "services.interfaces.service": "wms",
            "services.interfaces.version": "1.1.1"
        }
    }
    
    SERVICE = "wms"
    VERSIONS = "1.1.1"

    def _handleException(self, req, exception):
        return WMS11ExceptionHandler().handleException(req, exception)

WMS111VersionHandlerImplementation = VersionHandlerInterface.implement(WMS111VersionHandler)

class WMS13VersionHandler(OWSCommonVersionHandler):
    REGISTRY_CONF = {
        "name": "WMS 1.3.0 Version Handler",
        "impl_id": "services.ows.wms1x.WMS130VersionHandler",
        "registry_values": {
            "services.interfaces.service": "wms",
            "services.interfaces.version": "1.3.0"
        }
    }
    
    SERVICE = "wms"
    VERSION = "1.3.0"
        
    def _handleException(self, req, exception):
        return OGCExceptionHandler().handleException(req, exception)

WMS13VersionHandlerImplementation = VersionHandlerInterface.implement(WMS13VersionHandler)

class WMSCommonHandler(MapServerOperationHandler):
    def addLayers(self, ms_req):
        time_param = ms_req.getParamValue("time")
        slices = []
        if time_param:
            slices.append(Slice("time", None, "\"%s\"" % time_param))
        
        for coverage in ms_req.coverages:
            ms_req.map.insertLayer(self.getMapServerLayer(coverage, slices=slices))

    def getMapServerLayer(self, coverage, **kwargs):
        logging.debug("WMSCommonHandler.getMapServerLayer")
        
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
            layer = super(WMSCommonHandler, self).getMapServerLayer(coverage, **kwargs)
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
                    raise InternalError("Cannot handle empty coverages")
                elif len(datasets) == 1:
                    layer.data = os.path.abspath(datasets[0].getFilename())
                else:
                    raise InternalError("A single file or EO dataset should never return more than one dataset.")
                
            elif coverage.getType() == "eo.rect_mosaic":
                layer.tileindex = os.path.abspath(coverage.getShapeFilePath())
                layer.tileitem = "location"
                
            elif coverage.getType() == "eo.rect_dataset_series":
                datasets = coverage.getDatasets(**kwargs)
                if len(datasets) == 0:
                    raise InternalError("Cannot handle empty coverages")
                
                elif len(datasets) == 1:
                    layer.setExtent(*datasets[0].getGrid().getExtent2D())
                    layer.setProjection("EPSG:%d"%datasets[0].getGrid().srid)
                    layer.setMetaData("wms_srs", "EPSG:%d"%int(datasets[0].getGrid().srid))
                    #layer.setMetaData("wms_crs", "EPSG:%d"%datasets[0].getGrid().srid)
                    layer.data = datasets[0].getFilename() # TODO: Show all requested files. (Default without time parameter to all.)
                
                else: # we have multiple datasets
                    # set projection to the first datasets projection
                    # TODO: dataset projections can differ
                    layer.setProjection("EPSG:%d" % datasets[0].getGrid().srid)
                    layer.setMetaData("wms_srs", "EPSG:%d" % int(datasets[0].getGrid().srid))
                    
                    # initialize OGR driver
                    driver = ogr.GetDriverByName('ESRI Shapefile')
                    if driver is None:
                        raise InternalError("Cannot start GDAL Shapefile driver")
                    
                    # create path to temporary shapefile, if it already exists, delete it
                    path = os.path.join(settings.PROJECT_DIR, "data", "tmp", "tmp.shp")
                    if os.path.exists(path):
                        driver.DeleteDataSource(path)
                    
                    # create a new shapefile
                    shapefile = driver.CreateDataSource(path)
                    if shapefile is None:
                        raise InternalError("Cannot create shapefile '%s'." % path)
                    
                    # create a new srs object
                    srs = osr.SpatialReference()
                    srs.ImportFromEPSG(datasets[0].getGrid().srid) # TODO: srids can differ 
                    
                    # create a new shapefile layer
                    shapefile_layer = shapefile.CreateLayer("file_locations", srs, ogr.wkbPolygon)
                    if shapefile_layer is None:
                        raise InternalError("Cannot create layer 'file_locations' in shapefile '%s'" % path)
                    
                    # add a field definition for the file location
                    location_defn = ogr.FieldDefn("location", ogr.OFTString)
                    location_defn.SetWidth(256) # TODO: make this configurable
                    if shapefile_layer.CreateField(location_defn) != 0:
                        raise InternalError("Cannot create field 'location' on layer 'file_locations' in shapefile '%s'" % self.path)
                    
                    # add each dataset to the layer as a feature
                    for dataset in datasets:
                        feature = ogr.Feature(shapefile_layer.GetLayerDefn())
                        
                        extent = dataset.getGrid().getExtent2D()
                        
                        geom = ogr.CreateGeometryFromWkt("POLYGON((%f %f, %f %f, %f %f, %f %f, %f %f))" % (
                            extent[0], extent[1],
                            extent[2], extent[1],
                            extent[2], extent[3],
                            extent[0], extent[3],
                            extent[0], extent[1]
                        ), srs)
                        
                        feature.SetGeometry(geom)
                        feature.SetField("location", os.path.abspath(dataset.getFilename()))
                        if shapefile_layer.CreateFeature(feature) != 0:
                            raise InternalError("Could not create shapefile entry for file '%s'" % path)
                        feature = None
                    
                    #save the shapefile
                    shapefile_layer.SyncToDisk()
                    shapefile = None
                    
                    #set mapserver layer information for the shapefile
                    layer.tileindex = os.path.abspath(path)
                    layer.tileitem = "location"

        except InternalError:
            # create "no data" layer
            logging.debug(layer.data)
            layer.setProjection("EPSG:4326")
            layer.setMetaData("wms_srs", "EPSG:3035 EPSG:4326 EPSG:900913") # TODO find out possible projections

        return layer

class WMS1XGetCapabilitiesHandler(WMSCommonHandler):
    def createCoverages(self, ms_req):
        #ms_req.coverages = EOxSCoverageInterfaceFactory.getAllCoverageInterfaces()
        ms_req.coverages = EOxSCoverageInterfaceFactory.getVisibleCoverageInterfaces()
        ms_req.coverages.extend(EOxSDatasetSeriesFactory.getAllDatasetSeriesInterfaces())
        
    def getMapServerLayer(self, coverage, **kwargs):
        layer = super(WMS1XGetCapabilitiesHandler, self).getMapServerLayer(coverage, **kwargs)
        
        datasets = coverage.getDatasets(**kwargs)
        
        if coverage.getType() == "eo.rect_dataset_series":
            layer.setMetaData("wms_extent", "%f %f %f %f" % coverage.getWGS84Extent())
            layer.setExtent(*coverage.getWGS84Extent())
        
        if len(datasets) == 0:
            raise InternalError("Misconfigured coverage '%s' has no file data." % coverage.getCoverageId())
        else:
            layer.data = os.path.abspath(datasets[0].getFilename())
            
        logging.debug("WMSCommonHandler.getMapServerLayer: filename: %s" % layer.data)
        
        return layer

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

class WMS13GetCapabilitiesHandler(WMS1XGetCapabilitiesHandler):
    REGISTRY_CONF = {
        "name": "WMS 1.3 GetCapabilities Handler",
        "impl_id": "services.ows.wms1x.WMS13GetCapabilitiesHandler",
        "registry_values": {
            "services.interfaces.service": "wms",
            "services.interfaces.version": "1.3.0",
            "services.interfaces.operation": "getcapabilities"
        }
    }

WMS13GetCapabilitiesHandlerImplementation = OperationHandlerInterface.implement(WMS13GetCapabilitiesHandler)

class WMS1XGetMapHandler(WMSCommonHandler):
    def createCoverages(self, ms_req):
        layers = ms_req.getParamValue("layers")
        
        if layers is None:
            raise InvalidRequestException("Missing 'LAYERS' parameter", "MissingParameterValue", "layers")
        else:
            for layer in layers:
                try:
                    ms_req.coverages.append(EOxSCoverageInterfaceFactory.getCoverageInterface(layer))
                except NoSuchCoverageException:
                    try:
                        ms_req.coverages.append(EOxSDatasetSeriesFactory.getDatasetSeriesInterface(layer))
                    except NoSuchCoverageException, e:
                        raise InvalidRequestException(e.msg, "LayerNotDefined", "layers")

class WMS10_11GetMapHandler(WMS1XGetMapHandler):
    PARAM_SCHEMA = {
        "service": {"xml_location": "/@service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/@version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"},
        "srs": {"xml_location": "/srs", "xml_type": "string", "kvp_key": "srs", "kvp_type": "string"}, # TODO: check XML location
        "layers": {"xml_location": "/layer", "xml_type": "string[]", "kvp_key": "layers", "kvp_type": "string[]"}, # TODO: check XML location
        "time": {"xml_location": "/time", "xml_type": "string", "kvp_key": "time", "kvp_type": "string"}
    }
    
    def configureMapObj(self, ms_req):
        super(WMS10_11GetMapHandler, self).configureMapObj(ms_req)
        
        ms_req.map.setMetaData("wms_exceptions_format", "text/xml")# TODO: "application/vnd.ogc.se_xml")
        
        srs = ms_req.getParamValue("srs")
        if srs is not None:
            try:
                ms_req.map.setProjection(srs)
            except:
                ms_req.map.setProjection("EPSG:4326")
        else:
            raise InvalidRequestException("Mandatory 'SRS' parameter missing.", "MissingParameterValue", "srs")
    
    def getMapServerLayer(self, coverage, **kwargs):
        layer = super(WMS10_11GetMapHandler, self).getMapServerLayer(coverage, **kwargs)
        layer.setMetaData("wms_exceptions_format","application/vnd.ogc.se_xml")
        
        return layer

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

class WMS13GetMapHandler(WMS1XGetMapHandler):
    REGISTRY_CONF = {
        "name": "WMS 1.3 GetMap Handler",
        "impl_id": "services.ows.wms1x.WMS13GetMapHandler",
        "registry_values": {
            "services.interfaces.service": "wms",
            "services.interfaces.version": "1.3.0",
            "services.interfaces.operation": "getmap"
        }
    }
    
    PARAM_SCHEMA = {
        "service": {"xml_location": "/@service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/@version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"},
        "crs": {"xml_location": "/crs", "xml_type": "string", "kvp_key": "crs", "kvp_type": "string"}, # TODO: check XML location
        "layers": {"xml_location": "/layer", "xml_type": "string[]", "kvp_key": "layers", "kvp_type": "string[]"}, # TODO: check XML location
        "time": {"xml_location": "/time", "xml_type": "string", "kvp_key": "time", "kvp_type": "string"}
    }
    
    def configureMapObj(self, ms_req):
        super(WMS13GetMapHandler, self).configureMapObj(ms_req)

        ms_req.map.setMetaData("wms_exceptions_format", "xml")
        ms_req.map.setMetaData("ows_srs","EPSG:4326")
        
        crs = ms_req.getParamValue('crs')
        if crs is not None:
            try:        
                ms_req.map.setProjection(crs)
            except:
                ms_req.map.setProjection("EPSG:4326")
        else:
            raise InvalidRequestException("Mandatory 'CRS' parameter missing", "MissingParameterValue", "crs")
    
    def getMapServerLayer(self, coverage, **kwargs):
        layer = super(WMS13GetMapHandler, self).getMapServerLayer(coverage, **kwargs)
        layer.setMetaData("wms_exceptions_format","xml")
        

        return layer

WMS13GetMapHandlerImplementation = OperationHandlerInterface.implement(WMS13GetMapHandler)

class WMS10ExceptionHandler(BaseExceptionHandler):
    REGISTRY_CONF = {
        "name": "WMS 1.0 Exception Handler",
        "impl_id": "services.ows.wms1x.WMS10ExceptionHandler",
        "registry_values": {
            "services.interfaces.exception_scheme": "wms_1.0"
        }
    }
    
    def _filterExceptions(self, exception):
        if not isinstance(exception, InvalidRequestException):
            raise
    
    def _getEncoder(self):
        return WMS10ExceptionEncoder()
        
    def _getContentType(self, exception):
        return "text/xml"

WMS10ExceptionHandlerImplementation = ExceptionHandlerInterface.implement(WMS10ExceptionHandler)
        
class WMS10ExceptionEncoder(XMLEncoder):
    REGISTRY_CONF = {
        "name": "WMS 1.0 Exception Report Encoder",
        "impl_id": "services.ows.wms1x.WMS10ExceptionEncoder",
        "registry_values": {
            "services.interfaces.exception_scheme": "wms_1.0"
        }
    }
    
    def encodeExceptionReport(self, exception_text, exception_code):
        return self._makeElement("", "WMTException", [
            ("", "@version", "1.0.0"),
            ("", "@@", str(exception_text))
        ])
    
    def encodeInvalidRequestException(self, exception):
        return self.encodeExceptionReport(exception.msg, exception.error_code)
    
    def encodeVersionNegotiationException(self, exception):
        return ""

WMS10ExceptionEncoderImplementation = ExceptionEncoderInterface.implement(WMS10ExceptionEncoder)

class WMS11ExceptionHandler(BaseExceptionHandler):
    REGISTRY_CONF = {
        "name": "WMS 1.1 Exception Handler",
        "impl_id": "services.ows.wms1x.WMS11ExceptionHandler",
        "registry_values": {
            "services.interfaces.exception_scheme": "wms_1.1"
        }
    }
    
    def _filterExceptions(self, exception):
        if not isinstance(exception, InvalidRequestException):
            raise
    
    def _getEncoder(self):
        return WMS11ExceptionEncoder()
        
    def _getContentType(self, exception):
        return "application/vnd.ogc.se_xml"

WMS11ExceptionHandlerImplementation = ExceptionHandlerInterface.implement(WMS11ExceptionHandler)

class WMS11ExceptionEncoder(XMLEncoder):
    REGISTRY_CONF = {
        "name": "WMS 1.0 Exception Report Encoder",
        "impl_id": "services.ows.wms1x.WMS11ExceptionEncoder",
        "registry_values": {
            "services.interfaces.exception_scheme": "wms_1.1"
        }
    }

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
    
    def encodeVersionNegotiationException(self, exception):
        return ""

WMS11ExceptionEncoderImplementation = ExceptionEncoderInterface.implement(WMS11ExceptionEncoder)
