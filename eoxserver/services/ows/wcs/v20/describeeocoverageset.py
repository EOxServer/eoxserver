import logging

from eoxserver.core import Component, implements
from eoxserver.core.config import get_eoxserver_config
from eoxserver.core.decoders import xml, kvp, typelist, upper, enum
from eoxserver.resources.coverages import models
from eoxserver.services.interfaces import (
    OWSServiceHandlerInterface, 
    OWSGetServiceHandlerInterface, OWSPostServiceHandlerInterface
)
from eoxserver.services.ows.wcs.v20.util import nsmap, SectionsMixIn
from eoxserver.services.ows.wcs.v20.encoders import (
    WCS20CoverageDescriptionXMLEncoder
)

from eoxserver.services.ows.wcs.encoders import WCS20EOAPEncoder
from eoxserver.core.util.xmltools import DOMElementToXML
from eoxserver.services.ows.common.config import WCSEOConfigReader


logger = logging.getLogger(__name__)

class WCS20DescribeEOCoverageSetHandler(Component):
    implements(OWSServiceHandlerInterface)
    implements(OWSGetServiceHandlerInterface)
    implements(OWSPostServiceHandlerInterface)

    service = "WCS"
    versions = ("2.0.0", "2.0.1")
    request = "DescribeEOCoverageSet"


    def get_decoder(self, request):
        if request.method == "GET":
            return WCS20DescribeEOCoverageSetKVPDecoder(request.GET)
        elif request.method == "POST":
            return WCS20DescribeEOCoverageSetXMLDecoder(request.body)


    def handle(self, request):
        decoder = self.get_decoder(request)
        eo_ids = decoder.eo_ids
        subsets = decoder.subsets
        reader = WCSEOConfigReader(get_eoxserver_config())

        if len(eo_ids) == 0:
            raise

        self.check_subsets(subsets)

        eo_objects = set()
        failed = []
        for eo_id in eo_ids:
            try:
                qs = models.EOObject.objects.filter(identifier=eo_id)

                # TODO: important, distinguish between Containers/Coverages here!
                # perform "overlaps" only for Containers that might have subcoverages
                # Maybe merge with recursive lookup (same logic needs to be applied there)

                qs = apply_subsets(subsets, qs, "overlaps")
                eo_object = qs.get()
                self.recursive_add(
                    eo_object, eo_objects, subsets, decoder.containment
                )
                logger.debug("Got object %s." % eo_object)
            except models.EOObject.DoesNotExist:


                # TODO: check if the ID exists, if yes, then the subsets don't fit --> no error
                #
                if models.EOObject.objects.filter(identifier=eo_id).exists():
                    # no error, simply no match
                    continue

                failed.append(eo_id)
                logger.debug("Could not get object with id '%s'." % eo_id)

        if failed:
            raise NoSuchDatasetSeriesOrCoverage(failed)

        coverages = [] if decoder.section_included("CoverageDescriptions") else None
        dataset_series = [] if decoder.section_included("DatasetSeriesDescriptions") else None
        for eo_object in eo_objects:
            if coverages is not None and issubclass(eo_object.real_type, models.Coverage):
                coverages.append(eo_object.cast())
            elif dataset_series is not None and issubclass(eo_object.real_type, models.DatasetSeries):
                dataset_series.append(eo_object.cast())

            else:
                # TODO: what to do here?
                pass



        count_default = reader.paging_count_default


        # TODO: coverages should be sorted
        #coverages = sorted(coverages, ) 

        #encoder = WCS20CoverageDescriptionXMLEncoder()
        #return encoder.encode(coverages)

        # TODO: remove this at some point
        encoder = WCS20EOAPEncoder()
        return (
            DOMElementToXML(
                encoder.encodeEOCoverageSetDescription(
                    dataset_series, coverages, len(coverages)
                )
            ), 
            "text/xml"
        )


    def recursive_add(self, eo_object, eo_objects, subsets, containment):
        if models.iscollection(eo_object):
            # get a list of all EOObjects that are contained in this collection
            # and exclude all previously fetched items. 
            # TODO: Need proper performance checking
            items = models.EOObject.objects.filter(
                collections__in=[eo_object.pk]
            ).exclude(
                pk__in=map(lambda o: o.pk, eo_objects)
            )
            items = apply_subsets(subsets, items, containment)

            for item in items:
                if item not in eo_objects:
                    self.recursive_add(item, eo_objects, subsets, containment)

        eo_objects.add(eo_object)

    def check_subsets(self, subsets):
        has_x = False; has_y = False; has_t = False
        crs = None
        for subset in subsets:
            is_x = subset.is_x
            is_y = subset.is_x
            is_t = subset.is_temporal

            if not isinstance(subset, Trim):
                raise "Only Trims allowed"

            if subset.axis not in all_axes:
                raise "Invalid axis %s" % subset.axis

            if is_x and has_x or is_y and has_y or is_t and has_t:
                raise "Multiple trims for one axis"

            if is_t and subset.crs is not None and subset.crs != "":
                raise "invalid temporal crs"

            has_x = has_x or subset.is_x
            has_y = has_y or subset.is_y
            has_t = has_t or subset.is_temporal

        # TODO: check CRS


