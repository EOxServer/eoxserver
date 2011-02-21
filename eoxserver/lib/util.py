#-----------------------------------------------------------------------
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

import os
import os.path
import xml.dom.minidom
import re
from fnmatch import fnmatch
from datetime import datetime, tzinfo, timedelta
from cgi import escape, parse_qs
from sys import maxint

from django.http import QueryDict

from eoxserver.lib.exceptions import (EOxSInternalError, EOxSKVPException,
    EOxSXMLException, EOxSXMLNodeNotFound, EOxSXMLContentTypeError,
    EOxSUnknownParameterFormatException
)

import logging

class EOxSXMLEncoder(object):
    def __init__(self):
        super(EOxSXMLEncoder, self).__init__()
        
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
                raise EOxSInternalError("Encoding error: unknown namespace prefix '%s'" % prefix)
        else:
            element = self.dom.createElement(tag_name)

        if isinstance(content, xml.dom.minidom.Element):
            element.appendChild(content)
        elif type(content) == type([]):
            for subcontent in content:
                if not type(subcontent) == type(()):
                    raise EOxSInternalError("Encoding error: expecting tuples with 1 or 3 entries")
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
                                raise EOxSXMLEncodingException("Encoding error: unknown namespace prefix '%s'" % attr_prefix)
                        else:
                            element.setAttribute(attr_name, str(child_content))
                    else:
                        element.appendChild(self._makeElement(child_prefix, child_tag_name, child_content))
                elif len(subcontent) == 1:
                    element.appendChild(subcontent[0])
                else:
                    raise EOxSInternalError("Encoding error: tuples must have 1 or 3 entries")
        else:
            element.appendChild(self.dom.createTextNode(str(content)))
            
        return element

class EOxSXPath(object):
    def __init__(self, init_data):
        if isinstance(init_data, list):
            self.xpath = init_data
            self.xpath_expr = self.listToXPathExpr(init_data)
        else:
            self.xpath_expr = str(init_data)
            self.xpath = self.XPathExprToList(init_data)

    @classmethod
    def XPathExprToList(cls, xpath_expr):
        if xpath_expr.startswith("/"):
            xpath = ["/"]
        else:
            xpath = []
        
        if xpath_expr.lstrip("/"):
            xpath.extend(xpath_expr.lstrip("/").split("/"))
        
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
        logging.debug("Element: %s:%s XPath: %s" % (element.prefix, element.localName, str(xpath)))
        
        if len(xpath) == 0:
            return [element]
        else:
            locator = xpath[0]
            
            if locator == "/":
                if isinstance(element.parentNode, xml.dom.minidom.Document):
                    return self._getNodesXPath(element, xpath[1:])
                else:
                    raise EOxSInternalError("Absolute XPath expressions can only be applied to the document root element.")
            elif locator == "*":
                nodes = []
                
                child_elements = filter(lambda node: isinstance(node, xml.dom.minidom.Element), element.childNodes)
                for child_element in child_elements:
                    nodes.extend(self._getNodesXPath(child_element, xpath[1:]))
                    
                return nodes
            elif locator == "@*":
                if len(xpath) > 1:
                    raise EOxSInternalError("Attribute locators must be the final node in XPath expressions")
                else:
                    attrs = element.attributes
                    if attrs is None:
                        return []
                    else:
                        return list(attrs)
            elif locator.startswith("@"):
                if len(xpath) > 1:
                    raise EOxSInternalError("Attribute locators must be the final node in XPath expressions")
                else:
                    attr = element.getAttributeNode(locator.lstrip("@"))
                    if attr is None:
                        return []
                    else:
                        return [attr]
            else:
                nodes = []
                
                child_elements = filter(lambda node: isinstance(node, xml.dom.minidom.Element) and node.tagName == locator, element.childNodes)
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

