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


from eoxserver.core import Component, implements
from eoxserver.backends.access import connect
from eoxserver.contrib import vsi, vrt
from eoxserver.servics.mapserver.interfaces import ConnectorInterface


class MultiFileConnector(Component):
    """ Connects multiple files containing the various bands of the coverage
        with the given layer. A temporary VRT file is used as abstraction for 
        the different band files.
    """

    implements(ConnectorInterface)
    
    def supports(self, data_items):
        # TODO: better checks
        return (
            len(data_items) > 1 
            and all(
                map(lambda d: d[1].semantic.startswith("bands"), data_items)
            )
        )

    def connect(self, coverage, data_items, layer, cache):

        # TODO: implement
        vrt_doc = vrt.VRT()
        # TODO: configure vrt here

        path = join("/vsimem", uuid4().hex)
        with vsi.open(path, "w+") as f:
            vrt_doc.write(f)

        layer.data = path

    def disconnect(self, coverage, data_items, layer, cache):
        vsi.remove(layer.data)
