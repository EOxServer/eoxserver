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

class WCS20GetCapabilitiesMapGenerator(object):
    def _configureMapObj(self, ms_req):
        #---------------------------------------------------------------
        # from MapServerOperationHandler
        #---------------------------------------------------------------
        ms_req.map = mapscript.mapObj(os.path.join(settings.PROJECT_DIR, "conf", "template.map")) # TODO: Store information in database??? (title, abstract, etc.)
        
        ms_req.map.setMetaData("ows_onlineresource", OWSCommonConfigReader().getHTTPServiceURL() + "?")
        ms_req.map.setMetaData("wcs_label", "EOxServer WCS") # TODO: to WCS
        
        ms_req.map.setProjection("+init=epsg:4326") #TODO: Set correct projection!
        #===============================================================
    
    def _addLayers(self, ms_req, eo_objects):
        #---------------------------------------------------------------
        # from MapServerOperationHandler with local changes
        #---------------------------------------------------------------
        for coverage in eo_objects:
            ms_req.map.insertLayer(self._getMapServerLayer(coverage))
        #===============================================================
    
    def _getMapServerLayer(self, coverage):
        #---------------------------------------------------------------
        # from MapServerOperationHandler
        #---------------------------------------------------------------
        layer = mapscript.layerObj()
        
        layer.name = coverage.getCoverageId()
        layer.setMetaData("ows_title", coverage.getCoverageId())
        layer.status = mapscript.MS_ON
        #layer.debug = 5

        # TODO: getSRID is defined for rectified coverages only
        layer.setProjection("+init=epsg:%d" % int(coverage.getSRID()))

        for key, value in coverage.getLayerMetadata():
            layer.setMetaData(key, value)
        
        #---------------------------------------------------------------
        # from WCSCommonHandler
        #---------------------------------------------------------------
        
        layer.type = mapscript.MS_LAYER_RASTER
        layer.dump = mapscript.MS_TRUE
        layer.setConnectionType(mapscript.MS_RASTER, '')
        layer.setMetaData("ows_srs", "EPSG:%d" % int(coverage.getSRID())) # TODO: What about additional SRSs?; TODO: getSRID is defined for rectified coverages only
        
        layer.setMetaData("wcs_label", coverage.getCoverageId())
        
        layer.setExtent(*coverage.getExtent()) # TODO: getExtent is defined for rectified coverages only
        
        #---------------------------------------------------------------
        # from WCS20GetCapabilitiesOperationHandler
        #---------------------------------------------------------------
        datasets = coverage.getDatasets()
        
        if len(datasets) == 0:
            raise InternalError("Misconfigured coverage '%s' has no file data." % coverage.getCoverageId())
        else:
            layer.data = os.path.abspath(datasets[0].getFilename())
        #===============================================================
        
        return layer
    
    def configure(self, ms_req, eo_objects):
        self._configureMapObj(ms_req)
        self._addLayers(ms_req, eo_objects)

