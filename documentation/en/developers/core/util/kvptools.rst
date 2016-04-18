.. Module eoxserver.core.util.kvptools
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

.. _module_core_util_kvptools:

Module eoxserver.core.util.kvptools
===================================

.. automodule:: eoxserver.core.util.kvptools

.. _kvp_schemas:

Decoding Schemas
----------------

KVP decoding schemas can be defined following the general rules for
schemas defined in the :ref:`module_core_util_decoders`. The KVP
decoder expects ``kvp_key`` for the location parameter and ``kvp_type``
for the type definition parameter. That means, KVP decoding schemas
generally have the form::

    PARAM_SCHEMA = {
        "<parameter_name>": {
            "kvp_key": "<kvp_key>",
            "kvp_type": "<type_definition>"
        },
        ...
    }

where

* ``kvp_key`` designates the KVP key to be looked for,
* ``type_definition`` is a valid type definition as defined in
  :ref:`module_core_util_decoders`.

The valid base type names for KVP decoders are:

* ``string``: the string value of the parameter is returned as is,
* ``int``: the value will be typecasted to an integer; an exception is
  raised if the cast fails
* ``float``: the value will be typecasted to a float; an exception is
  raised if the cast fails
* ``stringlist``: the value is expected to be a comma separated list;
  a list of strings will be returned
* ``intlist``: the value is expected to be a comma separated list of 
  integers; a list of integers will be returned; if typecasting fails,
  an exception is raised
* ``floatlist``: the value is expected to be a comma separated list of
  floats; a list of floats will be returned; if typecasting fails, an
  exception is raised.

Minimum and maximum occurrences can be defined as described for the 
:ref:`module_core_util_decoders` and will be validated.

Classes
-------

.. class:: eoxserver.core.util.kvptools.KVPDecoder

   This class provides a parameter decoder for key-value-pair
   parameters.

   .. method:: KVPDecoder(params=None, schema=None)
   
      The constructor accepts two optional arguments:
      
      * ``params`` is expected to be either an URL-encoded string or
        a :class:`django.http.QueryDict` instance containing request
        parameter information
      * ``schema`` is expected to be a schema as described under 
        :ref:`kvp_schemas` above.

   .. method:: setParams(params)

      This method accepts one mandatory parameter ``params`` which is
      expected to be either an URL-encoded string or a
      :class:`django.http.QueryDict` instance containing request
      parameter information.
      
      The input ``params`` is converted to a canonical format
      internally. This information can be retrieved using
      :meth:`getParams`.
  
   .. method:: setSchema(schema)
   
      This method accepts a KVP decoding schema as described under 
      :ref:`kvp_schemas` above and sets the internal schema to this
      value. Note that the schema is validated only when
      :meth:`getValue` or :meth:`getValueStrict` are called. Invalid
      schemas will cause exceptions then.
  
   .. method:: getValue(expr, default=None)
   
      This method accepts an expression `expr` and a default value
      `default` as input.
      
      If no schema has been defined, ``expr`` will be interpreted as being
      the key of a key-value-pair. The string value of the last
      occurrence of the key will be returned; if the value is missing
      ``default`` is returned.
      
      If a schema has been defined, ``expr`` will be looked up in the
      schema, and the according value will be returned. If it is not
      found, ``default`` will be returned.
      
      This method raises a :exc:`~.KVPKeyOccurrenceError` if the
      minimum or maximum occurrence bounds for the given KVP key are
      violated. In case the raw value of the KVP could not be casted to
      the expected type :exc:`~.KVPTypeError` is raised. In case 
      ``expr`` is not defined in the schema or an error in the schema
      definition is detected, :exc:`~.InternalError` is raised.
  
   .. method:: getValueStrict(expr)
   
      This method accepts an expression ``expr`` as input. 

      If no schema has been defined, ``expr`` will be interpreted as being
      the key of a key-value-pair. The string value of the last
      occurrence of the key will be returned; if the value is missing
      :exc:`~.KVPKeyNotFound` will be raised.
      
      If a schema has been defined, ``expr`` will be looked up in the
      schema, and the according value will be returned. If it is not
      found, :exc:`~.KVPKeyNotFound` will be raised.
      
      This method raises a :exc:`~.KVPKeyOccurrenceError` if the
      minimum or maximum occurrence bounds for the given KVP key are
      violated. In case the raw value of the KVP could not be casted to
      the expected type :exc:`~.KVPTypeError` is raised. In case 
      ``expr`` is not defined in the schema or an error in the schema
      definition is detected, :exc:`~.InternalError` is raised.
      
   .. method:: getParams
   
      Returns a dictionary of params. The keys of the dictionary
      correspond to the KVP keys provided, the values are lists of
      KVP values (this is to account for multiple definitions for the
      same KVP key).
  
   .. method:: getParamType

      Returns ``"kvp"``.
