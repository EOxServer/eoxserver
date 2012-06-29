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
from tempfile import mkstemp
from xml.dom import minidom
from datetime import datetime

import mapscript
from osgeo import gdal
gdal.UseExceptions()
from django.contrib.gis.geos import GEOSGeometry

import logging

from eoxserver.core.system import System
from eoxserver.core.exceptions import InternalError, InvalidExpressionError
from eoxserver.core.util.xmltools import DOMElementToXML
from eoxserver.processing.gdal.reftools import (
    rect_from_subset, get_footprint_wkt
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
    WCSCommonHandler, getMSOutputFormat, 
    getWCSNativeFormat, getMSWCSFormatMD,
    getMSWCSNativeFormat, getMSWCSSRSMD,
    parse_format_param
)
from eoxserver.services.ows.wcs.encoders import WCS20EOAPEncoder
from eoxserver.services.ows.wcs.wcs20.subset import WCS20SubsetDecoder

from eoxserver.resources.coverages.formats import getFormatRegistry
from eoxserver.resources.coverages import crss  

_stripDot = lambda s : s[1:] if s[0] == '.' else s 

# register all GDAL drivers 
gdal.AllRegister()

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
            handler = WCS20GetReferenceableCoverageHandler()
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

class WCS20GetReferenceableCoverageHandler(BaseRequestHandler):
    PARAM_SCHEMA = {
        "service": {"xml_location": "/service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"},
        "coverageid": {"xml_location": "/{http://www.opengis.net/wcs/2.0}CoverageId", "xml_type": "string", "kvp_key": "coverageid", "kvp_type": "string"},
        "trims": {"xml_location": "/{http://www.opengis.net/wcs/2.0}DimensionTrim", "xml_type": "element[]"},
        "slices": {"xml_location": "/{http://www.opengis.net/wcs/2.0}DimensionSlice", "xml_type": "element[]"},
        "format": {"xml_location": "/{http://www.opengis.net/wcs/2.0}format", "xml_type": "string", "kvp_key": "format", "kvp_type": "string"},
        "mediatype": {"xml_location": "/{http://www.opengis.net/wcs/2.0}mediaType", "xml_type": "string", "kvp_key": "mediatype", "kvp_type": "string"}
    }
    
    def handle(self, req, coverage):

        # set request schema 
        req.setSchema(self.PARAM_SCHEMA)

        #=============================================
        # get subsetting

        decoder = WCS20SubsetDecoder(req, "imageCRS")

        cov_x_size, cov_y_size = coverage.getSize()
        
        try:
            subset = decoder.getSubset(cov_x_size, cov_y_size, coverage.getFootprint())
        except InvalidSubsettingException, e:
            raise InvalidRequestException( str(e), "InvalidSubsetting", "subset")
        except InvalidAxisLabelException, e:
            raise InvalidRequestException( str(e), "InvalidAxisLabel", "subset" )
        
        if subset is None:

            x_off, y_off, x_size, y_size = ( 0 , 0 , cov_x_size , cov_y_size ) 

        elif subset.crs_id != "imageCRS":

            x_off, y_off, x_size, y_size = rect_from_subset(
                coverage.getData().getGDALDatasetIdentifier(), subset.crs_id, 
                subset.minx, subset.miny, subset.maxx, subset.maxy )

        else:

            x_off, y_off   = ( subset.minx , subset.miny ) 
            x_size, y_size = ( subset.maxx - subset.minx + 1 , subset.maxy - subset.miny + 1 ) 

        # calculate effective offsets and buffer size  ) 
        
        src_x_off , src_y_off = ( max(0, x_off) , max(0, y_off) ) 
        dst_x_off , dst_y_off = ( max(0,-x_off) , max(0,-y_off) ) 
        
        buffer_x_size = max(min(x_off + x_size, cov_x_size) - src_x_off, 0)
        buffer_y_size = max(min(y_off + y_size, cov_y_size) - src_y_off, 0)
        
        if buffer_x_size == 0 or buffer_y_size == 0:
            raise InvalidRequestException(
                "Subset outside coverage extent.",
                "InvalidParameterValue",
                "subset"
            )

        #======================================================================

        # get the range type 
        range_type = coverage.getRangeType()

        # get format
        format_param = req.getParamValue("format")
        
        # handling format 
        if format_param is None:

            # map the source format to the native one 
            format = getWCSNativeFormat( coverage.getData().getSourceFormat() )  

            format_options = [] 

        else :
        
            # unpack format specification  
            mime_type, format_options = parse_format_param(format_param)
        
            format = getFormatRegistry().getFormatByMIME( mime_type )

            if format is None : 
                raise InvalidRequestException(
                    "Unknown or unsupported format '%s'" % mime_type,
                    "InvalidParameterValue", "format" )


        #======================================================================
        # TODO: change GDAL.Create to GDAL.CreateCopy to be in-line  
        #       with mapscript behaviour 

        gdal.AllRegister()

        _, dst_filename = mkstemp(
            prefix = "tmp",
            suffix = format.defaultExt
        )

        backend_name , _ , driver_name = format.driver.partition("/") ; 

        if  backend_name != "GDAL" : 
            raise InternalError( "Unsupported format backend \"%s\"!" % backend_name ) 
        
        gdal_driver = gdal.GetDriverByName( driver_name )
        
        if gdal_driver is None:
            raise InternalError( "Invalid GDAL Driver identifier '%s'" % driver_name )

        dst_ds = gdal_driver.Create(
            dst_filename, x_size, y_size, len(range_type.bands),
            range_type.data_type, ",".join(format_options) )

        if dst_ds is None:
            raise InternalError("Failed to create output dataset.")
        
        src_ds = coverage.getData().open()
        
        if src_ds is None:
            raise InternalError("Failed to open input dataset.")
        
        raster_buffer = src_ds.ReadRaster( src_x_off, src_y_off, buffer_x_size, buffer_y_size )
        
        dst_ds.WriteRaster( dst_x_off, dst_y_off, buffer_x_size, buffer_y_size, raster_buffer )
        
        # tag metadata onto raster buffer
        md_dict = src_ds.GetMetadata()
        
        for key, value in md_dict.items():
            dst_ds.SetMetadataItem(key, value)
        
        # save GCPs
        src_gcp_proj = src_ds.GetGCPProjection()
        src_gcps = src_ds.GetGCPs()
        
        dst_gcps = []
        for src_gcp in src_gcps:
            dst_gcps.append( gdal.GCP( src_gcp.GCPX, src_gcp.GCPY, src_gcp.GCPZ,
                src_gcp.GCPPixel+src_x_off-dst_x_off, src_gcp.GCPLine+src_y_off-dst_y_off,
                src_gcp.Info, src_gcp.Id ) )
        
        dst_ds.SetGCPs(dst_gcps, src_gcp_proj)
        
        # close datasets
        del src_ds
        del dst_ds

        #======================================================================
        # prepare response

        # set the response filename 
        time_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename   = "%s_%s%s" % ( coverage.getCoverageId(), time_stamp, format.defaultExt ) 


        # check the media type 
        media_type = req.getParamValue("mediatype")

        if media_type is None:

            resp = self._get_default_response(dst_filename, format.mimeType , filename)

        elif media_type in ( "multipart/related" , "multipart/mixed" ) :

            encoder = WCS20EOAPEncoder()

            reference = "coverage/%s" % filename
            mpsubtype = media_type.partition("/")[2]
            
            if subset is None : 
                _subset = None
            else : 
                footprint = GEOSGeometry(get_footprint_wkt(dst_filename))

                if subset.crs_id == "imageCRS":
                    _subset = ( 4326, (x_size, y_size), footprint.extent, footprint ) 
                else:
                    _subset = ( subset.crs_id, (x_size, y_size),
                        (subset.minx, subset.miny, subset.maxx, subset.maxy), footprint ) 

            cov_desc_el = encoder.encodeReferenceableDataset(coverage,reference,mime_type,True,_subset)
            
            # NOTE: the multipart subtype will be the same as the one requested 
            resp = self._get_multipart_response( dst_filename, reference , 
                        format.mimeType, DOMElementToXML(cov_desc_el), filename ,
                        subtype = mpsubtype )

        else:
            raise InvalidRequestException(
                "Unknown media type '%s'" % media_type,
                "InvalidParameterValue",
                "mediatype"
            )
            
        #clean up
        os.remove(dst_filename)
        
        return resp
    

    def _get_default_response(self, dst_filename, mime_type, filename):
        f = open(dst_filename)
        
        resp = Response(
            content_type = mime_type,
            content = f.read(),
            headers = {'Content-Disposition': "attachment; filename=\"%s\"" % filename},
            status = 200
        )
        
        f.close()
        
        return resp
    
    def _get_multipart_response(self, dst_filename, reference, mime_type, cov_desc, filename , subtype = "related" ):
        
        xml_msg = "Content-Type: text/xml\n\n%s" % cov_desc
                
        f = open(dst_filename)
        
        data = f.read()
        
        data_msg = "Content-Type: %s\n" \
                   "Content-Description: coverage data\n" \
                   "Content-Transfer-Encoding: binary\n" \
                   "Content-ID: %s\n" \
            "Content-Disposition: attachment; filename=\"%s\"\n\n%s" % (
            str(mime_type), str(reference), str(filename), data )

        content = "--wcs\n%s\n--wcs\n%s\n--wcs--" % (xml_msg, data_msg)

        resp = Response(
            content = content,
            content_type = "multipart/%s; boundary=wcs"%subtype,
            headers = {},
            status = 200
        )
        
        f.close()
        
        return resp


