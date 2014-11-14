
from django.conf.urls import url

from eoxserver.webclient.views import index, configuration

urlpatterns = [
    url(r'^$', index),
    url(r'^configuration/$', configuration)
]