class EOxSXMLNode(object):
    def __init__(self, xpath_expr, min_occ=1, max_occ=1):
        self.xpath = EOxSXPath(xpath_expr)
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
            raise EOxSXMLNodeNotFound("Node '%s' not found." % EOxSXPath.reverse(context_element).append(self.xpath).xpath_expr)
        elif len(nodes) < self.min_occ:
            raise EOxSXMLNodeOccurrenceError("Expected at least %d results for node '%s'. Found %d matching nodes." % (
                self.min_occ, EOxSXPath.reverse(context_element).append(self.xpath).xpath_expr, len(nodes)
            ))
        elif len(nodes) > self.max_occ:
            raise EOxSXMLNodeOccurenceError("Expected no more than %d results for node '%s'. Found %d matching nodes." % (
                self.max_occ, EOxSXPath.reverse(context_element).append(self.xpath).xpath_expr, len(nodes)
            ))

class EOxSXMLSimpleNode(EOxSXMLNode):
    def _failNoTextValue(self, element):
        raise EOxSXMLNodeNotFound("Element '%s' has no text value." % EOxSXPath.reverse(element))
    
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

class EOxSXMLStringNode(EOxSXMLSimpleNode):
    def _getValueFromElement(self, element):
        if hasattr(element.firstChild, "data"):
            return element.firstChild.data
        else:
            return self._failNoTextValue(element)
    
    def _getValueFromAttribute(self, attr):
        return attr.value

class EOxSXMLIntNode(EOxSXMLSimpleNode):
    def _getValueFromElement(self, element):
        if hasattr(elements.firstChild, "data"):
            try:
                return int(element.firstChild.data)
            except:
                raise EOxSXMLContentTypeError("Element '%s' value not of type int." % element.tagName)
        else:
            return self._failNoTextValue(element)
    
    def _getValueFromAttribute(self, attr):
        try:
            return int(attr.value)
        except:
            raise EOxSXMLContentTypeError("Attribute '%s' value not of type int." % attr.name)

class EOxSXMLFloatNode(EOxSXMLSimpleNode):
    def _getValueFromElement(self, element):
        if hasattr(element.firstChild, "data"):
            try:
                return float(element.firstChild.data)
            except:
                raise EOxSXMLContentTypeError("Element '%s' value not of type float." % element.tagName)
        else:
            return self._failNoTextValue(element)
    
    def _getValueFromAttribute(self, attr):
        try:
            return float(attr.value)
        except:
            raise EOxSXMLContentTypeError("Attribute '%s' value not of type float." % attr.name)
            
class EOxSXMLIntListNode(EOxSXMLSimpleNode):
    def _getValueFromElement(self, element):
        if hasattr(element.firstChild, "data"):
            values = []
            for i in element.firstChild.data.split():
                try:
                    value = int(i)
                except:
                    raise EOxSXMLContentTypeError("Element '%s' value not of type intlist" % element.tagName)
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
                raise EOxSXMLContentTypeError("Attribute '%s' value not of type intlist" % attr.name)
            
            values.append(value)
        
        return values

class EOxSXMLFloatListNode(EOxSXMLSimpleNode):
    def _getValueFromElement(self, element):
        if hasattr(element.firstChild, "data"):
            values = []
            for f in element.firstChild.data.split():
                try:
                    value = float(f)
                except:
                    raise EOxSXMLContentTypeError("Element '%s' value not of type floatlist" % element.tagName)
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
                raise EOxSXMLContentTypeError("Attribute '%s' value not of type floatlist" % attr.name)
            
            values.append(value)
        
        return values

class EOxSXMLNodeProperty(EOxSXMLNode):
    def isNodeProperty(self):
        return True

class EOxSXMLTagName(EOxSXMLNodeProperty):
    def _getNodeValues(self, nodes):
        values = []
        
        for node in nodes:
            if not node.prefix:
                values.append(node.localName)
            else:
                values.append("%s:%s" % (node.prefix, node.localName))
    
        return values

