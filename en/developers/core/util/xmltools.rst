.. Module eoxserver.core.util.xmltools
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Stephan Krause <stephan.krause@eox.at>
  #          Stephan Meissl <stephan.meissl@eox.at>
  #
  #-----------------------------------------------------------------------------
  # Copyright (C) 2011 EOX IT Services GmbH
  #
  # Permission is hereby granted, free of charge, to any person obtaining a copy
  # of this software and associated documentation files (the "Software"), to
  # deal in the Software without restriction, including without limitation the
  # rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
  # sell copies of the Software, and to permit persons to whom the Software is
  # furnished to do so, subject to the following conditions:
  #
  # The above copyright notice and this permission notice shall be included in
  # all copies of this Software or works derived from this Software.
  #
  # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
  # FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
  # IN THE SOFTWARE.
  #-----------------------------------------------------------------------------

.. _module_core_util_xmltools:

Module eoxserver.core.util.xmltools
===================================

.. automodule:: eoxserver.core.util.xmltools

.. _xml_schemas:

XML Decoding Schemas
--------------------

XML decoding schemas can be defined following the general rules for
schemas defined in the :ref:`module_core_util_decoders`. The XML
decoder expects ``xml_location`` for the location parameter and
``xml_type`` for the type definition parameter. That means, XML decoding
schemas generally have the form::

    PARAM_SCHEMA = {
        "<parameter_name>": {
            "xml_location": "<xpath_expr>",
            "xml_type": "<type_definition>"
        },
        ...
    }

where

* ``xpath_expr`` is an XPath expression which designates the element or
  attribute to be evaluated,
* ``type_definition`` is a valid type definition as defined in
  :ref:`module_core_util_decoders`.

EOxServer only supports a small subset of XPath expressions, see the
class documentation of :class:`~.XPath` below. Relative XPath
expressions are interpreted to be refer to the document root element.
The valid base type names for XML decoders are:

* ``string``: the string value of the parameter is returned as is,
* ``int``: the value will be typecasted to an integer; an exception is
  raised if the cast fails
* ``float``: the value will be typecasted to a float; an exception is
  raised if the cast fails
* ``intlist``: the value is expected to be a list of integers separated
  by whitespace; a list of integers will be returned; if typecasting
  fails, an exception is raised
* ``floatlist``: the value is expected to be a list of floats separated
  by whitespace; a list of floats will be returned; if typecasting
  fails, an exception is raised.
* ``tagName``: return the tag name of the designated element
* ``localName``: return the local name of the designated element
* ``element``: return the designated DOM Element
* ``attr``: return the designated DOM Attribute mode
* ``dict``: return a dictionary of values; the values will be retrieved
  according to a subschema given by the entry ``xml_dict_elements``; the
  subschema follows the same rules as any decoding schema with the
  exception that relative XPath expressions are rooted at the element
  designated by ``xml_location`` instead of the document root element
  

Minimum and maximum occurrences can be defined as described for the 
:ref:`module_core_util_decoders` and will be validated.

XML Decoder
-----------

.. class:: eoxserver.core.util.xmltools.XMLDecoder

   This class provides XML Decoding facilities.

   .. method:: XMLDecoder(params=None, schema=None)
   
      The constructor accepts two optional arguments:
      
      * ``params`` is expected to be either a string containing
        well-formed XML;
      * ``schema`` is expected to be a schema as described under 
        :ref:`xml_schemas` above.

   .. method:: setParams(params)

      This method accepts one mandatory parameter ``params`` which is
      expected to be a string containing well-formed XML.
      
      The input ``params`` is parsed into a DOM structure using
      Python's :mod:`xml.dom.minidom` module.
  
   .. method:: setSchema(schema)
   
      This method accepts an XML decoding schema as described under 
      :ref:`xml_schemas` above and sets the internal schema to this
      value.
      
      Internally, the schema is parsed into a node structure.
      :exc:`~.InternalError` is raised in case the schema does not
      validate.
      
   .. method:: getValue(expr, default=None)
   
      This method accepts an expression `expr` and a default value
      `default` as input.
      
      If no schema has been defined, ``expr`` will be interpreted as an
      XPath expression. The string value of the element text is
      returned; if the value is missing ``default`` is returned.
      
      If a schema has been defined, ``expr`` will be looked up in the
      schema, and the according value will be returned. If it is not
      found, ``default`` will be returned.
      
      This method raises a :exc:`~.XMLNodeOccurrenceError` if the
      minimum or maximum occurrence bounds for the given XML element are
      violated. In case the text value of the XML element or attribute
      could not be casted to the expected type :exc:`~.XMLTypeError` is
      raised. In case  ``expr`` is not defined in the schema
      :exc:`~.InternalError` is raised.
  
   .. method:: getValueStrict(expr)
   
      This method accepts an expression ``expr`` as input. 

      If no schema has been defined, ``expr`` will be interpreted as an
      XPath expression. The string value of the element text is
      returned; if the value is missing :exc:`~.XMLNodeNotFound` will be
      raised.
      
      If a schema has been defined, ``expr`` will be looked up in the
      schema, and the according value will be returned. If it is not
      found, :exc:`~.XMLNodeNotFound` will be raised.
      
      This method raises a :exc:`~.XMLNodeOccurrenceError` if the
      minimum or maximum occurrence bounds for the given XML element are
      violated. In case the text value of the XML element or attribute
      could not be casted to the expected type :exc:`~.XMLTypeError` is
      raised. In case  ``expr`` is not defined in the schema
      :exc:`~.InternalError` is raised.
      
   .. method:: getParams
   
      Returns the input XML.
  
   .. method:: getParamType

      Returns ``"xml"``.

XML Decoding Utilities
----------------------

.. autoclass:: eoxserver.core.util.xmltools.XPath
   :members:


XML Encoder
-----------

.. autoclass:: eoxserver.core.util.xmltools.XMLEncoder
   
   .. automethod:: _initializeNamespaces
   
   .. automethod:: _makeElement

Functions
---------

.. autofunction:: eoxserver.core.util.xmltools.DOMElementToXML

.. autofunction:: eoxserver.core.util.xmltools.DOMtoXML
