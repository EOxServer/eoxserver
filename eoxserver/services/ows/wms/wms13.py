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

import os.path
from xml.dom import minidom

import mapscript

import logging

from django.conf import settings

from eoxserver.core.system import System
from eoxserver.core.util.xmltools import XMLEncoder, DOMtoXML
from eoxserver.core.exceptions import InternalError
from eoxserver.resources.coverages.filters import BoundedArea
from eoxserver.services.base import BaseExceptionHandler
from eoxserver.services.requests import Response
from eoxserver.services.interfaces import (
    ExceptionHandlerInterface, ExceptionEncoderInterface
)
from eoxserver.services.owscommon import OWSCommonVersionHandler
from eoxserver.services.ows.wms.common import (
    WMSLayer, WMSCoverageLayer, WMSDatasetSeriesLayer,
    WMSRectifiedDatasetLayer, WMSReferenceableDatasetLayer,
    WMSRectifiedStitchedMosaicLayer, WMSCommonHandler,
    WMS1XGetCapabilitiesHandler, WMS1XGetMapHandler
)
from eoxserver.services.exceptions import InvalidRequestException

class EOWMSOutlinesLayer(WMSLayer):
    STYLES = (
        ("red", 255, 0, 0),
        ("green", 0, 128, 0),
        ("blue", 0, 0, 255),
        ("white", 255, 255, 255),
        ("black", 0, 0, 0),
        ("yellow", 255, 255, 0),
        ("orange", 255, 165, 0),
        ("magenta", 255, 0, 255),
        ("cyan", 0, 255, 255),
        ("brown", 165, 42, 42)
    )
    
    DEFAULT_STYLE = "red"
    
    def createOutlineClass(self, name, r, g, b):
        outline_class = mapscript.classObj()
        outline_style = mapscript.styleObj()
        outline_style.outlinecolor = mapscript.colorObj(r, g, b)
        outline_class.insertStyle(outline_style)
        outline_class.group = name
        
        return outline_class
    
    def configureConnection(self, layer):
        db_conf = settings.DATABASES["default"]
        
        if db_conf["ENGINE"] == "django.contrib.gis.db.backends.postgis":
            layer.setConnectionType(mapscript.MS_POSTGIS, "")
            
            conn_params = []
            
            if db_conf["HOST"]:
                conn_params.append("host=%s" % db_conf["HOST"])
            
            if db_conf["PORT"]:
                conn_params.append("port=%s" % db_conf["PORT"])
                
            conn_params.append("dbname=%s" % db_conf["NAME"])
            
            conn_params.append("user=%s" % db_conf["USER"])
            
            if db_conf["PASSWORD"]:
                conn_params.append("passwd=%s" % db_conf["PASSWORD"])
            
            layer.connection = " ".join(conn_params)
            
            layer.data = "footprint from (%s) sq USING SRID=4326 USING UNIQUE oid" % self.getSubQuery()
            
        elif db_conf["ENGINE"] == "django.contrib.gis.db.backends.spatialite":
            layer.setConnectionType(mapscript.MS_OGR, "")
            
            layer.connection = db_conf["NAME"]
            
            layer.data = self.getSubQuery()
    
    def getMapServerLayer(self, req):
        layer = super(EOWMSOutlinesLayer, self).getMapServerLayer(req)
        
        layer.setMetaData("wms_enable_request", "getcapabilities,getmap,getfeatureinfo")

        layer.setProjection("+init=epsg:4326")
        layer.setMetaData("wms_srs", "EPSG:4326")
        
        layer.type = mapscript.MS_LAYER_POLYGON
        
        self.configureConnection(layer)
        
        # TODO: make this configurable
        layer.header = os.path.join(settings.PROJECT_DIR, "conf", "outline_template_header.html")
        layer.template = os.path.join(settings.PROJECT_DIR, "conf", "outline_template_dataset.html")
        layer.footer = os.path.join(settings.PROJECT_DIR, "conf", "outline_template_footer.html")
        
        layer.setMetaData("gml_include_items", "all")
        
        #layer.tolerance = 10.0
        #layer.toleranceunits = mapscript.MS_PIXELS
            
        layer.offsite = mapscript.colorObj(0, 0, 0)
        
        for style_info in self.STYLES:
            layer.insertClass(self.createOutlineClass(*style_info))

        layer.classgroup = self.DEFAULT_STYLE

        return layer

