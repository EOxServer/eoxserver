.. Module eoxserver.core.util.kvptools

.. _module_core_util_kvptools:

Module eoxserver.core.util.kvptools
===================================

.. automodule:: eoxserver.core.util.kvptools

.. _kvp_schemas:

Decoding Schemas
----------------

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
  
   .. method:: getValueStrict(expr)
  
   .. method:: getParams
  
   .. method:: getParamType
