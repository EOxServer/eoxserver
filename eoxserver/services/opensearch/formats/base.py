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


import uuid

from eoxserver.contrib import ogr, vsi

from eoxserver.core import Component, implements
from eoxserver.core.util.timetools import isoformat
from eoxserver.services.opensearch.interfaces import ResultFormatInterface


class BaseResultFormat(Component):
    """ Base class for result formats
    """

    implements(ResultFormatInterface)

    abstract = True


class BaseOGRResultFormat(BaseResultFormat):
    """ Base ckass for result formats using OGR for encoding the records.
    """
    abstract = True

    driver_name = None
    extension = None

    def encode(self, queryset):
        """ Encode a query set as an OGR datasource and retrieve its contents.
        """
        # create a datasource and its fields
        driver = self.get_driver()
        filename = self.get_filename()
        ds = self.create_datasource(driver, filename)
        layer = self.create_layer(ds)
        self.create_fields(layer)
        definition = layer.GetLayerDefn()

        # encode the objects
        for eo_object in queryset:
            feature = self.create_feature(layer, definition)
            self.set_feature_values(feature, eo_object)
            layer.CreateFeature(feature)

        # close datasource and read contents
        ds.Destroy()

        with vsi.open(filename) as f:
            content = f.read()

        # perform cleanup and return content + mimetype
        self.cleanup(driver, ds, filename)
        return content

    def get_driver(self):
        """ Get the OGR driver.
        """
        return ogr.GetDriverByName(self.driver_name)

    def get_filename(self):
        """ Get the filename for the temporary file.
        """
        return "/vsimem/%s%s" % (uuid.uuid4().hex, self.extension)

    def create_datasource(self, driver, filename):
        """ Create the OGR DataSource. This needs to be overriden in formats
            that require certain creation options.
        """
        return driver.CreateDataSource(filename)

    def create_layer(self, datasource):
        """ Create the layer in the DataSource.
        """
        return datasource.CreateLayer("layer", geom_type=ogr.wkbMultiPolygon)

    def create_fields(self, layer):
        """ Create the field definitions of the layer. By default, it contains
            definitions of the `id`, `begin_time` and `end_time` fields. For
            certain formats, this needs to be overridden.
        """
        layer.CreateField(ogr.FieldDefn("id", ogr.OFTString))
        layer.CreateField(ogr.FieldDefn("begin_time", ogr.OFTString))
        layer.CreateField(ogr.FieldDefn("end_time", ogr.OFTString))

    def create_feature(self, layer, definition):
        """ Create a feature from the given definition.
        """
        return ogr.Feature(definition)

    def set_feature_values(self, feature, eo_object):
        """ Set the values and the geometry of the feature. This needs to be
            inline with the :meth:`create_fields` method.
        """
        feature.SetGeometry(
            ogr.CreateGeometryFromWkb(str(eo_object.footprint.wkb))
        )
        feature.SetField("id", eo_object.identifier.encode("utf-8"))
        feature.SetField("begin_time", isoformat(eo_object.begin_time))
        feature.SetField("end_time", isoformat(eo_object.end_time))

    def cleanup(self, driver, datasource, filename):
        """ Perform any necessary cleanup steps, like removing the temporary
            file.
        """
        driver.DeleteDataSource(filename)
