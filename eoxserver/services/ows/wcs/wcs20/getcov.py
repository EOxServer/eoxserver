#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Martin Paces <martin.paces@eox.at>
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


"""
This module contains handlers for WCS 2.0 / EO-WCS GetCoverage requests.
"""

import logging
from xml.dom import minidom
from datetime import datetime

import mapscript
from django.contrib.gis.geos import GEOSGeometry

from eoxserver.core.system import System
from eoxserver.core.exceptions import InternalError, InvalidExpressionError
from eoxserver.core.util.xmltools import DOMElementToXML
from eoxserver.core.util.multiparttools import mpPack
from eoxserver.core.util.bbox import BBox 
from eoxserver.core.util.filetools import TmpFile
from eoxserver.contrib import gdal 
from eoxserver.processing.gdal import reftools as rt 
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
from eoxserver.services.ows.wcs.wcs20.mask import WCS20MaskDecoder
from eoxserver.resources.coverages.formats import getFormatRegistry
from eoxserver.resources.coverages import crss


logger = logging.getLogger(__name__)

# stripping dot from file extension
_stripDot = lambda ext : ext[1:] if ext.startswith('.') else ext 

MASK_LAYER_NAME = "masklayername"#"__mask_layer__"

# register all GDAL drivers 


class WCS20GetCoverageHandler(WCSCommonHandler):
    """
    This handler takes care of all WCS 2.0 / EO-WCS GetCoverage requests. It
    inherits from :class:`~.WCSCommonHandler`.
    
    The main processing step is to determine the coverage concerned by the
    request and delegate the request handling to the handlers for Referenceable
    Datasets or other (rectified) coverages according to the coverage type.
    
    An :exc:`~.InvalidRequestException` is raised if the coverage ID parameter
    is missing in the request or the coverage ID is unknown.
    """
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
                
class WCS20CorrigendumGetCoverageHandler(WCS20GetCoverageHandler):
    """
    This handler takes care of all WCS 2.0.1 / EO-WCS GetCoverage requests. It
    inherits from :class:`~.WCS20GetCoverageHandler`.
    """
    
    REGISTRY_CONF = {
        "name": "WCS 2.0 GetCoverage Handler",
        "impl_id": "services.ows.wcs20.WCS20CorrigendumGetCoverageHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "2.0.1",
            "services.interfaces.operation": "getcoverage"
        }
    }

