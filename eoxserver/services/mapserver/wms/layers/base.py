#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2014 EOX IT Services GmbH
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
from eoxserver.contrib import mapserver as ms
from eoxserver.resources.coverages import crss
from eoxserver.services import models as service_models


class LayerFactory(object):
    """ Abstract base layer factory class. """

    @property
    def options(self):
        "Get layer options."
        return self.__options

    @property
    def suffix(self):
        "Get layer suffix handled by the factory."
        return self.__suffix

    @property
    def group(self):
        "Return layers group name."
        return self.__group

    @property
    def root(self):
        "Get the (root) EOObject of the requested layer."
        return self.__root

    @property
    def coverages(self):
        "Get list of the coverages needed by the requested layer."
        return self.__items

    @property
    def is_groupped(self):
        """Return a boolean flag indicating whether a group layer is needed.
           The group layer is not needed if the requested EOObject (layer)
           is the same as the rendered EOObject (coverage).
        """
        return not ((len(self.__items) == 1) and \
            (self.__items[0][1] == self.__root.identifier))

    def __init__(self, layer_selection, options):
        self.__root = layer_selection.root
        self.__items = layer_selection.coverages
        self.__suffix = (layer_selection.suffix or "")
        self.__group = layer_selection.layer_name
        self.__options = (options or {})

    def generate(self):
        """ Layer generator. """
        raise NotImplementedError


class GroupLayerMixIn(object):
    @staticmethod
    def _group_layer(name, group=None):
        """ Create group layer from a coverage."""
        layer = ms.layerObj()
        layer.name = name
        if group:
            layer.setMetaData("wms_layer_group", group)
        return layer


class StyledLayerMixIn(object):
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

    def apply_styles(self, layer, fill=False, default=None):
        """ Add style metadata. """
        for name, r, g, b in self.STYLES:
            cls = ms.classObj()
            style = ms.styleObj()
            style.outlinecolor = ms.colorObj(r, g, b)
            if fill:
                style.color = ms.colorObj(r, g, b)
            style.opacity = 50
            cls.insertStyle(style)
            cls.group = name
            layer.insertClass(cls)
        layer.classgroup = (default or self.DEFAULT_STYLE)


class PolygonLayerMixIn(object):
    def _polygon_layer(self, name, filled=False, srid=4326, default_style=None):
        layer = ms.layerObj()
        layer.name = name
        layer.type = ms.MS_LAYER_POLYGON

        self.apply_styles(layer, filled)

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


class PolygonMaskingLayerMixIn(object):
    @staticmethod
    def _polygon_masking_layer(cov, name, mask, group=None):
        layer = ms.layerObj()
        layer.name = name
        layer.type = ms.MS_LAYER_POLYGON
        #layer.setMetaData("eoxs_geometry_reversed", "true")

        if group:
            layer.setMetaData("wms_layer_group", group)

        cls = ms.classObj(layer)
        style = ms.styleObj(cls)
        style.color.setRGB(0, 0, 0)

        shape = ms.shapeObj.fromWKT(mask.wkt)
        shape.initValues(1)
        shape.setValue(0, cov.identifier)

        # add feature to the layer
        layer.addFeature(shape)

        return layer


