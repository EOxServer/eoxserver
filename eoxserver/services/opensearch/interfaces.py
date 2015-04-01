

class SearchExtensionInterface(object):
    """
    """

    @property
    def namespace(self):
        """
        """

    @property
    def schema(self):
        """
        """

    def filter(self, queryset, parameters):
        """
        """


class ResultFormatInterface(object):
    """
    """

    @property
    def mimetype(self):
        """ The mime type associated with the format.
        """

    @property
    def name(self):
        """ The name of the result format. This name is used in the description
            document and as a request parameter.
        """

    def encode(self, queryset):
        """ Encode the given
            :class:`QuerySet <django.contrib.gis.db.queryset.QuerySet>`
            and returns a
            :class:`ResultItem <eoxserver.services.result.ResultItem>` containing
            the encoded result.
        """
