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

import logging
import os
import os.path
import tempfile
import uuid

from osgeo import gdal, ogr, osr

from django.conf import settings

from eoxserver.core.system import System
from eoxserver.core.util.xmltools import XMLEncoder, DOMtoXML, DOMElementToXML
from eoxserver.core.util.timetools import isotime
from eoxserver.core.exceptions import InternalError
from eoxserver.resources.coverages.exceptions import (
    NoSuchCoverageException, SynchronizationErrors
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
#from eoxserver.services.ogc import OGCExceptionHandler
from eoxserver.services.requests import Response
from eoxserver.services.exceptions import InvalidRequestException

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
        schemas = {
            "http://www.opengis.net/ogc": "http://schemas.opengis.net/wms/1.3.0/exceptions_1_3_0.xsd"
        }
        return WMS13ExceptionHandler(schemas).handleException(req, exception)

WMS13VersionHandlerImplementation = VersionHandlerInterface.implement(WMS13VersionHandler)

class WMSCommonHandler(MapServerOperationHandler):
    def __init__(self):
        self.shapefiles_to_delete = []
    
    def getMapServerLayer(self, coverage, **kwargs):
        logging.debug("WMSCommonHandler.getMapServerLayer")
        
        if coverage.getType() == "eo.dataset_series":
            layer = mapscript.layerObj()
            
            layer.name = coverage.getEOID()
            layer.setMetaData("wms_title", coverage.getEOID()) 
            layer.status = mapscript.MS_ON
            layer.setMetaData("wms_label", coverage.getEOID())
            
            time_extent = ",".join([isotime(dataset.getBeginTime()) for dataset in coverage.getEOCoverages()])
            layer.setMetaData("wms_timeextent", time_extent)
            #layer.setMetaData("wms_timeitem", "valid_time_begin")
            #layer.setMetaData("wms_timedefault", time_layer["default"])

        else:
            layer = super(WMSCommonHandler, self).getMapServerLayer(coverage, **kwargs)
            layer.setMetaData("ows_srs", "EPSG:%d" % int(coverage.getSRID()))
            layer.setMetaData("wms_label", coverage.getCoverageId())
            layer.setMetaData("wms_extent", "%f %f %f %f" % coverage.getExtent())
            layer.setExtent(*coverage.getExtent())
            
            # set up the no-data value
            range_type = coverage.getRangeType()
            nil_values = []
            for band in range_type.bands:
                try: 
                    nil_values.append(int(band.nil_values[0].value))
                except IndexError:
                    nil_values.append(0)
            
            layer.offsite = mapscript.colorObj(*nil_values[:3])
        
        layer.type = mapscript.MS_LAYER_RASTER
        
        layer.setConnectionType(mapscript.MS_RASTER, '')
        layer.setMetaData("wms_enable_request", "*")
        
        try:
            if coverage.getType() in ("plain", "eo.rect_dataset"):
                datasets = coverage.getDatasets(**kwargs)
                if len(datasets) == 0:
                    raise InternalError("Cannot handle empty coverages")
                elif len(datasets) == 1:
                    connector = System.getRegistry().findAndBind(
                        intf_id = "services.mapserver.MapServerDataConnectorInterface",
                        params = {
                            "services.mapserver.data_structure_type": \
                                coverage.getDataStructureType()
                        }
                    ) 
                    layer = connector.configure(layer, coverage)
                    logging.debug("EOxSWMSCommonHandler.getMapServerLayer: filename: %s" % layer.data) 
                else:
                    raise InternalError("A single file or EO dataset should never return more than one dataset.")
                
            elif coverage.getType() == "eo.rect_stitched_mosaic":
                connector = System.getRegistry().findAndBind(
                    intf_id = "services.mapserver.MapServerDataConnectorInterface",
                    params = {
                        "services.mapserver.data_structure_type": \
                            coverage.getDataStructureType()
                    }
                ) 
                
                layer = connector.configure(layer, coverage)
                
                extent = coverage.getExtent()
                srid = coverage.getSRID()
                size = coverage.getSize()
                rangetype = coverage.getRangeType()
                resolution = ((extent[2]-extent[0]) / float(size[0]),
                              (extent[1]-extent[3]) / float(size[1]))
                
                layer.setExtent(*coverage.getExtent())
                layer.setMetaData("wms_extent", "%.10f %.10f %.10f %.10f" % extent)
                layer.setMetaData("wms_resolution", "%.10f %.10f" % resolution)
                layer.setMetaData("wms_size", "%d %d" % size)
                
                layer.type = mapscript.MS_LAYER_RASTER
                layer.setConnectionType(mapscript.MS_RASTER, '')
                layer.setMetaData("wms_srs", "EPSG:%d" % srid)
                layer.setProjection("+init=epsg:%d" % srid)
                
            elif coverage.getType() == "eo.dataset_series":
                datasets = coverage.getEOCoverages(**kwargs)
                if len(datasets) == 0:
                    raise InternalError("Cannot handle empty coverages")
                
                elif len(datasets) == 1:
                    layer.setExtent(*datasets[0].getExtent())
                    layer.setProjection("+init=epsg:%d" % datasets[0].getSRID())
                    layer.setMetaData("wms_srs", "EPSG:%d"%int(datasets[0].getSRID()))
                    connector = System.getRegistry().findAndBind(
                        intf_id = "services.mapserver.MapServerDataConnectorInterface",
                        params = {
                            "services.mapserver.data_structure_type": \
                                coverage.getDataStructureType()
                        }
                    ) 
                    layer = connector.configure(layer, coverage)
                    
                    # TODO: Show all requested files. (Default without time parameter to all.)
                
                else: # we have multiple datasets
                    # set projection to the first datasets projection
                    # TODO: dataset projections can differ
                    layer.setProjection("+init=epsg:%d" % datasets[0].getSRID())
                    layer.setMetaData("wms_srs", "EPSG:%d" % int(datasets[0].getSRID()))
                    
                    # initialize OGR driver
                    driver = ogr.GetDriverByName('ESRI Shapefile')
                    if driver is None:
                        raise InternalError("Cannot start GDAL Shapefile driver")
                    
                    # create path to temporary shapefile, if it already exists, delete it
                    path = os.path.join(tempfile.gettempdir(), "%s.shp" % uuid.uuid4().hex)
                    self.shapefiles_to_delete.append(path)
                    
                    if os.path.exists(path):
                        driver.DeleteDataSource(path)
                    
                    # create a new shapefile
                    shapefile = driver.CreateDataSource(path)
                    if shapefile is None:
                        logging.error("Cannot create shapefile '%s'." % path)
                        raise InternalError("Cannot create shapefile '%s'." % path)
                    
                    # create a new srs object
                    srs = osr.SpatialReference()
                    srs.ImportFromEPSG(datasets[0].getSRID()) # TODO: srids can differ 
                    
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
                    
                    tmp = []
                    for dataset in datasets:
                        tmp.extend(dataset.getDatasets())
                    datasets = tmp
                    
                    for dataset in datasets:
                        feature = ogr.Feature(shapefile_layer.GetLayerDefn())
                        
                        extent = dataset.getExtent()
                        
                        geom = ogr.CreateGeometryFromWkt("POLYGON((%f %f, %f %f, %f %f, %f %f, %f %f))" % (
                            extent[0], extent[1],
                            extent[2], extent[1],
                            extent[2], extent[3],
                            extent[0], extent[3],
                            extent[0], extent[1]
                        ), srs)
                        
                        feature.SetGeometry(geom)
                        
                        feature.SetField("location", str(os.path.abspath(dataset.getData().getGDALDatasetIdentifier())))
                        
                        if shapefile_layer.CreateFeature(feature) != 0:
                            raise InternalError("Could not create shapefile entry for file '%s'" % path)
                        feature = None
                    
                    #save the shapefile
                    shapefile_layer.SyncToDisk()
                    shapefile = None
                    
                    #set mapserver layer information for the shapefile
                    layer.tileindex = os.path.abspath(path)
                    layer.tileitem = "location"
                    
                    # set offsite; TODO: make this dependant on nilvalues
                    layer.offsite = mapscript.colorObj(0,0,0)
                    

        except InternalError:
            # create "no data" layer
            logging.debug(layer.data)
            layer.setProjection("+init=epsg:4326")
            layer.setMetaData("wms_srs", "EPSG:3035 EPSG:4326 EPSG:900913") # TODO find out possible projections

        return layer
    
    def postprocess(self, ms_req, resp):
        # delete temporary shapefiles used for dataset series
        driver = ogr.GetDriverByName('ESRI Shapefile')
        for path in self.shapefiles_to_delete:
            driver.DeleteDataSource(path)
        
        return super(WMSCommonHandler, self).postprocess(ms_req, resp)

class WMS1XGetCapabilitiesHandler(WMSCommonHandler):
    def createCoverages(self, ms_req):
        visible_expr = System.getRegistry().getFromFactory(
            "resources.coverages.filters.CoverageExpressionFactory",
            {"op_name": "attr", "operands": ("visible", "=", True)}
        )
        factory = System.getRegistry().bind("resources.coverages.wrappers.EOCoverageFactory")
        ms_req.coverages = factory.find(filter_exprs=[visible_expr])
        
        #factory = System.getRegistry().bind("resources.coverages.wrappers.DatasetSeriesFactory")
        #ms_req.coverages.extend(factory.find())
        
    def getMapServerLayer(self, coverage, **kwargs):
        layer = super(WMS1XGetCapabilitiesHandler, self).getMapServerLayer(coverage, **kwargs)
        
        if coverage.getType() == "eo.dataset_series":
            datasets = coverage.getEOCoverages(**kwargs)
        else:
            datasets = coverage.getDatasets(**kwargs)
        
        if coverage.getType() == "eo.dataset_series":
            layer.setMetaData("wms_extent", "%f %f %f %f" % coverage.getWGS84Extent())
            layer.setExtent(*coverage.getWGS84Extent())
        
        if len(datasets) == 0:
            raise InternalError("Misconfigured coverage '%s' has no file data." % coverage.getCoverageId())
        else:
            connector = System.getRegistry().findAndBind(
                intf_id = "services.mapserver.MapServerDataConnectorInterface",
                params = {
                    "services.mapserver.data_structure_type": \
                        coverage.getDataStructureType()
                }
            ) 
            layer = connector.configure(layer, coverage)
            
        logging.debug("WMS1XGetCapabilitiesHandler.getMapServerLayer: filename: %s" % layer.data)
        
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
    def addLayers(self, ms_req):
        time_param = ms_req.getParamValue("time")
        slices = []
        trims = []
        if time_param and len(time_param.split("/")) == 2:
            trims.append(Trim("time", None, "\"%s\"" % time_param.split("/")[0], "\"%s\"" % time_param.split("/")[1]))
        elif time_param:
            slices.append(Slice("time", None, "\"%s\"" % time_param))
        
        for coverage in ms_req.coverages:
            ms_req.map.insertLayer(self.getMapServerLayer(coverage))#, slices=slices, trims=trims))

    def createCoverages(self, ms_req):
        layers = ms_req.getParamValue("layers")
        
        if layers is None:
            raise InvalidRequestException("Missing 'LAYERS' parameter", "MissingParameterValue", "layers")

        coverages = []
        for layer in layers:
            obj = System.getRegistry().getFromFactory(
                "resources.coverages.wrappers.DatasetSeriesFactory",
                {"obj_id": layer}
            )
            if obj is not None:
                coverages.append(obj)
            else:
                obj = System.getRegistry().getFromFactory(
                    "resources.coverages.wrappers.EOCoverageFactory",
                    {"obj_id": layer}
                )
                if obj is not None:
                    coverages.append(obj)
                else:
                    raise InvalidRequestException("No coverage or dataset series with EO ID '%s' found" % layer, "LayerNotDefined", "layers")
        
        ms_req.coverages = coverages
        

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
                ms_req.map.setProjection("+init=epsg:4326")
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
        "layers": {"xml_location": "/layer", "xml_type": "string[]", "kvp_key": "layers", "kvp_type": "stringlist"}, # TODO: check XML location
        "format": {"xml_location": "/format", "xml_type": "string", "kvp_key": "format", "kvp_type": "string"},
        "time": {"xml_location": "/time", "xml_type": "string", "kvp_key": "time", "kvp_type": "string"}
    }
    
    def configureRequest(self, ms_req):
        
        # check if the format is known; if not MapServer will raise an 
        # exception instead of returning the correct service exception report
        # (bug)
        if not ms_req.getParamValue("format"):
            raise InvalidRequestException(
                "Missing mandatory 'format' parameter",
                "MissingParameterValue",
                "format"
            )
        else:
            format_name = ms_req.getParamValue("format")
            
            try:
                output_format = ms_req.map.getOutputFormatByName(format_name)
                
                if not output_format:
                    raise InvalidRequestException(
                        "Unknown format name '%s'" % format_name,
                        "InvalidFormat",
                        "format"
                    )
            except Exception, e:
                raise InvalidRequestException(
                    str(e),
                    "InvalidFormat",
                    "format"
                )
        
        super(WMS13GetMapHandler, self).configureRequest(ms_req)
    
    def configureMapObj(self, ms_req):
        super(WMS13GetMapHandler, self).configureMapObj(ms_req)
        
        ms_req.map.setMetaData("wms_exceptions_format", "xml")
        ms_req.map.setMetaData("ows_srs","EPSG:4326")
        
        crs = ms_req.getParamValue('crs')
        if crs is not None:
            try:        
                ms_req.map.setProjection(crs)
            except:
                ms_req.map.setProjection("+init=epsg:4326")
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

    def _initializeNamespaces(self):
        return {
            "ogc": "http://www.opengis.net/ogc",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance"
        }
    
    def encodeExceptionReport(self, exception_text, exception_code):
        return self._makeElement("", "ServiceExceptionReport", [
            ("", "@version", "1.1.1"),
            ("xsi", "schemaLocation", "http://www.opengis.net/ogc http://schemas.opengis.net/wms/1.1.1/OGC-exception.xsd"),
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

class WMS13ExceptionHandler(BaseExceptionHandler):
    REGISTRY_CONF = {
        "name": "OGC Namespace Exception Handler",
        "impl_id": "services.ogc.WMS13ExceptionHandler",
        "registry_values": {
            "services.interfaces.exception_scheme": "ogc"
        }
    }
    
    def _filterExceptions(self, exception):
        if not isinstance(exception, InvalidRequestException):
            raise
    
    def _getEncoder(self):
        return WMS13ExceptionEncoder(self.schemas)
    
    def _getContentType(self, exception):
        return "application/vnd.ogc.se_xml"

WMS13ExceptionHandlerImplementation = ExceptionHandlerInterface.implement(WMS13ExceptionHandler)

class WMS13ExceptionEncoder(XMLEncoder):
    REGISTRY_CONF = {
        "name": "OGC Namespace Exception Report Encoder",
        "impl_id": "services.ogc.WMS13ExceptionEncoder",
        "registry_values": {
            "services.interfaces.exception_scheme": "ogc"
        }
    }
    
    def _initializeNamespaces(self):
        return {
            "ogc": "http://www.opengis.net/ogc",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance"
        }
    
    def encodeExceptionReport(self, exception_text, exception_code, locator=None):
        if locator is None:
            element = self._makeElement("ogc", "ServiceExceptionReport", [
                ("", "@version", "1.3.0"),
                ("ogc", "ServiceException", [
                    ("", "@code", exception_code),
                    ("", "@@", exception_text)
                ])
            ])
        else:
            element = self._makeElement("ogc", "ServiceExceptionReport", [
                ("", "@version", "1.3.0"),
                ("ogc", "ServiceException", [
                    ("", "@code", exception_code),
                    ("", "@locator", locator),
                    ("", "@@", exception_text)
                ])
            ])
        
        if self.schemas is not None:
            schemas_location = " ".join(["%s %s"%(ns, location) for ns, location in self.schemas.iteritems()])
            element.setAttributeNS(self.ns_dict["xsi"], "%s:%s" % ("xsi", "schemaLocation"), schemas_location)
        
        return element
    
    def encodeInvalidRequestException(self, exception):
        return self.encodeExceptionReport(
            exception.msg,
            exception.error_code,
            exception.locator
        )
    
    def encodeVersionNegotiationException(self, exception):
        return "" # TODO: check against OWS Common

WMS13ExceptionEncoderImplementation = ExceptionEncoderInterface.implement(WMS13ExceptionEncoder)

