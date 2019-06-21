# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH
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
# ------------------------------------------------------------------------------

from functools import wraps
from itertools import chain

from django.http import HttpResponse, JsonResponse, QueryDict
from django.urls import reverse
from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from eoxserver.core.util.httptools import get_best_acceptable_type, get_best_match
from eoxserver.resources.coverages import models
from eoxserver.services.ows.wcs.v20.encoders import WCS20EOXMLEncoder
from eoxserver.render.coverage.objects import Coverage
from eoxserver.services.ows.wcs.v20.getcoverage import WCS20GetCoverageKVPDecoder
from eoxserver.services.ows.wcs.v20.encodings import get_encoding_extensions
from eoxserver.services.exceptions import InvalidRequestException
from eoxserver.services.subset import Subsets
from eoxserver.services.ows.wcs.v20.parameters import WCS20CoverageRenderParams
from eoxserver.services.ows.wcs.renderers import get_coverage_renderer
from eoxserver.services.result import to_http_response, ResultBuffer


class HttpResponseNotAcceptable(HttpResponse):
    status_code = 406


def collection_view(view):
    @wraps(view)
    def wrapper(request, collection_id=None):
        if collection_id:
            collection = get_object_or_404(models.Collection,
                identifier=collection_id,
            )
        else:
            collection = None
        return view(request, collection)

    return wrapper


def coverage_view(view):
    @wraps(view)
    def wrapper(request, collection_id=None, coverage_id=None):
        if collection_id:
            coverage = get_object_or_404(models.Coverage,
                collections__identifier=collection_id,
                identifier=coverage_id,
            )
        else:
            coverage = get_object_or_404(models.Coverage,
                identifier=coverage_id,
            )
        return view(request, coverage, collection_id)

    return wrapper


def conformance(request):
    # TODO: implement
    pass

def index(request):
    data = {
        "links": [{
            "href": request.build_absolute_uri(
                reverse("openapi:collections")
            ),
            "rel": "collections",
        }, {
            "href": request.build_absolute_uri(
                reverse("openapi:coverages")
            ),
            "rel": "coverages",
        }],
    }
    match = get_best_match(
        request.GET.get('f', request.META.get('HTTP_ACCEPT')),
        ['text/html', 'application/json']
    )

    if match == 'application/json':
        return JsonResponse(data)
    elif match == 'text/html':
        return render(request, 'openapi/index.html', data)

    return HttpResponseNotAcceptable()


def collections(request):
    data = {
        "collections": [{
            "id": collection.identifier,
            "title": collection.identifier,
            "description": "",
            "links": [{
                "href": request.build_absolute_uri(
                    reverse(
                        "openapi:collection:collection",
                        kwargs={"collection_id": collection.identifier}
                    )
                ),
                "rel": "collection",
            }],
        } for collection in models.Collection.objects.all()
        ]
    }
    match = get_best_match(
        request.GET.get('f', request.META.get('HTTP_ACCEPT')),
        ['text/html', 'application/json']
    )

    if match == 'application/json':
        return JsonResponse(data)
    elif match == 'text/html':
        return render(request, 'openapi/collections.html', data)

    return HttpResponseNotAcceptable()


@csrf_exempt
@collection_view
def collection(request, collection):
    # TODO: show collection metadata?
    data = {
        "identifier": collection.identifier,
        "coverages_href": reverse(
            "openapi:collection:coverages",
            kwargs={"collection_id": collection.identifier}
        )
    }
    match = get_best_match(
        request.GET.get('f', request.META.get('HTTP_ACCEPT')),
        ['text/html', 'application/json']
    )

    if match == 'application/json':
        return JsonResponse(data)
    elif match == 'text/html':
        return render(request, 'openapi/collection.html', data)

    return HttpResponseNotAcceptable()

