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


class MetadataReaderInterface(object):
    """ Interface for metadata readers.
    """

    def test(self, obj):
        """ Return a boolean value, whether or not metadata can be extracted 
            from the given object.
        """
        pass


    def format(self, obj):
        """ Returns a format specifier for the given object. Can be ignored, 
            when the reader only supports one format.
        """
        pass


    def read(self, obj):
        """ Returns a dict with any of the following keys:
            - identifier (string)
            - extent (a four tuple of floats)
            - size (a two-tuple of ints)
            - projection (an integer or two-tuple of two strings (definition and format))
            - footprint (a django.contrib.gis.geos.MultiPolygon)
            - begin_time (a python datetime.datetime)
            - end_time (a python datetime.datetime)

            The argument obj is of an arbitrary type, the reader needs to 
            determine whether or not the type is supported and an exception 
            shall be raised if not.
        """
        pass


class MetadataWriterInterface(object):
    """ Interface for metadata writers.
    """

    @property
    def formats(self):
        pass


    def write(self, values, file_obj, format=None):
        """ Write the given values (a dict) to the file-like object `file_obj`.
            The dict contains all of the following entries:
            - identifier (string)
            - extent (a four tuple of floats)
            - size (a two-tuple of ints)
            - projection (an integer or two-tuple of two strings (definition and format))
            - footprint (a django.contrib.gis.geos.MultiPolygon)
            - begin_time (a python datetime.datetime)
            - end_time (a python datetime.datetime)

            The writer may ignore non-applicable parameters.
        """
        pass


class GDALDatasetMetadataReaderInterface(object):
    """ Interface for GDAL dataset metadata readers.
    """

    def test_ds(self, obj):
        """ Return a boolean value, whether or not metadata can be extracted 
            from the given object.
        """
        pass


    def format(self, obj):
        """ Returns a format specifier for the given object. Can be ignored, 
            when the reader only supports one format.
        """
        pass


    def read_ds(self, ds):
        """ Returns a dict with any of the following keys:
            - identifier (string)
            - extent (a four tuple of floats)
            - size (a two-tuple of ints)
            - projection (an integer or two-tuple of two strings (definition and format))
            - footprint (a django.contrib.gis.geos.MultiPolygon)
            - begin_time (a python datetime.datetime)
            - end_time (a python datetime.datetime)

            The argument `ds` is a gdal.Dataset.
        """
        pass
