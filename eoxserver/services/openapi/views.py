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

from django.http import HttpResponse, JsonResponse, QueryDict
from django.urls import reverse
from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator

from eoxserver.resources.coverages import models
from eoxserver.services.ows.wcs.v20.encoders import WCS20EOXMLEncoder
from eoxserver.render.coverage.objects import Coverage


def collection_view(view):
    @wraps(view)
    def wrapper(request, collection_id):
        collection = get_object_or_404(models.Collection,
            identifier=collection_id,
        )
        return view(request, collection)

    return wrapper


def coverage_view(view):
    @wraps(view)
    def wrapper(request, collection_id, coverage_id):
        coverage = get_object_or_404(models.Coverage,
            collections__identifier=collection_id,
            identifier=coverage_id,
        )
        return view(request, coverage)

    return wrapper


def conformance(request):
    pass


def collections(request):
    data = {
        "collections": [{
            "identifier": collection.identifier,
            "href": request.build_absolute_uri(
                reverse(
                    "openapi:collection:collection",
                    kwargs={"collection_id": collection.identifier}
                )
            )
        } for collection in models.Collection.objects.all()
        ]
    }
    accept = request.META.get('HTTP_ACCEPT', 'text/html').split(',')
    if 'text/html' in accept:
        return render(request, 'openapi/index.html', data)
    elif 'application/json' in accept:
        return JsonResponse(data)
    raise


@collection_view
def collection(request, collection):
    # TODO: show collection metadata?
    data = {
        "identifier": collection.identifier
    }

    accept = request.META.get('HTTP_ACCEPT', 'text/html').split(',')
    if 'text/html' in accept:
        return render(request, 'openapi/collection.html', data)
    elif 'application/json' in accept:
        return JsonResponse(data)


@collection_view
def coverages(request, collection):
    offset = int(request.GET.get('offset', 0))
    limit = int(request.GET.get('limit', 10))

    qs = base_qs = collection.coverages.all()

    # TODO: implement filtering of coverages etc
    qs = base_qs[offset:offset+limit]

    url = request.build_absolute_uri(
        reverse(
            "openapi:collection:coverages",
            kwargs={"collection_id": collection.identifier}
        )
    )

    count = base_qs.count()

    data = {
        "identifier": collection.identifier,
        "coverages": [{
                "identifier": coverage.identifier,
                "href": reverse(
                    "openapi:collection:coverage:coverage",
                    kwargs={
                        "collection_id": collection.identifier,
                        "coverage_id": coverage.identifier,
                    }
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

    accept = request.META.get('HTTP_ACCEPT', 'text/html').split(',')
    if 'text/html' in accept:
        return render(request, 'openapi/coverages.html', data)
    elif 'application/json' in accept:
        return JsonResponse(data)


@coverage_view
def coverage(request, coverage):

    return JsonResponse({
        "identifier": coverage.identifier
    })


@coverage_view
def metadata(request, coverage):
    pass


@coverage_view
def domainset(request, coverage):
    pass


@coverage_view
def rangetype(request, coverage):
    render_coverage = Coverage.from_model(coverage)
    encoder = WCS20EOXMLEncoder()
    return HttpResponse(
        encoder.serialize(
            encoder.encode_range_type(render_coverage.range_type),
            pretty_print=True,
        ),
        content_type='text/plain'
    )


@coverage_view
def rangeset(request, coverage):
    pass
