from eoxserver.core import Component, implements
from eoxserver.services.opensearch.interfaces import ResultFormatInterface


class KMLResultFormat(Component):
    """ KML result format.
    """

    implements(ResultFormatInterface)

    mimetype = "application/vnd.google-earth.kml+xml"
    name = "kml"

    def encode(self, queryset):
        pass