class WCS20GetCoverageFileMapGenerator(object):
    def _configureMapObj(self, ms_req):
        #---------------------------------------------------------------
        # from MapServerOperationHandler
        #---------------------------------------------------------------
        ms_req.map = mapscript.mapObj(os.path.join(settings.PROJECT_DIR, "conf", "template.map")) # TODO: Store information in database??? (title, abstract, etc.)
        
        ms_req.map.setMetaData("ows_onlineresource", OWSCommonConfigReader().getHTTPServiceURL() + "?")
        ms_req.map.setMetaData("wcs_label", "EOxServer WCS") # TODO: to WCS
        
        ms_req.map.setProjection("+init=epsg:4326") #TODO: Set correct projection!
        
        #===============================================================
    
    def _setOutputFormat(self, ms_req, eo_objects):
        
        #---------------------------------------------------------------
        # from WCS20GetCoverageOperationHandler with local changes
        #---------------------------------------------------------------

        output_format = mapscript.outputFormatObj("GDAL/GTiff", "GTiff_")
        output_format.mimetype = "image/tiff"
        output_format.extension = "tif"
        
        coverage = eo_objects[0]
        rangetype = coverage.getRangeType()
        
        output_format.imagemode = gdalconst_to_imagemode(
            ms_req.coverages[0].getRangeType().data_type
        )
        
        ms_req.map.appendOutputFormat(output_format)
        ms_req.map.setOutputFormat(output_format)
    
    def _addLayers(self, ms_req, eo_objects):
        #---------------------------------------------------------------
        # from WCS20GetCoverageOperationHandler with local changes
        #---------------------------------------------------------------
        
        decoder = WCS20SubsetDecoder(ms_req, "imageCRS")
        filter_exprs = decoder.getFilterExpressions()

        for coverage in eo_objects:
            ms_req.map.insertLayer(self._getMapServerLayer(coverage, filter_exprs=filter_exprs))
    
    def _getMapServerLayer(self, coverage, **kwargs):
        #---------------------------------------------------------------
        # from MapServerOperationHandler
        #---------------------------------------------------------------
        layer = mapscript.layerObj()
        
        layer.name = coverage.getCoverageId()
        layer.setMetaData("ows_title", coverage.getCoverageId())
        layer.status = mapscript.MS_ON
        #layer.debug = 5

        # TODO: getSRID is defined for rectified coverages only
        layer.setProjection("+init=epsg:%d" % int(coverage.getSRID()))

        for key, value in coverage.getLayerMetadata():
            layer.setMetaData(key, value)
        
        #---------------------------------------------------------------
        # from WCSCommonHandler
        #---------------------------------------------------------------
        
        layer.type = mapscript.MS_LAYER_RASTER
        layer.dump = mapscript.MS_TRUE
        layer.setConnectionType(mapscript.MS_RASTER, '')
        layer.setMetaData("ows_srs", "EPSG:%d" % int(coverage.getSRID())) # TODO: What about additional SRSs?; TODO: getSRID is defined for rectified coverages only
        
        layer.setMetaData("wcs_label", coverage.getCoverageId())
        
        layer.setExtent(*coverage.getExtent()) # TODO: getExtent is defined for rectified coverages only
        
        #---------------------------------------------------------------
        # from WCS20GetCoverageOperationHandler (for file coverages only)
        #---------------------------------------------------------------
        
        datasets = coverage.getDatasets(
            filter_exprs = kwargs.get("filter_exprs", [])
        )
        
        if len(datasets) == 0:
            raise InvalidRequestException("Image extent does not intersect with desired region.", "ExtentError", "extent") # TODO: check if this is the right exception report
        elif len(datasets) == 1:
            layer.data = os.path.abspath(datasets[0].getFilename())
            
        else:
            raise InternalError("A single file or EO dataset should never return more than one dataset.")
        
        #---------------------------------------------------------------
        # from WCS20GetCoverageOperationHandler (common)
        #---------------------------------------------------------------
        
        # this was under the "eo.rect_mosaic"-path. minor accurracy issues
        # have evolved since making it accissible to all paths
             
        extent = coverage.getExtent()
        srid = coverage.getSRID()
        size = coverage.getSize()
        rangetype = coverage.getRangeType()
        resolution = ((extent[2]-extent[0]) / float(size[0]),
                      (extent[1]-extent[3]) / float(size[1]))
        
        layer.setMetaData("wcs_extent", "%.10f %.10f %.10f %.10f" % extent)
        layer.setMetaData("wcs_resolution", "%f %f" % resolution)
        layer.setMetaData("wcs_size", "%d %d" % size)
        layer.setMetaData("wcs_nativeformat", "GTiff")
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

    
    def configure(self, ms_req, eo_objects):
        self._configureMapObj(ms_req)
        self._setOutputFormat(ms_req, eo_objects)
        self._addLayers(ms_req, eo_objects)

