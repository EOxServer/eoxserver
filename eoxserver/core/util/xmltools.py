#-----------------------------------------------------------------------
# $Id$
#
# This software is named EOxServer, a server for Earth Observation data.
#
# Copyright (C) 2011 EOX IT Services GmbH
# Authors: Stephan Krause, Stephan Meissl
#
# This file is part of EOxServer <http://www.eoxserver.org>.
#
#    EOxServer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License,
#    or (at your option) any later version.
#
#    EOxServer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with EOxServer. If not, see <http://www.gnu.org/licenses/>.
#
#-----------------------------------------------------------------------

import xml.dom.minidom
import re
from sys import maxint

from eoxserver.core.exceptions import (
    InternalError, XMLDecoderException, XMLNodeNotFound,
    XMLNodeOccurrenceError, XMLTypeError,  XMLEncoderException
)
from eoxserver.core.util.decoders import Decoder, DecoderInterface

import logging

class XMLEncoder(object):
    def __init__(self):
        super(XMLEncoder, self).__init__()
        
        self.ns_dict = self._initializeNamespaces()
        self.dom = self._createDOM()
    
    def _initializeNamespaces(self):
        return {}
    
    def _createDOM(self):
        return xml.dom.minidom.getDOMImplementation().createDocument(None, None, None)
    
    def _makeElement(self, prefix, tag_name, content):
        if prefix != "":
            if prefix in self.ns_dict:
                element = self.dom.createElementNS(self.ns_dict[prefix], "%s:%s" % (prefix, tag_name))
            else:
                raise InternalError("Encoding error: unknown namespace prefix '%s'" % prefix)
        else:
            element = self.dom.createElement(tag_name)

        if isinstance(content, xml.dom.minidom.Element):
            element.appendChild(content)
        elif type(content) == type([]):
            for subcontent in content:
                if not type(subcontent) == type(()):
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

# safe split 

class XPath(object):
    def __init__(self, init_data):
        if isinstance(init_data, list):
            self.xpath = init_data
            self.xpath_expr = self.listToXPathExpr(init_data)
        else:
            self.xpath_expr = str(init_data)
            self.xpath = self.XPathExprToList(init_data)

    @classmethod
    def XPathExprToList(cls, xpath_expr):
        
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
            head1 , sep , tmp = tmp.partition(d)
            xpath.append( head0 + head1 )

        return xpath

    @classmethod
    def listToXPathExpr(cls, xpath):
        if xpath[0] == "/":
            xpath_expr = "/%s" % "/".join(xpath[1:])
        else:
            xpath_expr = "/".join(xpath)
    
        return xpath_expr
    
    @classmethod
    def reverse(cls, node):
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
        return self.xpath[0] == "/"
    
    def append(self, other):
        if not other.isAbsolute():
            xpath = self.xpath
            xpath.extend(other.xpath)
            
            return self.__class__(xpath)
        else:
            return other

    def _getNodesXPath(self, element, xpath):
        logging.debug("Element: {%s}%s XPath: %s" % (element.namespaceURI, element.localName, str(xpath)))
        
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
        return self._getNodesXPath(context_element, self.xpath)

    def getNodeType(self):
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

class XMLDecoder(Decoder):
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

def _getChildNamespaces(node):
    nsmap = {}
    for child in node.childNodes:
        nsmap.update(_getChildNamespaces(child))
    
    if node.attributes is not None:
        for i in range(0, node.attributes.length):
            attr = node.attributes.item(i)
            if attr.namespaceURI is not None and not attr.prefix.startswith("xml"):
                nsmap[attr.prefix] = attr.namespaceURI
    
    if node.namespaceURI is not None and not node.prefix.startswith("xml"):
        nsmap[node.prefix] = node.namespaceURI
    
    return nsmap

def DOMtoXML(xmldom, nsmap=None):
    return DOMElementToXML(xmldom.documentElement, nsmap)

def DOMElementToXML(element, nsmap=None):
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
