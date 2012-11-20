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
from eoxserver.core.util.decoders import Decoder, DecoderInterface

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
# XML decoding utilities used by XMLDecoder
#----------------------------------------------------------------------- 

class XPath(object):
    """
    This class represents an XPath expression. It provides methods
    for decoding an encoding XPath expressions as well as looking up the
    specified nodes in an XML structure.
    
    The constructor accepts either an XPath expression or a list of
    locators as generated by :meth:`XPathExprToList` as input.
    
    Note that this implementation supports only a small subset of
    XPath expressions, namely parts of the abbreviated notation.
    
    .. productionlist::
       xpath_expr: "/" | ["/"] locator_list
       locator_list: (element_locator "/")* node_locator
       node_locator: element_locator | attribute_locator
       element_locator: locator | "*"
       attribute_locator: "@" locator | "@*"
       locator: prefix ":" localname | ["{" namespaceuri "}"] localname
       prefix: NCName
       localname: NCName
       namespaceuri: URI | "*"
    """
    
    def __init__(self, init_data):
        if isinstance(init_data, list):
            self.xpath = init_data
            self.xpath_expr = self.listToXPathExpr(init_data)
        else:
            self.xpath_expr = str(init_data)
            self.xpath = self.XPathExprToList(init_data)

    @classmethod
    def XPathExprToList(cls, xpath_expr):
        """
        This method converts an XPath expression to a list of locators.
        """
        
        d , e0 , e1 = "/" , "{" , "}"

        tmp   = xpath_expr
        xpath = []

        if tmp[0] == d :    # leading slash 
            xpath.append(d)
            tmp = tmp[1:]

        while tmp :         # splitting path but preserving namespaces 
            head0 = ""
            if tmp[0] == e0 :
                idx = tmp.find(e1)
                if ( idx > 0 ) :
                    head0 = tmp[:(idx+1)]
                    tmp   = tmp[(idx+1):]
                else :
                    head0 = tmp
                    tmp   = ""
            head1, _, tmp = tmp.partition(d)
            xpath.append( head0 + head1 )

        return xpath

    @classmethod
    def listToXPathExpr(cls, xpath):
        """
        This method converts a list of locators to an XPath expression.
        """
        
        if xpath[0] == "/":
            xpath_expr = "/%s" % "/".join(xpath[1:])
        else:
            xpath_expr = "/".join(xpath)
    
        return xpath_expr
    
    @classmethod
    def reverse(cls, node):
        """
        Generate an absolute XPath expression for the given node from
        the DOM.
        """
        
        parent = node.parentNode
        
        if isinstance(parent, xml.dom.minidom.Document):
            return cls("/")
        else:
            if not node.prefix:
                name = node.localName
            else:
                name = "%s:%s" % (node.prefix, node.localName)
            
            if node.nodeType == xml.dom.minidom.Node.ATTRIBUTE_NODE:
                name = "@%s" % name                
            
            return cls.reverse(parent).append(cls(name))

    def isAbsolute(self):
        """
        Returns ``True`` if the XPath expression is absolute, ``False``
        otherwise.
        """
        
        return self.xpath[0] == "/"
    
    def append(self, other):
        """
        Append another XPath expression and return the result.
        """
        
        if not other.isAbsolute():
            xpath = self.xpath
            xpath.extend(other.xpath)
            
            return self.__class__(xpath)
        else:
            return other

    def _getNodesXPath(self, element, xpath):
        logger.debug("Element: {%s}%s XPath: %s" % (element.namespaceURI, element.localName, str(xpath)))
        
        if len(xpath) == 0:
            return [element]
        else:
            locator = xpath[0]
            
            if locator == "/":
                if isinstance(element.parentNode, xml.dom.minidom.Document):
                    return self._getNodesXPath(element, xpath[1:])
                else:
                    raise InternalError("Absolute XPath expressions can only be applied to the document root element.")
            elif locator == "*":
                nodes = []
                
                child_elements = filter(lambda node: isinstance(node, xml.dom.minidom.Element), element.childNodes)
                for child_element in child_elements:
                    nodes.extend(self._getNodesXPath(child_element, xpath[1:]))
                    
                return nodes
            elif locator == "@*":
                if len(xpath) > 1:
                    raise InternalError("Attribute locators must be the final node in XPath expressions")
                else:
                    attrs = element.attributes
                    if attrs is None:
                        return []
                    else:
                        return list(attrs)
            elif locator.startswith("@"):
                if len(xpath) > 1:
                    raise InternalError("Attribute locators must be the final node in XPath expressions")
                else:
                    attr = element.getAttributeNode(locator.lstrip("@"))
                    if attr is None:
                        return []
                    else:
                        return [attr]
            else:

                # split name and namespace 
                if locator.startswith("{") : 
                    namespace , lname = locator[1:].split("}")[:2]
                else : 
                    namespace , lname = "" , locator 
               
                nodes = []
                
                # filter child elements 

                child_elements = filter(lambda node: isinstance(node, xml.dom.minidom.Element) , element.childNodes )

                if namespace == ""  : # unqualified match 
                    child_elements = filter(lambda node: node.tagName == lname , child_elements )

                else : # qualified match 
                    if namespace == "*" and lname == "*" : 
                        pass 
                    elif namespace == "*" :
                        child_elements = filter( lambda node: node.localName == lname , child_elements ) 
                    elif lname == "*" :
                        child_elements = filter( lambda node: node.namespaceURI == namespace , child_elements ) 
                    else : 
                        child_elements = filter( lambda node: node.localName == lname and node.namespaceURI == namespace , child_elements )

                # process the matched elements 
                for child_element in child_elements:
                    nodes.extend(self._getNodesXPath(child_element, xpath[1:]))
                
                return nodes
                
    def getNodes(self, context_element):
        """
        Return all the nodes designated by the XPath expression.
        """
        
        return self._getNodesXPath(context_element, self.xpath)

    def getNodeType(self):
        """
        Returns ``"element"`` if the XPath expression points to an
        element, or ``"attribute"`` if it points to an attribute.
        """
        
        if self.xpath[-1].startswith("@"):
            return "attribute"
        else:
            return "element"

