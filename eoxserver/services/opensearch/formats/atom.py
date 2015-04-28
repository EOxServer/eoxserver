#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH
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


from eoxserver.core import implements
from eoxserver.core.util.timetools import isoformat
from eoxserver.contrib import ogr
from eoxserver.services.opensearch.interfaces import ResultFormatInterface
from eoxserver.services.opensearch.formats import base


class AtomResultFormat(base.BaseOGRResultFormat):
    """ Atom result format.
    """

    implements(ResultFormatInterface)

    mimetype = "application/atom+xml"
    name = "atom"
    extension = ".xml"
    driver_name = "GeoRSS"

    def create_datasource(self, driver, filename):
        return driver.CreateDataSource(
            filename, ["FORMAT=ATOM", "USE_EXTENSIONS=YES"]
        )

    def create_fields(self, layer):
        layer.CreateField(ogr.FieldDefn("id", ogr.OFTString))
        layer.CreateField(ogr.FieldDefn("title", ogr.OFTString))
        layer.CreateField(ogr.FieldDefn("begintime", ogr.OFTString))
        layer.CreateField(ogr.FieldDefn("endtime", ogr.OFTString))

    def set_feature_values(self, feature, eo_object):
        # TODO: try to convert to polygon
        feature.SetGeometry(
            ogr.ForceToPolygon(
                ogr.CreateGeometryFromWkb(str(eo_object.footprint.wkb))
            )
        )
        feature.SetField("id", eo_object.identifier.encode("utf-8"))
        feature.SetField("title", eo_object.identifier.encode("utf-8"))
        feature.SetField("begintime", isoformat(eo_object.begin_time))
        feature.SetField("endtime", isoformat(eo_object.end_time))
