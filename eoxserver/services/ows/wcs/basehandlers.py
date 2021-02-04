# -----------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# -----------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
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

"""\
This module contains a set of handler base classes which shall help to
implement a specific handler. Interface methods need to be overridden in order
to work, default methods can be overidden.
"""
from django.db.models import Q

from eoxserver.resources.coverages import models
from eoxserver.services.result import to_http_response
from eoxserver.services.ows.wcs.parameters import WCSCapabilitiesRenderParams
from eoxserver.services.exceptions import (
    NoSuchCoverageException, OperationNotSupportedException
)
from eoxserver.services.ows.wcs.renderers import (
    get_capabilities_renderer, get_coverage_description_renderer,
    get_coverage_renderer,
)
from eoxserver.render.coverage.objects import Coverage, Mosaic
from eoxserver.services.ecql import parse, to_filter
from eoxserver.services import filters


class WCSGetCapabilitiesHandlerBase(object):
    """ Base for Coverage description handlers.
    """

    service = "WCS"
    request = "GetCapabilities"

    index = 0

    def get_decoder(self, request):
        """ Interface method to get the correct decoder for this request.
        """

    def lookup_coverages(self, decoder):
        """ Default implementation of the coverage lookup. Simply returns all
            coverages in no specific order.
        """

        cql_text = decoder.cql
        if cql_text:
            qs = models.EOObject.objects.all()
            mapping, mapping_choices = filters.get_field_mapping_for_model(
                qs.model
            )
            ast = parse(cql_text)
            filter_expressions = to_filter(ast, mapping, mapping_choices)
            qs = qs.filter(filter_expressions)

        else:
            qs = models.EOObject.objects.filter(
                Q(
                    service_visibility__service='wcs',
                    service_visibility__visibility=True
                ) | Q(  # include mosaics with a Grid
                    mosaic__isnull=False,
                    mosaic__grid__isnull=False,
                    service_visibility__service='wcs',
                    service_visibility__visibility=True
                )
            )

        return qs.order_by(
            "identifier"
        ).select_subclasses(models.Coverage, models.Mosaic)

    def get_params(self, coverages, decoder):
        """ Default method to return a render params object from the given
            coverages/decoder.
        """

        return WCSCapabilitiesRenderParams(
            coverages,
            getattr(decoder, "version", None),
            getattr(decoder, "sections", None),
            getattr(decoder, "acceptlanguages", None),
            getattr(decoder, "acceptformats", None),
            getattr(decoder, "updatesequence", None),
        )

    def get_renderer(self, params):
        """ Default implementation for a renderer retrieval.
        """
        renderer = get_capabilities_renderer(params)
        if not renderer:
            raise OperationNotSupportedException(
                "No Capabilities renderer found for the given parameters.",
                self.request
            )
        return renderer

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

    index = 1

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

        # qs = models.Coverage.objects.filter(identifier__in=ids)
        qs = models.EOObject.objects.filter(
            identifier__in=ids,
        ).filter(
            Q(coverage__isnull=False) | Q(mosaic__isnull=False)
        ).select_subclasses()

        objects = sorted(
            qs,
            key=(lambda coverage: ids.index(coverage.identifier))
        )

        # check correct number
        if len(objects) < len(ids):
            available_ids = set([coverage.identifier for coverage in objects])
            raise NoSuchCoverageException(set(ids) - available_ids)

        return [
            Coverage.from_model(obj)
            if isinstance(obj, models.Coverage) else Mosaic.from_model(obj)
            for obj in objects
        ]

    def get_params(self, coverages, decoder):
        """ Interface method to return a render params object from the given
            coverages/decoder.
        """

    def get_renderer(self, params):
        """ Default implementation for a renderer retrieval.
        """

        renderer = get_coverage_description_renderer(params)
        if not renderer:
            raise OperationNotSupportedException(
                "No suitable coverage description renderer found.",
                self.request
            )
        return renderer

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

    index = 10

    def get_decoder(self, request):
        """ Interface method to get the correct decoder for this request.
        """

    def get_subsets(self, decoder):
        """ Interface method to get the subsets for this request.
        """

    def lookup_coverage(self, decoder, subsets):
        """ Default implementation of the coverage lookup. Returns the coverage
            model for the given request decoder or raises an exception if it is
            not found.
        """
        coverage_id = decoder.coverage_id

        try:
            obj = models.EOObject.objects.select_subclasses(
                models.Coverage, models.Mosaic
            ).get(
                Q(identifier=coverage_id) & (
                    Q(coverage__isnull=False) | Q(mosaic__isnull=False)
                )
            )
        except models.EOObject.DoesNotExist:
            raise NoSuchCoverageException((coverage_id,))

        if isinstance(obj, models.Coverage):
            return Coverage.from_model(obj)
        else:
            coverages = obj.coverages.all().order_by("begin_time")
            if subsets:
                subset_polygon = subsets.bounding_polygon(
                    Mosaic.from_model(obj, [])
                )
                coverages = coverages.filter(
                    footprint__intersects=subset_polygon
                )
            return Mosaic.from_model(obj, coverages)

    def get_params(self, coverages, decoder, request):
        """ Interface method to return a render params object from the given
            coverages/decoder.
        """

    def get_renderer(self, params):
        """ Default implementation for a renderer retrieval.
        """
        renderer = get_coverage_renderer(params)
        if not renderer:
            raise OperationNotSupportedException(
                "No renderer found for coverage '%s'."
                % params.coverage.identifier,
                self.request
            )
        return renderer

    def to_http_response(self, result_set):
        """ Default result to response conversion method.
        """
        return to_http_response(result_set)

    def handle(self, request):
        """ Default handling method implementation.
        """

        # parse the request
        decoder = self.get_decoder(request)

        # get the decoded subsets
        subsets = self.get_subsets(decoder)

        # get the coverage model
        coverage = self.lookup_coverage(decoder, subsets)

        # create the render params
        params = self.get_params(coverage, decoder, request)

        # get the renderer
        renderer = self.get_renderer(params)

        # render the coverage and return the response
        result_set = renderer.render(params)
        return self.to_http_response(result_set)
