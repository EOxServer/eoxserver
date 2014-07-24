#-------------------------------------------------------------------------------
# $Id$
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


class ConnectorInterface(object):
    """ Interface for connectors between `mapscript.layerObj` and associated 
        data.
    """

    def supports(self, data_items):
        """ Returns `True` if the given `data_items` are supported and 
            `False` if not.
        """

    def connect(self, coverage, data_items, layer):
        """ Connect a layer (a `mapscript.layerObj`) with the given data 
            items and coverage (a list of two-tuples: location and semantic).
        """

    def disconnect(self, coverage, data_items, layer):
        """ Performs all necessary cleanup operations.
        """

class LayerPluginInterface(object):
    """
        Interface for layer plug-in components. The component creates
        instances of factories that create `mapscript.layerObj`
        objects for coverages.
    """

    @property
    def suffixes(self):
        """ The suffixes associated with layers this factory produces. This is
            used for "specialized" layers such as "bands" or "outlines" layers.
            For factories that don't use this feature, it can be left out.
        """

    def get_layer_factory(self, layer_selection, options):
        """ Get a ``LayerFactory`` object creating the map layer for the given
            ``LayerSelection`` object.
        """

class StyleApplicatorInterface(object):
    """ Interface for style applicators.
    """

    def apply(self, coverage, data_items, layer):
        """ Apply all relevant styles.
        """
