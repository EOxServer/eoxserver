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

from xml.dom import minidom

import mapscript

import logging

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
    WMS1XGetCapabilitiesHandler, WMS1XGetMapHandler
)
from eoxserver.services.exceptions import InvalidRequestException

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
    
    def addLayers(self):
        super(WMS13GetCapabilitiesHandler, self).addLayers()
        
        for coverage in self.coverages:
            if coverage.getType() == "eo.rect_stitched_mosaic":
                self.map.insertLayer(
                    self.getMapServerMosaicOutlinesLayer(coverage)
                )
    
        for dataset_series in self.dataset_series_set:
            self.map.insertLayer(
                self.getMapServerDatasetSeriesOutlinesLayer(dataset_series)
            )
    
    def getMapServerOutlinesLayer(self, base_name):
        layer = mapscript.layerObj()
        
        layer_name = "%s_outlines" % base_name
        
        layer.name = layer_name
        layer.setMetaData("ows_title", layer_name)
        layer.setMetaData("wms_group", layer_name)
        layer.setMetaData("wms_layer_group", "/%s" % base_name)
        
        layer.setMetaData("wms_enable_request", "*")

        layer.setProjection("+init=epsg:4326")
        layer.setMetaData("wms_srs", "EPSG:4326")
        
        layer.type = mapscript.MS_LAYER_POLYGON
        
        layer.setConnectionType(mapscript.MS_INLINE, "")
        
        return layer
        
    def getMapServerMosaicOutlinesLayer(self, mosaic):
        layer = self.getMapServerOutlinesLayer(mosaic.getCoverageId())
        
        layer.setMetaData("wms_extent", "%f %f %f %f" % mosaic.getWGS84Extent())
        
        shape = mapscript.shapeObj().fromWKT(
            mosaic.getFootprint().wkt
        )

        layer.addFeature(shape)
        
        layer.status = mapscript.MS_ON
        
        return layer

    def getMapServerDatasetSeriesOutlinesLayer(self, dataset_series):
        layer = self.getMapServerOutlinesLayer(dataset_series.getEOID())
        
        layer.setMetaData("wms_extent", "%f %f %f %f" % dataset_series.getWGS84Extent())
        
        shape = mapscript.shapeObj().fromWKT(
            dataset_series.getFootprint().wkt
        )
        
        layer.addFeature(shape)
        
        layer.status = mapscript.MS_ON
        
        return layer
    
    def getMapServerLayer(self, coverage):
        layer = super(WMS13GetCapabilitiesHandler, self).getMapServerLayer(coverage)
        
        if coverage.getType() == "eo.rect_stitched_mosaic":
            layer.setMetaData("wms_layer_group", "/%s" % coverage.getCoverageId())
        
        return layer
    
    def getDatasetSeriesMapServerLayer(self, dataset_series):
        layer = super(WMS13GetCapabilitiesHandler, self).getDatasetSeriesMapServerLayer(dataset_series)
        
        layer.setMetaData("wms_layer_group", "/%s" % dataset_series.getEOID())
        
        return layer
    
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
        
        # add _bands and _outlines layers to EO Coverages
        for coverage in self.coverages:
            layer_el = self._get_layer_element(
                layer_els, coverage.getCoverageId()
            )
            
            layer_el.appendChild(encoder.encodeBandsLayer(
                "%s_bands" % coverage.getCoverageId(),
                coverage.getRangeType()
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
