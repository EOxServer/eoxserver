#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011-2014 EOX IT Services GmbH
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

from django.conf import settings

from eoxserver.core import Component, implements
from eoxserver.contrib import mapserver as ms
from eoxserver.contrib import gdal
from eoxserver.resources.coverages import models, crss
from eoxserver.services.mapserver.interfaces import LayerFactoryInterface
from eoxserver.services import models as service_models

from eoxserver.resources.coverages.dateline import (
    extent_crosses_dateline, wrap_extent_around_dateline
)

#-------------------------------------------------------------------------------


class BaseStyleMixIn(object):
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

    def apply_styles(self, layer, fill=False):
        # add style info
        for name, r, g, b in self.STYLES:
            cls = ms.classObj()
            style = ms.styleObj()
            style.outlinecolor = ms.colorObj(r, g, b)
            if fill:
                style.color = ms.colorObj(r, g, b)
            cls.insertStyle(style)
            cls.group = name

            layer.insertClass(cls)

        layer.classgroup = self.DEFAULT_STYLE


class OffsiteColorMixIn(object):
    def offsite_color_from_range_type(self, range_type, band_indices=None):
        """ Helper function to create an offsite color for a given range type
            and optionally band indices.
        """
        if band_indices is None:
            if len(range_type) == 1:
                band_indices = [0, 0, 0]
            elif len(range_type) >= 3:
                band_indices = [0, 1, 2]
            else:
                # no offsite color possible
                return None

        if len(band_indices) != 3:
            raise ValueError(
                "Wrong number of band indices to calculate offsite color."
            )

        values = []
        for index in band_indices:
            band = range_type[index]
            nil_value_set = band.nil_value_set

            # we only support offsite colors for "Byte" bands
            if nil_value_set and nil_value_set.data_type != gdal.GDT_Byte:
                return None

            if nil_value_set and len(nil_value_set) > 0:
                values.append(nil_value_set[0].value)
            else:
                return None

        return ms.colorObj(*values)


class PolygonLayerMixIn(object):
    def _create_polygon_layer(self, name):
        layer = ms.layerObj()
        layer.name = name
        layer.type = ms.MS_LAYER_POLYGON

        self.apply_styles(layer)

        srid = 4326
        layer.setProjection(crss.asProj4Str(srid))
        layer.setMetaData("ows_srs", crss.asShortCode(srid))
        layer.setMetaData("wms_srs", crss.asShortCode(srid))

        layer.dump = True

        layer.header = os.path.join(settings.PROJECT_DIR, "conf", "outline_template_header.html")
        layer.template = os.path.join(settings.PROJECT_DIR, "conf", "outline_template_dataset.html")
        layer.footer = os.path.join(settings.PROJECT_DIR, "conf", "outline_template_footer.html")

        layer.setMetaData("gml_include_items", "all")
        layer.setMetaData("wms_include_items", "all")

        layer.addProcessing("ITEMS=identifier")

        layer.offsite = ms.colorObj(0, 0, 0)

        return layer