class XMLNode(object):
    def __init__(self, xpath_expr, min_occ=1, max_occ=1):
        self.xpath = XPath(xpath_expr)
        self.min_occ = min_occ
        self.max_occ = max_occ
    
    def isMultiple(self):
        return self.max_occ > 1
    
    def _getNodeValues(self, nodes):
        return []

    def getValue(self, context_element):
        nodes = self.xpath.getNodes(context_element)
        
        if len(nodes) >= self.min_occ and len(nodes) <= self.max_occ:
            values = self._getNodeValues(nodes)

            if self.isMultiple():
                return values
            else:
                if len(values) == 1:
                    return values[0]
                else:
                    return None
        elif len(nodes) == 0:
            raise XMLNodeNotFound("Node '%s' not found." % XPath.reverse(context_element).append(self.xpath).xpath_expr)
        elif len(nodes) < self.min_occ:
            raise XMLNodeOccurrenceError("Expected at least %d results for node '%s'. Found %d matching nodes." % (
                self.min_occ, XPath.reverse(context_element).append(self.xpath).xpath_expr, len(nodes)
            ))
        elif len(nodes) > self.max_occ:
            raise XMLNodeOccurrenceError("Expected no more than %d results for node '%s'. Found %d matching nodes." % (
                self.max_occ, XPath.reverse(context_element).append(self.xpath).xpath_expr, len(nodes)
            ))