from eoxserver.resources.coverages import crss
from django.contrib.gis.gdal import SpatialReference
from django.contrib.gis.geos import Polygon

def crs_bounds(srid):
    srs = SpatialReference(srid)
        
    if srs.geographic:
        return (-180.0, -90.0, 180.0, 90.0)
    else:
        earth_circumference = 2 * math.pi * srs.semi_major
    
        return (
            -earth_circumference,
            -earth_circumference,
            earth_circumference,
            earth_circumference
        )

def crs_tolerance(srid):
    srs = SpatialReference(srid)
        
    if srs.geographic:
        return 1e-8
    else:
        return 1e-2


def get_subset_crs(subsets):
    if not subsets:
        return None

    crss = set(
        map(lambda s: s.crs, filter(lambda s: s.is_x or s.is_y, subsets))
    )

    if len(crss) != 1:
        raise "all X/Y crss must be the same"

    xy_crs = iter(crss).next()
    if xy_crs is not None:
        return crss.parseEPSGCode(crs_id_str, (crss.fromURL, crss.fromURN))
    return None


def apply_subsets(subsets, queryset, containment="overlaps"):
    if not subsets: 
        return queryset

    qs = queryset
    bbox = [None, None, None, None]
    srid = get_subset_crs(subsets)
    if srid is None:
        srid = 4326
    max_extent = crs_bounds(srid)
    tolerance = crs_tolerance(srid)

    for subset in subsets:
        if isinstance(subset, Slice):
            is_slice = True
            value = subset.value
        elif isinstance(subset, Trim):
            is_slice = False
            low = subset.low
            high = subset.high

        if subset.is_temporal:
            if is_slice:
                qs = qs.filter(
                    begin_time__lte=value,
                    end_time__gte=value
                )
            elif low is None and high is not None:
                qs = qs.filter(
                    begin_time__lte=high
                )
            elif low is not None and high is None:
                qs = qs.filter(
                    end_time__gte=low
                )
            else:
                qs = qs.exclude(
                    begin_time__gt=high
                ).exclude(
                    end_time__lt=low
                )

        else:
            if is_slice:
                if subset.is_x:
                    line = Line(
                        (value, max_extent[1]),
                        (value, max_extent[3])
                    )
                else:
                    line = Line(
                        (max_extent[0], value),
                        (max_extent[2], value)
                    )
                line.srid = srid
                if srid != 4326:
                    line.transform(4326)
                qs = qs.filter(footprint__intersects=line)

            else:
                if subset.is_x:
                    bbox[0] = subset.low
                    bbox[2] = subset.high
                else:
                    bbox[1] = subset.low
                    bbox[3] = subset.high


    if bbox != [None, None, None, None]:
        bbox = map(
            lambda v: v[0] if v[0] is not None else v[1], zip(bbox, max_extent)
        )

        bbox[0] -= tolerance; bbox[1] -= tolerance
        bbox[2] += tolerance; bbox[3] += tolerance

        logger.debug("Applying BBox %s with containment '%s'." % (bbox, containment))

        poly = Polygon.from_bbox(bbox)
        poly.srid = srid

        if srid != 4326:
            poly.transform(4326)
        if containment == "overlaps":
            qs = qs.filter(footprint__intersects=poly)
        elif containment == "contains":
            qs = qs.filter(footprint__within=poly)

    return qs


