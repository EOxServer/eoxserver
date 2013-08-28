
from django.utils.dateparse import parse_date, parse_datetime
from django.contrib.gis.geos import Polygon, MultiPolygon

from eoxserver.core import Component, implements
from eoxserver.core.decoders import xml
from eoxserver.core.util.xmltools import parse
from eoxserver.resources.coverages.metadata.interfaces import (
    MetadataReaderInterface
)


class DimapGeneralFormatReader(Component):
    implements(MetadataReaderInterface)

    def test(self, obj):
        tree = parse(obj)
        return tree is not None and tree.tag == "Dimap_Document"

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

            values =  {
                "identifier": decoder.identifier,
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
    value = parse_date(string) or parse_datetime(string)
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
