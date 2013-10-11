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

"""
This module contains utils for XML encoding, decoding and printing.
"""

import xml.dom.minidom
import logging

from eoxserver.core.exceptions import (
    InternalError, XMLDecoderException, XMLNodeNotFound,
    XMLNodeOccurrenceError, XMLTypeError,  XMLEncoderException
)

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


#-----------------------------------------------------------------------
# XML Encoder
#-----------------------------------------------------------------------

class XMLEncoder(object):
    """
    This is the base class for XML encoders. It is intended to be
    subclassed by concrete encoder implementations which can use its
    utility methods to compose XML documents.
    """
    
    def __init__(self, schemas=None):
        super(XMLEncoder, self).__init__()
        
        self.ns_dict = self._initializeNamespaces()
        self.dom = self._createDOM()
        self.schemas = schemas
    
    def _initializeNamespaces(self):
        """
        This method must be overridden by descendants in order to
        initialize the namespace dictionary of the object. The
        dictionary keys are interpreted as namespace prefixes whereas
        the values contain the namespace URIs.
        
        The return value is the namespace dictionary.
        """
        return {}
    
    def _createDOM(self):
        return xml.dom.minidom.getDOMImplementation().createDocument(None, None, None)
    
    def _makeElement(self, prefix, tag_name, content):
        """
        This method creates elements. It expects three arguments as
        input:
        
        * the namespace prefix of the element; this can be the empty
          string for the default namespace or unqualified names.
        * the tag name of the element
        * the content of the element
        
        If the content is
        
        * a DOM Element; it will be appended to the newly created
          element's child nodes;
        * a list of node definitions; these nodes will be created
          and then appended to the newly created element
        * some other argument, it will be converted to a string and
          be appended to the element as text value.
        
        Node definition lists contain tuples that describe the
        elements or attributes to be created and/or to be appended to
        the parent element. 3-tuples of ``(prefix, tag_name, content)``
        will be interpreted in the same way as the input parameters.
        
        If the ``prefix`` or ``tag_name`` parameters start with a ``@``
        an attribute will be created and appended to the parent element.
        If the ``prefix`` or ``tag_name`` parameters contain ``@@`` a
        text node will be created.
        
        The ``content`` parameter can contain a node definition list as
        well.
        
        Alternatively, 1-tuples containing a DOM Element can be
        specified. The DOM Element will be appended to the respective
        parent element.
        
        
        """
        
        if prefix != "":
            if prefix in self.ns_dict:
                element = self.dom.createElementNS(self.ns_dict[prefix], "%s:%s" % (prefix, tag_name))
            else:
                raise InternalError("Encoding error: unknown namespace prefix '%s'" % prefix)
        else:
            element = self.dom.createElement(tag_name)

        if isinstance(content, xml.dom.minidom.Element):
            element.appendChild(content)
        elif isinstance(content, list):
            for subcontent in content:
                if not isinstance(subcontent, tuple):
                    raise InternalError("Encoding error: expecting tuples with 1 or 3 entries")
                if len(subcontent) == 3:
                    child_prefix, child_tag_name, child_content = subcontent
                    if child_prefix == "@@" or child_tag_name == "@@":
                        element.appendChild(self.dom.createTextNode(str(child_content)))
                    elif child_prefix.startswith("@") or child_tag_name.startswith("@"):
                        attr_prefix = child_prefix.lstrip("@")
                        attr_name = child_tag_name.lstrip("@")
                        if attr_prefix != "":
                            if attr_prefix in self.ns_dict:
                                element.setAttributeNS(self.ns_dict[attr_prefix], "%s:%s" % (attr_prefix, attr_name), str(child_content))
                            else:
                                raise XMLEncoderException("Encoding error: unknown namespace prefix '%s'" % attr_prefix)
                        else:
                            element.setAttribute(attr_name, str(child_content))
                    else:
                        element.appendChild(self._makeElement(child_prefix, child_tag_name, child_content))
                elif len(subcontent) == 1:
                    element.appendChild(subcontent[0])
                else:
                    raise InternalError("Encoding error: tuples must have 1 or 3 entries")
        else:
            element.appendChild(self.dom.createTextNode(str(content)))
            
        return element

#-----------------------------------------------------------------------
# Utility functions
#-----------------------------------------------------------------------

def _getChildNamespaces(node):
    nsmap = {}
    for child in node.childNodes:
        nsmap.update(_getChildNamespaces(child))
    
    if node.attributes is not None:
        for i in range(0, node.attributes.length):
            attr = node.attributes.item(i)
            if attr.namespaceURI is not None:
                if attr.prefix is None:
                    nsmap[""] = attr.namespaceURI
                elif not attr.prefix.startswith("xml"):
                    nsmap[attr.prefix] = attr.namespaceURI
    
    if node.namespaceURI is not None:
        if node.prefix is None:
            nsmap[""] = node.namespaceURI
        elif not node.prefix.startswith("xml"):
            nsmap[node.prefix] = node.namespaceURI
    
    return nsmap

def DOMtoXML(xmldom, nsmap=None):
    """
    Takes a DOM document as input and returns the corresponding XML
    (no pretty printing) encoded as ISO-8859-1 string. This function is 
    namespace aware.
    
    The optional ``nsmap`` parameter may contain a dictionary of
    XML prefixes and namespace URIs; these namespace definitions will
    be appended to the document root elements list of xmlns attributes.
    In case it is missing, the namespaces used throughout the document
    are automatically determined and the corresponding xmlns attributes
    will be created.
    """
    
    return DOMElementToXML(xmldom.documentElement, nsmap)

def DOMElementToXML(element, nsmap=None):
    """
    This function takes a DOM element as input and returns an XML 
    document with the input element as root encoded as ISO-8859-1
    string. This function is namespace aware.
    
    The optional ``nsmap`` parameter may contain a dictionary of
    XML prefixes and namespace URIs; these namespace definitions will
    be appended to the document root elements list of xmlns attributes.
    In case it is missing, the namespaces used throughout the document
    are automatically determined and the corresponding xmlns attributes
    will be created.
    """
    
    # search the dom for namespace definitions
    if nsmap is None:
        nsmap = _getChildNamespaces(element)
    
    for prefix, uri in nsmap.items():
        if prefix == "":
            element.setAttribute("xmlns", uri)
        else:
            element.setAttribute("xmlns:%s" % prefix, uri)
    
    xml  = '<?xml version="1.0" encoding="ISO-8859-1"?>'
    
    xml += element.toxml(encoding="ISO-8859-1")
    
    return xml