class PlainLayerMixIn(object):

    def _create_layer(self, coverage, name, extent=None, group=None,
                      wrapped=False):
        layer = ms.layerObj()
        layer.name = name
        layer.type = ms.MS_LAYER_RASTER
        if extent:
            layer.setMetaData("wms_extent", "%f %f %f %f" % extent)
            layer.setExtent(*extent)

        #layer.setMetaData(
        #    "wms_enable_request", "getcapabilities getmap getfeatureinfo"
        #)

        if wrapped:
            # set the info for the connector to wrap this layer around the
            # dateline
            layer.setMetaData("eoxs_wrap_dateline", "true")

        self._set_projection(layer, coverage.spatial_reference)
        if group:
            layer.group = group

        return layer

    def get_render_options(self, coverage):
        try:
            return service_models.WMSRenderOptions.objects.get(
                coverage=coverage
            )
        except service_models.WMSRenderOptions.DoesNotExist:
            return None

    def set_render_options(self, layer, offsite=None, options=None):
        if offsite:
            layer.offsite = offsite
        if options:
            red = options.default_red
            green = options.default_green
            blue = options.default_blue
            alpha = options.default_alpha

            # rgb(a) bands
            if red is not None and green is not None and blue is not None:
                bands = "%d,%d,%d" % (red, green, blue)
                if alpha is not None:
                    bands += alpha
                layer.setProcessingKey("BANDS", bands)

            # single band grey
            elif red is not None and (green, blue, alpha) == (None, None, None):
                layer.setProcessingKey("BANDS", str(red))

            if options.bands_scale_min and options.bands_scale_max:
                bands_scale_min = str(options.bands_scale_min).split(',')
                bands_scale_max = str(options.bands_scale_max).split(',')

                if red is not None and (green, blue) == (None, None):
                    idx1 = red - 1
                    layer.setProcessingKey("SCALE", "%d,%d" % (
                        bands_scale_min[idx1], bands_scale_max[idx1]
                    ))
                else:
                    idx1 = (red or 1) - 1
                    idx2 = (green or 2) - 1
                    idx3 = (blue or 3) - 1
                    layer.setProcessingKey("SCALE_1", "%s,%s" % (
                        bands_scale_min[idx1], bands_scale_max[idx1]
                    ))
                    layer.setProcessingKey("SCALE_2", "%s,%s" % (
                        bands_scale_min[idx2], bands_scale_max[idx2]
                    ))
                    layer.setProcessingKey("SCALE_3", "%s,%s" % (
                        bands_scale_min[idx3], bands_scale_max[idx3]
                    ))

            elif options.scale_auto:
                layer.setProcessingKey("SCALE", "AUTO")
            elif options.scale_min is not None and options.scale_max is not None:
                layer.setProcessingKey(
                    "SCALE", "%d,%d" % (options.scale_min, options.scale_max)
                )

            if options.resampling:
                layer.setProcessingKey("RESAMPLE", str(options.resampling))

    def _set_projection(self, layer, sr):
        if sr.srid is not None:
            short_epsg = "EPSG:%d" % sr.srid
            layer.setMetaData("ows_srs", short_epsg)
            layer.setMetaData("wms_srs", short_epsg)
        layer.setProjection(sr.proj)


class AbstractLayerFactory(PlainLayerMixIn, Component):
    implements(LayerFactoryInterface)
    abstract = True

    def generate(self, eo_object, group_layer, suffix, options):
        raise NotImplementedError


class BaseCoverageLayerFactory(OffsiteColorMixIn, PlainLayerMixIn, Component):
    implements(LayerFactoryInterface)
    # NOTE: Technically, this class is not abstract but we need it labeled
    #       as an abstract class to allow inheritance while avoiding multiple
    #       component's imports.
    abstract = True

    def generate(self, eo_object, group_layer, suffix, options):
        coverage = eo_object.cast()
        extent = coverage.extent
        srid = coverage.srid

        data_items = coverage.data_items.all()
        range_type = coverage.range_type

        offsite = self.offsite_color_from_range_type(range_type)
        options = self.get_render_options(coverage)

        if srid is not None and extent_crosses_dateline(extent, srid):
            identifier = coverage.identifier
            wrapped_extent = wrap_extent_around_dateline(extent, srid)
            layer = self._create_layer(
                coverage, identifier + "_unwrapped", extent, identifier
            )

            self.set_render_options(layer, offsite, options)
            self.set_render_options(layer, offsite, options)
            yield layer, data_items
            wrapped_layer = self._create_layer(
                coverage, identifier + "_wrapped", wrapped_extent, identifier, True
            )
            self.set_render_options(wrapped_layer, offsite, options)
            yield wrapped_layer, data_items
        else:
            layer = self._create_layer(
                coverage, coverage.identifier, extent
            )
            self.set_render_options(layer, offsite, options)
            yield layer, data_items

    def generate_group(self, name):
        return ms.Layer(name)
