#-------------------------------------------------------------------------------
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

"""
This module contains utils for XML encoding, decoding and printing.
"""

import logging
try:
    from lxml import etree
except ImportError:
    try:
        # Python 2.5
        import xml.etree.cElementTree as etree
    except ImportError:
        try:
            # Python 2.5
            import xml.etree.ElementTree as etree
        except ImportError:
            try:
                # normal cElementTree install
                import cElementTree as etree
            except ImportError:
                try:
                    # normal ElementTree install
                    import elementtree.ElementTree as etree
                except ImportError:
                    pass # could not get etree


logger = logging.getLogger(__name__)


#-----------------------------------------------------------------------
# lxml.etree helpers
#-----------------------------------------------------------------------


class NameSpace(object):
    def __init__(self, uri, prefix=None, schema_location=None):
        self._uri = uri
        self._lxml_uri = "{%s}" % uri
        self._prefix = prefix
        self._schema_location = schema_location

    @property
    def uri(self):
        return self._uri

    @property
    def prefix(self):
        return self._prefix

    @property
    def schema_location(self):
        return self._schema_location
    
    def __call__(self, tag):
        return self._lxml_uri + tag


class NameSpaceMap(dict):
    def __init__(self, *namespaces):
        self._schema_location_dict = {}
        for namespace in namespaces:
            self.add(namespace)

    def add(self, namespace):
        self[namespace.prefix] = namespace.uri
        if namespace.schema_location:
            self._schema_location_dict[namespace.uri] = namespace.schema_location

    @property
    def schema_locations(self):
        return self._schema_location_dict


def parse(obj):
    """ Helper function to parse XML either directly from a string, or fall back
        to whatever ``lxml.etree.parse`` parses. Returns ``None`` if it could 
        not parse any XML.
    """

    tree = None
    if etree.iselement(obj):
        return obj
    elif isinstance(obj, basestring):
        try:
            tree = etree.fromstring(obj)
        except:
            pass
    else:
        try:
            tree = etree.parse(obj)
        except:
            pass

    return tree


ns_xsi = NameSpace("http://www.w3.org/2001/XMLSchema-instance", "xsi")

class XMLEncoder(object):
    """ Base class for XML encoders using lxml.etree. This class does not 
        actually provide any helpers for encoding XML in a tree structure (this
        is already done in lxml.etree), but adds tree to string serialization 
        and automatic handling of schema locations.
    """
    
    def serialize(self, tree, pretty_print=True, encoding='iso-8859-1'):
        """ Serialize a tree to an XML string. Also adds the ``schemaLocations``
            attribute to the root node.
        """
        schema_locations = self.get_schema_locations()
        tree.attrib[ns_xsi("schemaLocation")] = " ".join(
            "%s %s" % (uri, loc) for uri, loc in schema_locations.items()
        )

        return etree.tostring(
            tree, pretty_print=pretty_print, encoding=encoding
        )

    @property
    def content_type(self):
        return "text/xml"

    def get_schema_locations(self):
        """ Interface method. Returns a dict mapping namespace URIs to a network
            locations.
        """
        return {}
