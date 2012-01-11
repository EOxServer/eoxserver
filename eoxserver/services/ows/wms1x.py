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

import logging

from osgeo import ogr
from eoxserver.core.system import System
from eoxserver.core.util.xmltools import XMLEncoder
from eoxserver.core.util.timetools import isotime
from eoxserver.core.util.geotools import getSRIDFromCRSIdentifier
from eoxserver.core.exceptions import InternalError, InvalidParameterException
from eoxserver.resources.coverages.domainset import Trim, Slice
from eoxserver.resources.coverages.filters import BoundedArea
from eoxserver.resources.coverages.helpers import CoverageSet
from eoxserver.processing.gdal.reftools import (
    create_rectified_vrt, create_temporary_vrt
)
from eoxserver.resources.coverages.filters import BoundedArea
from eoxserver.resources.coverages.helpers import CoverageSet

from eoxserver.services.interfaces import (
    ServiceHandlerInterface, VersionHandlerInterface,
    OperationHandlerInterface, ExceptionHandlerInterface,
    ExceptionEncoderInterface
)
from eoxserver.services.mapserver import MapServerOperationHandler
from eoxserver.services.base import BaseExceptionHandler
from eoxserver.services.owscommon import (
    OWSCommonServiceHandler, OWSCommonVersionHandler
)
from eoxserver.services.exceptions import InvalidRequestException

import mapscript

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
        super(WMSCommonHandler, self).__init__()
        
        self.dataset_series_set = []
    
    def getMapServerLayer(self, coverage):
        logging.debug("WMSCommonHandler.getMapServerLayer")
        
        layer = super(WMSCommonHandler, self).getMapServerLayer(coverage)
        layer.setMetaData("wms_label", coverage.getCoverageId())
        
        if coverage.getType() == "eo.ref_dataset":
            layer.setMetaData("ows_srs", "EPSG:4326")
            layer.setMetaData("wms_extent", "%f %f %f %f" % coverage.getFootprint().extent)
            layer.setExtent(*coverage.getFootprint().extent)
        else:
            layer.setMetaData("ows_srs", "EPSG:%d" % int(coverage.getSRID()))
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
        layer.status = mapscript.MS_DEFAULT
        
        try:
            if coverage.getType() in ("plain", "eo.rect_dataset"):
                connector = System.getRegistry().findAndBind(
                    intf_id = "services.mapserver.MapServerDataConnectorInterface",
                    params = {
                        "services.mapserver.data_structure_type": \
                            coverage.getDataStructureType()
                    }
                ) 
                layer = connector.configure(layer, coverage)
                logging.debug("EOxSWMSCommonHandler.getMapServerLayer: filename: %s" % layer.data) 
            elif coverage.getType() == "eo.ref_dataset":
                vrt_path = self.rectify(coverage)
                
                layer.data = vrt_path
                layer.addProcessing("SCALE=1,2000") # TODO: Make the scale configurable.
                
                logging.debug("EOxSWMSCommonHandler.getMapServerLayer: filename: %s" % layer.data)
                
                self.temp_files.append(vrt_path)
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
                    

        except InternalError:
            # create "no data" layer
            logging.debug(layer.data)
            layer.setProjection("+init=epsg:4326")
            layer.setMetaData("wms_srs", "EPSG:3035 EPSG:4326 EPSG:900913") # TODO find out possible projections

        return layer
        
        def rectify(self, coverage):
            return create_temporary_vrt(
                coverage.getData().getGDALDatasetIdentifier()
            )

