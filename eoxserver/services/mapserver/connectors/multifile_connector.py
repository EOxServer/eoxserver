#-------------------------------------------------------------------------------
# $Id$
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

from os.path import join
from uuid import uuid4

from eoxserver.core import Component, implements
from eoxserver.backends.access import connect
from eoxserver.contrib import vsi, vrt
from eoxserver.services.mapserver.interfaces import ConnectorInterface


class MultiFileConnector(Component):
    """ Connects multiple files containing the various bands of the coverage
        with the given layer. A temporary VRT file is used as abstraction for 
        the different band files.
    """

    implements(ConnectorInterface)
    
    def supports(self, data_items):
        # TODO: better checks
        return (
            len(data_items) > 1 
            and all(
                map(lambda d: d.semantic.startswith("bands"), data_items)
            )
        )

    def connect(self, coverage, data_items, layer, options):

        # TODO: implement
        vrt_doc = vrt.VRT()
        # TODO: configure vrt here

        path = join("/vsimem", uuid4().hex)
        with vsi.open(path, "w+") as f:
            vrt_doc.write(f)


        # TODO!!
        if layer.metadata.get("eoxs_wrap_dateline") == "true":
            e = wrap_extent_around_dateline(coverage.extent, coverage.srid)

            vrt_path = join("/vsimem", uuid4().hex)
            ds = gdal.Open(data)
            vrt_ds = create_simple_vrt(ds, vrt_path)
            size_x = ds.RasterXSize
            size_y = ds.RasterYSize
            
            dx = abs(e[0] - e[2]) / size_x
            dy = abs(e[1] - e[3]) / size_y 
            
            vrt_ds.SetGeoTransform([e[0], dx, 0, e[3], 0, -dy])
            vrt_ds = None
            
            layer.data = vrt_path

        layer.data = path

    def disconnect(self, coverage, data_items, layer, options):
        vsi.remove(layer.data)