class EOWMSRectifiedStitchedMosaicOutlinesLayer(EOWMSOutlinesLayer):
    def __init__(self, mosaic):
        super(EOWMSRectifiedStitchedMosaicOutlinesLayer, self).__init__()
        
        self.mosaic = mosaic
    
    def getName(self):
        return "%s_outlines" % self.mosaic.getCoverageId()
    
    def getSubQuery(self):
        return "SELECT eomd.id AS oid, eomd.footprint AS geometry, cov.coverage_id FROM coverages_eometadatarecord AS eomd, coverages_coveragerecord AS cov, coverages_rectifieddatasetrecord AS rd, coverages_rectifiedstitchedmosaicrecord_rect_datasets AS rsm2rd WHERE rsm2rd.rectifiedstitchedmosaicrecord_id = %d AND rsm2rd.rectifieddatasetrecord_id = rd.coveragerecord_ptr_id AND cov.resource_ptr_id = rd.coveragerecord_ptr_id AND rd.eo_metadata_id = eomd.id" % self.mosaic.getModel().pk
    
    def getMapServerLayer(self, req):
        layer = super(EOWMSRectifiedStitchedMosaicOutlinesLayer, self).getMapServerLayer(req)
        
        layer.setMetaData("wms_extent", "%f %f %f %f" % self.mosaic.getWGS84Extent())
        
        return layer

class EOWMSDatasetSeriesOutlinesLayer(EOWMSOutlinesLayer):
    def __init__(self, dataset_series):
        super(EOWMSDatasetSeriesOutlinesLayer, self).__init__()
        
        self.dataset_series = dataset_series
        
    def getName(self):
        return "%s_outlines" % self.dataset_series.getEOID()
    
    def getSubQuery(self):
        return "SELECT eomd.id AS oid, eomd.footprint AS geometry, cov.coverage_id FROM coverages_eometadatarecord AS eomd, coverages_coveragerecord AS cov, coverages_rectifieddatasetrecord AS rd, coverages_datasetseriesrecord_rect_datasets AS ds2rd WHERE ds2rd.datasetseriesrecord_id = %d AND ds2rd.rectifieddatasetrecord_id = rd.coveragerecord_ptr_id AND cov.resource_ptr_id = rd.coveragerecord_ptr_id AND rd.eo_metadata_id = eomd.id" % self.dataset_series.getModel().pk
    
    def getMapServerLayer(self, req):
        layer = super(EOWMSDatasetSeriesOutlinesLayer, self).getMapServerLayer(req)
        
        layer.setMetaData("wms_extent", "%f %f %f %f" % self.dataset_series.getWGS84Extent())

        return layer

class EOWMSBandsLayerMixIn(object):
    def isRGB(self):
        return False
        
    def isGrayscale(self):
        return False
    
    def getName(self):
        return "%s_bands" % self.coverage.getCoverageId()
    
    def _get_band_index(self, band_name):
        c = 0
        for band in self.coverage.getRangeType().bands:
            c += 1
            if normalize_band_name(band.name) == band_name:
                return c

        raise InvalidRequestException(
            "Unknown band name '%s'." % band_name,
            "InvalidDimensionValue",
            "dim_band"
        )

    def _get_band(self, band_name):
        for band in self.coverage.getRangeType().bands:
            if normalize_band_name(band.name) == band_name:
                return band
                
        raise InvalidRequestException(
            "Unknown band name '%s'." % band_name,
            "InvalidDimensionValue",
            "dim_band"
        )
        
    def getBandIndices(self, req):
        band_list = req.getParamValue("dim_band")
        
        if not band_list or len(band_list) not in (1, 3):
            raise InvalidRequestException(
                "Exactly one or three band names need to be provided in DIM_BAND parameter.",
                "InvalidDimensionValue",
                "dim_band"            
            )
        
        if len(band_list) == 1:
            c = self._get_band_index(band_list[0])
            
            return [c, c, c]
            
        elif len(band_list) == 3:
            band_indices = []
            
            for band_name in band_list:
                band_indices.append(self._get_band_index(band_name))
            
            return band_indices
        
    def getBandSelection(self, req):
        band_list = req.getParamValue("dim_band")
        
        if not band_list or len(band_list) not in (1, 3):
            raise InvalidRequestException(
                "Exactly one or three band names need to be provided in DIM_BAND parameter.",
                "InvalidDimensionValue",
                "dim_band"            
            )
        
        if len(band_list) == 1:
            return [self._get_band(band_list[0])]
        elif len(band_list) == 3:
            bands = []
            
            for band_name in band_list:
                bands.append(self._get_band(band_name))
            
            return bands

