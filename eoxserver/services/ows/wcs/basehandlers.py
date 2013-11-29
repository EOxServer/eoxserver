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


"""\
This module contains a set of handler base classes which shall help to implement
a specific handler. Interface methods need to be overridden in order to work, 
default methods can be overidden.
"""

from eoxserver.core import ExtensionPoint
from eoxserver.resources.coverages import models
from eoxserver.services.result import to_http_response
from eoxserver.services.ows.wcs.parameters import WCSCapabilitiesRenderParams
from eoxserver.services.exceptions import (
    NoSuchCoverageException, OperationNotSupportedException
)
from eoxserver.services.ows.wcs.interfaces import (
    WCSCoverageDescriptionRendererInterface, WCSCoverageRendererInterface,
    WCSCapabilitiesRendererInterface
)


class WCSGetCapabilitiesHandlerBase(object):
    """ Base for Coverage description handlers.
    """

    service = "WCS"
    request = "GetCapabilities"

    renderers = ExtensionPoint(WCSCapabilitiesRendererInterface)

    def get_decoder(self, request):
        """ Interface method to get the correct decoder for this request.
        """

    def lookup_coverages(self, decoder):
        """ Default implementation of the coverage lookup. Simply returns all 
            coverages in no specific order.
        """
        return models.Coverage.objects.all()

    def get_params(self, coverages, decoder):
        """ Default method to return a render params object from the given 
            coverages/decoder.
        """

        return WCSCapabilitiesRenderParams(coverages,
            getattr(decoder, "version", None),
            getattr(decoder, "sections", None), 
            getattr(decoder, "acceptlanguages", None),
            getattr(decoder, "acceptformats", None),
            getattr(decoder, "updatesequence", None),
        )


    def get_renderer(self, params):
        """ Default implementation for a renderer retrieval.
        """
        for renderer in self.renderers:
            if renderer.supports(params):
                return renderer

        raise OperationNotSupportedException(
            "No Capabilities renderer found for the given parameters.",
            self.request
        )

    def to_http_response(self, result_set):
        """ Default result to response conversion method.
        """
        return to_http_response(result_set)


    def handle(self, request):
        """ Default handler method.
        """

        # parse the parameters
        decoder = self.get_decoder(request)

        # get the coverages
        coverages = self.lookup_coverages(decoder)

        # create the render params
        params = self.get_params(coverages, decoder)
        params.http_request = request

        # get the renderer
        renderer = self.get_renderer(params)

        # dispatch the renderer and return the response
        result_set = renderer.render(params)
        return self.to_http_response(result_set)


class WCSDescribeCoverageHandlerBase(object):
    """ Base for Coverage description handlers.
    """

    service = "WCS"
    request = "DescribeCoverage"

    renderers = ExtensionPoint(WCSCoverageDescriptionRendererInterface)

    def get_decoder(self, request):
        """ Interface method to get the correct decoder for this request.
        """

    def lookup_coverages(self, decoder):
        """ Default implementation of the coverage lookup. Returns a sorted list
            of coverage models according to the decoders `coverage_ids` 
            attribute. Raises a `NoSuchCoverageException` if any of the given
            IDs was not found in the database.
        """
        ids = decoder.coverage_ids
        coverages = sorted(
            models.Coverage.objects.filter(identifier__in=ids),
            key=(lambda coverage: ids.index(coverage.identifier))
        )

        # check correct number
        if len(coverages) < len(ids):
            available_ids = set([coverage.identifier for coverage in coverages])
            raise NoSuchCoverageException(set(ids) - available_ids)

        return coverages

    def get_params(self, coverages, decoder):
        """ Interface method to return a render params object from the given 
            coverages/decoder.
        """

    def get_renderer(self, params):
        """ Default implementation for a renderer retrieval.
        """
        for renderer in self.renderers:
            if renderer.supports(params):
                return renderer

        raise OperationNotSupportedException(
            "No suitable coverage description renderer found.",
            self.request
        )

    def to_http_response(self, result_set):
        """ Default result to response conversion method.
        """
        return to_http_response(result_set)


    def handle(self, request):
        """ Default request handling method implementation.
        """
        # parse the parameters
        decoder = self.get_decoder(request)

        # lookup the coverages
        coverages = self.lookup_coverages(decoder)

        # create the render parameters
        params = self.get_params(coverages, decoder)

        # find the correct renderer
        renderer = self.get_renderer(params)

        # render and return the response
        result_set = renderer.render(params)
        return self.to_http_response(result_set)


class WCSGetCoverageHandlerBase(object):
    """ Base for get coverage handlers.
    """

    service = "WCS"
    request = "GetCoverage"

    renderers = ExtensionPoint(WCSCoverageRendererInterface)

    def get_decoder(self, request):
        """ Interface method to get the correct decoder for this request.
        """

    def lookup_coverage(self, decoder):
        """ Default implementation of the coverage lookup. Returns the coverage
            model for the given request decoder or raises an exception if it is 
            not found.
        """
        coverage_id = decoder.coverage_id
        
        try:
            coverage = models.Coverage.objects.get(identifier=coverage_id)
        except models.Coverage.DoesNotExist:
            raise NoSuchCoverageException((coverage_id,))

        return coverage

    def get_params(self, coverages, decoder):
        """ Interface method to return a render params object from the given 
            coverages/decoder.
        """

    def get_renderer(self, params):
        """ Default implementation for a renderer retrieval.
        """
        for renderer in self.renderers:
            if renderer.supports(params):
                return renderer

        raise OperationNotSupportedException(
            "No renderer found for coverage '%s'." % params.coverage, 
            self.request
        )

    def to_http_response(self, result_set):
        """ Default result to response conversion method.
        """
        return to_http_response(result_set)

    def handle(self, request):
        """ Default handling method implementation.
        """

        # parse the request
        decoder = self.get_decoder(request)

        # get the coverage model
        coverage = self.lookup_coverage(decoder)

        # create the render params
        params = self.get_params(coverage, decoder)

        # get the renderer
        renderer = self.get_renderer(params)

        # render the coverage and return the response
        result_set = renderer.render(params)
        return self.to_http_response(result_set)
