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


from eoxserver.core.util.timetools import parse_iso8601
from django.contrib.gis.geos import Polygon, MultiPolygon

from eoxserver.core.decoders import xml
from eoxserver.core.util.xmltools import parse


class DimapGeneralFormatReader(object):
    def test(self, obj):
        tree = parse(obj)
        return tree is not None and tree.getroot().tag == "Dimap_Document"

    def get_format_name(self, obj):
        return "dimap"

    def read(self, obj):
        tree = parse(obj)
        if self.test(tree):
            version = tree.xpath(
                "Metadadata_Id/METADATA_FORMAT/"
                "|Metadata_Identification/METADATA_FORMAT"
            )[0].get("version", "1.1")
            if version.startswith("1.1"):
                decoder = DimapGeneralFormat11Decoder(tree)
            elif version.startswith("2.0"):
                decoder = DimapGeneralFormat20Decoder(tree)
            else:
                raise Exception(
                    "DIMAP version '%s' is not supported." % version
                )

            values = {
                "identifier": decoder.identifier,
                "format": "dimap"
            }

            # in Dimap, pretty much everything is optional
            def cond_set(dct, key, value):
                if value is not None:
                    dct[key] = value

            # decode
            begin_time = decoder.begin_time
            end_time = decoder.end_time
            footprint = decoder.footprint
            projection = decoder.projection
            size = decoder.size
            gt = decoder.geotransform

            # calculate extent
            extent = None
            if size and gt:
                extent = (
                    gt[0], gt[3], gt[0] + gt[1] * size[0], gt[3] + gt[5] * size[1]
                )

            # set values
            cond_set(values, "begin_time", begin_time)
            cond_set(values, "end_time", begin_time)
            cond_set(values, "footprint", begin_time)
            cond_set(values, "size", begin_time)
            cond_set(values, "extent", begin_time)
            cond_set(values, "projection", begin_time)

            return values

        raise Exception("Could not parse from obj '%s'." % repr(obj))


def parse_date_or_datetime_11(string):
    value = parse_iso8601(string)
    if not value:
        raise Exception("Could not parse date or datetime from '%s'." % string)
    return value


def parse_footprint_11(elem):
    points = []

    for vertex in elem.findall("Vertex"):
        points.append((
            float(vertex.findtext("FRAME_LON")),
            float(vertex.findtext("FRAME_LAT"))
        ))

    if points[0] != points[-1]:
        points.append(points[0])

    return MultiPolygon(Polygon(points))


def parse_size_11(elem):
    return (int(elem.findtext("NCOLS")), int(elem.findtext("NROWS")))


def parse_geotransform_11(elem):
    values = (
        elem.findtext("ULXMAP"), elem.findtext("XDIM"), 0,
        elem.findtext("ULYMAP"), 0, elem.findtext("YDIM")
    )
    return map(float, values)


def parse_projection_11(elem):
    pass
    # TODO


class DimapGeneralFormat11Decoder(xml.Decoder):
    identifier  = xml.Parameter("Dataset_Id/DATASET_NAME/text()")
    begin_time  = xml.Parameter("Production/DATASET_PRODUCTION_DATE/text()", type=parse_date_or_datetime_11, num="?")
    end_time    = xml.Parameter("Production/DATASET_PRODUCTION_DATE/text()", type=parse_date_or_datetime_11, num="?")
    footprint   = xml.Parameter("Dataset_Frame", type=parse_footprint_11, num="?")
    size        = xml.Parameter("Raster_Dimensions", type=parse_size_11, num="?")
    geotransform = xml.Parameter("Geoposition/Geoposition_Insert", type=parse_geotransform_11, num="?")
    projection  = xml.Parameter("Coordinate_Reference_System/Horizontal_CS", type=parse_projection_11, num="?") # TODO


class DimapGeneralFormat20Decoder(xml.Decoder):
    identifier  = xml.Parameter("Dataset_Identification/DATASET_ID/text()")
    # TODO implement further parameters
