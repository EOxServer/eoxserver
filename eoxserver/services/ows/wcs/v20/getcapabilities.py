#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
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

from django.db.models import Q

from eoxserver.core import Component, implements
from eoxserver.core.decoders import xml, kvp, typelist, lower
from eoxserver.resources.coverages import models
from eoxserver.render.coverage.objects import from_model
from eoxserver.services.ows.interfaces import (
    ServiceHandlerInterface, GetServiceHandlerInterface,
    PostServiceHandlerInterface, VersionNegotiationInterface
)
from eoxserver.services.ows.wcs.basehandlers import (
    WCSGetCapabilitiesHandlerBase
)
from eoxserver.services.ows.wcs.v20.util import nsmap, SectionsMixIn
from eoxserver.services.ows.wcs.v20.parameters import (
    WCS20CapabilitiesRenderParams
)


class WCS20GetCapabilitiesHandler(WCSGetCapabilitiesHandlerBase, Component):
    implements(ServiceHandlerInterface)
    implements(GetServiceHandlerInterface)
    implements(PostServiceHandlerInterface)
    implements(VersionNegotiationInterface)

    versions = ("2.0.0", "2.0.1")
    methods = ['GET', 'POST']

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
            qs = models.EOObject.objects.filter(
                service_visibility__service='wcs',
                service_visibility__visibility=True
            ).order_by('id').select_subclasses(models.Coverage, models.Mosaic)

            coverages = [
                from_model(coverage)
                for coverage in qs
            ]
        else:
            coverages = []

        if inc_dataset_series:
            dataset_series_qs = models.EOObject.objects.filter(
                Q(
                    product__isnull=False,
                    service_visibility__service='wcs',
                    service_visibility__visibility=True
                ) | Q(
                    collection__isnull=False
                )
            ).exclude(
                collection__isnull=False,
                service_visibility__service='wcs',
                service_visibility__visibility=False
            )

            # reduce data transfer by only selecting required elements
            dataset_series_qs = dataset_series_qs.only(
                "identifier", "begin_time", "end_time", "footprint"
            )

        else:
            dataset_series_qs = models.EOObject.objects.none()

        return coverages, dataset_series_qs

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


class WCS20GetCapabilitiesXMLDecoder(xml.Decoder, SectionsMixIn):
    sections            = xml.Parameter("ows:Sections/ows:Section/text()", num="*", default=["all"])
    updatesequence      = xml.Parameter("@updateSequence", num="?")
    acceptversions      = xml.Parameter("ows:AcceptVersions/ows:Version/text()", num="*")
    acceptformats       = xml.Parameter("ows:AcceptFormats/ows:OutputFormat/text()", num="*", default=["text/xml"])
    acceptlanguages     = xml.Parameter("ows:AcceptLanguages/ows:Language/text()", num="*")

    namespaces = nsmap
