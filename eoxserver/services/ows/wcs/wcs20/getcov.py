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

import os
from tempfile import mkstemp, mkdtemp
from xml.dom import minidom
from email.message import Message

import mapscript
from osgeo import gdal
gdal.UseExceptions()

import logging

from eoxserver.core.system import System
from eoxserver.core.readers import ConfigReaderInterface
from eoxserver.core.exceptions import InternalError, InvalidExpressionError
from eoxserver.core.util.xmltools import DOMElementToXML
from eoxserver.processing.gdal.reftools import rect_from_subset
from eoxserver.processing.nest.gpt import (
    convert_format, create_geo_subset, create_pixel_subset
)
from eoxserver.services.base import BaseRequestHandler
from eoxserver.services.requests import Response
from eoxserver.services.mapserver import (
    gdalconst_to_imagemode, gdalconst_to_imagemode_string
)
from eoxserver.services.exceptions import (
    InvalidRequestException, InvalidSubsettingException,
    InvalidAxisLabelException
)
from eoxserver.services.ows.wcs.common import (
    WCSCommonHandler, get_output_format, parse_format_param
)
from eoxserver.services.ows.wcs.encoders import WCS20EOAPEncoder
from eoxserver.services.ows.wcs.wcs20.subset import WCS20SubsetDecoder

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
        "service": {"xml_location": "/service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"},
        "coverageid": {"xml_location": "/{http://www.opengis.net/wcs/2.0}CoverageId", "xml_type": "string", "kvp_key": "coverageid", "kvp_type": "string"},
    }

    def _processRequest(self, req):
        req.setSchema(self.PARAM_SCHEMA)
        
        coverage = self._get_coverage(req)
        
        if coverage.getType() == "plain":
            handler = WCS20GetRectifiedCoverageHandler() # TODO: write plain coverage handler
            return handler.handle(req)
        elif coverage.getType() in ("eo.rect_stitched_mosaic", "eo.rect_dataset"):
            handler = WCS20GetRectifiedCoverageHandler()
            return handler.handle(req)
        elif coverage.getType() == "eo.ref_dataset":
            if WCS20GetCoverageConfigReader().useNest():
                handler = WCS20GetReferenceableCoverageNESTHandler()
                return handler.handle(req, coverage)
            else:
                handler = WCS20GetReferenceableCoverageGDALHandler()
                return handler.handle(req, coverage)
    
    def _get_coverage(self, req):
        coverage_id = req.getParamValue("coverageid")
            
        if coverage_id is None:
            raise InvalidRequestException("Missing 'coverageid' parameter", "MissingParameterValue", "coverageid")
        else:
            coverage = System.getRegistry().getFromFactory(
                "resources.coverages.wrappers.EOCoverageFactory",
                {"obj_id": coverage_id}
            )
            
            if coverage is not None:
                return coverage
            else:
                raise InvalidRequestException(
                    "No coverage with id '%s' found" % coverage_id, "NoSuchCoverage", coverage_id
                )
                
