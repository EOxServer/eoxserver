#-------------------------------------------------------------------------------
#
# WPS 1.0 base XML encoder
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
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

from eoxserver.core.util.xmltools import XMLEncoder
from eoxserver.services.ows.wps.v10.util import ns_wps

class WPS10BaseXMLEncoder(XMLEncoder):
    """ Base class of the WPS 1.0 XML response encoders. """
    content_type = "application/xml; charset=utf-8"

    def get_schema_locations(self):
        return {"wps": ns_wps.schema_location}

    def serialize(self, tree, **kwargs):
        """ Serialize a XML tree to the pair (tuple) of the XML string
        and the content type.
        """
        # override the default ASCII encoding to the standard UTF-8
        kwargs['encoding'] = 'utf-8'
        payload = super(WPS10BaseXMLEncoder, self).serialize(tree, **kwargs)
        return payload, self.content_type
