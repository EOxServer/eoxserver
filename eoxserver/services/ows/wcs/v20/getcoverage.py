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


from eoxserver.core import Component, implements, ExtensionPoint
from eoxserver.core.decoders import xml, kvp, typelist, upper, enum
from eoxserver.resources.coverages import models
from eoxserver.services.interfaces import (
    OWSServiceHandlerInterface, 
    OWSGetServiceHandlerInterface, OWSPostServiceHandlerInterface,
    CoverageRendererInterface
)
from eoxserver.services.exceptions import NoSuchCoverageException
from eoxserver.services.ows.wcs.v20.util import (
    nsmap, SectionsMixIn, parse_subset_kvp, parse_subset_xml,
    parse_size_kvp, parse_resolution_kvp
)

class WCS20GetCoverageHandler(Component):
    implements(OWSServiceHandlerInterface)
    implements(OWSGetServiceHandlerInterface)
    implements(OWSPostServiceHandlerInterface)

    renderers = ExtensionPoint(CoverageRendererInterface)

    service = "WCS" 
    versions = ("2.0.0", "2.0.1")
    request = "GetCoverage"

    def get_decoder(self, request):
        if request.method == "GET":
            return WCS20GetCoverageKVPDecoder(request.GET)
        elif request.method == "POST":
            return WCS20GetCoverageXMLDecoder(request.body)


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
        if not renderer:
            raise Exception() # TODO: error message


        # translate arguments
        kwargs = {
            "subsets": decoder.subsets,
            "sizes": decoder.sizes,
            "resolutions": decoder.resolutions,
            "rangesubset": decoder.rangesubset,
            "format": decoder.format,
            "outputcrs": decoder.outputcrs,
            "mediatype": decoder.mediatype,
            "interpolation": decoder.interpolation
        }

        try:
            return renderer.render(coverage, **kwargs) # TODO: pass arguments
        except Exception, e:
            # TODO: ?
            raise



    def get_renderer(self, coverage_type):
        for renderer in self.renderers:
            if issubclass(coverage_type, renderer.handles):
                return renderer

        raise "No renderer found for coverage type '%s'." % coverage_type.__name__


class WCS20GetCoverageKVPDecoder(kvp.Decoder):
    coverage_id = kvp.Parameter("coverageid", num=1)
    subsets     = kvp.Parameter("subset", type=parse_subset_kvp, num="*")
    sizes       = kvp.Parameter("size", type=parse_size_kvp, num="*")
    resolutions = kvp.Parameter("resolution", type=parse_resolution_kvp, num="*")
    rangesubset = kvp.Parameter("rangesubset", type=typelist(str, ","), num="?")
    format      = kvp.Parameter("format", num="?")
    outputcrs   = kvp.Parameter("outputcrs", num="?")
    mediatype   = kvp.Parameter("mediatype", num="?")
    interpolation = kvp.Parameter("mediatype", num="?")


class WCS20GetCoverageXMLDecoder(xml.Decoder):
    coverage_id = xml.Parameter("/wcs:CoverageId/text()", num=1, locator="coverageid")
    subsets     = xml.Parameter("/wcs:DimensionTrim", type=parse_subset_xml, num="*")

    rangesubset = kvp.Parameter("rangesubset", type=typelist(str, ","), num="?")

    format      = xml.Parameter("/wcs:format/text()", num="?", locator="format")
    # TODO:!!!
    outputcrs   = xml.Parameter("/wcs:mediaType/text()", num="?", locator="outputcrs")
    mediatype   = xml.Parameter("/wcs:mediaType/text()", num="?", locator="mediatype")
    
    namespaces = nsmap
