from django.conf import settings


from django.conf.urls import include, url
from django.contrib import admin
from django.conf.urls.static import static

from eoxserver.services.opensearch.urls import urlpatterns as opensearch
from eoxserver.webclient.urls import urlpatterns as webclient
from eoxserver.views import index


admin.autodiscover()


urlpatterns = [
    url(r'^$', index),
    url(r'^ows', include("eoxserver.services.urls")),
    url(r'^opensearch/', include(opensearch)),

    # enable the client
    url(r'^client/', include(webclient)),

    # Enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    # Enable the admin:
    url(r'^admin/', include(admin.site.urls)),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