class DataLayerMixIn(object):
    @staticmethod
    def _render_options(cov):
        """ Extract coverage specific renderer options from the database. """
        try:
            return service_models.WMSRenderOptions.objects.get(coverage=cov)
        except service_models.WMSRenderOptions.DoesNotExist:
            return None

    @staticmethod
    def _offsite_color(range_type, indices=None):
        """
        Cretate an offsite color for a given range type and optional list
        of band indices.
        The bands' offise colors are set either from the nil-values of the
        range type or set to zero if there is no nil-value available.
        """
        # TODO: Review the offsite color method.
        if indices == None:
            if len(range_type) >= 3:
                band_indices = [0, 1, 2]
            elif len(range_type) == 2:
                band_indices = [0, 1, 1]
            elif len(range_type) == 1:
                band_indices = [0, 0, 0]
            else:
                # no offsite color possible
                return None
        else:
            band_indices = [v-1 for v in indices]

        if len(band_indices) < 3 or len(band_indices) > 4:
            raise ValueError("Wrong number of band indices to calculate"
                             " the offsite color.")
        values = []
        for index in band_indices:
            nilvalset = range_type[index].nil_value_set
            values.append(nilvalset[0].value if nilvalset else 0)

        return ms.colorObj(*values)

    @staticmethod
    def _indeces(cov, options, ropt):
        def _default_indeces(ropt):
            if ropt is None:
                return None
            red = ropt.default_red
            green = ropt.default_green
            blue = ropt.default_blue
            alpha = ropt.default_alpha
            if red is not None and green is not None and blue is not None:
                if alpha is not None:
                    return [red, green, blue, alpha]
                else:
                    return [red, green, blue]
            else:
                return None

        req_bands = options.get("bands", None)
        range_types = cov.range_type

        if not req_bands:
            req_bands = _default_indeces(ropt)
        if not req_bands:
            return None
        if len(req_bands) < 1:
            raise Exception("No band selected!")
        if len(req_bands) > 3:
            raise Exception("More than three selected bands cannot be composed "
                "to an RGB image!. BANDS=%s"%(req_bands))

        indices = []
        for req_band in req_bands[:4]:
            if isinstance(req_band, int): # band index
                if req_band < 1 or req_band > len(range_types):
                    raise Exception("Coverage '%s' does not have a band with"
                        " index %d."%(cov.identifier, req_band))
                indices.append(req_band)
            else: # band identifier
                for i, band in enumerate(range_types):
                    if band.identifier == req_band:
                        indices.append(i + 1)
                        break
                else:
                    raise Exception("Coverage '%s' does not have a band with"
                        " name '%s'."%(cov.identifier, req_band))

        if len(indices) == 2:
            indices = [indices[0], indices[1], indices[1]]
        elif len(indices) == 1:
            indices = [indices[0], indices[0], indices[0]]

        return indices


    def _data_layer(self, cov, name, extent=None, group=None, offsite=None,
                        wrapped=False, mask=None, indices=None, ropt=None):
        """ Create plain data layer from a coverage."""
        layer = ms.layerObj()
        layer.name = name
        layer.type = ms.MS_LAYER_RASTER

        if extent:
            layer.setMetaData("wms_extent", "%.12e %.12e %.12e %.12e"%extent)
            layer.setExtent(*extent)

        #layer.setMetaData(
        #    "wms_enable_request", "getcapabilities getmap getfeatureinfo"
        #)

        if wrapped:
            # set the info for the connector to wrap this layer around the dateline
            layer.setMetaData("eoxs_wrap_dateline", "true")

        # set projection
        sr = cov.spatial_reference
        layer.setProjection(sr.proj)
        layer.setMetaData("ows_srs", "EPSG:%d"%sr.srid)
        layer.setMetaData("wms_srs", "EPSG:%d"%sr.srid)

        if indices:
            #layer.addProcessing("CLOSE_CONNECTION=CLOSE") #What it this good for?
            layer.setProcessingKey("BANDS", ",".join("%d"%v for v in indices))

        if group:
            layer.setMetaData("wms_layer_group", group)

        if offsite:
            layer.offsite = offsite
        else:
            layer.offsite = self._offsite_color(cov.range_type, indices)

        if ropt:
            if ropt.scale_min is not None and ropt.scale_max is not None:
                scale = "%d,%d"%(ropt.scale_min, ropt.scale_max)
                layer.setProcessingKey("SCALE", scale)
            elif ropt.scale_auto:
                layer.setProcessingKey("SCALE", "AUTO")

        if mask:
            layer.mask = mask

        return layer
