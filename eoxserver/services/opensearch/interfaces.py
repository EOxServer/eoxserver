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


class ResultItemFeedLinkGenerator(object):
    """ Interface to allow extending the search items links.
    """

    def get_links(self, request, item):
        """ Returns the available additional links for this item as a list of
            2-tuples: rel and href
        """
        pass
