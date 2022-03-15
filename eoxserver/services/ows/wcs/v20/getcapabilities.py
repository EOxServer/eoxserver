# -----------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# -----------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# -----------------------------------------------------------------------------

from itertools import chain

from eoxserver.core.decoders import xml, kvp, typelist, lower
from eoxserver.resources.coverages import models
from eoxserver.render.coverage.objects import from_model
from eoxserver.services.ows.wcs.basehandlers import (
    WCSGetCapabilitiesHandlerBase
)
from eoxserver.services.ows.wcs.v20.util import nsmap, SectionsMixIn
from eoxserver.services.ows.wcs.v20.parameters import (
    WCS20CapabilitiesRenderParams
)
from eoxserver.services.ecql import parse, to_filter
from eoxserver.services import filters


class WCS20GetCapabilitiesHandler(WCSGetCapabilitiesHandlerBase):
    versions = ("2.0.0", "2.0.1")
    methods = ['GET', 'POST']

    additional_parameters = {
        'cql': None
    }

    def get_decoder(self, request):
        if request.method == "GET":
            return WCS20GetCapabilitiesKVPDecoder(request.GET)
        elif request.method == "POST":
            return WCS20GetCapabilitiesXMLDecoder(request.body)

    def lookup_coverages(self, decoder):
        sections = decoder.sections
        inc_coverages = (
            "all" in sections or "contents" in sections or
            "coveragesummary" in sections
        )
        inc_dataset_series = (
            "all" in sections or "contents" in sections or
            "datasetseriessummary" in sections
        )

        if inc_coverages:
            cql_text = decoder.cql
            if cql_text:
                qs = models.EOObject.objects.all()
                mapping, mapping_choices = filters.get_field_mapping_for_model(
                    models.Coverage  # TODO: allow mapping to Mosaic as-well?
                )
                ast = parse(cql_text)
                filter_expressions = to_filter(ast, mapping, mapping_choices)
                qs = qs.filter(filter_expressions)

            else:
                qs = models.EOObject.objects.filter(
                    service_visibility__service='wcs',
                    service_visibility__visibility=True
                )

            qs = qs.order_by('id').select_subclasses(
                models.Coverage, models.Mosaic
            )

            coverages = [
                from_model(coverage)
                for coverage in qs
            ]
        else:
            coverages = []

        if inc_dataset_series:
            cql_text = decoder.datasetseriescql
            if cql_text:
                qs = models.EOObject.objects.all()
                mapping, mapping_choices = filters.get_field_mapping_for_model(
                    qs.model  # TODO: mapping to Collection/Product would be better
                )
                ast = parse(cql_text)
                filter_expressions = to_filter(ast, mapping, mapping_choices)
            else:
                filter_expressions = {}

            dataset_series = chain(
                models.Collection.objects.exclude(
                    service_visibility__service='wcs',
                    service_visibility__visibility=False
                ).filter(**filter_expressions).only(
                    "identifier", "begin_time", "end_time", "footprint"
                ),
                models.Product.objects.filter(
                    service_visibility__service='wcs',
                    service_visibility__visibility=True
                ).filter(**filter_expressions).only(
                    "identifier", "begin_time", "end_time", "footprint"
                ),
            )

        else:
            dataset_series = models.EOObject.objects.none()

        return coverages, dataset_series

    def get_params(self, models, decoder):
        coverages, dataset_series = models
        return WCS20CapabilitiesRenderParams(
            coverages, dataset_series, decoder.sections,
            decoder.acceptlanguages, decoder.acceptformats,
            decoder.updatesequence
        )


class WCS20GetCapabilitiesKVPDecoder(kvp.Decoder, SectionsMixIn):
    sections            = kvp.Parameter(type=typelist(lower, ","), num="?", default=["all"])
    updatesequence      = kvp.Parameter(num="?")
    acceptversions      = kvp.Parameter(type=typelist(str, ","), num="?")
    acceptformats       = kvp.Parameter(type=typelist(str, ","), num="?", default=["text/xml"])
    acceptlanguages     = kvp.Parameter(type=typelist(str, ","), num="?")
    cql                 = kvp.Parameter(num="?")
    datasetseriescql    = kvp.Parameter(num="?")


class WCS20GetCapabilitiesXMLDecoder(xml.Decoder, SectionsMixIn):
    sections            = xml.Parameter("ows:Sections/ows:Section/text()", num="*", default=["all"])
    updatesequence      = xml.Parameter("@updateSequence", num="?")
    acceptversions      = xml.Parameter("ows:AcceptVersions/ows:Version/text()", num="*")
    acceptformats       = xml.Parameter("ows:AcceptFormats/ows:OutputFormat/text()", num="*", default=["text/xml"])
    acceptlanguages     = xml.Parameter("ows:AcceptLanguages/ows:Language/text()", num="*")

    # TODO: find suitable place in XML to pass CQL queries
    cql                 = None
    datasetseriescql    = None

    namespaces = nsmap