class EOxSXMLLocalName(EOxSXMLNodeProperty):
    def _getNodeValues(self, nodes):
        return [node.localName for node in nodes]

class EOxSXMLPrefix(EOxSXMLNodeProperty):
    def _getNodeValues(self, nodes):
        values = []
        
        for node in nodes:
            if not node.prefix:
                values.append("")
            else:
                values.append(node.prefix)
        
        return values

class EOxSXMLDOMNode(EOxSXMLNodeProperty):
    def _getNodeValues(self, nodes):
        return nodes

class EOxSXMLComplexNode(EOxSXMLNode):
    pass

class EOxSXMLNodeDict(EOxSXMLComplexNode):
    def __init__(self, xpath_expr, min_occ, max_occ, sub_nodes):
        super(EOxSXMLNodeDict, self).__init__(xpath_expr, min_occ, max_occ)
        
        self.sub_nodes = sub_nodes
    
    def _getNodeValues(self, nodes):
        values = []
        
        for node in nodes:
            value = {}
            
            for key, sub_node in self.sub_nodes.items():
                value[key] = sub_node.getValue(node)
            
            values.append(value)
        
        return values

class EOxSXMLDecoder(object):
    def __init__(self, input_xml, schema=None):
        super(EOxSXMLDecoder, self).__init__()
        
        self.input_xml = input_xml
        try:
            self.dom = xml.dom.minidom.parseString(self.input_xml)
        except Exception, e:
            raise EOxSXMLException("Could not parse input XML. Exception was '%s'" % str(e))
        
        self.setSchema(schema)
    
    def setSchema(self, schema):
        self.schema = schema
        
        if schema is not None:
            self.nodes = self._getNodesFromSchema(schema)
        else:
            self.nodes = {}

    def _parseTypeExpression(self, type_expr):
        match = re.match(r'([A-Za-z]+)(\[(\d+)?(:(\d+)?)?\])?', type_expr)
        
        if match is None:
            raise EOxSInternalError("Invalid XML decoding schema type expression '%s'" % type_expr)
        
        type_expr = match.group(1)
        
        if match.group(2):
            if match.group(3) and match.group(5):
                min_occ = int(match.group(3))
                max_occ = int(match.group(5))
            elif match.group(3) and match.group(4):
                min_occ = int(match.group(3))
                max_occ = maxint
            elif match.group(3):
                min_occ = int(match.group(3))
                max_occ = min_occ
            elif match.group(5):
                min_occ = 0
                max_occ = int(match.group(5))
            else:
                min_occ = 0
                max_occ = maxint
        else:
            min_occ = 1
            max_occ = 1
        
        return (type_expr, min_occ, max_occ)
            
    def _getNodeFromConf(self, key, conf):
        if "xml_location" in conf:
            xpath_expr = conf["xml_location"]
        else:
            raise EOxSInternalError("XML decoding schema has no 'xml_location' entry for key '%s'" % key)
        
        if "xml_type" in conf:
            type_expr = conf["xml_type"]
        else:
            raise EOxSInternalError("XML decoding schema has no 'xml_type' entry for key '%s'" % key)
        
        type_name, min_occ, max_occ = self._parseTypeExpression(type_expr)
        
        if type_name == "string":
            return EOxSXMLStringNode(xpath_expr, min_occ, max_occ)
        elif type_name == "int":
            return EOxSXMLIntNode(xpath_expr, min_occ, max_occ)
        elif type_name == "float":
            return EOxSXMLFloatNode(xpath_expr, min_occ, max_occ)
        elif type_name == "intlist":
            return EOxSXMLIntListNode(xpath_expr, min_occ, max_occ)
        elif type_name == "floatlist":
            return EOxSXMLFloatListNode(xpath_expr, min_occ, max_occ)
        elif type_name == "tagName":
            return EOxSXMLTagName(xpath_expr, min_occ, max_occ)
        elif type_name == "localName":
            return EOxSXMLLocalName(xpath_expr, min_occ, max_occ)
        elif type_name == "element" or type_name == "attr":
            return EOxSXMLDOMNode(xpath_expr, min_occ, max_occ)
        elif type_name == "dict":
            if "xml_dict_elements" in conf:
                sub_schema = conf["xml_dict_elements"]
                
                return EOxSXMLNodeDict(xpath_expr, min_occ, max_occ, self._getNodesFromSchema(sub_schema))
            else:
                raise EOxSInternalError("XML decoding schema has no 'xml_dict_elements' entry for key '%s'" % key)

    def _getNodesFromSchema(self, schema):
        nodes = {}
        
        for key, conf in schema.items():
            nodes[key] = self._getNodeFromConf(key, conf)
        
        return nodes
   
    def _getValueDefault(self, xpath_expr):
        node = EOxSXMLStringNode(xpath_expr, 1, 1)
        
        return node.getValue(self.dom.documentElement)

    def _getValueSchema(self, key):
        if key in self.nodes:
            node = self.nodes[key]
            
            return node.getValue(self.dom.documentElement)
        else:
            raise EOxSInternalError("No schema entry for key '%s'." % key)
    
    def getValue(self, expr):
        if self.schema is None:
            return self._getValueDefault(expr)
        else:
            return self._getValueSchema(expr)
    
    def getParams(self):
        return self.input_xml
    
    def getParamType(self):
        return "xml"