class XMLSimpleNode(XMLNode):
    def _failNoTextValue(self, element):
        raise XMLNodeNotFound("Element '%s' has no text value." % XPath.reverse(element))
    
    def _getValueFromElement(self, element, graceful=True):
        return None
    
    def _getValueFromAttribute(self, attr, graceful=True):
        return None

    def _getNodeValues(self, nodes):
        node_type = self.xpath.getNodeType()
        
        if node_type == "attribute":
            return [self._getValueFromAttribute(attr) for attr in nodes]
        else:
            return [self._getValueFromElement(element) for element in nodes]

class XMLStringNode(XMLSimpleNode):
    def _getValueFromElement(self, element):
        if hasattr(element.firstChild, "data"):
            return element.firstChild.data
        else:
            return self._failNoTextValue(element)
    
    def _getValueFromAttribute(self, attr):
        return attr.value

class XMLIntNode(XMLSimpleNode):
    def _getValueFromElement(self, element):
        if hasattr(element.firstChild, "data"):
            try:
                return int(element.firstChild.data)
            except:
                raise XMLTypeError("Element '%s' value not of type int." % element.tagName)
        else:
            return self._failNoTextValue(element)
    
    def _getValueFromAttribute(self, attr):
        try:
            return int(attr.value)
        except:
            raise XMLTypeError("Attribute '%s' value not of type int." % attr.name)

class XMLFloatNode(XMLSimpleNode):
    def _getValueFromElement(self, element):
        if hasattr(element.firstChild, "data"):
            try:
                return float(element.firstChild.data)
            except:
                raise XMLTypeError("Element '%s' value not of type float." % element.tagName)
        else:
            return self._failNoTextValue(element)
    
    def _getValueFromAttribute(self, attr):
        try:
            return float(attr.value)
        except:
            raise XMLTypeError("Attribute '%s' value not of type float." % attr.name)
            
class XMLIntListNode(XMLSimpleNode):
    def _getValueFromElement(self, element):
        if hasattr(element.firstChild, "data"):
            values = []
            for i in element.firstChild.data.split():
                try:
                    value = int(i)
                except:
                    raise XMLTypeError("Element '%s' value not of type intlist" % element.tagName)
                values.append(value)
            return values
        else:
            self._failNoTextValue(element)
    
    def _getValueFromAttribute(self, attr):
        values = []
        
        for i in attr.value.split():
            try:
                value = int(i)
            except:
                raise XMLTypeError("Attribute '%s' value not of type intlist" % attr.name)
            
            values.append(value)
        
        return values

class XMLFloatListNode(XMLSimpleNode):
    def _getValueFromElement(self, element):
        if hasattr(element.firstChild, "data"):
            values = []
            for f in element.firstChild.data.split():
                try:
                    value = float(f)
                except:
                    raise XMLTypeError("Element '%s' value not of type floatlist" % element.tagName)
                values.append(value)
            return values
        else:
            self._failNoTextValue(element)
    
    def _getValueFromAttribute(self, attr):
        values = []
        
        for f in attr.value.split():
            try:
                value = float(f)
            except:
                raise XMLTypeError("Attribute '%s' value not of type floatlist" % attr.name)
            
            values.append(value)
        
        return values

class XMLNodeProperty(XMLNode):
    def isNodeProperty(self):
        return True

class XMLTagName(XMLNodeProperty):
    def _getNodeValues(self, nodes):
        values = []
        
        for node in nodes:
            if not node.prefix:
                values.append(node.localName)
            else:
                values.append("%s:%s" % (node.prefix, node.localName))
    
        return values

class XMLLocalName(XMLNodeProperty):
    def _getNodeValues(self, nodes):
        return [node.localName for node in nodes]

class XMLPrefix(XMLNodeProperty):
    def _getNodeValues(self, nodes):
        values = []
        
        for node in nodes:
            if not node.prefix:
                values.append("")
            else:
                values.append(node.prefix)
        
        return values

class XMLDOMNode(XMLNodeProperty):
    def _getNodeValues(self, nodes):
        return nodes

class XMLComplexNode(XMLNode):
    pass