temporal_axes = ("t", "time", "phenomenontime")
x_axes = ("x", "lon", "long")
y_axes = ("y", "lat")
all_axes = temporal_axes + x_axes + y_axes


def float_or_star(value):
    if value == "*":
        return None
    return float(value)


class Subset(object):
    def __init__(self, axis, crs=None):
        self.axis = axis.lower()
        self.crs = crs

    @property
    def is_temporal(self):
        return self.axis in temporal_axes

    @property
    def is_x(self):
        return self.axis in x_axes

    @property
    def is_y(self):
        return self.axis in y_axes


class Slice(Subset):
    def __init__(self, axis, value, crs=None):
        super(Slice, self).__init__(axis, crs)
        self.value = parse_temporal(value) if self.is_temporal else float(value)


class Trim(Subset):
    def __init__(self, axis, low=None, high=None, crs=None):
        super(Trim, self).__init__(axis, crs)
        dt = parse_temporal if self.is_temporal else float_or_star
        self.low = dt(low)
        self.high = dt(high)



# subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(32,47)
# subset=long,http://www.opengis.net/def/crs/EPSG/0/4326(11,33)
# subset=phenomenonTime("2006-08-01", "2006-08-22T09:22:00Z")
# containment=overlaps containment=contains

def parse_temporal(string):
    for parser in (parse_datetime, parse_date):
        temporal = parser(string)
        if temporal:
            return temporal

    raise "invalid temporal value"

def parse_subset_kvp(string):
    from django.utils.dateparse import parse_datetime
    import re

    subset_re = re.compile(r'(\w+)(,([^(]+))?\(([^,]*)(,([^)]*))?\)')
    match = subset_re.match(string)
    if not match:
        raise

    axis = match.group(1)
    crs = match.group(3)
    
    if match.group(6) is not None:
        return Trim(axis, match.group(4), match.group(6), crs)
    else:
        return Slice(axis_label, match.group(4), crs)


def parse_subset_xml(elem):
    if elem.tag == ns_wcs("DimensionTrim"):
        return Trim(
            elem.findtext(ns_wcs("Dimension")),
            elem.findtext(ns_wcs("TrimLow")),
            elem.findtext(ns_wcs("TrimHigh"))
        )
    elif elem.tag == ns_wcs("DimensionSlice"):
        return Slice()
    

def pos_int(value):
    value = int(value)
    if value < 0:
        raise ""

containment_type = enum(("overlaps", "contains"), False)


class WCS20DescribeEOCoverageSetKVPDecoder(kvp.Decoder, SectionsMixIn):
    eo_ids      = kvp.Parameter("eoid", type=typelist(str, ","), num=1)
    subsets     = kvp.Parameter("subset", type=parse_subset_kvp, num="*")
    containment = kvp.Parameter(type=containment_type, num="?")
    count       = kvp.Parameter(type=pos_int, num="?")
    sections    = kvp.Parameter(type=typelist(upper, ","), num="?")


class WCS20DescribeEOCoverageSetXMLDecoder(xml.Decoder, SectionsMixIn):
    eo_ids      = xml.Parameter("/wcs:CoverageId/text()", num="+")
    subsets     = xml.Parameter("/wcs:DimensionTrim", type=parse_subset_xml)
    containment = xml.Parameter("/wcseo:containment/text()", type=containment_type)
    count       = xml.Parameter("/@count", type=pos_int, num="?")
    sections    = xml.Parameter("/wcseo:sections/wcseo:section/text()", num="*")

    namespaces = nsmap