class EOxSKVPDecoder(object):
    def __init__(self, kvp, schema=None):
        super(EOxSKVPDecoder, self).__init__()
        
        self.kvp = kvp
        self.schema = schema
        
        self.param_dict = self._getParamDict()
        
    def _getParamDict(self):
        if isinstance(self.kvp, QueryDict):
            param_dict = {}
            for key, values in self.kvp.lists():
                param_dict[key.lower()] = values
        
        else:
            tmp = parse_qs(self.kvp)
            param_dict = {}
            for key, values in tmp.items():
                param_dict[key.lower()] = values
        
        return param_dict
    
    def setSchema(self, schema):
        self.schema = schema
        
    def _getValueDefault(self, key):
        if key.lower() in self.param_dict:
            return self.param_dict[key.lower()][-1]
        else:
            return None
    
    def _getValueSchema(self, key):
        if key in self.schema:
            if "kvp_key" in self.schema[key]:
                kvp_key = self.schema[key]["kvp_key"]
            else:
                kvp_key = key
            
            if "kvp_type" in self.schema[key]:
                kvp_type = self.schema[key]["kvp_type"]
            else:
                kvp_type = "string"
            
            if kvp_key.lower() in self.param_dict:
                values = self.param_dict[kvp_key.lower()]
                
                if kvp_type.endswith("[]"):
                    if kvp_type == "string[]":
                        return values
                    elif kvp_type == "int[]":
                        return [int(value) for value in values]
                    elif kvp_type == "float[]":
                        return [float(value) for value in values]
                    else:
                        raise EOxSInternalError("Unknown KVP Item Type '%s'." % kvp_type)
                else:
                    if len(values) > 1:
                        raise EOxSKVPException("Ambiguous result for KVP key '%s'. Single occurence expected." % kvp_key)
                    else:
                        raw_value = values[0]
                    
                        if kvp_type == "string":
                            return raw_value
                        elif kvp_type == "stringlist":
                            return raw_value.split(",")
                        elif kvp_type == "int":
                            return int(raw_value)
                        elif kvp_type == "intlist":
                            return [int(i) for i in raw_value.split(",")]
                        elif kvp_type == "float":
                            return float(raw_value)
                        elif kvp_type == "floatlist":
                            return [float(f) for f in raw_value.split(",")]
                        else:
                            raise EOxSInternalError("Unknown KVP item type '%s'" % kvp_type)
            else:
                return None
            
        else:
            return None
        
    def getValue(self, key):
        if self.schema is None:
            return self._getValueDefault(key)
        else:
            return self._getValueSchema(key)
    
    def getParams(self):
        return self.param_dict
    
    def getParamType(self):
        return "kvp"

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
    
