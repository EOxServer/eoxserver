#-------------------------------------------------------------------------------
# $Id$
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


from itertools import chain

from eoxserver.core import Component, implements, ExtensionPoint
from eoxserver.core.decoders import xml, kvp, typelist, upper, enum
from eoxserver.resources.coverages import models
from eoxserver.services.ows.interfaces import (
    ServiceHandlerInterface, GetServiceHandlerInterface, 
    PostServiceHandlerInterface
)
from eoxserver.services.ows.wcs.interfaces import WCSCoverageRendererInterface
from eoxserver.services.exceptions import (
    NoSuchCoverageException, OperationNotSupportedException
)
from eoxserver.services.ows.wcs.v20.util import (
    nsmap, SectionsMixIn, parse_subset_kvp, parse_subset_xml,
    parse_size_kvp, parse_resolution_kvp, Slice, Trim
)


class WCS20GetCoverageHandler(Component):
    implements(ServiceHandlerInterface)
    implements(GetServiceHandlerInterface)
    implements(PostServiceHandlerInterface)

    renderers = ExtensionPoint(WCSCoverageRendererInterface)

    service = "WCS" 
    versions = ("2.0.0", "2.0.1")
    request = "GetCoverage"

    def get_decoder(self, request):
        if request.method == "GET":
            return WCS20GetCoverageKVPDecoder(request.GET)
        elif request.method == "POST":
            return WCS20GetCoverageXMLDecoder(request.body)


    def get_renderer(self, coverage_type):
        for renderer in self.renderers:
            if issubclass(coverage_type, renderer.handles):
                return renderer

        raise OperationNotSupportedException(
            "No renderer found for coverage type '%s'." % coverage_type.__name__
        )


    def handle(self, request):
        decoder = self.get_decoder(request)

        #get parameters
        coverage_id = decoder.coverage_id
        
        try:
            coverage = models.Coverage.objects.get(identifier=coverage_id)
        except models.Coverage.DoesNotExist:
            raise NoSuchCoverageException((coverage_id,))

        coverage_type = coverage.real_type

        renderer = self.get_renderer(coverage_type)

        # translate arguments

        request_values = [
            ("service", "wcs"),
            ("version", "2.0.1"),
            ("request", "GetCoverage"),
            ("coverageid", decoder.coverage_id)
        ] + map(subset_to_kvp, decoder.subsets) \
          + map(size_to_kvp, decoder.sizes) \
          + map(resolution_to_kvp, decoder.resolutions)
        
        if decoder.rangesubset:
            request_values.append(
                ("rangesubset", ",".join(decoder.rangesubset))
            )

        if decoder.format:
            request_values.append(
                ("format", decoder.format)
            )

        if decoder.outputcrs:
            request_values.append(
                ("outputcrs", decoder.outputcrs)
            )

        if decoder.mediatype:
            request_values.append(
                ("mediatype", decoder.mediatype)
            )

        if decoder.interpolation:
            request_values.append(
                ("interpolation", decoder.interpolation)
            )

        return renderer.render(coverage, request_values)


def subset_to_kvp(subset):
    temporal_format = lambda v: ('"%s"' % isoformat(v) if v else "*")
    spatial_format = lambda v: (str(v) if v is not None else "*")

    frmt = temporal_format if subset.is_temporal else spatial_format

    if isinstance(subset, Slice):
        value = frmt(subset.value)
    else:
        value = "%s,%s" % (frmt(subset.low), frmt(subset.high))

    if subset.crs:
        return "subset", "%s,%s(%s)" % (subset.axis, subset.crs, value)
    else:
        return "subset", "%s(%s)" % (subset.axis, value)


def size_to_kvp(size):
    return "size", "%s(%d)" % (size.axis, size.value)


def resolution_to_kvp(resolution):
    return "resolution", "%s(%f)" % (resolution.axis, resolution.value)


class WCS20GetCoverageKVPDecoder(kvp.Decoder):
    coverage_id = kvp.Parameter("coverageid", num=1)
    subsets     = kvp.Parameter("subset", type=parse_subset_kvp, num="*")
    sizes       = kvp.Parameter("size", type=parse_size_kvp, num="*")
    resolutions = kvp.Parameter("resolution", type=parse_resolution_kvp, num="*")
    rangesubset = kvp.Parameter("rangesubset", type=typelist(str, ","), num="?")
    format      = kvp.Parameter("format", num="?")
    outputcrs   = kvp.Parameter("outputcrs", num="?")
    mediatype   = kvp.Parameter("mediatype", num="?")
    interpolation = kvp.Parameter("interpolation", num="?")


class WCS20GetCoverageXMLDecoder(xml.Decoder):
    coverage_id = xml.Parameter("wcs:CoverageId/text()", num=1, locator="coverageid")
    subsets     = xml.Parameter("wcs:DimensionTrim", type=parse_subset_xml, num="*")

    sizes       = xml.Parameter("TODO", type=parse_size_kvp, num="*")
    resolutions = xml.Parameter("TODO", type=parse_size_kvp, num="*")
    interpolation = xml.Parameter("TODO", type=parse_size_kvp, num="?")

    rangesubset = xml.Parameter("rangesubset", type=typelist(str, ","), num="?")

    format      = xml.Parameter("wcs:format/text()", num="?", locator="format")
    # TODO:!!!
    outputcrs   = xml.Parameter("TODO", num="?", locator="outputcrs")
    mediatype   = xml.Parameter("wcs:mediaType/text()", num="?", locator="mediatype")
    
    namespaces = nsmap
