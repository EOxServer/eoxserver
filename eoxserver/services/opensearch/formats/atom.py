from eoxserver.core import Component, implements
from eoxserver.services.opensearch.interfaces import ResultFormatInterface


class AtomResultFormat(Component):
    """ Atom result format.
    """

    implements(ResultFormatInterface)

    mimetype = "application/atom+xml"
    name = "atom"

    def encode(self, queryset):
        pass
