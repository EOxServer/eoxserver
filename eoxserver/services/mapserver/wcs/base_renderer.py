#-------------------------------------------------------------------------------
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
from eoxserver.core.decoders import config, typelist
from eoxserver.contrib import mapserver as ms
from eoxserver.resources.coverages import crss
from eoxserver.resources.coverages.models import RectifiedStitchedMosaic
from eoxserver.resources.coverages.formats import getFormatRegistry


class WCSConfigReader(config.Reader):
    section = "services.ows.wcs"
    supported_formats = config.Option(type=typelist(str, ","), default=())
    maxsize = config.Option(type=int, default=None)

    section = "services.ows"
    update_sequence = config.Option(default="0")


class BaseRenderer(Component):
    abstract = True

    def create_map(self):
        """ Helper function to create a WCS enabled MapServer mapObj.
        """
        map_ = ms.mapObj()
        map_.setMetaData("ows_enable_request", "*")
        maxsize = WCSConfigReader(get_eoxserver_config()).maxsize
        if maxsize is not None:
            map_.maxsize = maxsize
        map_.setMetaData("ows_updateSequence",
            WCSConfigReader(get_eoxserver_config()).update_sequence
        )
        return map_

    def data_items_for_coverage(self, coverage):
        """ Helper function to query all relevant data items for any raster data
            from the database.
        """
        return coverage.data_items.filter(
            Q(semantic__startswith="bands") | Q(semantic="tileindex")
        )

    def layer_for_coverage(self, coverage, native_format, version=None):
        """ Helper method to generate a WCS enabled MapServer layer for a given
            coverage.
        """
        range_type = coverage.range_type
        bands = list(range_type)

        # create and configure layer
        layer = ms.layerObj()
        layer.name = coverage.identifier
        layer.type = ms.MS_LAYER_RASTER

        layer.setProjection(coverage.spatial_reference.proj)

        extent = coverage.extent
        size = coverage.size
        resolution = ((extent[2] - extent[0]) / float(size[0]),
                      (extent[1] - extent[3]) / float(size[1]))

        layer.setExtent(*extent)

        ms.setMetaData(layer, {
            "title": coverage.identifier,
            "enable_request": "*"
        }, namespace="ows")

        ms.setMetaData(layer, {
            "label": coverage.identifier,
            "extent": "%.10g %.10g %.10g %.10g" % extent,
            "resolution": "%.10g %.10g" % resolution,
            "size": "%d %d" % size,
            "bandcount": str(len(bands)),
            "interval": "%f %f" % bands[0].allowed_values,
            "significant_figures": "%d" % bands[0].significant_figures,
            "rangeset_name": range_type.name,
            "rangeset_label": range_type.name,
            "imagemode": ms.gdalconst_to_imagemode_string(bands[0].data_type),
            "formats": " ".join([
                f.wcs10name if version.startswith("1.0") else f.mimeType
                for f in self.get_wcs_formats()]
            )
        }, namespace="wcs")

        if version is None or version.startswith("2.0"):
            ms.setMetaData(layer, {
                "band_names": " ".join([band.name for band in bands]),
            }, namespace="wcs")
        else:
            ms.setMetaData(layer, {
                "rangeset_axes": ",".join(band.name for band in bands),
            }, namespace="wcs")

        if native_format:
            if version.startswith("1.0"):
                native_format = next((
                    x.wcs10name for x in self.get_wcs_formats()
                    if x.mimeType == native_format), native_format
                )
            ms.setMetaData(layer, {
                "native_format": native_format,
                "nativeformat": native_format
            }, namespace="wcs")

        native_crs = "EPSG:%d" % coverage.spatial_reference.srid
        all_crss = crss.getSupportedCRS_WCS(format_function=crss.asShortCode)
        if native_crs in all_crss:
            all_crss.remove(native_crs)

        # setting the coverages CRS as the first one is important!
        all_crss.insert(0, native_crs)

        supported_crss = " ".join(all_crss)
        layer.setMetaData("ows_srs", supported_crss)
        layer.setMetaData("wcs_srs", supported_crss)

        for band in bands:
            ms.setMetaData(layer, {
                "band_description": band.description,
                "band_definition": band.definition,
                "band_uom": band.uom,
            }, namespace=band.name)

            # For MS WCS 1.x interface
            ms.setMetaData(layer, {
                "label": band.name,
                "interval": "%d %d" % band.allowed_values
            }, namespace="wcs_%s" % band.name)

        if bands[0].nil_value_set:
            nilvalues = " ".join(
                str(nil_value.value) for nil_value in bands[0].nil_value_set
            )
            nilvalues_reasons = " ".join(
                nil_value.reason for nil_value in bands[0].nil_value_set
            )
            if nilvalues:
                ms.setMetaData(layer, {
                    "nilvalues": nilvalues,
                    "nilvalues_reasons": nilvalues_reasons
                }, namespace="wcs")

        return layer

    def get_native_format(self, coverage, data_items):
        if issubclass(coverage.real_type, RectifiedStitchedMosaic):
            # use the default format for RectifiedStitchedMosaics
            return getFormatRegistry().getDefaultNativeFormat().wcs10name

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
            of = ms.outputFormatObj(frmt.driver, "custom")
            of.name = frmt.mimeType if use_mime else frmt.wcs10name
            of.mimetype = frmt.mimeType
            of.extension = frmt.defaultExt
            outputformats.append(of)
        return outputformats


def is_format_supported(mime_type):
    reader = WCSConfigReader(get_eoxserver_config())
    return mime_type in reader.supported_formats