class WCS20GetReferenceableCoverageHandler(BaseRequestHandler):
    """
    This class handles WCS 2.0 / EO-WCS GetCoverage requests for Referenceable
    datasets. It inherits from :class:`~.BaseRequestHandler`. It is instantiated
    by :class:`WCS20GetCoverageHandler`.
    """
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
        """
        This method handles the GetCoverage request for Referenceable Datasets.
        It takes two parameters: the :class:`~.OWSRequest` object ``req`` and
        the :class:`~.ReferenceableDatasetWrapper` object ``coverage``.
        
        The method makes ample use of the functions in
        :mod:`eoxserver.processing.gdal.reftools` in order to transform
        the pixel coordinates to the underlying CRS.
        
        It starts by decoding the (optional) subset parameters using the
        methods of :class:`~.WCS20SubsetDecoder`. There are two possible
        meanings of the subset coordinates: absent a CRS definition, they are
        assumed to be expressed in pixel coordinates (imageCRS); otherwise they
        are treated as coordinates in the respective CRS.
        
        In the latter case, the subset is transformed to pixel coordinates
        using :func:`eoxserver.processing.gdal.reftools.rect_from_subset`.
        This results in a pixel subset that contains the whole area of the
        subset taking into account the GCP information. See the function
        docs for details.
        
        The next step is to determine the format of the response data. This
        is done based on the format parameter and the format configurations
        (see also :mod:`eoxserver.resources.coverages.formats`). The format
        MIME type has to be known to the server and it has to be supported by
        GDAL, otherwise an :exc:`~.InternalError` is raised.
        
        For technical reasons, though, the initial dataset is not created with
        the output format driver, but as a virtual dataset in the memory. Only
        later the dataset is copied using the :meth:`CreateCopy` method of
        the GDAL driver.
        
        The method tags several metadata items on the output, most importantly
        the GCPs. Note that all GCPs of the coverage are tagged on the
        output dataset even if only a subset has been requested. This because
        all of them may have influence on the computation of the coordinate
        transformation in the subset even if they lie outside.
        
        Finally, the response is composed. According to the mediatype parameter,
        either a multipart message containing the coverage description of the
        output coverage and the output coverage data or just the data is
        returned.
        """
        # set request schema 
        req.setSchema(self.PARAM_SCHEMA)

        # get reftool transformer's parameters 
        rt_prm = rt.suggest_transformer(coverage.getData().getGDALDatasetIdentifier()) 

        #=============================================
        # coverage subsetting

        # get image bounds as a bounding box 
        bb_img = BBox( *coverage.getSize() ) 

        #decode subset 

        decoder = WCS20SubsetDecoder(req, "imageCRS")
        
        try:
            subset = decoder.getSubset( bb_img.sx, bb_img.sy, coverage.getFootprint())
        except InvalidSubsettingException, e:
            raise InvalidRequestException( str(e), "InvalidSubsetting", "subset")
        except InvalidAxisLabelException, e:
            raise InvalidRequestException( str(e), "InvalidAxisLabel", "subset" )

        # convert subset to bounding box in image coordinates (bbox)

        if subset is None: # whole coverage 

            bbox = bb_img 

        elif subset.crs_id == "imageCRS" : # pixel subset 

            bbox = BBox( None, None, subset.minx, subset.miny,
                         subset.maxx+1, subset.maxy+1 ) 

        else : # otherwise let GDAL handle the projection

            bbox = rt.rect_from_subset(
                coverage.getData().getGDALDatasetIdentifier(), subset.crs_id,
                subset.minx, subset.miny, subset.maxx, subset.maxy, **rt_prm )  

        # calculate effective offsets and size of the overlapped area

        bb_src = bbox & bb_img      # trim bounding box to match the coverage
        bb_dst = bb_src - bbox.off  # adjust the output offset 

        # check the extent of the effective area 

        if 0 == bb_src.ext : 
            raise InvalidRequestException( "Subset outside coverage extent.",
                "InvalidParameterValue", "subset" )

        #======================================================================

        # get the range type 
        rtype = coverage.getRangeType()

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
        # creating the output image 

        # check anf get the output GDAL driver 
        backend_name , _ , driver_name = format.driver.partition("/") ; 

        if backend_name != "GDAL" : 
            raise InternalError( "Unsupported format backend \"%s\"!" % backend_name ) 
        
        drv_dst = gdal.GetDriverByName( driver_name )
        
        if drv_dst is None:
            raise InternalError( "Invalid GDAL Driver identifier '%s'" % driver_name )
        
        # get the GDAL virtual driver 
        drv_vrt = gdal.GetDriverByName( "VRT" )

        #input DS - NOTE: GDAL is not capable to handle unicode filenames!
        src_path = str( coverage.getData().getGDALDatasetIdentifier() ) 
        ds_src = gdal.OpenShared( src_path )

        # create a new GDAL in-memory virtual DS 
        ds_vrt = drv_vrt.Create( "", bbox.sx, bbox.sy, len(rtype.bands),
                                rtype.data_type )

        # set mapping from the source DS 

        # simple source XML template 
        tmp = []                                                                      
        tmp.append( "<SimpleSource>" )                                                
        tmp.append( "<SourceFilename>%s</SourceFilename>" % src_path )               
        tmp.append( "<SourceBand>%d</SourceBand>" )                         
        tmp.append( "<SrcRect xSize=\"%d\" ySize=\"%d\" xOff=\"%d\" yOff=\"%d\"/>" % bb_src.as_tuple() )
        tmp.append( "<DstRect xSize=\"%d\" ySize=\"%d\" xOff=\"%d\" yOff=\"%d\"/>" % bb_dst.as_tuple() )
        tmp.append( "</SimpleSource>" )                                               
        tmp = "".join(tmp)  
                                                                                
        # raster data mapping  
        for i in xrange(1,len(rtype.bands)+1) :                                                   
            ds_vrt.GetRasterBand(i).SetMetadataItem( "source_0", tmp%i,
                                                     "new_vrt_sources" ) 

        # copy metadata 
        for key, value in ds_src.GetMetadata().items() :
            ds_vrt.SetMetadataItem(key, value)

        # copy tie-points 

        # tiepoint offset - higher order function                                         
        def _tpOff( ( ox , oy ) ) :                                                         
            def function( p ) :                                                              
                return gdal.GCP( p.GCPX, p.GCPY, p.GCPZ, p.GCPPixel - ox, 
                                 p.GCPLine - oy, p.Info, p.Id )                                                  
            return function                                                                  

        # instantiate tiepoint offset function for current offset value 
        tpOff = _tpOff( bbox.off )                                               

        # copy tiepoints                                                                
        ds_vrt.SetGCPs( [ tpOff(p) for p in ds_src.GetGCPs() ],
                        ds_src.GetGCPProjection() )

        #======================================================================
        # create final DS 

        # get the requested media type 
        media_type = req.getParamValue("mediatype")

        # NOTE: MP: Direct use of MIME params as GDAL param is quite smelly,
        # thus I made decision to keep it away. (",".join(format_options))
                
        with TmpFile( format.defaultExt , "tmp_" ) as dst_path :

            #NOTE: the format option (last param.) must be None or a sequence
            drv_dst.CreateCopy( dst_path , ds_vrt , True , () ) 

            # get footprint if needed 

            if ( media_type is not None ) and ( subset is not None ) : 
                footprint = GEOSGeometry(rt.get_footprint_wkt(dst_path,**rt_prm))
            else : 
                footprint = None 

            # load data 
            f = open(dst_path) ; data = f.read() ; f.close() 

        #======================================================================
        # prepare response

        # set the response filename 
        time_stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename   = "%s_%s%s" % ( coverage.getCoverageId(), time_stamp, format.defaultExt ) 

        if media_type is None:

            resp = self._get_default_response( data, format.mimeType, filename)

        elif media_type in ( "multipart/related" , "multipart/mixed" ) :

            encoder = WCS20EOAPEncoder()

            reference = "coverage/%s" % filename
            mpsubtype = media_type.partition("/")[2]
            
            if subset is None : 
                _subset = None
            else : 

                if subset.crs_id == "imageCRS":
                    _subset = ( 4326, bbox.size, footprint.extent, footprint ) 
                else:
                    _subset = ( subset.crs_id, bbox.size,
                        (subset.minx, subset.miny, subset.maxx, subset.maxy), footprint ) 

            cov_desc_el = encoder.encodeReferenceableDataset(coverage,
                            "cid:%s"%reference,mime_type,True,_subset)
            
            # NOTE: the multipart subtype will be the same as the one requested 
            resp = self._get_multipart_response( data, format.mimeType, filename, reference,
                    DOMElementToXML(cov_desc_el), boundary = "wcs" , subtype = mpsubtype )

        else:
            raise InvalidRequestException(
                "Unknown media type '%s'" % media_type,
                "InvalidParameterValue",
                "mediatype"
            )
        
        return resp
    
    def _get_default_response(self, data, mime_type, filename):

        # create response 
        resp = Response(
            content_type = mime_type,
            content = data, 
            headers = {'Content-Disposition': "inline; filename=\"%s\"" % filename},
            status = 200
        )
        
        return resp
    
    def _get_multipart_response(self, data, mime_type, filename, 
            reference, cov_desc, boundary = "wcs", subtype = "related" ):

        # prepare multipart package 
        parts = [ # u
            ( [( "Content-Type" , "text/xml" )] , cov_desc ) , 
            ( [( "Content-Type" , str(mime_type) ) , 
               ( "Content-Description" , "coverage data" ),
               ( "Content-Transfer-Encoding" , "binary" ),
               ( "Content-Id" , str(reference) ),
               ( "Content-Disposition" , "inline; filename=\"%s\"" % str(filename) ) ,
              ] , data ) ] 

        # create response 
        resp = Response(
            content = mpPack( parts , boundary ) ,
            content_type = "multipart/%s; boundary=%s"%(subtype,boundary),
            headers = {},
            status = 200
        )
        
        return resp


