from eoxserver.core import Component, implements
from eoxserver.core.decoders import xml, kvp, typelist, upper
from eoxserver.resources.coverages import models
from eoxserver.services.interfaces import (
    OWSServiceHandlerInterface, 
    OWSGetServiceHandlerInterface, OWSPostServiceHandlerInterface
)
from eoxserver.services.ows.wcs.v20.util import nsmap
from eoxserver.services.ows.wcs.v20.encoders import (
    WCS20CoverageDescriptionXMLEncoder
)

from eoxserver.services.ows.wcs.encoders import WCS20EOAPEncoder
from eoxserver.core.util.xmltools import DOMElementToXML


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
        coverage_ids = decoder.coverage_ids

        if len(coverage_ids) == 0:
            raise

        coverages = []
        for coverage_id in coverage_ids:
            try:
                coverages.append(
                    models.Coverage.objects.get(identifier__exact=coverage_id)
                )
            except models.Coverage.DoesNotExist:
                raise NoSuchCoverage(coveage_id)

        #encoder = WCS20CoverageDescriptionXMLEncoder()
        #return encoder.encode(coverages)

        # TODO: remove this at some point
        encoder = WCS20EOAPEncoder()
        return DOMElementToXML(encoder.encodeCoverageDescriptions(coverages)), "text/xml"





temporal_axes = ("t", "time", "phenomenontime")
x_axes = ("x", "lon", "long")
y_axes = ("y", "lat")
all_axes = temporal_axes + x_axes + y_axes


class Subset(object):
    def __init__(self, axis, crs=None):
        self.axis = axis.lower()
        if crs is not None:
            # TODO: check CRS
            pass
        self.crs = crs

    @property
    def is_temporal(self):
        return self.axis in temporal_axes


class Slice(Subset):
    def __init__(self, axis, value, crs=None):
        super(Slice, self).__init__(axis, crs)
        self.value = parse_temporal(value) if self.is_temporal else float(value)


class Trim(Subset):
    def __init__(self, axis, low=None, high=None, crs=None):
        super(Trim, self).__init__(axis, crs)
        dt = parse_temporal if self.is_temporal else float
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
    if elem.tag == ns_wcseo("DimensionTrim"):
        return Trim(
            elem.find(ns_wcseo("Dimension")),
            elem.find(ns_wcseo("TrimLow")),
            elem.find(ns_wcseo("TrimHigh"))
        )
    elif elem.tag == ns_wcseo("DimensionSlice"):
        return Slice()
    


class WCS20DescribeEOCoverageSetKVPDecoder(kvp.Decoder):
    eo_ids = kvp.Parameter("coverageid", type=typelist(str, ","), num=1)
    sections = 
    subsets = kvp.Parameter("subset", type=parse_subset_kvp, num="*")



class WCS20DescribeEOCoverageSetXMLDecoder(xml.Decoder):
    eo_ids = xml.Parameter("/wcs:CoverageId/text()", num="+")
    subsets = xml.Parameter("/wcseo:DimensionTrim", type=parse_subset_xml)

    namespaces = nsmap