class WCS20GetCoverageTileIndexMapGenerator(object):
    def _configureMapObj(self, ms_req):
        #---------------------------------------------------------------
        # from MapServerOperationHandler
        #---------------------------------------------------------------
        ms_req.map = mapscript.mapObj(os.path.join(settings.PROJECT_DIR, "conf", "template.map")) # TODO: Store information in database??? (title, abstract, etc.)
        
        ms_req.map.setMetaData("ows_onlineresource", OWSCommonConfigReader().getHTTPServiceURL() + "?")
        ms_req.map.setMetaData("wcs_label", "EOxServer WCS") # TODO: to WCS
        
        ms_req.map.setProjection("+init=epsg:4326") #TODO: Set correct projection!
        
        #===============================================================
    
    def _setOutputFormat(self, ms_req, eo_objects):
        
        #---------------------------------------------------------------
        # from WCS20GetCoverageOperationHandler with local changes
        #---------------------------------------------------------------

        output_format = mapscript.outputFormatObj("GDAL/GTiff", "GTiff_")
        output_format.mimetype = "image/tiff"
        output_format.extension = "tif"
        
        coverage = eo_objects[0]
        rangetype = coverage.getRangeType()
        
        output_format.imagemode = gdalconst_to_imagemode(
            ms_req.coverages[0].getRangeType().data_type
        )
        
        ms_req.map.appendOutputFormat(output_format)
        ms_req.map.setOutputFormat(output_format)
    
    def _addLayers(self, ms_req, eo_objects):
        #---------------------------------------------------------------
        # from WCS20GetCoverageOperationHandler with local changes
        #---------------------------------------------------------------
        
        decoder = WCS20SubsetDecoder(ms_req, "imageCRS")
        filter_exprs = decoder.getFilterExpressions()

        for coverage in eo_objects:
            ms_req.map.insertLayer(self._getMapServerLayer(coverage, filter_exprs=filter_exprs))
    
    def _getMapServerLayer(self, coverage, **kwargs):
        #---------------------------------------------------------------
        # from MapServerOperationHandler
        #---------------------------------------------------------------
        layer = mapscript.layerObj()
        
        layer.name = coverage.getCoverageId()
        layer.setMetaData("ows_title", coverage.getCoverageId())
        layer.status = mapscript.MS_ON
        #layer.debug = 5

        # TODO: getSRID is defined for rectified coverages only
        layer.setProjection("+init=epsg:%d" % int(coverage.getSRID()))

        for key, value in coverage.getLayerMetadata():
            layer.setMetaData(key, value)
        
        #---------------------------------------------------------------
        # from WCSCommonHandler
        #---------------------------------------------------------------
        
        layer.type = mapscript.MS_LAYER_RASTER
        layer.dump = mapscript.MS_TRUE
        layer.setConnectionType(mapscript.MS_RASTER, '')
        layer.setMetaData("ows_srs", "EPSG:%d" % int(coverage.getSRID())) # TODO: What about additional SRSs?; TODO: getSRID is defined for rectified coverages only
        
        layer.setMetaData("wcs_label", coverage.getCoverageId())
        
        layer.setExtent(*coverage.getExtent()) # TODO: getExtent is defined for rectified coverages only
        
        #---------------------------------------------------------------
        # from WCS20GetCoverageOperationHandler (for tiled coverages only)
        #---------------------------------------------------------------
        
        layer.tileindex = os.path.abspath(coverage.getShapeFilePath())
        layer.tileitem = "location"
        
        #---------------------------------------------------------------
        # from WCS20GetCoverageOperationHandler (common)
        #---------------------------------------------------------------
        
        # this was under the "eo.rect_mosaic"-path. minor accurracy issues
        # have evolved since making it accissible to all paths
             
        extent = coverage.getExtent()
        srid = coverage.getSRID()
        size = coverage.getSize()
        rangetype = coverage.getRangeType()
        resolution = ((extent[2]-extent[0]) / float(size[0]),
                      (extent[1]-extent[3]) / float(size[1]))
        
        layer.setMetaData("wcs_extent", "%.10f %.10f %.10f %.10f" % extent)
        layer.setMetaData("wcs_resolution", "%f %f" % resolution)
        layer.setMetaData("wcs_size", "%d %d" % size)
        layer.setMetaData("wcs_nativeformat", "GTiff")
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

    
    def configure(self, ms_req, eo_objects):
        self._configureMapObj(ms_req)
        self._setOutputFormat(ms_req, eo_objects)
        self._addLayers(ms_req, eo_objects)

class WCS20GetCoverageRasdamanMapGenerator(object):
    pass

class WMSGetCapabilitiesMapGenerator(object):
    pass

class WMSGetMapFileMapGenerator(object):
    pass

class WMSGetMapTileIndexMapGenerator(object):
    pass

class WMSGetMapRasdamanMapGenerator(object):
    pass

