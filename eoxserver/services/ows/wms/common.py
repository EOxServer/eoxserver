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
import os

from osgeo.gdalconst import GDT_Byte
import mapscript

from eoxserver.core.system import System
from eoxserver.core.util.timetools import (
    isotime, getDateTime
)
from eoxserver.core.util.geotools import getSRIDFromCRSIdentifier
from eoxserver.core.exceptions import InternalError, InvalidParameterException
from eoxserver.resources.coverages.filters import (
    BoundedArea, TimeInterval
)
from eoxserver.processing.gdal.reftools import create_temporary_vrt
from eoxserver.services.owscommon import OWSCommonConfigReader
from eoxserver.services.mapserver import MapServerOperationHandler
from eoxserver.services.exceptions import InvalidRequestException

class WMSLayer(object):
    def __init__(self):
        self.group_name = None
                
        self.temp_files = []
        
    def getName(self):
        raise NotImplementedError
        
    def setGroup(self, group_name):
        self.group_name = group_name
    
    def getGroup(self):
        return self.group_name
    
    def getMapServerLayer(self, req):
        layer = mapscript.layerObj()
        
        layer.name = self.getName()
        layer.setMetaData("ows_title", self.getName())
        layer.setMetaData("wms_label", self.getName())
    
        if self.group_name:
            layer.group = self.group_name
            layer.setMetaData("wms_group_title", self.group_name)
        
        return layer

    def cleanup(self):
        for temp_file in self.temp_files:
            try:
                os.remove(temp_file)
            except:
                logging.warning("Could not remove temporary file '%s'" % temp_file)
                
class WMSEmptyLayer(WMSLayer):
    def __init__(self, layer_name):
        super(WMSEmptyLayer, self).__init__()
        
        self.layer_name = layer_name
        
    def getName(self):
        return self.layer_name
    
    def getMapServerLayer(self, req):
        layer = super(WMSEmptyLayer, self).getMapServerLayer(req)
        
        layer.setMetaData("wms_enable_request", "getmap")
                
        return layer

class WMSCoverageLayer(WMSLayer):
    def __init__(self, coverage):
        super(WMSCoverageLayer, self).__init__()
        
        self.coverage = coverage
        
    def getName(self):
        return self.coverage.getCoverageId()
        
    def isRGB(self):
        return self.coverage.getRangeType().name == "RGB"
    
    def isGrayscale(self):
        return self.coverage.getRangeType().name == "Grayscale"
        
    def getBandIndices(self, req):
        if len(self.coverage.getRangeType().bands) >= 3:
            return [1, 2, 3]
        else:
            return [1, 1, 1]

    def getBandSelection(self, req):
        bands = self.coverage.getRangeType().bands
        
        if len(bands) == 1 or len(bands) == 3:
            return bands
        elif len(bands) == 2:
            return bands
        else:
            return bands[:3]
        
    def setOffsiteColor(self, layer, bands):
        nil_values = []
        
        if len(bands) == 1:
            if len(bands[0].nil_values) > 0:
                nil_values = [
                    int(bands[0].nil_values[0].value),
                    int(bands[0].nil_values[0].value),
                    int(bands[0].nil_values[0].value)
                ]
                
                layer.offsite = mapscript.colorObj(*nil_values)

        if len(bands) == 3:
            for band in bands:
                if len(band.nil_values) > 0:
                    nil_values.append(int(band.nil_values[0].value))
                else:
                    return
                
            layer.offsite = mapscript.colorObj(*nil_values)
    
    def setScale(self, layer):
        if self.coverage.getRangeType().data_type != GDT_Byte:
            layer.setProcessingKey("SCALE", "AUTO")
    
    def configureBands(self, layer, req):
        bands = self.getBandSelection(req)
        
        if not self.isRGB() and not self.isGrayscale():
            layer.setProcessingKey("BANDS", "%d,%d,%d" % tuple(self.getBandIndices(req)))
        
        self.setOffsiteColor(layer, bands)
        
        self.setScale(layer)

    def getMapServerLayer(self, req):
        layer = super(WMSCoverageLayer, self).getMapServerLayer(req)
        
        layer.setMetaData("wms_enable_request", "getcapabilities,getmap")

        for key, value in self.coverage.getLayerMetadata():
            layer.setMetaData(key, value)

        layer.type = mapscript.MS_LAYER_RASTER
        layer.setConnectionType(mapscript.MS_RASTER, '')
        
        self.configureBands(layer, req)

        return layer