class WCS20GetReferenceableCoverageBaseHandler(object):
    PARAM_SCHEMA = {
        "service": {"xml_location": "/service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"},
        "coverageid": {"xml_location": "/{http://www.opengis.net/wcs/2.0}CoverageId", "xml_type": "string", "kvp_key": "coverageid", "kvp_type": "string"},
        "trims": {"xml_location": "/{http://www.opengis.net/wcs/2.0}DimensionTrim", "xml_type": "element[]"},
        "slices": {"xml_location": "/{http://www.opengis.net/wcs/2.0}DimensionSlice", "xml_type": "element[]"},
        "format": {"xml_location": "/{http://www.opengis.net/wcs/2.0}Format", "xml_type": "string", "kvp_key": "format", "kvp_type": "string"},
        "mediatype": {"xml_location": "/{http://www.opengis.net/wcs/2.0}Mediatype", "xml_type": "string", "kvp_key": "mediatype", "kvp_type": "string"}
    }
    
    def _get_subset(self, req, coverage):
        cov_x_size, cov_y_size = coverage.getSize()
        
        # get subsetting
        decoder = WCS20SubsetDecoder(req, "imageCRS")
        
        try:
            return decoder.getSubset(cov_x_size, cov_y_size, coverage.getFootprint())
        except InvalidSubsettingException, e:
            raise InvalidRequestException(
                str(e), "InvalidSubsetting", "subset"
            )
        except InvalidAxisLabelException, e:
            raise InvalidRequestException(
                str(e), "InvalidAxisLabel", "subset"
            )
            
    def _parse_format_param(self, req):
        format_param = req.getParamValue("format")
        
        if format_param is None:
            raise InvalidRequestException(
                "Missing mandatory 'format' parameter.",
                "MissingParameterValue",
                "format"
            )
        
        mime_type, format_options = parse_format_param(format_param)
        
        if mime_type not in self.FORMAT_MAPPING:
            raise InvalidRequestException(
                "Unknown or unsupported format '%s'" % mime_type,
                "InvalidParameterValue",
                "format"
            )
        else:
            return (mime_type, format_options)
    
    def _get_temp_file(self, mime_type):
        return os.path.join(
            mkdtemp(),
            "tmp.%s" % self.EXT_MAPPING[mime_type]
        )

    def _remove_temp_file(self, dst_filename):
        if os.path.exists(dst_filename):
            os.remove(dst_filename)
        
        dirname = os.path.dirname(dst_filename)
        
        if os.path.exists(dirname):
            os.rmdir(dirname)
        

    def _get_default_response(self, dst_filename, mime_type):
        f = open(dst_filename)
        
        resp = Response(
            content_type = mime_type,
            content = f.read(),
            headers = {},
            status = 200
        )
        
        f.close()
        
        return resp
    
    def _get_multipart_response(self, dst_filename, mime_type, cov_desc):
        
        xml_msg = Message()
        
        xml_msg.set_payload(cov_desc)
        xml_msg.add_header("Content-type", "text/xml")
        
        f = open(dst_filename)
        
        data = f.read()
        
        data_msg = Message()
        
        data_msg.set_payload(data)
        data_msg.add_header("Content-type", mime_type)
        
        content = "--wcs\n%s\n--wcs\n%s\n--wcs--" % (xml_msg.as_string(), data_msg.as_string())
        
        resp = Response(
            content = content,
            content_type = "multipart/mixed; boundary=wcs",
            headers = {},
            status = 200
        )
        
        f.close()
        
        return resp