class XMLNodeDict(XMLComplexNode):
    def __init__(self, xpath_expr, min_occ, max_occ, sub_nodes):
        super(XMLNodeDict, self).__init__(xpath_expr, min_occ, max_occ)
        
        self.sub_nodes = sub_nodes
    
    def _getNodeValues(self, nodes):
        values = []
        
        for node in nodes:
            value = {}
            
            for key, sub_node in self.sub_nodes.items():
                value[key] = sub_node.getValue(node)
            
            values.append(value)
        
        return values

#-----------------------------------------------------------------------
# XML Decoder
#-----------------------------------------------------------------------

class XMLDecoder(Decoder):
    """
    This class provides XML Decoding facilities.
    
    See docs/sphinx/en/developers/core/util/xmltools.rst for
    comprehensive documentation.
    """
    def _setParamsDefault(self):
        self.input_xml = ""
        self.dom = None
    
    def setParams(self, params):
        self.input_xml = params
        
        try:
            self.dom = xml.dom.minidom.parseString(self.input_xml)
        except Exception, e:
            raise XMLDecoderException("Could not parse input XML. Exception was '%s'" % str(e))
        
    def setSchema(self, schema):
        self.schema = schema
        
        if schema is not None:
            self.nodes = self._getNodesFromSchema(schema)
        else:
            self.nodes = {}
            
    def _getNodeFromConf(self, key, conf):
        if "xml_location" in conf:
            xpath_expr = conf["xml_location"]
        else:
            raise InternalError("XML decoding schema has no 'xml_location' entry for key '%s'" % key)
        
        if "xml_type" in conf:
            type_expr = conf["xml_type"]
        else:
            raise InternalError("XML decoding schema has no 'xml_type' entry for key '%s'" % key)
        
        type_name, min_occ, max_occ = self._parseTypeExpression(type_expr)
        
        if type_name == "string":
            return XMLStringNode(xpath_expr, min_occ, max_occ)
        elif type_name == "int":
            return XMLIntNode(xpath_expr, min_occ, max_occ)
        elif type_name == "float":
            return XMLFloatNode(xpath_expr, min_occ, max_occ)
        elif type_name == "intlist":
            return XMLIntListNode(xpath_expr, min_occ, max_occ)
        elif type_name == "floatlist":
            return XMLFloatListNode(xpath_expr, min_occ, max_occ)
        elif type_name == "tagName":
            return XMLTagName(xpath_expr, min_occ, max_occ)
        elif type_name == "localName":
            return XMLLocalName(xpath_expr, min_occ, max_occ)
        elif type_name == "element" or type_name == "attr":
            return XMLDOMNode(xpath_expr, min_occ, max_occ)
        elif type_name == "dict":
            if "xml_dict_elements" in conf:
                sub_schema = conf["xml_dict_elements"]
                
                return XMLNodeDict(xpath_expr, min_occ, max_occ, self._getNodesFromSchema(sub_schema))
            else:
                raise InternalError("XML decoding schema has no 'xml_dict_elements' entry for key '%s'" % key)

    def _getNodesFromSchema(self, schema):
        nodes = {}
        
        for key, conf in schema.items():
            nodes[key] = self._getNodeFromConf(key, conf)
        
        return nodes
   
    def _getValueDefault(self, xpath_expr):
        if self.dom is None:
            raise InternalError("No input XML given.")
        
        node = XMLStringNode(xpath_expr, 1, 1)
        
        return node.getValue(self.dom.documentElement)

    def _getValueSchema(self, key):
        if self.dom is None:
            raise InternalError("No input XML given.")
        
        if key in self.nodes:
            node = self.nodes[key]
            
            return node.getValue(self.dom.documentElement)
        else:
            raise InternalError("No schema entry for key '%s'." % key)
    
    def getParams(self):
        return self.input_xml
    
    def getParamType(self):
        return "xml"
        
XMLDecoder = DecoderInterface.implement(XMLDecoder)

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