class WMSRectifiedDatasetLayer(WMSCoverageLayer):
    def getMapServerLayer(self, req):
        layer = super(WMSRectifiedDatasetLayer, self).getMapServerLayer(req)

        # general rectified coverage stuff
        layer.setProjection("+init=epsg:%d" % int(self.coverage.getSRID()))
        layer.setMetaData("ows_srs", "EPSG:%d" % int(self.coverage.getSRID()))
        layer.setMetaData("wms_extent", "%f %f %f %f" % self.coverage.getExtent())
        layer.setExtent(*self.coverage.getExtent())

        # rectified dataset stuff
        connector = System.getRegistry().findAndBind(
            intf_id = "services.mapserver.MapServerDataConnectorInterface",
            params = {
                "services.mapserver.data_structure_type": \
                    self.coverage.getDataStructureType()
            }
        )
        
        layer = connector.configure(layer, self.coverage)

        return layer
        
class WMSReferenceableDatasetLayer(WMSCoverageLayer):
    def setScale(self, layer):
        layer.setProcessingKey("SCALE", "1,2000") # TODO: make this configurable
    
    def getMapServerLayer(self, req):
        layer = super(WMSReferenceableDatasetLayer, self).getMapServerLayer(req)

        layer.setMetaData("ows_srs", "EPSG:4326")
        layer.setMetaData("wms_extent", "%f %f %f %f" % self.coverage.getWGS84Extent())
        layer.setExtent(*self.coverage.getWGS84Extent())
        
        layer.setProjection("+init=epsg:4326") # TODO: read this from dataset or database

        vrt_path = self.rectify()
        
        layer.data = vrt_path
        
        self.temp_files.append(vrt_path)

        return layer

    def rectify(self):
        return create_temporary_vrt(
            self.coverage.getData().getGDALDatasetIdentifier()
        )

class WMSRectifiedStitchedMosaicLayer(WMSCoverageLayer):
    def getMapServerLayer(self, req):
        layer = super(WMSRectifiedStitchedMosaicLayer, self).getMapServerLayer(req)
        
        layer.setProjection("+init=epsg:%d" % int(self.coverage.getSRID()))
        layer.setMetaData("ows_srs", "EPSG:%d" % int(self.coverage.getSRID()))

        #
        connector = System.getRegistry().findAndBind(
            intf_id = "services.mapserver.MapServerDataConnectorInterface",
            params = {
                "services.mapserver.data_structure_type": \
                    self.coverage.getDataStructureType()
            }
        ) 
        
        layer = connector.configure(layer, self.coverage)
        
        extent = self.coverage.getExtent()
        srid = self.coverage.getSRID()
        size = self.coverage.getSize()
        resolution = ((extent[2]-extent[0]) / float(size[0]),
                      (extent[1]-extent[3]) / float(size[1]))
        
        layer.setExtent(*self.coverage.getExtent())
        layer.setMetaData("wms_extent", "%.10f %.10f %.10f %.10f" % extent)
        layer.setMetaData("wms_resolution", "%.10f %.10f" % resolution)
        layer.setMetaData("wms_size", "%d %d" % size)
        
        layer.type = mapscript.MS_LAYER_RASTER
        layer.setConnectionType(mapscript.MS_RASTER, '')
        layer.setMetaData("wms_srs", "EPSG:%d" % srid)
        layer.setProjection("+init=epsg:%d" % srid)

        return layer

