from django.conf.urls import url

from eoxserver.services.opensearch.views import description, search

urlpatterns = [
    url(r'^$', description, name='opensearch_description'),
    url(r'^(?P<collection_id>)$', search, name='opensearch_search')
]
