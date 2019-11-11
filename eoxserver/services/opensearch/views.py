#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH
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


from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from eoxserver.services.opensearch.v11.description import (
    OpenSearch11DescriptionHandler
)
from eoxserver.services.opensearch.v11.search import (
    OpenSearch11SearchHandler
)


@csrf_exempt
def description(request, collection_id=None):
    """ View function for OpenSearch Description requests.
    """
    content, content_type = OpenSearch11DescriptionHandler().handle(
        request, collection_id
    )
    return HttpResponse(
        content=content, content_type=content_type, status=200
    )


@csrf_exempt
def search(request, collection_id=None, format_name=None):
    content, content_type = OpenSearch11SearchHandler().handle(
        request, collection_id, format_name
    )
    return HttpResponse(
        content=content, content_type=content_type, status=200
    )