class WCS20GetReferenceableCoverageGDALHandler(WCS20GetReferenceableCoverageBaseHandler):
    FORMAT_MAPPING = {
        "image/tiff": "GTiff",
        "image/jp2": "JPEG2000",
        "application/x-netcdf": "NetCDF",
        "application/x-hdf": "HDF4Image"
    }
    
    EXT_MAPPING = {
        "image/tiff": "tif",
        "image/jp2": "jp2",
        "application/x-netcdf": "nc",
        "application/x-hdf": "hdf"
    }


    def handle(self, req, coverage):
        req.setSchema(self.PARAM_SCHEMA)
        
        subset = self._get_subset(req, coverage)
    
        cov_x_size, cov_y_size = coverage.getSize()
        
        if subset is None:
            x_off = 0
            y_off = 0
            x_size = cov_x_size
            y_size = cov_y_size
        elif subset.crs_id != "imageCRS":
            x_off, y_off, x_size, y_size = rect_from_subset(
                coverage.getData().getGDALDatasetIdentifier(),
                subset.crs_id,
                subset.minx,
                subset.miny,
                subset.maxx,
                subset.maxy
            )
        else:
            x_off = subset.minx
            y_off = subset.miny
            x_size = subset.maxx - subset.minx
            y_size = subset.maxy - subset.miny
            
        # calculate effective offsets and buffer size
        
        src_x_off = max(0, x_off)
        src_y_off = max(0, y_off)
        
        dst_x_off = max(0, -x_off)
        dst_y_off = max(0, -y_off)
        
        buffer_x_size = max(min(x_off + x_size, cov_x_size) - src_x_off, 0)
        buffer_y_size = max(min(y_off + y_size, cov_y_size) - src_y_off, 0)
        
        if buffer_x_size == 0 or buffer_y_size == 0:
            raise InvalidRequestException(
                "Subset outside coverage extent.",
                "InvalidParameterValue",
                "subset"
            )

        # get format
        mime_type, format_options = self._parse_format_param(req)
        
        dst_filename = self._get_temp_file(mime_type)

        range_type = coverage.getRangeType()
        
        gdal_driver = gdal.GetDriverByName(self.FORMAT_MAPPING[mime_type])
        
        if gdal_driver is None:
            raise InternalError(
                "Could not retrieve GDAL Driver '%s'" % FORMAT_MAPPING[mime_type]
            )
    
        dst_ds = gdal_driver.Create(
            dst_filename, x_size, y_size, len(range_type.bands),
            range_type.data_type, ",".join(format_options)
        )
        
        if dst_ds is None:
            raise InternalError("Could not create output dataset.")
        
        src_ds = coverage.getData().open()
        
        if src_ds is None:
            raise InternalError("Could not open input dataset.")
        
        raster_buffer = src_ds.ReadRaster(
            src_x_off,
            src_y_off,
            buffer_x_size,
            buffer_y_size
        )
        
        dst_ds.WriteRaster(
            dst_x_off,
            dst_y_off,
            buffer_x_size,
            buffer_y_size,
            raster_buffer
        )
        
        # tag metadata onto raster buffer
        md_dict = src_ds.GetMetadata()
        
        for key, value in md_dict.items():
            dst_ds.SetMetadataItem(key, value)
        
        # save GCPs
        src_gcp_proj = src_ds.GetGCPProjection()
        src_gcps = src_ds.GetGCPs()
        
        dst_gcps = []
        for src_gcp in src_gcps:
            dst_gcps.append(gdal.GCP(
                src_gcp.GCPX,
                src_gcp.GCPY,
                src_gcp.GCPZ,
                src_gcp.GCPPixel + src_x_off - dst_x_off,
                src_gcp.GCPLine + src_y_off - dst_y_off,
                src_gcp.Info,
                src_gcp.Id
            ))
        
        dst_ds.SetGCPs(dst_gcps, src_gcp_proj)
        
        # close datasets
        del src_ds
        del dst_ds
        
        # prepare response
        media_type = req.getParamValue("mediatype")
        
        if media_type is None:
            resp = self._get_default_response(dst_filename, mime_type)
        elif media_type == "multipart/related" or media_type == "multipart/mixed":
            encoder = WCS20EOAPEncoder()
            
            if subset is not None:
                if subset.crs_id != "imageCRS":
                    cov_desc_el = encoder.encodeSubsetCoverageDescription(
                        coverage,
                        subset.crs_id,
                        (x_size, y_size),
                        (subset.minx, subset.miny, subset.maxx, subset.maxy)
                    )
                else:
                    cov_desc_el = encoder.encodeCoverageDescription(coverage)
# TODO: this should read as follows
#                    cov_desc_el = encoder.encodeSubsetCoverageDescription(
#                        coverage,
#                        4326,
#                        (x_size, y_size),
#                        ...
#                    
#                    )
            else:
                cov_desc_el = encoder.encodeCoverageDescription(coverage)
            
            resp = self._get_multipart_response(
                dst_filename, mime_type, DOMElementToXML(cov_desc_el)
            )
        else:
            raise InvalidRequestException(
                "Unknown media type '%s'" % media_type,
                "InvalidParameterValue",
                "mediatype"
            )
            
        #clean up
        self._remove_temp_file(dst_filename)
        
        return resp
    


