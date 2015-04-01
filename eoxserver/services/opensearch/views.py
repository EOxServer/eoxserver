from django.http import HttpResponse

from eoxserver.core import env
from eoxserver.services.opensearch.v11.description import (
    OpenSearch11DescriptionHandler
)
from eoxserver.services.opensearch.v11.search import (
    OpenSearch11SearchHandler
)


def description(request):
    """ View function for OpenSearch Descripton requests.
    """
    content, content_type = OpenSearch11DescriptionHandler(env).handle(request)
    return HttpResponse(
        content=content, content_type=content_type, status=200
    )


def search(request, collection_id=None):
    content, content_type = OpenSearch11SearchHandler(env).handle(
        request, collection_id
    )
    return HttpResponse(
        content=content, content_type=content_type, status=200
    )