class EOWMSRectifiedDatasetBandsLayer(EOWMSBandsLayerMixIn, WMSRectifiedDatasetLayer):
    pass
    
class EOWMSReferenceableDatasetBandsLayer(EOWMSBandsLayerMixIn, WMSReferenceableDatasetLayer):
    pass
    
class EOWMSRectifiedStitchedMosaicBandsLayer(EOWMSBandsLayerMixIn, WMSRectifiedStitchedMosaicLayer):
    pass
    
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
    
    def configureMapObj(self):
        super(WMS13GetCapabilitiesHandler, self).configureMapObj()
        
        self.map.setMetaData("wms_enable_requests", "getcapabilities,getmap,getfeatureinfo")
        self.map.setMetaData("wms_feature_info_mime_type", "text/html")
    
    def createLayers(self):
        visible_expr = System.getRegistry().getFromFactory(
            "resources.coverages.filters.CoverageExpressionFactory",
            {"op_name": "attr", "operands": ("visible", "=", True)}
        )
        
        cov_factory = System.getRegistry().bind("resources.coverages.wrappers.EOCoverageFactory")
        
        for coverage in cov_factory.find(filter_exprs=[visible_expr]):
            layer = self.createCoverageLayer(coverage)
            if coverage.getType() == "eo.rect_stitched_mosaic":
                layer.setGroup(coverage.getCoverageId())
                self.addLayer(layer)
                
                outlines_layer = EOWMSRectifiedStitchedMosaicOutlinesLayer(coverage)
                outlines_layer.setGroup(coverage.getCoverageId())
                self.addLayer(outlines_layer)
            else:
                self.addLayer(layer)
        
        dss_factory = System.getRegistry().bind("resources.coverages.wrappers.DatasetSeriesFactory")
        
        # TODO: find a more efficient way to do this check
        for dataset_series in dss_factory.find():
            if len(dataset_series.getEOCoverages()) > 0:
                layer = WMSDatasetSeriesLayer(dataset_series)
                layer.setGroup(dataset_series.getEOID())
                self.addLayer(layer)
                
                outlines_layer = EOWMSDatasetSeriesOutlinesLayer(dataset_series)
                outlines_layer.setGroup(dataset_series.getEOID())
                self.addLayer(outlines_layer)
    
    def postprocess(self, resp):
        # if the content cannot be parsed, return the response unchanged
        try:
            xml = minidom.parseString(resp.getContent())
        except:
            return resp
        
        # Exception reports are not changed
        if xml.documentElement.localName == "ExceptionReport":
            return resp

        layer_els = xml.getElementsByTagNameNS(
            "http://www.opengis.net/wms", "Layer"
        )
        
        encoder = EOWMSEncoder()
        
        # add _bands layers
        # TODO: this solution really is not nice
        for layer in self.layers:
            if not isinstance(layer, EOWMSOutlinesLayer) and not isinstance(layer, WMSDatasetSeriesLayer):
                layer_el = self._get_layer_element(
                    layer_els, layer.getName()
                )
                
                layer_el.appendChild(encoder.encodeBandsLayer(
                    "%s_bands" % layer.getName(),
                    layer.coverage.getRangeType()
                ))
            
        return Response(
            content = DOMtoXML(xml),
            content_type = resp.getContentType(),
            status = 200,
            headers = resp.getHeaders()
        )

    def _get_layer_element(self, layer_els, layer_name):
        for layer_el in layer_els:
            for node in layer_el.childNodes:
                if node.localName == "Name":
                    if node.firstChild.data == layer_name:
                        return layer_el
                    else:
                        break
        
        raise InternalError(
            "Could not find 'Layer' element with name '%s' in WMS 1.3 GetCapabilities response" %\
            layer_name
        )
    

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
        "service": {"xml_location": "/@service",     "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/@version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"},
        "crs": {"xml_location": "/crs", "xml_type": "string", "kvp_key": "crs", "kvp_type": "string"}, # TODO: check XML location
        "layers": {"xml_location": "/layer", "xml_type": "string[]", "kvp_key": "layers", "kvp_type": "stringlist"}, # TODO: check XML location
        "format": {"xml_location": "/format", "xml_type": "string", "kvp_key": "format", "kvp_type": "string"},
        "time": {"xml_location": "/time", "xml_type": "string", "kvp_key": "time", "kvp_type": "string"},
        "bbox": {"xml_location": "/bbox", "xml_type": "floatlist", "kvp_key": "bbox", "kvp_type": "floatlist"},
        "dim_band": {"kvp_key": "dim_band", "kvp_type": "stringlist"}
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
        
        self.map.setMetaData("wms_enable_requests", "getcapabilities,getmap,getfeatureinfo")
        self.map.setMetaData("wms_feature_info_mime_type", "text/html")
        
    def createLayersForName(self, layer_name, filter_exprs):
        if layer_name.endswith("_outlines"):
            self.createOutlinesLayer(layer_name[:-9])
        elif layer_name.endswith("_bands"):
            self.createBandsLayers(layer_name[:-6], filter_exprs)
        else:
            super(WMS13GetMapHandler, self).createLayersForName(
                layer_name, filter_exprs
            )
    
    def createOutlinesLayer(self, base_name):
        dataset_series = System.getRegistry().getFromFactory(
            "resources.coverages.wrappers.DatasetSeriesFactory",
            {"obj_id": base_name}
        )
        if dataset_series is not None:
            outlines_layer = EOWMSDatasetSeriesOutlinesLayer(dataset_series)
            
            self.addLayer(outlines_layer)
        else:
            coverage = System.getRegistry().getFromFactory(
                "resources.coverages.wrappers.EOCoverageFactory",
                {"obj_id": base_name}
            )
            if coverage is not None and coverage.getType() == "eo.rect_stitched_mosaic":
                outlines_layer = EOWMSRectifiedStitchedMosaicOutlinesLayer(coverage)
                
                self.addLayer(outlines_layer)
            else:
                raise InvalidRequestException(
                    "No coverage or dataset series with EO ID '%s' found" % base_name,
                    "LayerNotDefined",
                    "layers"
                )
    
    def createBandsLayers(self, base_name, filter_exprs):
        dataset_series = System.getRegistry().getFromFactory(
            "resources.coverages.wrappers.DatasetSeriesFactory",
            {"obj_id": base_name}
        )
        if dataset_series is not None:
            self.createDatasetSeriesBandsLayers(dataset_series, filter_exprs)
        else:
            coverage = System.getRegistry().getFromFactory(
                "resources.coverages.wrappers.EOCoverageFactory",
                {"obj_id": base_name}
            )
            if coverage is not None:
                if coverage.matches(filter_exprs):
                    self.addLayer(self.createCoverageBandsLayer(coverage))
                else:
                    pass # TODO: check WMS spec for correct handling
            else:
                raise InvalidRequestException(
                    "No coverage or dataset series with EO ID '%s' found" % base_name,
                    "LayerNotDefined",
                    "layers"
                )

    def createCoverageBandsLayer(self, coverage):
        if coverage.getType() == "plain":
            raise InternalError(
                "Plain coverages are not yet supported"
            )
        elif coverage.getType() == "eo.rect_dataset":
            return EOWMSRectifiedDatasetBandsLayer(coverage)
        elif coverage.getType() == "eo.ref_dataset":
            return EOWMSReferenceableDatasetBandsLayer(coverage)
        elif coverage.getType() == "eo.rect_stitched_mosaic":
            return EOWMSRectifiedStitchedMosaicBandsLayer(coverage)
    
    def createDatasetSeriesBandsLayers(self, dataset_series, filter_exprs):
        def _get_begin_time(coverage):
            return coverage.getBeginTime()
        
        coverages = dataset_series.getEOCoverages(filter_exprs)
        
        if len(coverages) == 0:
            return # TODO: this will cause errors because of missing layers
            
        coverages.sort(key=_get_begin_time)
        
        for coverage in coverage:
            layer = self.createCoverageBandsLayer(coverage)
            
            layer.setGroup("%s_bands" % dataset_series.getEOID())
            
            self.addLayer(layer)
        
    def getMapServerLayer(self, layer):
        ms_layer = super(WMS13GetMapHandler, self).getMapServerLayer(layer)
        ms_layer.setMetaData("wms_exceptions_format","xml")
        
        return ms_layer

