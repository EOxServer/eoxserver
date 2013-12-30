#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
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


class WMSCapabilitiesRendererInterface(object):
    """ Interface for WMS compatible capabilities renderers.
    """

    def render(self, collections, coverages, request_values):
        """ Render a capabilities document, containing metadata of the given 
            collections and coverages.
        """


class WMSMapRendererInterface(object):
    """ Interface for WMS compatible map renderers.
    """

    @property
    def suffixes(self):
        """ Return a list of supported layer suffixes for this renderer.
        """

    def render(self, layer_groups, request_values, **options):
        """ Render the given layer hierarchy with the provided request values 
            and further options.

            ``options`` contains relevant options such as specified bands.
        """

class WMSFeatureInfoRendererInterface(object):
    """ Interface for WMS compatible feature info renderers.
    """

    @property
    def suffixes(self):
        """ Return a list of supported layer suffixes for this renderer.
        """

    def render(self, layer_groups, request_values, **options):
        """ Render the given layer hierarchy with the provided request values 
            and further options.

            ``options`` contains relevant options such as specified bands.
        """

class WMSLegendGraphicRendererInterface(object):
    """ Interface for WMS compatible legend graphic renderers.
    """

    @property
    def suffixes(self):
        """ Return a list of supported layer suffixes for this renderer.
        """

    def render(self, collection, eo_object, request_values, **options):
        """ Render the given collection and coverage with the provided request
            values and further options.

            ``options`` contains relevant options such as specified bands.
        """