@csrf_exempt
@collection_view
def coverages(request, collection=None):
    offset = int(request.GET.get('offset', 0))
    limit = int(request.GET.get('limit', 10))

    if collection:
        qs = base_qs = collection.coverages.all()
    else:
        qs = base_qs = models.Coverage.objects.all()

    # TODO: implement filtering of coverages etc
    qs = base_qs[offset:offset+limit]

    url = request.build_absolute_uri(
        reverse(
            "openapi:collection:coverages",
            kwargs={"collection_id": collection.identifier}
        ) if collection else reverse("openapi:coverages")
    )

    count = base_qs.count()

    data = {
        "identifier": collection.identifier if collection else None,
        "coverages": [{
                "identifier": coverage.identifier,
                "href": request.build_absolute_uri(
                    reverse(
                        "openapi:collection:coverage:coverage",
                        kwargs={
                            "collection_id": collection.identifier,
                            "coverage_id": coverage.identifier,
                        }
                    )
                ) if collection else request.build_absolute_uri(
                    reverse(
                        "openapi:coverage:coverage",
                        kwargs={
                            "coverage_id": coverage.identifier,
                        }
                    )
                )
            } for coverage in qs
        ],
        "count": count,
        "offset": offset,
        "limit": limit,
        "links": {
            "first": "%s?limit=%d&offset=0" % (url, limit) if offset > 0 else None,
            "prev": "%s?limit=%d&offset=%d" % (url, limit, max(0, offset - limit)) if offset > 0 else None,
            "next": "%s?limit=%d&offset=%d" % (url, limit, offset + limit) if offset + limit < count else None,
            "last": "%s?limit=%d&offset=%d" % (url, limit, count - limit) if offset + limit < count else None,
        }
    }

    frmt = request.GET.get('f', request.META.get('HTTP_ACCEPT'))
    match = get_best_match(
        request.GET.get('f', request.META.get('HTTP_ACCEPT')),
        ['text/html', 'application/json']
    )

    if match == 'application/json':
        return JsonResponse(data)
    elif match == 'text/html':
        return render(request, 'openapi/coverages.html', data)

    return HttpResponseNotAcceptable("%s %s" %(frmt, match))


def encode_description(coverage, frmt):
    if frmt == 'text/xml':
        render_coverage = Coverage.from_model(coverage)
        encoder = WCS20EOXMLEncoder()
        return ResultBuffer(
            encoder.serialize(
                encoder.encode_coverage_description(render_coverage),
                pretty_print=settings.DEBUG,
            ),
            content_type='text/xml'
        )
    elif frmt == 'application/json':
        # TODO: CIS 1.1 encoding
        pass


def encode_metadata(coverage, frmt):
    if frmt == 'text/xml':
        render_coverage = Coverage.from_model(coverage)
        encoder = WCS20EOXMLEncoder()
        return ResultBuffer(
            encoder.serialize(
                encoder.encode_eo_metadata(render_coverage),
                pretty_print=settings.DEBUG,
            ),
            content_type='text/xml'
        )
    elif frmt == 'application/json':
        # TODO: CIS 1.1 encoding
        pass

def encode_domainset(coverage, frmt):
    if frmt == 'text/xml':
        render_coverage = Coverage.from_model(coverage)
        encoder = WCS20EOXMLEncoder()
        return ResultBuffer(
                encoder.serialize(
                encoder.encode_domain_set(render_coverage),
                pretty_print=settings.DEBUG,
            ),
            content_type='text/xml'
        )
    elif frmt == 'application/json':
        # TODO: CIS 1.1 encoding
        pass

def encode_rangetype(coverage, frmt, rangesubset=None):
    render_coverage = Coverage.from_model(coverage)
    range_type = render_coverage.range_type
    if rangesubset:
        range_type = range_type.subset(rangesubset)

    if frmt == 'text/xml':
        encoder = WCS20EOXMLEncoder()
        return ResultBuffer(
                encoder.serialize(
                encoder.encode_range_type(range_type),
                pretty_print=settings.DEBUG,
            ),
            content_type='text/xml'
        )
    elif frmt == 'application/json':
        # TODO: CIS 1.1 encoding
        pass


def encode_rangeset(request, coverage, frmt):
    render_coverage = Coverage.from_model(coverage)
    decoder = WCS20GetCoverageKVPDecoder(request.GET)

    subsets = Subsets(decoder.subsets, crs=decoder.subsettingcrs)
    encoding_params = None

    match = get_best_acceptable_type(
        request.GET.get('f', request.META.get('HTTP_ACCEPT')),
        ['image/tiff', 'application/*']
    )

    if match:
        encoding_params = match.parameters
        encoding_params.pop('q', None)

    scalefactor = decoder.scalefactor
    scales = list(
        chain(decoder.scaleaxes, decoder.scalesize, decoder.scaleextent)
    )

    # check scales validity: ScaleFactor and any other scale
    if scalefactor and scales:
        raise InvalidRequestException(
            "ScaleFactor and any other scale operation are mutually "
            "exclusive.", locator="scalefactor"
        )

    # check scales validity: Axis uniqueness
    axes = set()
    for scale in scales:
        if scale.axis in axes:
            raise InvalidRequestException(
                "Axis '%s' is scaled multiple times." % scale.axis,
                locator=scale.axis
            )
        axes.add(scale.axis)

    params = WCS20CoverageRenderParams(
        render_coverage, subsets, decoder.rangesubset, frmt,
        decoder.outputcrs, decoder.mediatype, decoder.interpolation,
        scalefactor, scales, encoding_params or {}, request
    )

    renderer = get_coverage_renderer(params)
    return renderer.render(params)