class WCS20GetRectifiedCoverageHandler(WCSCommonHandler):

    PARAM_SCHEMA = {
        "service": {"xml_location": "/service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"},
        "coverageid": {"xml_location": "/{http://www.opengis.net/wcs/2.0}CoverageId", "xml_type": "string", "kvp_key": "coverageid", "kvp_type": "string"},
        "trims": {"xml_location": "/{http://www.opengis.net/wcs/2.0}DimensionTrim", "xml_type": "element[]"},
        "slices": {"xml_location": "/{http://www.opengis.net/wcs/2.0}DimensionSlice", "xml_type": "element[]"},
        "format": {"xml_location": "/{http://www.opengis.net/wcs/2.0}format", "xml_type": "string", "kvp_key": "format", "kvp_type": "string"},
        "mediatype": {"xml_location": "/{http://www.opengis.net/wcs/2.0}mediaType", "xml_type": "string", "kvp_key": "mediatype", "kvp_type": "string"}
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
        
        # get format
        format_param = self.req.getParamValue("format")
        
        if format_param is None:
            # no format specification provided -> use the native one 
            format_param = getMSWCSNativeFormat( self.coverages[0].getData().getSourceFormat() ) 

        # prepare output format (the subroutine checks format and throws proper exception 
        # in case of an incorrect format parameter ) 
        output_format = getMSOutputFormat( format_param, self.coverages[0] )
        
        # set only the currently requested output format 
        self.map.appendOutputFormat(output_format)
        self.map.setOutputFormat(output_format)
        
        # set supported CRSes 
        self.map.setMetaData( 'ows_srs' , getMSWCSSRSMD() ) 
        self.map.setMetaData( 'wcs_srs' , getMSWCSSRSMD() ) 


    def getMapServerLayer(self, coverage):

        layer = super(WCS20GetRectifiedCoverageHandler, self).getMapServerLayer(coverage)

        # set layer's supported CRSes (using the per-service global data) 
        layer.setMetaData( 'ows_srs' , getMSWCSSRSMD() ) 
        layer.setMetaData( 'wcs_srs' , getMSWCSSRSMD() ) 

        connector = System.getRegistry().findAndBind(
            intf_id = "services.mapserver.MapServerDataConnectorInterface",
            params = {
                "services.mapserver.data_structure_type": \
                    coverage.getDataStructureType()
            }
        )
        layer = connector.configure(layer, coverage)

        # TODO: Change the following comment to something making sense or remove it!
        # this was under the "eo.rect_mosaic"-path. minor accurracy issues
        # have evolved since making it accissible to all paths
        rangetype = coverage.getRangeType()

        layer.setMetaData("wcs_bandcount", "%d" % len(rangetype.bands))
        layer.setMetaData("wcs_band_names", " ".join([band.name for band in rangetype.bands]) ) 
        layer.setMetaData("wcs_interval", "%f %f" % rangetype.getAllowedValues())
        layer.setMetaData("wcs_significant_figures", "%d" % rangetype.getSignificantFigures())
        
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
        
        # set the layer's native format 
        layer.setMetaData("wcs_native_format", getMSWCSNativeFormat(coverage.getData().getSourceFormat()) ) 

        # set per-layer supported formats (using the per-service global data)
        layer.setMetaData("wcs_formats", getMSWCSFormatMD() )

        layer.setMetaData( "wcs_imagemode", gdalconst_to_imagemode_string(rangetype.data_type) )
        
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

        else: # coverage only

            coverage = self.coverages[0]
            mime_type = resp.getContentType()
            
            filename = "%s_%s%s" % (
                coverage.getCoverageId(),
                datetime.now().strftime("%Y%m%d%H%M%S"),
                getFormatRegistry().getFormatByMIME( mime_type ).defaultExt
            )
            
            resp.headers.update({'Content-Disposition': "attachment; filename=\"%s\"" % filename})

        return resp