class WCS20GetReferenceableCoverageNESTHandler(WCS20GetReferenceableCoverageBaseHandler):
    FORMAT_MAPPING = {
        "image/tiff": "geotiff",
        "application/x-netcdf": "netcdf",
        "application/x-hdf": "hdf" # Does not work with vanilla NEST 4B-1.1
    }
    
    EXT_MAPPING = {
        "image/tiff": "tif",
        "application/x-netcdf": "nc",
        "application/x-hdf": "hdf"
    }
    
    def handle(self, req, coverage):
        req.setSchema(self.PARAM_SCHEMA)
                
        mime_type, format_options = self._parse_format_param(req)
        
        subset = self._get_subset(req, coverage)
        
        dst_filename = self._get_temp_file(mime_type)
        
        if subset is None:
            convert_format(
                coverage.getData().getGDALDatasetIdentifier(),
                dst_filename,
                self.FORMAT_MAPPING[mime_type]
            )
        elif subset.crs_id != "imageCRS":
            create_geo_subset(
                coverage.getData().getGDALDatasetIdentifier(),
                dst_filename,
                subset.crs_id,
                (subset.minx, subset.miny, subset.maxx, subset.maxy),
                self.FORMAT_MAPPING[mime_type]           
            )
        else:
            create_pixel_subset(
                coverage.getData().getGDALDatasetIdentifier(),
                dst_filename,
                (subset.minx, subset.miny, subset.maxx, subset.maxy),
                self.FORMAT_MAPPING[mime_type]
            )
        
        # prepare response
        media_type = req.getParamValue("mediatype")
        
        if media_type is None:
            resp = self._get_default_response(dst_filename, mime_type)
        elif media_type == "multipart/related" or media_type == "multipart/mixed":
            encoder = WCS20EOAPEncoder()
            
#            if subset is not None:
#                if subset.crs_id != "imageCRS":
#                    cov_desc = encoder.encodeSubsetCoverageDescription(
#                        coverage,
#                        subset.crs_id,
#                        (x_size, y_size), # TODO!
#                        (subset.minx, subset.miny, subset.maxx, subset.maxy)
#                    )
#                else:
#                    cov_desc = encoder.encodeCoverageDescription(coverage)
# TODO: this should read as follows
#                    cov_desc = encoder.encodeSubsetCoverageDescription(
#                        coverage,
#                        4326,
#                        (x_size, y_size),
#                        ...
#                    
#                    )
#            else:
#                cov_desc = encoder.encodeCoverageDescription(coverage)
            
            cov_desc_el = encoder.encodeCoverageDescription(coverage)
            
            resp = self._get_multipart_response(
                dst_filename, mime_type, DOMElementToXML(cov_desc_el)
            )
        else:
            raise InvalidRequestException(
                "Unknown media type '%s'" % media_type,
                "InvalidParameterValue",
                "mediatype"
            )
        
        #clean up
        self._remove_temp_file(dst_filename)
        
        return resp