def findFiles(dir, pattern):
    filenames = []
    
    for path in os.listdir(dir):
        if os.path.isdir(os.path.join(dir, path)):
            filenames.extend(findFiles(os.path.join(dir, path), pattern))
        elif fnmatch(path, pattern):
            filenames.append(os.path.join(dir, path))
    
    return filenames

class EOxSUTCOffsetTimeZoneInfo(tzinfo):
    def __init__(self):
        super(EOxSUTCOffsetTimeZoneInfo, self).__init__
        
        self.offset_td = timedelta()
    
    def setOffsets(self, offset_sign, offset_hours, offset_minutes):
        if offset_sign == "+":
            self.offset_td = timedelta(hours = offset_hours, minutes = offset_minutes)
        else:
            self.offset_td = timedelta(hours = -offset_hours, minutes = -offset_minutes)
    
    def utcoffset(self, dt):
        return self.offset_td
    
    def dst(self, dt):
        return timedelta()
    
    def tzname(self, dt):
        return None

def getDateTime(s):
    match = re.match(r"(\d{4})-(\d{2})-(\d{2})(T(\d{2}):(\d{2}):(\d{2})(Z|([+-])(\d{2}):?(\d{2})?)?)?", s)
    if match is None:
        raise EOxSUnknownParameterFormatException("'%s' does not match any known datetime format." % s)
    
    year = int(match.group(1))
    month = int(match.group(2))
    day = int(match.group(3))
    
    if match.group(4) is None:
        hour = 0
        minute = 0
        second = 0
        offset_sign = "+"
        offset_hours = 0
        offset_minutes = 0
    else:
        hour = int(match.group(5))
        minute = int(match.group(6))
        second = int(match.group(7))
        
        if match.group(8) is None or match.group(8) == "Z":
            offset_sign = "+"
            offset_hours = 0
            offset_minutes = 0
        else:
            offset_sign = match.group(9)
            offset_hours = int(match.group(10))
            if match.group(11) is None:
                offset_minutes = 0
            else:
                offset_minutes = int(match.group(11))
    
    tzi = EOxSUTCOffsetTimeZoneInfo()
    tzi.setOffsets(offset_sign, offset_hours, offset_minutes)
    
    try:
        dt = datetime(year, month, day, hour, minute, second, 0, tzi)
    except ValueError, e:
        raise EOxSUnknownParameterFormatException("Invalid date/time '%s'" % s) # TODO: change to EOxSInvalidParameterException
    
    utc = EOxSUTCOffsetTimeZoneInfo()
    utct = dt.astimezone(utc)
    
    #logging.debug("Original datetime: %s" % dt.strftime("%Y-%m-%dT%H:%M:%S"))
    #logging.debug("UTC Offset: %s" % str(dt.utcoffset()))
    #logging.debug("offset_sign: %s, offset_hours: %d, offset_minutes: %d" % (offset_sign, offset_hours, offset_minutes))
    #logging.debug("UTC Time: %s" % utct.strftime("%Y-%m-%dT%H:%M:%S"))
    
    return utct

def isotime(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    
def getSRIDFromCRSURI(uri):
    match = re.match(r"urn:ogc:def:crs:EPSG:\d*\.?\d*:(\d+)", uri)
    
    if match is not None:
        return int(match.group(1))
    else:
        match = re.match(r"http://www.opengis.net/def/crs/EPSG/\d+\.?\d*/(\d+)", uri)
        
        if match is not None:
            return int(match.group(1))
        else:
            return None

def posListToWkt(pos_list):
    return ",".join("%f %f" % (pos_list[2*c], pos_list[2*c+1]) for c in range(0, len(pos_list) / 2))
