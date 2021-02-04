from django.conf import settings

try:
    from django.conf.urls import include, url as re_path
except ImportError:
    from django.urls import include, re_path
from django.contrib import admin
from django.conf.urls.static import static

from eoxserver.services.opensearch.urls import urlpatterns as opensearch
from eoxserver.webclient.urls import urlpatterns as webclient
from eoxserver.views import index


admin.autodiscover()


urlpatterns = [
    re_path(r'^$', index),
    re_path(r'^ows', include("eoxserver.services.urls")),
    re_path(r'^opensearch/', include('eoxserver.services.opensearch.urls')),

    # enable the client
    re_path(r'^client/', include('eoxserver.webclient.urls')),

    # Enable admin documentation:
    re_path(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    # Enable the admin:
    re_path(r'^admin/', admin.site.urls),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