class WCS20GetRectifiedCoverageHandler(WCSCommonHandler):
    PARAM_SCHEMA = {
        "service": {"xml_location": "/service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"},
        "coverageid": {"xml_location": "/{http://www.opengis.net/wcs/2.0}CoverageId", "xml_type": "string", "kvp_key": "coverageid", "kvp_type": "string"},
        "trims": {"xml_location": "/{http://www.opengis.net/wcs/2.0}DimensionTrim", "xml_type": "element[]"},
        "slices": {"xml_location": "/{http://www.opengis.net/wcs/2.0}DimensionSlice", "xml_type": "element[]"},
        "format": {"xml_location": "/{http://www.opengis.net/wcs/2.0}Format", "xml_type": "string", "kvp_key": "format", "kvp_type": "string"},
        "mediatype": {"xml_location": "/{http://www.opengis.net/wcs/2.0}Mediatype", "xml_type": "string", "kvp_key": "mediatype", "kvp_type": "string"}
    }
    
    def createCoverages(self):
        coverage_id = self.req.getParamValue("coverageid")
        
        if coverage_id is None:
            raise InvalidRequestException("Missing 'coverageid' parameter", "MissingParameterValue", "coverageid")
        else:
            coverage = System.getRegistry().getFromFactory(
                "resources.coverages.wrappers.EOCoverageFactory",
                {"obj_id": coverage_id}
            )
            
            if coverage is not None:
                decoder = WCS20SubsetDecoder(self.req, "imageCRS")
                filter_exprs = decoder.getFilterExpressions()

                try:
                    if coverage.matches(filter_exprs):
                        self.coverages.append(coverage)
                    else:
                        # TODO: check for right exception report
                        raise InvalidRequestException(
                            "Coverage does not match subset expressions.",
                            "NoSuchCoverage",
                            coverage_id
                        )
                except InvalidExpressionError, e:
                    raise InvalidRequestException(
                        "Error when evaluating subset expression: %s" % str(e),
                        "InvalidParameterValue",
                        "subset"
                    )
            else:
                raise InvalidRequestException(
                    "No coverage with id '%s' found" % coverage_id, "NoSuchCoverage", coverage_id
                )

    def _setParameter(self, key, value):
        if key.lower() == "format":
            super(WCS20GetRectifiedCoverageHandler, self)._setParameter("format", "custom")
        else:
            super(WCS20GetRectifiedCoverageHandler, self)._setParameter(key, value)

    def configureMapObj(self):
        super(WCS20GetRectifiedCoverageHandler, self).configureMapObj()
        
        
        format_param = self.req.getParamValue("format")
        if not format_param:
            raise InvalidRequestException(
                "Missing mandatory 'format' parameter",
                "MissingParameterValue",
                "format"
            )
        
        output_format = get_output_format(
            format_param,
            self.coverages[0]
        )
        
        self.map.appendOutputFormat(output_format)
        self.map.setOutputFormat(output_format)
        
        logging.debug("WCS20GetCoverageHandler.configureMapObj: %s" % self.map.imagetype)

    def getMapServerLayer(self, coverage):
        layer = super(WCS20GetRectifiedCoverageHandler, self).getMapServerLayer(coverage)
        
        connector = System.getRegistry().findAndBind(
            intf_id = "services.mapserver.MapServerDataConnectorInterface",
            params = {
                "services.mapserver.data_structure_type": \
                    coverage.getDataStructureType()
            }
        )
        layer = connector.configure(layer, coverage)

        # this was under the "eo.rect_mosaic"-path. minor accurracy issues
        # have evolved since making it accissible to all paths
        rangetype = coverage.getRangeType()

        #layer.setMetaData("wcs_nativeformat", coverage.getDataFormat().getDriverName())
        layer.setMetaData("wcs_nativeformat", "GTiff") # TODO: make this configurable like in the line above
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

    def postprocess(self, resp):
        coverage_id = self.req.getParamValue("coverageid")
        
        if self.coverages[0].getType() == "eo.rect_stitched_mosaic":
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
                
                coverage = self.coverages[0]
                
                decoder = WCS20SubsetDecoder(self.req, "imageCRS")
                    
                poly = decoder.getBoundingPolygon(
                     coverage.getFootprint(),
                     coverage.getSRID(),
                     coverage.getSize()[0],
                     coverage.getSize()[1],
                     coverage.getExtent()
                )
                
                if coverage.getType() == "eo.rect_dataset":
                    resp_xml = encoder.encodeRectifiedDataset(
                        coverage,
                        req=self.req,
                        nodes=rectified_grid_coverage.childNodes,
                        poly=poly
                    )
                elif coverage.getType() == "eo.rect_stitched_mosaic":
                    resp_xml = encoder.encodeRectifiedStitchedMosaic(
                        coverage,
                        req=self.req,
                        nodes=rectified_grid_coverage.childNodes,
                        poly=poly
                    )
                    
                resp = resp.getProcessedResponse(DOMElementToXML(resp_xml))
                dom.unlink()

        return resp

class WCS20GetCoverageConfigReader(object):
    REGISTRY_CONF = {
        "name": "WCS 2.0 GetCoverage Configuration Reader",
        "impl_id": "services.ows.wcs20.WCS20GetCoverageConfigReader"
    }
    
    def validate(self, config):
        pass
    
    def useNest(self):
        conf_value = System.getConfig().getConfigValue("services.ows.wcs20", "use_nest")
        
        return conf_value is not None and conf_value.lower() == "true"

WCS20GetCoverageConfigReaderImplementation = \
ConfigReaderInterface.implement(WCS20GetCoverageConfigReader)