class WCS20GetRectifiedCoverageHandler(WCSCommonHandler):
    """
    This is the handler for GetCoverage requests for Rectified Datasets
    and Rectified Stitched Mosaics. It inherits from
    :class:`~.WCSCommonHandler`.
    
    It follows the workflow of the base class and modifies the
    :meth:`createCoverages`, :meth:`configureMapObj`, :meth:`getMapServerLayer`
    and :meth:`postprocess` methods.
    """
    PARAM_SCHEMA = {
        "service": {"xml_location": "/service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"},
        "coverageid": {"xml_location": "/{http://www.opengis.net/wcs/2.0}CoverageId", "xml_type": "string", "kvp_key": "coverageid", "kvp_type": "string"},
        "trims": {"xml_location": "/{http://www.opengis.net/wcs/2.0}DimensionTrim", "xml_type": "element[]"},
        "slices": {"xml_location": "/{http://www.opengis.net/wcs/2.0}DimensionSlice", "xml_type": "element[]"},
        "format": {"xml_location": "/{http://www.opengis.net/wcs/2.0}format", "xml_type": "string", "kvp_key": "format", "kvp_type": "string"},
        "mediatype": {"xml_location": "/{http://www.opengis.net/wcs/2.0}mediaType", "xml_type": "string", "kvp_key": "mediatype", "kvp_type": "string"},
        "polygonmasks": {"xml_location": "/{http://www.opengis.net/wcs/2.0}Extension/{http://www.opengis.net/wcs/mask/1.0}polygonMask", "xml_type": "string[]", "kvp_key": "polygon", "kvp_type": "string"},
    }
    
    def addLayers(self):
        masks = WCS20MaskDecoder(self.req)
        
        self.has_mask = masks.has_mask
        
        if self.has_mask:
            # create a mask layer
            mask_layer = mapscript.layerObj()
            mask_layer.name = MASK_LAYER_NAME
            mask_layer.status = mapscript.MS_DEFAULT
            mask_layer.type = mapscript.MS_LAYER_POLYGON
            mask_layer.setProjection("init=epsg:4326") # TODO: make this dependant on the actually given crs 
            
            # add features for each mask polygon
            for polygon in masks.polygons:
                shape = mapscript.shapeObj(mapscript.MS_SHAPE_POLYGON)
                line = mapscript.lineObj()
                for x, y in polygon:
                    line.add(mapscript.pointObj(x, y))
                shape.add(line)
                mask_layer.addFeature(shape)
            
            cls = mapscript.classObj(mask_layer)
            style = mapscript.styleObj(cls)
            style.color.setRGB(0, 0, 0) # requires a color
            
            self.map.insertLayer(mask_layer)
            
            self.has_mask = True
        
        super(WCS20GetRectifiedCoverageHandler, self).addLayers()
    
    
    def createCoverages(self):
        """
        This method retrieves the coverage object denoted by the request and
        stores it in the ``coverages`` property of the handler. The method
        also checks if the subset expressions (if present) match with the
        coverage extent.
        
        An :exc:`~.InvalidRequestException` is raised if the coverageid
        parameter is missing or the coverage ID is unknown or the subset
        expressions do not match with the coverage extent.
        """
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
                try:
                    filter_exprs = decoder.getFilterExpressions()
                except InvalidSubsettingException, e:
                    raise InvalidRequestException(str(e), "InvalidParameterValue", "subset")

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
        """
        This method extends the base method
        (:meth:`~.WCSCommonHandler.configureMapObj`). The format configurations
        are added to the MapScript :class:`mapObj`.
        """
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


    def getMapServerLayer(self, coverage):
        """
        This method returns a MapServer :class:`layerObj` for the corresponding
        coverage. It extends the base class method
        :class:`~.WCSCommonHandler.getMapServerLayer`. The method configures
        the input data for the layer using the appropriate connector for the
        coverage (see :mod:`eoxserver.services.connectors`). Furthermore,
        it sets WCS 2.0 specific metadata on the layer.
        """
        
        layer = super(WCS20GetRectifiedCoverageHandler, self).getMapServerLayer(coverage)

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
        
        if self.has_mask:
            layer.mask = MASK_LAYER_NAME
        
        return layer

    def postprocess(self, resp):
        """
        This method overrides the no-op method of the base class. It adds
        EO-WCS specific metadata to the multipart messages that include an
        XML coverage description part. It expects a :class:`~.MapServerResponse`
        object ``resp`` as input and returns it either unchanged or a
        new :class:`~.Response` object containing the modified multipart
        message.
        
        MapServer returns a WCS 2.0 coverage description, but this does not
        include EO-WCS specific parts like the coverage subtype (Rectified
        Dataset or Rectified Stitched Mosaic) and EO-WCS metadata. Therefore
        the description is replaced with the corresponding EO-WCS complient
        XML.
        """
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

                dom.unlink()

                #TODO: MP: Set the subtype to 'related' for 'multipart/related' responses!
                resp = resp.getProcessedResponse( DOMElementToXML(resp_xml) , subtype = "mixed" )

            # else : pass - using the unchanged original response TODO: Is this correct? MP
 
        else: # coverage only

            coverage = self.coverages[0]
            mime_type = resp.getContentType()
            
            if not mime_type.lower().startswith("multipart/"):
                filename = "%s_%s%s" % (
                    coverage.getCoverageId(),
                    datetime.now().strftime("%Y%m%d%H%M%S"),
                    getFormatRegistry().getFormatByMIME( mime_type ).defaultExt
                )
                
                resp.headers.update({'Content-Disposition': "inline; filename=\"%s\"" % filename})

        return resp