class WMS1XGetCapabilitiesHandler(WMSCommonHandler):
    def createCoverages(self):
        visible_expr = System.getRegistry().getFromFactory(
            "resources.coverages.filters.CoverageExpressionFactory",
            {"op_name": "attr", "operands": ("visible", "=", True)}
        )
        
        cov_factory = System.getRegistry().bind("resources.coverages.wrappers.EOCoverageFactory")
        
        self.coverages = cov_factory.find(filter_exprs=[visible_expr])
        
        dss_factory = System.getRegistry().bind("resources.coverages.wrappers.DatasetSeriesFactory")
        
        # TODO: find a more efficient way to do this check
        for dataset_series in dss_factory.find():
            if len(dataset_series.getEOCoverages()) > 0:
                self.dataset_series_set.append(dataset_series)
                
    
    def addLayers(self):
        super(WMS1XGetCapabilitiesHandler, self).addLayers()
    
        for dataset_series in self.dataset_series_set:
            self.map.insertLayer(self.getDatasetSeriesMapServerLayer(dataset_series))
    
    def getMapServerLayer(self, coverage):
        layer = super(WMS1XGetCapabilitiesHandler, self).getMapServerLayer(coverage)
        
        connector = System.getRegistry().findAndBind(
            intf_id = "services.mapserver.MapServerDataConnectorInterface",
            params = {
                "services.mapserver.data_structure_type": \
                    coverage.getDataStructureType()
            }
        ) 
        layer = connector.configure(layer, coverage)
        
        layer.status = mapscript.MS_ON
        
        logging.debug("WMS1XGetCapabilitiesHandler.getMapServerLayer: filename: %s" % layer.data)
        
        return layer
    
    def getDatasetSeriesMapServerLayer(self, dataset_series):
        layer = mapscript.layerObj()
        
        layer.name = dataset_series.getEOID()
        layer.setMetaData("wms_title", dataset_series.getEOID()) 
        layer.setMetaData("wms_label", dataset_series.getEOID())
        
        coverages = dataset_series.getEOCoverages()

        layer.setMetaData("wms_extent", "%f %f %f %f" % dataset_series.getWGS84Extent())
        layer.setExtent(*dataset_series.getWGS84Extent())
        
        time_extent = ",".join(
            [isotime(coverage.getBeginTime()) for coverage in coverages]
        )
        layer.setMetaData("wms_timeextent", time_extent)
        
        layer.setProjection("+init=epsg:4326")
        layer.setMetaData("wms_srs", "EPSG:4326")
        
        layer.type = mapscript.MS_LAYER_RASTER
        
        layer.setConnectionType(mapscript.MS_RASTER, '')
        layer.setMetaData("wms_enable_request", "*")
        layer.status = mapscript.MS_ON

        # use a dummy coverage to connect to
        
        connector = System.getRegistry().findAndBind(
            intf_id = "services.mapserver.MapServerDataConnectorInterface",
            params = {
                "services.mapserver.data_structure_type": \
                    coverages[0].getDataStructureType()
            }
        )
        
        layer = connector.configure(layer, coverages[0])
        
        return layer
    
    def rectify(self, coverage):
        return create_temporary_vrt(
            coverage.getData().getGDALDatasetIdentifier()
        )
        

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
    def getSRSParameterName(self):
        raise NotImplementedError()
    
    def getBoundedArea(self, srid, bbox):
        return BoundedArea(srid, *bbox)
        
    def getTimeFilterExpr(self, time_param):
        timestamps = time_param.split("/")
        
        if len(timestamps) == 1:
            try:
                timestamp = getDateTime(timestamps[1])
            except InvalidParameterException:
                raise InvalidRequestException(
                    "Invalid 'TIME' parameter format.",
                    "InvalidParameterValue",
                    "time"
                )
            
            return System.getRegistry().getFromFactory(
                "resources.coverages.filters.CoverageExpressionFactory",
                {
                    "op_name": "time_slice",
                    "operands": (timestamp,)
                }
            )
        
        elif len(timestamps) == 2:
            try:
                time_intv = TimeInterval(
                    getDateTime(timestamps[0]),
                    getDateTime(timestamps[1])
                )
            except InvalidParameterException:
                raise InvalidRequestException(
                    "Invalid 'TIME' parameter format.",
                    "InvalidParameterValue",
                    "time"
                )
                
            return System.getRegistry().getFromFactory(
                "resources.coverages.filters.CoverageExpressionFactory",
                {
                    "op_name": "time_intersects",
                    "operands": (time_intv,)
                }
            )
        else:
            raise InvalidRequestException(
                "Invalid 'TIME' parameter format.",
                "InvalidParameterValue",
                "time"
            )

    def createCoverages(self):
        layers = self.req.getParamValue("layers")
        
        try:
            bbox = self.req.getParamValue("bbox")
        except InvalidParameterException:
            raise InvalidRequestException(
                "Invalid BBOX parameter value",
                "InvalidParameterValue",
                "bbox"
            )
        if len(bbox) != 4:
            raise InvalidRequestException("Wrong number of arguments for 'BBOX' parameter", "InvalidParameterValue", "bbox")

        if layers is None:
            raise InvalidRequestException("Missing 'LAYERS' parameter", "MissingParameterValue", "layers")
        
        
        srs = self.req.getParamValue(self.getSRSParameterName())
        if srs is None:
            raise InvalidRequestException("Missing '%s' parameter"% self.getSRSParameterName().upper(), "MissingParameterValue" , self.getSRSParameterName())

        srid = getSRIDFromCRSIdentifier(srs)
        if srid is None:
            raise InvalidRequestException("Invalid '%s' parameter value"% self.getSRSParameterName().upper(), "InvalidCRS" , self.getSRSParameterName())
        
        area = self.getBoundedArea(srid, bbox)
        
        filter_exprs = []
        
        # TODO sqlite assert ahead `GEOSCoordSeq_setOrdinate_r`
        filter_exprs.append(
            System.getRegistry().getFromFactory(
                "resources.coverages.filters.CoverageExpressionFactory",
                {
                    "op_name": "footprint_intersects_area",
                    "operands": (area,)
                }
            )
        )
        
        time_param = self.req.getParamValue("time")
        
        if time_param is not None:
            filter_exprs.append(self.getTimeFilterExpr(time_param))
        
        coverages = CoverageSet()
        
        for layer_name in layers:
            dataset_series = System.getRegistry().getFromFactory(
                "resources.coverages.wrappers.DatasetSeriesFactory",
                {"obj_id": layer_name}
            )
            if dataset_series is not None:
                coverages.union(dataset_series.getEOCoverages(filter_exprs))
            else:
                coverage = System.getRegistry().getFromFactory(
                    "resources.coverages.wrappers.EOCoverageFactory",
                    {"obj_id": layer_name}
                )
                if coverage is not None:
                    if coverage.matches(filter_exprs):
                        coverages.add(coverage)
                else:
                    raise InvalidRequestException(
                        "No coverage or dataset series with EO ID '%s' found" % layer_name,
                        "LayerNotDefined",
                        "layers"
                    )
        
        self.coverages = coverages.to_sorted_list()
        
        if len(self.coverages) == 0:
            raise InvalidRequestException(
                "No coverages with the given spatiotemporal extent found.",
                "ExtentError", # TODO: check error code
                None
            )
            
    def getSRID(self):
        srs = self.req.getParamValue(self.getSRSParameterName())

        if srs is None:
            raise InvalidRequestException("Missing '%s' parameter"% self.getSRSParameterName().upper(), "MissingParameterValue" , self.getSRSParameterName())
        
        srid = getSRIDFromCRSIdentifier(srs)
        if srid is None:
            raise InvalidRequestException("Invalid '%s' parameter value"% self.getSRSParameterName().upper(), "InvalidCRS" , self.getSRSParameterName())
            
        return srid

    
    def rectify(self, coverage):
        return create_temporary_vrt(
            coverage.getData().getGDALDatasetIdentifier(),
            self.getSRID()
        )
        