class WMSDatasetSeriesLayer(WMSLayer):
    def __init__(self, dataset_series):
        super(WMSDatasetSeriesLayer, self).__init__()
        
        self.dataset_series = dataset_series
        
    def getName(self):
        return self.dataset_series.getEOID()
        
    def getMapServerLayer(self, req):
        layer = super(WMSDatasetSeriesLayer, self).getMapServerLayer(req)
        
        coverages = self.dataset_series.getEOCoverages()

        layer.setMetaData("wms_extent", "%f %f %f %f" % self.dataset_series.getWGS84Extent())
        layer.setExtent(*self.dataset_series.getWGS84Extent())
        
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

class WMSCommonHandler(MapServerOperationHandler):
    PARAM_SCHEMA = {
        "service": {"xml_location": "/@service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/@version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"}
    }
    
    def __init__(self):
        super(WMSCommonHandler, self).__init__()
        
        self.req = None
        
        self.layers = []
        
        self.temp_files = []
        
    def _processRequest(self, req):
        self.req = req
        self.req.setSchema(self.PARAM_SCHEMA)

        try:
            self.validateParams()
            self.configureRequest()
            self.configureMapObj()
            self.createLayers()
            self.addMapServerLayers()
            response = self.postprocess(self.dispatch())
        finally:
            self.cleanup()
        
        return response

    def validateParams(self):
        pass
        
    def _setMapProjection(self):
        pass
        
    def configureMapObj(self):
        """
        This method configures the ``ms_req.map`` object (an
        instance of ``mapscript.mapObj``) with parameters from the
        config. This method can be overridden in order to implement more
        sophisticated behaviour. 
        
        @param  ms_req  An :class:`MapServerRequest` object
        
        @return         None
        """
        
        self.map.setMetaData("ows_onlineresource", OWSCommonConfigReader().getHTTPServiceURL() + "?")
        
        self._setMapProjection()
    
    def createLayers(self):
        pass
        
    def createCoverageLayer(self, coverage):
        if coverage.getType() == "plain":
            raise InternalError(
                "Plain coverage WMS views are not yet implemented."
            )        
        elif coverage.getType() == "eo.rect_dataset":
            return WMSRectifiedDatasetLayer(coverage)
        elif coverage.getType()  == "eo.ref_dataset":
            return WMSReferenceableDatasetLayer(coverage)
        elif coverage.getType() == "eo.rect_stitched_mosaic":
            return WMSRectifiedStitchedMosaicLayer(coverage)

    def addLayer(self, layer):
        self.layers.append(layer)
        
    def addMapServerLayers(self):
        for layer in self.layers:
            self.map.insertLayer(self.getMapServerLayer(layer))
    
    def getMapServerLayer(self, layer):
        return layer.getMapServerLayer(self.req)
        
    def postprocess(self, resp):
        return resp

    def cleanup(self):
        super(WMSCommonHandler, self).cleanup()
        
        for layer in self.layers:
            layer.cleanup()

class WMS1XGetCapabilitiesHandler(WMSCommonHandler):
    def _setMapProjection(self):
        self.map.setProjection("+init=epsg:4326")
    
    def createLayers(self):
        visible_expr = System.getRegistry().getFromFactory(
            "resources.coverages.filters.CoverageExpressionFactory",
            {"op_name": "attr", "operands": ("visible", "=", True)}
        )
        
        cov_factory = System.getRegistry().bind("resources.coverages.wrappers.EOCoverageFactory")
        
        for coverage in cov_factory.find(filter_exprs=[visible_expr]):
            self.addLayer(self.createCoverageLayer(coverage))
        
        dss_factory = System.getRegistry().bind("resources.coverages.wrappers.DatasetSeriesFactory")
        
        # TODO: find a more efficient way to do this check
        for dataset_series in dss_factory.find():
            if len(dataset_series.getEOCoverages()) > 0:
                self.layers.append(WMSDatasetSeriesLayer(dataset_series))

    def getMapServerLayer(self, layer):
        ms_layer = super(WMS1XGetCapabilitiesHandler, self).getMapServerLayer(layer)
                
        ms_layer.status = mapscript.MS_ON
        
        return ms_layer
    
