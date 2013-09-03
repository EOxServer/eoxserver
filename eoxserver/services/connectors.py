#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
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


from os.path import join
from uuid import uuid4

from eoxserver.core import Component, implements
from eoxserver.contrib import vsi, vrt
from eoxserver.services.interfaces import MapServerConnectorInterface


class SimpleConnector(Component):
    implements(MapServerConnectorInterface)
    
    def supports(self, data_statements):
        return (
            len(data_statements) == 1 
            and data_statements[0][1].startswith("bands")
        )

    def connect(self, layer, data_statements):
        location, _ = data_statements[0]
        layer.data = location

    def disconnect(self, layer, data_statements):
        pass


class MultiFileConnector(Component):
    implements(MapServerConnectorInterface)
    
    def supports(self, data_statements):
        return (
            len(data_statements) > 1 
            and all(map(lambda d: d[1].startswith("bands"), data_statements))
        )

    def connect(self, layer, data_statements):

        vrt_doc = vrt.VRT()
        # TODO: configure vrt here

        path = join("/vsimem", uuid4().hex)
        with vsi.open(path, "w+") as f:
            vrt_doc.write(f)

        layer.data = path

    def disconnect(self, layer, data_statements):
        vsi.remove(layer.data)


class TileIndexConnector(Component):
    implements(MapServerConnectorInterface)

    def supports(self, data_statements):
        return (
            len(data_statements) == 1 and data_statements[0][1] == "tileindex"
        )

    def connect(self, layer, data_statements):
        location, semantic = data_statements[0]
        layer.tileindex = os.path.abspath(path)
        layer.tileitem = "location"

    def disconnect(self, layer, data_statements):
        pass
