import re
import sys
import logging
from itertools import chain

from django.db.models import Q

from eoxserver.core import Component, implements
from eoxserver.core.config import get_eoxserver_config
from eoxserver.core.decoders import xml, kvp, typelist, upper, enum
from eoxserver.core.util.xmltools import DOMElementToXML
from eoxserver.resources.coverages import models
from eoxserver.services.interfaces import (
    OWSServiceHandlerInterface, 
    OWSGetServiceHandlerInterface, OWSPostServiceHandlerInterface
)
from eoxserver.services.ows.wcs.v20.util import nsmap, SectionsMixIn
from eoxserver.services.ows.wcs.encoders import WCS20EOAPEncoder
from eoxserver.services.ows.common.config import WCSEOConfigReader
from eoxserver.services.subset import Subsets, Trim
from eoxserver.services.exceptions import NoSuchDatasetSeriesOrCoverageException


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
        reader = WCSEOConfigReader(get_eoxserver_config())

        containment = decoder.containment

        count = decoder.count
        if reader.paging_count_default is not None:
            count = min(count, reader.paging_count_default)

        try:
            subsets = Subsets(decoder.subsets, allowed_types=Trim)
        except ValueError, e:
            raise InvalidSubset(str(e))

        inc_dss_section = decoder.section_included("DatasetSeriesDescriptions")
        inc_cov_section = decoder.section_included("CoverageDescriptions")

        if len(eo_ids) == 0:
            raise

        # fetch a list of all requested EOObjects
        available_ids = models.EOObject.objects.filter(
            identifier__in=eo_ids
        ).values_list("identifier", flat=True)

        # match the requested EOIDs against the available ones. If any are
        # requested, that are not available, raise and exit.
        failed = [ eo_id for eo_id in eo_ids if eo_id not in available_ids ]
        if failed:
            raise NoSuchDatasetSeriesOrCoverageException(failed)

        collections_qs = subsets.filter(models.Collection.objects.filter(
            identifier__in=eo_ids
        ), containment="overlaps")

        # create a set of all indirectly referenced containers by iterating
        # recursively. The containment is set to "overlaps", to also include 
        # collections that might have been excluded with "contains" but would 
        # have matching coverages inserted.

        def recursive_lookup(super_collection, collection_set):
            sub_collections = models.Collection.objects.filter(
                collections__in=[super_collection.pk]
            ).exclude(
                pk__in=map(lambda c: c.pk, collection_set)
            )
            sub_collections = subsets.filter(sub_collections, "overlaps")

            # Add all to the set
            collection_set |= set(sub_collections)

            for sub_collection in sub_collections:
                recursive_lookup(sub_collection, collection_set)

        collection_set = set(collections_qs)
        for collection in set(collection_set):
            recursive_lookup(collection, collection_set)

        collection_pks = map(lambda c: c.pk, collection_set)

        # Get all either directly referenced coverages or coverages that are
        # within referenced containers. Full subsetting is applied here.

        coverages_qs = models.Coverage.objects.filter(
            Q(identifier__in=eo_ids) | Q(collections__in=collection_pks)
        )
        coverages_qs = subsets.filter(coverages_qs, containment=containment)

        # save a reference before limits are applied to obtain the full number
        # of matched coverages.
        coverages_no_limit_qs = coverages_qs

        # compute how many (if any) coverages can be retrieved. This depends on
        # the "count" parameter and default setting. Also, if we already 
        # exceeded the count, limit the number of dataset series aswell

        if inc_dss_section:
            num_collections = len(collection_set)
        else:
            num_collections = 0

        if num_collections < count and inc_cov_section:
            coverages_qs = coverages_qs.order_by("identifier")[:count - num_collections]
        elif num_collections == count or not inc_cov_section:
            coverages_qs = []
        else:
            coverages_qs = []
            collection_set = sorted(collection_set, key=lambda c: c.identifier)[:count]

        # get a number of coverages that *would* have been included, but are not
        # because of the count parameter
        count_all_coverages = coverages_no_limit_qs.count()

        # TODO: if containment is "within" we need to check all collections again
        if containment == "within":
            collection_set = filter(lambda c: subsets.matches(c), collection_set)

        coverages = []
        dataset_series = []

        # finally iterate over everything that has been retrieved and get
        # a list of dataset series and coverages to be encoded into the response
        for eo_object in chain(coverages_qs, collection_set):
            if inc_cov_section and issubclass(eo_object.real_type, models.Coverage):
                coverages.append(eo_object.cast())
            elif inc_dss_section and issubclass(eo_object.real_type, models.DatasetSeries):
                dataset_series.append(eo_object.cast())

            else:
                # TODO: what to do here?
                pass

        # TODO: coverages should be sorted
        #coverages = sorted(coverages, ) 

        #encoder = WCS20CoverageDescriptionXMLEncoder()
        #return encoder.encode(coverages)

        # TODO: remove this at some point
        encoder = WCS20EOAPEncoder()
        return (
            DOMElementToXML(
                encoder.encodeEOCoverageSetDescription(
                    dataset_series, coverages, count_all_coverages
                )
            ), 
            "text/xml"
        )


def parse_subset_kvp(string):
    """ 

    """

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
        #TODO
    

def pos_int(value):
    value = int(value)
    if value < 0:
        raise ValueError("Negative values are not allowed.")
    return value

containment_enum = enum(
    ("overlaps", "contains"), False
)
sections_enum = enum(
    ("DatasetSeriesDescriptions", "CoverageDescriptions", "All"), False
)

class WCS20DescribeEOCoverageSetKVPDecoder(kvp.Decoder, SectionsMixIn):
    eo_ids      = kvp.Parameter("eoid", type=typelist(str, ","), num=1, locator="eoid")
    subsets     = kvp.Parameter("subset", type=parse_subset_kvp, num="*")
    containment = kvp.Parameter(type=containment_enum, num="?")
    count       = kvp.Parameter(type=pos_int, num="?", default=sys.maxint)
    sections    = kvp.Parameter(type=typelist(sections_enum, ","), num="?")


class WCS20DescribeEOCoverageSetXMLDecoder(xml.Decoder, SectionsMixIn):
    eo_ids      = xml.Parameter("/wcs:CoverageId/text()", num="+", locator="eoid")
    subsets     = xml.Parameter("/wcs:DimensionTrim", type=parse_subset_xml)
    containment = xml.Parameter("/wcseo:containment/text()", type=containment_enum, locator="containment")
    count       = xml.Parameter("/@count", type=pos_int, num="?", default=sys.maxint, locator="count")
    sections    = xml.Parameter("/wcseo:sections/wcseo:section/text()", type=sections_enum, num="*", locator="sections")

    namespaces = nsmap