class WMS1XGetMapHandler(WMSCommonHandler):
    def _setMapProjection(self):
        srid = self.getSRID()
        self.map.setProjection("+init=epsg:%d" % srid)

    def getSRSParameterName(self):
        raise NotImplementedError()

    def getBoundedArea(self, srid, bbox):
        return BoundedArea(srid, *bbox)
        
    def getTimeFilterExpr(self, time_param):
        timestamps = time_param.split("/")
        
        if len(timestamps) == 1:
            try:
                timestamp = getDateTime(timestamps[0])
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
    
    def getFilterExpressions(self):
        try:
            bbox = self.req.getParamValue("bbox")
        except InvalidParameterException:
            raise InvalidRequestException(
                "Invalid BBOX parameter value",
                "InvalidParameterValue",
                "bbox"
            )
        
        if len(bbox) != 4:
            raise InvalidRequestException(
                "Wrong number of arguments for 'BBOX' parameter",
                "InvalidParameterValue",
                "bbox"
            )
        
        srid = self.getSRID()
        
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
        
        return filter_exprs

    def createLayers(self):
        layer_names = self.req.getParamValue("layers")
        
        if layer_names is None:
            raise InvalidRequestException(
                "Missing 'LAYERS' parameter",
                "MissingParameterValue",
                "layers"
            )
        
        filter_exprs = self.getFilterExpressions()
        
        for layer_name in layer_names:
            self.createLayersForName(layer_name, filter_exprs)
    
    def createLayersForName(self, layer_name, filter_exprs):
        dataset_series = System.getRegistry().getFromFactory(
            "resources.coverages.wrappers.DatasetSeriesFactory",
            {"obj_id": layer_name}
        )
        if dataset_series is not None:
            self.createDatasetSeriesLayers(dataset_series, filter_exprs)
        else:
            coverage = System.getRegistry().getFromFactory(
                "resources.coverages.wrappers.EOCoverageFactory",
                {"obj_id": layer_name}
            )
            if coverage is not None:
                if coverage.matches(filter_exprs):
                    self.addLayer(self.createCoverageLayer(coverage))
                else:
                    self.addLayer(WMSEmptyLayer(coverage.getCoverageId()))
            else:
                raise InvalidRequestException(
                    "No coverage or dataset series with EO ID '%s' found" % layer_name,
                    "LayerNotDefined",
                    "layers"
                )
        
    def createDatasetSeriesLayers(self, dataset_series, filter_exprs):
        def _get_begin_time(coverage):
            return coverage.getBeginTime()
        
        coverages = dataset_series.getEOCoverages(filter_exprs)
        
        if len(coverages) == 0:
            layer = WMSEmptyLayer(dataset_series.getEOID())
            
            self.addLayer(layer)
            
        coverages.sort(key=_get_begin_time)
        
        for coverage in coverages:
            layer = self.createCoverageLayer(coverage)
            
            layer.setGroup(dataset_series.getEOID())
            
            self.addLayer(layer)
            
    def addLayer(self, layer):
        # TODO: more performant solution based on hashes
        for other_layer in self.layers:
            if other_layer.getName() == layer.getName():
                return
                
        self.layers.append(layer)
            
    def getSRID(self):
        srs = self.req.getParamValue(self.getSRSParameterName())

        if srs is None:
            raise InvalidRequestException("Missing '%s' parameter"% self.getSRSParameterName().upper(), "MissingParameterValue" , self.getSRSParameterName())
        
        srid = getSRIDFromCRSIdentifier(srs)
        if srid is None:
            raise InvalidRequestException("Invalid '%s' parameter value"% self.getSRSParameterName().upper(), "InvalidCRS" , self.getSRSParameterName())
            
        return srid
    
    def getMapServerLayer(self, layer):
        ms_layer = super(WMS1XGetMapHandler, self).getMapServerLayer(layer)
        
        ms_layer.status = mapscript.MS_DEFAULT
        
        return ms_layer
