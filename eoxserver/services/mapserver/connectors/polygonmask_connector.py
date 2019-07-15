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

from eoxserver.contrib import ogr
from eoxserver.contrib import mapserver as ms
from eoxserver.backends.access import get_vsi_path


class PolygonMaskConnector(object):
    """ Connects polygon mask files to MapServer polygon layers. For some
        purposes this can also be done via "reverse" polygons, where the actual
        polygons are subtracted from the coverages footprint.
    """

    def supports(self, coverage, data_items):
        num = len(data_items)
        return (
            len(data_items) >= 1 and
            len(filter(
                lambda d: d.semantic.startswith("polygonmask"), data_items
            )) == num
        )

    def connect(self, coverage, data_items, layer, options):
        mask_item = data_items[0]

        try:
            is_reversed = (
                layer.metadata.get("eoxs_geometry_reversed") == "true"
            )
        except ms.MapServerError:
            is_reversed = False

        # check if the geometry is "reversed"
        if is_reversed:
            # TODO: better use the coverages Extent?
            geom_types = (ogr.wkbPolygon, ogr.wkbMultiPolygon)
            output_polygon = ogr.Geometry(wkt=str(coverage.footprint.wkt))

            for mask_item in data_items:
                ds = ogr.Open(get_vsi_path(mask_item))
                for i in range(ds.GetLayerCount()):
                    ogr_layer = ds.GetLayer(i)
                    if not ogr_layer:
                        continue

                    feature = ogr_layer.GetNextFeature()
                    while feature:
                        # TODO: reproject if necessary
                        geometry = feature.GetGeometryRef()
                        if geometry.GetGeometryType() not in geom_types:
                            continue
                        if geometry:
                            output_polygon = output_polygon.Difference(geometry)
                        feature = ogr_layer.GetNextFeature()

            # since we have the geometry already in memory, add it to the layer
            # as WKT
            shape = ms.shapeObj.fromWKT(output_polygon.ExportToWkt())
            shape.initValues(1)
            shape.setValue(0, coverage.identifier)
            layer.addFeature(shape)

        else:
            layer.connectiontype = ms.MS_OGR
            layer.connection = connect(data_items[0])
            # TODO: more than one mask_item?

        layer.setProjection("EPSG:4326")
        layer.setMetaData("ows_srs", "EPSG:4326")
        layer.setMetaData("wms_srs", "EPSG:4326")

    def disconnect(self, coverage, data_items, layer, options):
        pass