class WMS10_11GetMapHandler(WMS1XGetMapHandler):
    PARAM_SCHEMA = {
        "service": {"xml_location": "/@service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/@version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"},
        "srs": {"xml_location": "/srs", "xml_type": "string", "kvp_key": "srs", "kvp_type": "string"}, # TODO: check XML location
        "layers": {"xml_location": "/layer", "xml_type": "string[]", "kvp_key": "layers", "kvp_type": "string[]"}, # TODO: check XML location
        "time": {"xml_location": "/time", "xml_type": "string", "kvp_key": "time", "kvp_type": "string"},
        "bbox": {"xml_location": "/bbox", "xml_type": "floatlist", "kvp_key": "bbox", "kvp_type": "floatlist"}
    }
    
    def getSRSParameterName(self):
        return "srs"
    
    def configureMapObj(self):
        super(WMS10_11GetMapHandler, self).configureMapObj()
        
        self.map.setMetaData("wms_exceptions_format", "application/vnd.ogc.se_xml")
        
        srid = self.getSRID()
        self.map.setProjection("+init=epsg:%d" % srid)
    
    def getMapServerLayer(self, coverage):
        layer = super(WMS10_11GetMapHandler, self).getMapServerLayer(coverage)
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
        "time": {"xml_location": "/time", "xml_type": "string", "kvp_key": "time", "kvp_type": "string"},
        "bbox": {"xml_location": "/bbox", "xml_type": "floatlist", "kvp_key": "bbox", "kvp_type": "floatlist"}
    }
    
    def getSRSParameterName(self):
        return "crs"
        
    def getBoundedArea(self, srid, bbox):
        if srid == 4326:
            return BoundedArea(srid, bbox[1], bbox[0], bbox[3], bbox[2])
        else:
            return BoundedArea(srid, *bbox)
    
    def configureRequest(self):
        
        # check if the format is known; if not MapServer will raise an 
        # exception instead of returning the correct service exception report
        # (bug)
        if not self.req.getParamValue("format"):
            raise InvalidRequestException(
                "Missing mandatory 'format' parameter",
                "MissingParameterValue",
                "format"
            )
        else:
            format_name = self.req.getParamValue("format")
            
            try:
                output_format = self.map.getOutputFormatByName(format_name)
                
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
        
        super(WMS13GetMapHandler, self).configureRequest()
    
    def configureMapObj(self):
        super(WMS13GetMapHandler, self).configureMapObj()
        
        self.map.setMetaData("wms_exceptions_format", "xml")
        self.map.setMetaData("ows_srs","EPSG:4326")
        
        srid = self.getSRID()
        self.map.setProjection("+init=epsg:%d" % srid)
    
    def getMapServerLayer(self, coverage):
        layer = super(WMS13GetMapHandler, self).getMapServerLayer(coverage)
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

