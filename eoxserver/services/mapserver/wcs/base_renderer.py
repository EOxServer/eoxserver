#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
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


from django.db.models import Q

from eoxserver.core import Component
from eoxserver.core.config import get_eoxserver_config
from eoxserver.core.decoders import config
from eoxserver.contrib.mapserver import (
    Map, Layer, gdalconst_to_imagemode_string, outputFormatObj
)
from eoxserver.resources.coverages import crss
from eoxserver.resources.coverages.formats import getFormatRegistry


class WCSConfigReader(config.Reader):
    section = "services.ows.wcs"
    maxsize = config.Option(type=int, default=None)


class BaseRenderer(Component):
    abstract = True

    def create_map(self):
        """ Helper function to create a WCS enabled MapServer mapObj.
        """
        map_ = Map()
        map_.setMetaData("ows_enable_request", "*")
        maxsize = WCSConfigReader(get_eoxserver_config()).maxsize
        if maxsize is not None:
            map_.maxsize = maxsize
        return map_

    def data_items_for_coverage(self, coverage):
        """ Helper function to query all relevant data items for any raster data
            from the database.
        """
        return coverage.data_items.filter(
            Q(semantic__startswith="bands") | Q(semantic="tileindex")
        )

    def layer_for_coverage(self, coverage, native_format):
        """ Helper method to generate a WCS enabled MapServer layer for a given 
            coverage.
        """
        range_type = coverage.range_type
        bands = list(range_type)

        # create and configure layer
        layer = Layer(coverage.identifier)
        layer.setProjection(coverage.spatial_reference.proj)

        extent = coverage.extent
        size = coverage.size
        resolution = ((extent[2] - extent[0]) / float(size[0]),
                      (extent[1] - extent[3]) / float(size[1]))

        layer.setExtent(*extent)

        layer.setMetaData({
            "title": coverage.identifier,
            "enable_request": "*"
        }, namespace="ows")

        layer.setMetaData({
            "label": coverage.identifier,
            "extent": "%.10g %.10g %.10g %.10g" % extent,
            "resolution": "%.10g %.10g" % resolution,
            "size": "%d %d" % size,
            "bandcount": str(len(bands)),
            "band_names": " ".join([band.name for band in bands]),
            "interval": "%f %f" % bands[0].allowed_values,
            "significant_figures": "%d" % bands[0].significant_figures,
            "rangeset_name": range_type.name,
            "rangeset_label": range_type.name,
            "rangeset_axes": ",".join(band.name for band in bands),
            "imagemode": gdalconst_to_imagemode_string(bands[0].data_type),
            "formats": " ".join([f.mimeType for f in self.get_wcs_formats()])
        }, namespace="wcs")

        if native_format:
            layer.setMetaData({
                "native_format": native_format,
                "nativeformat": native_format
            }, namespace="wcs")

        supported_crss = " ".join(
            crss.getSupportedCRS_WCS(format_function=crss.asShortCode)
        ) 
        layer.setMetaData("ows_srs", supported_crss) 
        layer.setMetaData("wcs_srs", supported_crss) 

        for band in bands:
            layer.setMetaData({
                "band_description": band.description,
                "band_definition": band.definition,
                "band_uom": band.uom
            }, namespace=band.name)

            # For MS WCS 1.x interface
            layer.setMetaData({
                "label": band.name,
                "interval": "%d %d" % band.allowed_values
            }, namespace="wcs_%s" % band.name)

        return layer


    def get_native_format(self, coverage, data_items):
        if len(data_items) == 1:
            return data_items[0].format

        return None


    def find_param(self, params, name, default=None):
        for key, value in params:
            if key == name:
                return value
        return default


    def get_wcs_formats(self):
        return getFormatRegistry().getSupportedFormatsWCS()


    def get_all_outputformats(self, use_mime=True):
        outputformats = []
        for frmt in self.get_wcs_formats():
            of = outputFormatObj(frmt.driver, "custom")
            of.name = frmt.mimeType if use_mime else frmt.wcs10name
            of.mimetype = frmt.mimeType 
            of.extension = frmt.defaultExt
            outputformats.append(of)
        return outputformats