class WMS13GetFeatureInfoHandler(WMSCommonHandler):
    REGISTRY_CONF = {
        "name": "WMS 1.3 GetFeatureInfo Handler",
        "impl_id": "services.ows.wms1x.WMS13GetFeatureInfoHandler",
        "registry_values": {
            "services.interfaces.service": "wms",
            "services.interfaces.version": "1.3.0",
            "services.interfaces.operation": "getfeatureinfo"
        }
    }
    
    PARAM_SCHEMA = {
        "service": {"xml_location": "/@service",     "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/@version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"},
        "crs": {"xml_location": "/crs", "xml_type": "string", "kvp_key": "crs", "kvp_type": "string"}, # TODO: check XML location
        "query_layers": {"xml_location": "/query_layer", "xml_type": "string[]", "kvp_key": "query_layers", "kvp_type": "stringlist"}, # TODO: check XML location
        "info_format": {"xml_location": "/info_format", "xml_type": "string", "kvp_key": "info_format", "kvp_type": "string"},
        "bbox": {"xml_location": "/bbox", "xml_type": "floatlist", "kvp_key": "bbox", "kvp_type": "floatlist"},
        "i": {"kvp_key": "i", "kvp_type": "int"},
        "j": {"kvp_key": "j", "kvp_type": "int"}
    }
    
    def _setMapProjection(self):
        self.map.setProjection("+init=epsg:4326")
        self.map.setMetaData("ows_srs", "EPSG:4326")
    
    def configureMapObj(self):
        super(WMS13GetFeatureInfoHandler, self).configureMapObj()
        
        self.map.setMetaData("wms_exceptions_format", "xml")
        self.map.setMetaData("ows_srs","EPSG:4326")
        
        self.map.setMetaData("wms_enable_requests", "getcapabilities,getmap,getfeatureinfo")
        self.map.setMetaData("wms_feature_info_mime_type", "text/html")

    def createLayers(self):
        layer_names = self.req.getParamValue("query_layers")
        
        if layer_names is None:
            raise InvalidRequestException(
                "Missing 'QUERY_LAYERS' parameter",
                "MissingParameterValue",
                "layers"
            )
        
        for layer_name in layer_names:
            self.createLayerForName(layer_name)
    
    def createLayerForName(self, layer_name):
        if not layer_name.endswith("_outlines"):
            raise InternalError(
                "Cannot query layer '%s'" % layer_name,
                "LayerNotDefined",
                "query_layers"
            )
        
        base_name = layer_name[:-9]
        
        dataset_series = System.getRegistry().getFromFactory(
            "resources.coverages.wrappers.DatasetSeriesFactory",
            {"obj_id": base_name}
        )
        if dataset_series is not None:
            outlines_layer = EOWMSDatasetSeriesOutlinesLayer(dataset_series)
            
            self.addLayer(outlines_layer)
        else:
            coverage = System.getRegistry().getFromFactory(
                "resources.coverages.wrappers.EOCoverageFactory",
                {"obj_id": base_name}
            )
            if coverage is not None and coverage.getType() == "eo.rect_stitched_mosaic":
                outlines_layer = EOWMSRectifiedStitchedMosaicOutlinesLayer(coverage)
                
                self.addLayer(outlines_layer)
            else:
                raise InvalidRequestException(
                    "No coverage or dataset series with EO ID '%s' found" % base_name,
                    "LayerNotDefined",
                    "layers"
                )

    def getMapServerLayer(self, layer):
        ms_layer = super(WMS13GetFeatureInfoHandler, self).getMapServerLayer(layer)
        ms_layer.setMetaData("wms_exceptions_format","xml")
        
        return ms_layer

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

    def encodeException(self, exception):
        return self.encodeExceptionReport("Internal Server Error", "NoApplicableCode")

WMS13ExceptionEncoderImplementation = ExceptionEncoderInterface.implement(WMS13ExceptionEncoder)

class EOWMSEncoder(XMLEncoder):
    def _initializeNamespaces(self):
        ns_dict = super(EOWMSEncoder, self)._initializeNamespaces()
        
        ns_dict.update({
            "wms": "http://www.opengis.net/wms"
        })
        
        return ns_dict
    
    def encodeBandsLayer(self, layer_name, range_type):
        band_name_list = ",".join(
            [normalize_band_name(band.name) for band in range_type.bands]
        )
        
        return self._makeElement("wms", "Layer", [
            ("wms", "Name", layer_name),
            ("wms", "Title", layer_name),
            ("wms", "Dimension", [
                ("", "@name", "band"),
                ("", "@units", ""),
                ("", "@multipleValues", "1"),
                ("", "@@", band_name_list)
            ])
        ])

def normalize_band_name(band_name):
    return band_name.replace(" ", "_")
