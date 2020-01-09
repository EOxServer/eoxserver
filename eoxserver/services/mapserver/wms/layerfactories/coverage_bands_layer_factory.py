#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
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


from eoxserver.contrib.mapserver import Layer

from eoxserver.services.mapserver.wms.layerfactories.base import (
    AbstractLayerFactory, OffsiteColorMixIn
)


class CoverageBandsLayerFactory(OffsiteColorMixIn, AbstractLayerFactory):
    suffixes = ("_bands",)
    requires_connection = True

    def generate(self, eo_object, group_layer, suffix, options):
        name = eo_object.identifier + "_bands"
        layer = Layer(name)
        layer.setMetaData("ows_title", name)
        layer.setMetaData("wms_label", name)
        layer.addProcessing("CLOSE_CONNECTION=CLOSE")

        coverage = eo_object.cast()
        range_type = coverage.range_type

        req_bands = options["bands"]
        band_indices = []
        bands = []

        for req_band in req_bands:
            if isinstance(req_band, int):
                band_indices.append(req_band + 1)

                bands.append(range_type[req_band])
            else:
                for i, band in enumerate(range_type):
                    if band.name == req_band:
                        band_indices.append(i + 1)
                        bands.append(band)
                        break
                else:
                    raise Exception(
                        "Coverage '%s' does not have a band with name '%s'."
                        % (coverage.identifier, req_band)
                    )

        if len(req_bands) in (3, 4):
            indices_str = ",".join(map(str, band_indices))
            offsite_indices = list(map(lambda v: v-1, band_indices[:3]))
        elif len(req_bands) == 1:
            indices_str = ",".join(map(str, band_indices * 3))
            v = band_indices[0] - 1
            offsite_indices = [v, v, v]
        else:
            raise Exception("Invalid number of bands requested.")

        offsite = self.offsite_color_from_range_type(
            range_type, offsite_indices
        )
        options = self.get_render_options(coverage)
        self.set_render_options(layer, offsite, options)

        layer.setProcessingKey("BANDS", indices_str)

        if options.bands_scale_min and options.bands_scale_max:
            bands_scale_min = str(options.bands_scale_min).split(',')
            bands_scale_max = str(options.bands_scale_max).split(',')
            idx1, idx2, idx3 = offsite_indices
            layer.setProcessingKey("SCALE_1", "%s,%s" % (
                bands_scale_min[idx1], bands_scale_max[idx1]
            ))
            layer.setProcessingKey("SCALE_2", "%s,%s" % (
                bands_scale_min[idx2], bands_scale_max[idx2]
            ))
            layer.setProcessingKey("SCALE_3", "%s,%s" % (
                bands_scale_min[idx3], bands_scale_max[idx3]
            ))

        yield (layer, coverage.data_items.all())

    def generate_group(self, name):
        return Layer(name)
