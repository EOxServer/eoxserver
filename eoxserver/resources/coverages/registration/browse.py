# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2017 EOX IT Services GmbH
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
# ------------------------------------------------------------------------------

from eoxserver.contrib import gdal
from eoxserver.backends.access import get_vsi_path, gdal_open
from eoxserver.backends.util import resolve_storage
from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.registration import base
from eoxserver.resources.coverages.registration.exceptions import (
    RegistrationError
)


class BrowseRegistrator(base.BaseRegistrator):
    def register(self, product_identifier, location, type_name=None):
        try:
            product = models.Product.objects.get(identifier=product_identifier)
        except models.Product.DoesNotExist:
            raise RegistrationError('No such product %r' % product_identifier)

        browse_type = None
        if type_name:
            browse_type = models.BrowseType.objects.get(
                name=type_name,
                product_type=product.product_type
            )

        browse = models.Browse(
            product=product,
            location=location[-1],
            storage=resolve_storage(location[:-1]),
            browse_type=browse_type
        )

        # Get a VSI handle for the browse to get the size, extent and CRS
        # via GDAL
        ds = gdal_open(browse)
        browse.width = ds.RasterXSize
        browse.height = ds.RasterYSize
        browse.coordinate_reference_system = ds.GetProjection()
        extent = gdal.get_extent(ds)
        browse.min_x, browse.min_y, browse.max_x, browse.max_y = extent

        browse.full_clean()
        browse.save()
        return browse