@csrf_exempt
@coverage_view
def coverage(request, coverage, collection_id=None):
    match = get_best_acceptable_type(
        request.GET.get('f', request.META.get('HTTP_ACCEPT')),
        ['multipart/related', 'image/tiff', 'application/*', 'text/html']
    )

    if match.matches('multipart/related'):
        metadata_format = match.parameters.get('metadata', 'text/xml')
        domainset_format = match.parameters.get('domainset', 'text/xml')
        rangetype_format = match.parameters.get('rangetype', 'text/xml')
        rangeset_format = match.parameters.get('rangeset', 'text/xml')

        decoder = WCS20GetCoverageKVPDecoder(request.GET)

        metadata = encode_metadata(coverage, metadata_format)
        domainset = encode_domainset(coverage, domainset_format)
        rangetype = encode_rangetype(
            coverage, rangetype_format, decoder.rangesubset
        )
        rangeset_items = encode_rangeset(request, coverage, rangeset_format)

        return to_http_response([
            metadata, domainset, rangetype
        ] + rangeset_items)

    elif match.matches('text/html'):
        return render(request, 'openapi/coverage.html', {
            'identifier': coverage.identifier,
            'links': {
                'description': reverse(
                    "openapi:collection:coverage:description",
                    kwargs={
                        "collection_id": collection_id,
                        "coverage_id": coverage.identifier,
                    }
                ),
                'domainset': reverse(
                    "openapi:collection:coverage:domainset",
                    kwargs={
                        "collection_id": collection_id,
                        "coverage_id": coverage.identifier,
                    }
                ),
                'rangetype': reverse(
                    "openapi:collection:coverage:rangetype",
                    kwargs={
                        "collection_id": collection_id,
                        "coverage_id": coverage.identifier,
                    }
                ),
                'metadata': reverse(
                    "openapi:collection:coverage:metadata",
                    kwargs={
                        "collection_id": collection_id,
                        "coverage_id": coverage.identifier,
                    }
                ),
                'rangeset': reverse(
                    "openapi:collection:coverage:rangeset",
                    kwargs={
                        "collection_id": collection_id,
                        "coverage_id": coverage.identifier,
                    }
                ),
            } if collection_id else {
                'description': reverse(
                    "openapi:coverage:description",
                    kwargs={"coverage_id": coverage.identifier}
                ),
                'domainset': reverse(
                    "openapi:coverage:domainset",
                    kwargs={"coverage_id": coverage.identifier}
                ),
                'rangetype': reverse(
                    "openapi:coverage:rangetype",
                    kwargs={"coverage_id": coverage.identifier}
                ),
                'metadata': reverse(
                    "openapi:coverage:metadata",
                    kwargs={"coverage_id": coverage.identifier}
                ),
                'rangeset': reverse(
                    "openapi:coverage:rangeset",
                    kwargs={"coverage_id": coverage.identifier}
                ),
            }
        })

    elif match.matches('image/tiff'):
        return to_http_response(
            encode_rangeset(request, coverage, match.mime_type)
        )
    raise ""


@csrf_exempt
@coverage_view
def description(request, coverage, collection_id=None):
    match = get_best_match(
        request.GET.get('f', request.META.get('HTTP_ACCEPT')),
        ['text/xml', 'application/json']
    )
    if match:
        return to_http_response(
            [encode_description(coverage, match)]
        )
    return HttpResponseNotAcceptable()


@csrf_exempt
@coverage_view
def metadata(request, coverage, collection_id=None):
    match = get_best_match(
        request.GET.get('f', request.META.get('HTTP_ACCEPT')),
        ['text/xml', 'application/json']
    )
    if match:
        return to_http_response(
            [encode_metadata(coverage, match)]
        )
    return HttpResponseNotAcceptable()


@csrf_exempt
@coverage_view
def domainset(request, coverage, collection_id=None):
    match = get_best_match(
        request.GET.get('f', request.META.get('HTTP_ACCEPT')),
        ['text/xml', 'application/json']
    )
    if match:
        return to_http_response(
            [encode_domainset(coverage, match)]
        )
    return HttpResponseNotAcceptable()


@csrf_exempt
@coverage_view
def rangetype(request, coverage, collection_id=None):
    match = get_best_match(
        request.GET.get('f', request.META.get('HTTP_ACCEPT')),
        ['text/xml', 'application/json']
    )
    if match:
        return to_http_response(
            [encode_rangetype(coverage, match)]
        )
    return HttpResponseNotAcceptable()


@csrf_exempt
@coverage_view
def rangeset(request, coverage, collection_id=None):
    return to_http_response(
        encode_rangeset(
            request, coverage,
            request.GET.get('f', request.META.get('HTTP_ACCEPT'))
        )
    )
