from eoxserver.core import Component, implements
from eoxserver.services.opensearch.interfaces import ResultFormatInterface


class RSSResultFormat(Component):
    """ RSS result format.
    """

    implements(ResultFormatInterface)

    mimetype = "application/rss+xml"
    name = "rss"

    def encode(self, queryset):
        pass
