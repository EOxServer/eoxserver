
from django.utils.dateparse import parse_date, parse_datetime
from django.contrib.gis.geos import Polygon

from eoxserver.core import Component, implements
from eoxserver.core.decoders import xml
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
        if tree is not None:
            version = tree.attr["version"]
            if version.startswith("1.1"):
                decoder = DimapGeneralFormat11Decoder(tree)
            elif version.startswith("2.0"):
                decoder = DimapGeneralFormat20Decoder(tree)
            else:
                raise Exception(
                    "DIMAP version '%s' is not supported." % version
                )

            size = decoder.size
            gt = decoder.geotransform

            extent = (
                gt[0], gt[3], gt[0] + gt[1] * size[0], gt[3] + gt[5] * size[1]
            )

            return {
                "identifier": decoder.identifier,
                "begin_time": decoder.begin_time,
                "end_time": decoder.end_time,
                "footprint": decoder.footprint,
                "size": size,
                "extent": extent,
                "projection": decoder.projection
            }
        raise Exception("Could not parse from obj '%s'." % repr(obj))


def parse_date_or_datetime(string):
    value = parse_date(string) or parse_datetime(string)
    if not value:
        raise Exception("Could not parse date or datetime from '%s'." % string)
    return value


def parse_footprint(elem):
    points = []

    for vertex in elem.findall("Vertex"):
        points.append((
            float(vertex.findtext("FRAME_LON")),
            float(vertex.findtext("FRAME_LAT"))
        ))

    if points[0] != points[-1]:
        points.append(points[0])

    return Polygon(points)


def parse_size(elem):
    return (int(elem.findtext("NCOLS")), int(elem.findtext("NROWS")))


def parse_geotransform(elem):
    values = (
        elem.findtext("ULXMAP"), elem.findtext("XDIM"), 0, 
        elem.findtext("ULYMAP"), 0, elem.findtext("YDIM")
    )
    return map(float, values)


def parse_projection(elem):
    pass
    # TODO


class DimapGeneralFormat11Decoder(xml.Decoder):
    identifier  = xml.Parameter("Dataset_Id/DATASET_NAME/text()")
    begin_time  = xml.Parameter("Production/DATASET_PRODUCTION_DATE/text()", type=parse_date_or_datetime)
    end_time    = xml.Parameter("Production/DATASET_PRODUCTION_DATE/text()", type=parse_date_or_datetime)
    footprint   = xml.Parameter("Dataset_Frame", type=parse_footprint)
    size        = xml.Parameter("Raster_Dimensions", type=parse_size)
    geotransform = xml.Parameter("Geoposition/Geoposition_Insert", type=parse_geotransform)
    projection  = xml.Parameter("Coordinate_Reference_System/Horizontal_CS", type=parse_projection) # TODO


class DimapGeneralFormat20Decoder(xml.Decoder):
    pass # TODO: implement